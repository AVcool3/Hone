"""Does El Niño / the PDO predict bad snow seasons better than history alone?

The question Hone needs answered before it uses a forecast in a price:
"if we had used this model in past winters, would our odds have been
closer to what happened than the plain historical odds?" This study
answers it honestly:

- **Data** (``forecast_data.py``): ~25,000 station-winters at ~580 SNOTEL
  stations, 1980–2025; ONI (El Niño index) for Aug–Oct, PDO for Sep–Oct —
  readings that exist *before* each winter starts.
- **Bad season** = peak snow water below 70% of the station's normal
  (median), the same rule Hone's quotes default to.
- **Baseline** = Hone's current method: the station's own bad-season rate
  (Jeffreys-smoothed, ``(bad + ½) / (n + 1)``).
- **Models**: the shipped design (``hone.prediction.forecast``: history +
  a regional El Niño / La Niña / PDO shift), a West-wide-only version, and
  a gradient-boosted tree model with location as inputs.
- **Test 1, leave-one-winter-out**: hold out a whole winter (every station
  at once, because they all share that winter's El Niño), fit on the
  rest, predict it. Repeat for all 45 winters.
- **Test 2, forward in time**: for each winter 2006–2025, fit only on the
  winters before it — exactly what Hone would have known.
- **Score** = Brier skill score (BSS) vs the baseline: 1 − Brier(model) /
  Brier(baseline). Above 0 = the model's odds were closer to reality.
  Uncertainty comes from resampling whole winters (there are only ~45
  independent El Niño outcomes, however many stations there are).

Run it:

    python research/prediction/forecast_study.py           # report
    python research/prediction/forecast_study.py --save    # + write the model file

``--save`` writes ``hone/prediction/data/forecast_snow.json``: the
coefficients (fitted on all winters) and, per region, whether the model
passed both tests. Only regions that passed are adjusted in quotes.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

from hone.prediction import forecast as fc

DATA = Path(__file__).parent / "data" / "forecast"
TRIGGER = 0.70          # bad = below 70% of normal (Hone's default)
MIN_SEASONS = 20        # stations with fewer complete winters are dropped
#: Ridge penalties: West-wide slopes are shrunk gently, regional deviations
#: harder (they rest on fewer, correlated stations). The trend columns are
#: a nuisance: fitted so the PDO doesn't soak up climate change, never applied.
L2_WEST, L2_REGION, L2_TREND = 5.0, 50.0, 5.0
FORWARD_FROM = 2006     # forward test predicts winters 2006..last
BOOT = 2000
SEED = 0


# ------------------------------------------------------------------ data
def load(trigger: float = TRIGGER, oni_season: str = fc.ONI_SEASON) -> pd.DataFrame:
    st = pd.read_csv(DATA / "snotel_stations.csv")
    pk = pd.read_csv(DATA / "snotel_peak_swe.csv.gz")
    oni = pd.read_csv(DATA / "oni.csv")
    pdo = pd.read_csv(DATA / "pdo.csv")
    oni = oni[oni.seas == oni_season].set_index("year").anom.rename("oni")
    pdo = pdo[pdo.month.isin(fc.PDO_MONTHS)].groupby("year").pdo.mean().rename("pdo")
    df = pk.merge(st, on="triplet")
    df = df[df.peak_swe_in.notna()]
    n = df.groupby("triplet").season.transform("size")
    df = df[n >= MIN_SEASONS].copy()
    df["region"] = df.state.map(fc.REGION_OF_STATE)
    df = df.dropna(subset=["region"])
    df = df.join(oni, on="season").join(pdo, on="season").dropna(subset=["oni", "pdo"])
    # Decades from the middle of the record, so the trend term averages ~0
    # and leaving it out at prediction time doesn't shift the average.
    df["trend"] = (df.season - df.season.mean()) / 10.0
    df.attrs["trigger"] = trigger
    return df.reset_index(drop=True)


def label(df: pd.DataFrame, train_mask: np.ndarray, trigger: float) -> pd.DataFrame:
    """Bad-season labels and baseline odds using ONLY the training winters.

    Each station's normal (median) comes from its training winters. Training
    rows get a leave-self-out baseline, so the model is fitted on the same
    kind of offset it will see when predicting a winter it hasn't seen.
    """
    out = df.copy()
    med = out[train_mask].groupby("triplet").peak_swe_in.median()
    out["normal"] = out.triplet.map(med)
    out = out[out.normal.notna() & (out.normal > 0)]
    train_mask = train_mask[out.index]
    out["bad"] = (out.peak_swe_in < trigger * out.normal).astype(float)
    k = out[train_mask].groupby("triplet").bad.sum()
    n = out[train_mask].groupby("triplet").bad.size()
    kk, nn = out.triplet.map(k).fillna(0), out.triplet.map(n).fillna(0)
    self_k = np.where(train_mask, out.bad, 0.0)
    self_n = np.where(train_mask, 1.0, 0.0)
    out["clim"] = (kk - self_k + 0.5) / (nn - self_n + 1.0)
    out["train"] = train_mask
    return out.reset_index(drop=True)


# ---------------------------------------------------------------- models
def design(df: pd.DataFrame, west_only: bool = False, trend: bool = True) -> np.ndarray:
    X = np.vstack([fc.features(o, p, r) for o, p, r in zip(df.oni, df.pdo, df.region)])
    if west_only:
        X = X[:, :fc.N_SIGNALS]
    if trend:
        T = np.column_stack([df.trend] + [df.trend * (df.region == r) for r in fc.REGIONS])
        X = np.hstack([X, T])
    return X


def penalties(n_cols: int, west_only: bool, trend: bool) -> np.ndarray:
    k = fc.N_SIGNALS
    n_sig = k if west_only else k * (1 + len(fc.REGIONS))
    l2 = [L2_WEST] * k + [L2_REGION] * (n_sig - k)
    if trend:
        l2 += [L2_TREND] + [L2_REGION] * len(fc.REGIONS)
    assert len(l2) == n_cols
    return np.array(l2, dtype=float)


def fit_predict(train: pd.DataFrame, test: pd.DataFrame, kind: str) -> np.ndarray:
    """Probability of a bad winter for each test row."""
    if kind == "history":
        return test.clim.to_numpy()
    if kind == "trees":
        cols = ["oni", "pdo", "lat", "lon", "elev_ft"]
        Xtr = np.column_stack([fc.logit(train.clim)] + [train[c] for c in cols])
        Xte = np.column_stack([fc.logit(test.clim)] + [test[c] for c in cols])
        m = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, max_leaf_nodes=15,
                                           min_samples_leaf=200, l2_regularization=1.0, random_state=SEED)
        m.fit(Xtr, train.bad)
        return m.predict_proba(Xte)[:, 1]
    west_only = kind == "west"
    Xtr = design(train, west_only)
    beta = fc.fit_offset_logit(Xtr, train.bad.to_numpy(), fc.logit(train.clim.to_numpy()),
                               penalties(Xtr.shape[1], west_only, True))
    n_sig = Xtr.shape[1] - (1 + len(fc.REGIONS))
    # Apply ONLY the climate-signal part: trends are left to the quote engine.
    Xte = design(test, west_only, trend=False)
    return fc.expit(fc.logit(test.clim.to_numpy()) + Xte @ beta[:n_sig])


KINDS = ["history", "west", "regional", "trees"]


def leave_one_winter_out(df: pd.DataFrame, trigger: float, kinds=KINDS) -> pd.DataFrame:
    rows = []
    for s in sorted(df.season.unique()):
        lab = label(df, (df.season != s).to_numpy(), trigger)
        train, test = lab[lab.train], lab[~lab.train]
        if test.empty:
            continue
        preds = {k: fit_predict(train, test, k) for k in kinds}
        rows.append(test[["triplet", "season", "region", "oni", "pdo", "bad"]].assign(**preds))
    return pd.concat(rows, ignore_index=True)


def forward(df: pd.DataFrame, trigger: float, kinds=KINDS) -> pd.DataFrame:
    rows = []
    for s in sorted(df.season.unique()):
        if s < FORWARD_FROM:
            continue
        sub = df[df.season <= s].reset_index(drop=True)
        lab = label(sub, (sub.season < s).to_numpy(), trigger)
        # A station needs a real history before the test winter.
        n_hist = lab[lab.train].groupby("triplet").size()
        lab = lab[lab.triplet.map(n_hist).fillna(0) >= 15]
        train, test = lab[lab.train], lab[~lab.train]
        if test.empty:
            continue
        preds = {k: fit_predict(train, test, k) for k in kinds}
        rows.append(test[["triplet", "season", "region", "oni", "pdo", "bad"]].assign(**preds))
    return pd.concat(rows, ignore_index=True)


# ---------------------------------------------------------------- scoring
def brier(y, p):
    return float(np.mean((np.asarray(p) - np.asarray(y)) ** 2))


def bss(res: pd.DataFrame, kind: str) -> float:
    return 1.0 - brier(res.bad, res[kind]) / brier(res.bad, res.history)


def bss_interval(res: pd.DataFrame, kind: str, n: int = BOOT) -> tuple[float, float]:
    """5th–95th percentile of BSS when whole winters are resampled."""
    rng = np.random.default_rng(SEED)
    seasons = res.season.unique()
    # Per-winter sums make each bootstrap draw cheap.
    g = res.assign(em=(res[kind] - res.bad) ** 2, eh=(res.history - res.bad) ** 2).groupby("season")[["em", "eh"]].sum()
    g = g.loc[seasons].to_numpy()
    draws = []
    for _ in range(n):
        idx = rng.integers(0, len(seasons), len(seasons))
        s = g[idx].sum(axis=0)
        draws.append(1 - s[0] / s[1])
    return float(np.percentile(draws, 5)), float(np.percentile(draws, 95))


def log_loss(y, p):
    p = np.clip(np.asarray(p), 1e-6, 1 - 1e-6)
    y = np.asarray(y)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def phase(oni: float) -> str:
    return "El Niño" if oni >= 0.5 else "La Niña" if oni <= -0.5 else "neutral"


def report(loso: pd.DataFrame, fwd: pd.DataFrame, kinds=KINDS) -> dict:
    out = {"overall": {}, "regions": {}, "phases": {}}
    print(f"\nLeave-one-winter-out: {len(loso):,} station-winters, {loso.season.nunique()} winters, "
          f"bad-season rate {loso.bad.mean():.1%}")
    print(f"Forward test (each winter {FORWARD_FROM}+ predicted from earlier winters only): {len(fwd):,} station-winters\n")
    print(f"{'model':<10} {'mean p':>7} {'Brier':>7} {'logloss':>8} {'BSS':>7} {'90% range':>16} {'fwd BSS':>8}")
    for k in kinds:
        lo, hi = bss_interval(loso, k) if k != "history" else (0.0, 0.0)
        out["overall"][k] = {"brier": brier(loso.bad, loso[k]), "log_loss": log_loss(loso.bad, loso[k]),
                             "bss": bss(loso, k), "bss_5": lo, "bss_95": hi, "bss_forward": bss(fwd, k)}
        o = out["overall"][k]
        print(f"{k:<10} {loso[k].mean():7.3f} {o['brier']:7.4f} {o['log_loss']:8.4f} {o['bss']:+7.3f} [{lo:+.3f}, {hi:+.3f}] {o['bss_forward']:+8.3f}")

    print("\nBy region (shipped 'regional' model vs history):")
    print(f"{'region':<20} {'stations':>8} {'bad%':>6} {'BSS':>7} {'90% range':>16} {'fwd BSS':>8}  skillful")
    for r in fc.REGIONS:
        a, b = loso[loso.region == r], fwd[fwd.region == r]
        if a.empty:
            continue
        lo, hi = bss_interval(a, "regional")
        f = bss(b, "regional") if len(b) else float("nan")
        skill = bool(lo > 0 and f > 0)
        out["regions"][r] = {"stations": int(a.triplet.nunique()), "bad_rate": float(a.bad.mean()),
                             "bss": bss(a, "regional"), "bss_5": lo, "bss_95": hi, "bss_forward": f,
                             "skillful": skill}
        print(f"{r:<20} {a.triplet.nunique():8d} {a.bad.mean():6.1%} {bss(a, 'regional'):+7.3f} "
              f"[{lo:+.3f}, {hi:+.3f}] {f:+8.3f}  {'yes' if skill else 'no'}")

    print("\nBy Pacific phase (leave-one-winter-out):")
    for ph in ["El Niño", "La Niña", "neutral"]:
        a = loso[loso.oni.map(phase) == ph]
        out["phases"][ph] = {"winters": int(a.season.nunique()), "bad_rate": float(a.bad.mean()),
                             **{k: bss(a, k) for k in kinds if k != "history"}}
        print(f"  {ph:<8} {a.season.nunique():3d} winters, bad {a.bad.mean():5.1%}  "
              + "  ".join(f"{k} {bss(a, k):+.3f}" for k in kinds if k != "history"))

    print("\nReliability (regional model, leave-one-winter-out): predicted vs observed")
    bins = pd.cut(loso.regional, [0, .05, .1, .15, .2, .3, .4, .6, 1])
    rel = loso.groupby(bins, observed=True).agg(n=("bad", "size"), predicted=("regional", "mean"), observed=("bad", "mean"))
    print(rel.to_string(float_format=lambda x: f"{x:.3f}"))
    out["reliability"] = rel.reset_index().assign(bin=lambda d: d.regional.astype(str)).drop(columns="regional").to_dict("records")
    return out


def regional_bad_rates(df: pd.DataFrame) -> pd.DataFrame:
    """Plain-numbers view: how often each region had a bad winter by phase."""
    lab = label(df, np.ones(len(df), bool), TRIGGER)
    lab["phase"] = lab.oni.map(phase)
    return lab.pivot_table(index="region", columns="phase", values="bad", aggfunc="mean")


def fit_all(df: pd.DataFrame) -> np.ndarray:
    lab = label(df, np.ones(len(df), bool), TRIGGER)
    X = design(lab)
    beta = fc.fit_offset_logit(X, lab.bad.to_numpy(), fc.logit(lab.clim.to_numpy()),
                               penalties(X.shape[1], False, True))
    return beta, lab


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--save", action="store_true", help="write hone/prediction/data/forecast_snow.json")
    ap.add_argument("--quick", action="store_true", help="skip the slower robustness checks")
    args = ap.parse_args()

    df = load()
    print(f"{df.triplet.nunique()} stations, {df.season.min()}–{df.season.max()}, {len(df):,} station-winters")
    print("\nHow often each region had a bad winter (below 70% of normal), by Pacific phase:")
    print(regional_bad_rates(df).to_string(float_format=lambda x: f"{x:.1%}"))

    loso = leave_one_winter_out(df, TRIGGER)
    fwd = forward(df, TRIGGER)
    res = report(loso, fwd)

    if not args.quick:
        print("\nRobustness: other bad-season rules (shipped model, refitted at each rule)")
        res["triggers"] = {}
        for trig in (0.6, 0.8):
            a = leave_one_winter_out(df, trig, kinds=["history", "regional"])
            res["triggers"][str(trig)] = bss(a, "regional")
            print(f"  below {trig:.0%} of normal: BSS {bss(a, 'regional'):+.3f}  (bad rate {a.bad.mean():.1%})")
        print("\nLead time: El Niño read earlier in the year (Jun–Aug instead of Aug–Oct)")
        early = load(oni_season="JJA")
        a = leave_one_winter_out(early, TRIGGER, kinds=["history", "regional"])
        res["lead_JJA_bss"] = bss(a, "regional")
        print(f"  JJA reading: BSS {bss(a, 'regional'):+.3f}")

    beta, lab = fit_all(df)
    names = fc.feature_names()
    n_sig = len(names)
    print("\nFitted on all winters (log-odds shift per unit of signal; + = more bad winters):")
    coef = pd.Series(beta[:n_sig], index=names)
    total = pd.DataFrame({sig: [coef[f"west:{sig}"] + coef[f"{r}:{sig}"] for r in fc.REGIONS]
                          for sig in fc.SIGNAL_NAMES}, index=fc.REGIONS)
    print(total.to_string(float_format=lambda x: f"{x:+.2f}"))

    if args.save:
        regions = {}
        for r, info in res["regions"].items():
            ev = (f"Tested on {info['stations']} stations over {loso.season.nunique()} past winters: "
                  f"Brier skill {info['bss']:+.1%} vs history alone (range {info['bss_5']:+.1%} to {info['bss_95']:+.1%}), "
                  f"{info['bss_forward']:+.1%} when predicting {FORWARD_FROM}–{int(fwd.season.max())} forward in time.")
            regions[r] = {**info, "evidence": ev}
        st = lab.drop_duplicates("triplet")
        model = {
            "trained": date.today().isoformat(),
            "trigger": TRIGGER, "oni_season": fc.ONI_SEASON, "pdo_months": list(fc.PDO_MONTHS),
            "features": names, "coef": [round(float(b), 5) for b in beta[:n_sig]],
            "oni_range": [float(df.oni.min()), float(df.oni.max())],
            "pdo_range": [float(df.pdo.min()), float(df.pdo.max())],
            "n_station_winters": int(len(df)), "n_stations": int(df.triplet.nunique()),
            "seasons": [int(df.season.min()), int(df.season.max())],
            "regions": regions,
            "overall": res["overall"],
            "stations": [[round(float(a), 3), round(float(b), 3), r] for a, b, r in zip(st.lat, st.lon, st.region)],
            # Per region and winter: [ONI, PDO, share of stations that had a
            # bad winter]. Lets a quote name the most similar past winters.
            "winters": {r: {int(s): [round(float(g.oni.iloc[0]), 2), round(float(g.pdo.iloc[0]), 2), round(float(g.bad.mean()), 3)]
                            for s, g in lab[lab.region == r].groupby("season")} for r in fc.REGIONS},
        }
        fc.MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        fc.MODEL_PATH.write_text(json.dumps(model, indent=1))
        print(f"\nwrote {fc.MODEL_PATH}")
    return res


if __name__ == "__main__":
    main()
