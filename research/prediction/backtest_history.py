"""Backtest the income-hedge model against Kalshi markets that have already settled.

    python research/prediction/backtest_history.py            # fetch what's missing, then analyse
    python research/prediction/backtest_history.py --offline  # cache only, no network
    python research/prediction/backtest_history.py --refresh  # re-download everything

What it does
------------
1. **Data.** For each series in ``SERIES`` it lists every settled market on
   Kalshi's public API — ``/historical/markets`` (markets settled before the
   exchange's historical cutoff) plus ``/markets?status=settled`` (newer
   ones) — and pulls *daily* candlesticks for the last ``WINDOW_DAYS`` days
   of each market's life (``/historical/markets/{t}/candlesticks`` or
   ``/series/{s}/markets/{t}/candlesticks``). A candle carries the closing
   YES bid, YES ask, last trade and open interest for the day, which is
   what a hedger would have seen ``h`` days before the market closed.
   Everything is cached, trimmed and gzipped, under
   ``research/prediction/data/kalshi_history/`` so a re-run needs no network.
2. **Calibration** (question 1). The mid price ``h`` days before close
   (h = 1, 7, 14, 28) against the realized YES/NO: Brier score, log loss,
   a reliability table, and a logistic recalibration
   ``logit P(yes) = a + b * logit(p)``. Every strike in an event is
   resolved by the same number, so the strikes are *not* independent:
   confidence intervals come from a bootstrap that resamples whole events.
3. **Hedge backtest** (question 2). For each settled period a persona
   (``PERSONAS``) is sized with :func:`hone.prediction.hedge.hedge_income`
   at the ask that was on the screen ``h`` days before close, with the
   basis correlation ``research/prediction/segments.py`` assumes, at
   gamma 2/4/8, with and without the open-interest liquidity cap. The
   realized loss is computed from the realized value; the contract pays
   from the market's own result.
4. **Basis** (question 3). The correlation between the contract payoff and
   the persona's realized loss across the history, against the
   ``segments.py`` assumption.

Look-ahead: the persona's budget, strike choice and model loss use only
values settled *before* the entry date and prices on the entry date.
The *measured* basis and the loss model parameters of the contract worker
(hazard elasticity) are in-sample choices and are labelled as such.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
import requests
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from hone.prediction.hedge import (  # noqa: E402
    IncomeExposure,
    crra_inverse,
    crra_utility,
    hedge_income,
)
from hone.prediction.contracts import implied_probability  # noqa: E402
from hone.prediction.liquidity import Liquidity  # noqa: E402

BASE = "https://api.elections.kalshi.com/trade-api/v2"
DATA_DIR = Path(__file__).parent / "data" / "kalshi_history"
RESULTS_CSV = Path(__file__).parent / "data" / "backtest_periods.csv"

#: Series analysed. All are "greater" ladders: YES pays if value > strike.
SERIES = ["KXAAAGASM", "KXCPIYOY", "KXU3", "KXU3MAX", "KXPAYROLLS", "KXFED", "KX30YMORTW"]
#: Days of daily candles kept per market, counted back from close.
WINDOW_DAYS = 40
#: Calibration horizons, days before close.
HORIZONS = [1, 7, 14, 28]
#: A candle at or before the target counts only if it is at most this stale.
MAX_STALE_DAYS = 2.0
#: Mid price is used when the quoted spread is at most this; else the last trade.
MAX_SPREAD_FOR_MID = 0.10
GAMMAS = [2.0, 4.0, 8.0]
#: How the sizing call is fed.
#:  app      - as the Hedge page wires it: price = ask, market_prob = the
#:             catalog's implied probability (bid/ask mid, else last trade),
#:             selling allowed (hedge_income's default)
#:  buy_only - the same, but allow_selling=False (what quote.py does)
#:  no_tilt  - market_prob = price, as segments.py does: the belief equals
#:             the ask, so the position is the pure hedge with no
#:             speculative tilt from the spread
VARIANTS = ["app", "buy_only", "no_tilt"]
DAY = 86400


# =================================================================== fetch
class Api:
    def __init__(self, pause: float = 0.35) -> None:
        # The public API answers ~2-3 requests a second from one client and
        # 429s the rest (no Retry-After header): keep a steady pace and, on a
        # 429, wait a moment and retry rather than backing off exponentially.
        self.s = requests.Session()
        self.pause = pause
        self.calls = 0
        self.throttled = 0

    def get(self, path: str, **params: Any) -> tuple[int, dict]:
        for attempt in range(20):
            try:
                r = self.s.get(BASE + path, params=params, timeout=30)
            except requests.RequestException:
                time.sleep(2.0 * (attempt + 1))
                continue
            self.calls += 1
            time.sleep(self.pause)
            if r.status_code == 429 or r.status_code >= 500:
                self.throttled += 1
                time.sleep(min(0.4 + 0.3 * attempt, 6.0))
                continue
            try:
                return r.status_code, r.json()
            except ValueError:
                return r.status_code, {}
        return 599, {}


def _f(x: Any) -> float | None:
    if x is None or x == "":
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


MARKET_FIELDS = ["ticker", "event_ticker", "market_type", "strike_type", "floor_strike",
                 "cap_strike", "open_time", "close_time", "settlement_ts", "result",
                 "expiration_value", "yes_sub_title", "status"]


def _trim_market(m: dict, source: str) -> dict:
    out = {k: m.get(k) for k in MARKET_FIELDS}
    out["volume"] = _f(m.get("volume_fp", m.get("volume")))
    out["final_open_interest"] = _f(m.get("open_interest_fp", m.get("open_interest")))
    out["source"] = source
    return out


def _list_markets(api: Api, path: str, series: str, status: str | None) -> list[dict]:
    out, cursor = [], None
    while True:
        params: dict[str, Any] = {"series_ticker": series, "limit": 1000}
        if status:
            params["status"] = status
        if cursor:
            params["cursor"] = cursor
        code, d = api.get(path, **params)
        if code != 200:
            print(f"  ! {path} {series}: HTTP {code}", file=sys.stderr)
            break
        out += d.get("markets", [])
        cursor = d.get("cursor")
        if not cursor or not d.get("markets"):
            break
    return out


def _compact_candle(c: dict) -> list:
    """[end_ts, yes_bid, yes_ask, last, open_interest, volume] from either schema."""
    def px(block: str, key: str) -> float | None:
        b = c.get(block) or {}
        return _f(b.get(f"{key}_dollars", b.get(key)))
    return [
        int(c["end_period_ts"]),
        px("yes_bid", "close"),
        px("yes_ask", "close"),
        px("price", "close"),
        _f(c.get("open_interest_fp", c.get("open_interest"))),
        _f(c.get("volume_fp", c.get("volume"))),
    ]


def _ts(iso: str | None) -> int | None:
    if not iso:
        return None
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp())


def fetch_series(api: Api, series: str, refresh: bool = False) -> dict:
    """Markets + candles for one series, from cache when possible."""
    path = DATA_DIR / f"{series}.json.gz"
    cached = {"markets": [], "candles": {}}
    if path.exists() and not refresh:
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            cached = json.load(fh)
        if cached.get("complete"):
            return cached
    print(f"[{series}] listing markets", file=sys.stderr)
    hist = _list_markets(api, "/historical/markets", series, None)
    live = _list_markets(api, "/markets", series, "settled")
    markets: dict[str, dict] = {}
    for m in hist:
        markets[m["ticker"]] = _trim_market(m, "historical")
    for m in live:  # the live listing carries final open interest; prefer it
        markets[m["ticker"]] = _trim_market(m, "live")
    candles: dict[str, list] = dict(cached.get("candles", {}))
    todo = [m for m in markets.values() if m["ticker"] not in candles
            and m.get("result") in ("yes", "no") and m.get("market_type") == "binary"]
    print(f"[{series}] {len(markets)} markets, {len(todo)} need candles", file=sys.stderr)
    for i, m in enumerate(todo):
        close = _ts(m["close_time"])
        opened = _ts(m["open_time"]) or close - WINDOW_DAYS * DAY
        start = max(opened - DAY, close - WINDOW_DAYS * DAY)
        params = dict(start_ts=start, end_ts=close + DAY, period_interval=1440)
        paths = [f"/historical/markets/{m['ticker']}/candlesticks",
                 f"/series/{series}/markets/{m['ticker']}/candlesticks"]
        if m["source"] == "live":
            paths.reverse()
        got = None
        for p in paths:
            code, d = api.get(p, **params)
            if code == 200 and d.get("candlesticks"):
                got = [_compact_candle(c) for c in d["candlesticks"]]
                break
        candles[m["ticker"]] = got or []
        if (i + 1) % 50 == 0:
            print(f"[{series}] {i + 1}/{len(todo)} candles ({api.calls} calls, "
                  f"{api.throttled} throttled, pace {api.pause:.2f}s)", file=sys.stderr)
            _save(path, list(markets.values()), candles, complete=False)
    _save(path, list(markets.values()), candles, complete=True)
    return {"markets": list(markets.values()), "candles": candles, "complete": True}


def _save(path: Path, markets: list, candles: dict, complete: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "window_days": WINDOW_DAYS, "complete": complete,
               "markets": markets, "candles": candles}
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        json.dump(payload, fh, separators=(",", ":"))


def load_all(offline: bool, refresh: bool) -> dict[str, dict]:
    api = Api()
    out = {}
    for s in SERIES:
        p = DATA_DIR / f"{s}.json.gz"
        if offline:
            if not p.exists():
                print(f"[{s}] no cache, skipped", file=sys.stderr)
                continue
            with gzip.open(p, "rt", encoding="utf-8") as fh:
                out[s] = json.load(fh)
        else:
            out[s] = fetch_series(api, s, refresh=refresh)
    if api.calls:
        print(f"{api.calls} API calls", file=sys.stderr)
    return out


# ============================================================ market table
_NUM = re.compile(r"^\s*\$?\s*(-?[\d,]*\.?\d+)\s*%?\s*$")
#: Series whose realized values sit on the strike grid (0.1pp, 25bp): when
#: the value has to be inferred from the strikes' results it is the upper
#: end of the bracket, not its midpoint.
GRID_SERIES = {"KXCPIYOY", "KXU3", "KXU3MAX", "KXFED"}


def _parse_value(s: Any) -> float | None:
    if s is None:
        return None
    m = _NUM.match(str(s))
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


def market_table(data: dict[str, dict]) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    """One row per binary market that settled yes/no; candles keyed by ticker."""
    rows, candles = [], {}
    for series, d in data.items():
        for m in d["markets"]:
            if m.get("market_type") != "binary" or m.get("result") not in ("yes", "no"):
                continue
            c = d["candles"].get(m["ticker"]) or []
            candles[m["ticker"]] = np.array(
                [[np.nan if v is None else v for v in row] for row in c], dtype=float
            ).reshape(-1, 6)
            rows.append({
                "series": series, "ticker": m["ticker"], "event": m["event_ticker"],
                "strike_type": m.get("strike_type"), "strike": _f(m.get("floor_strike")),
                "cap": _f(m.get("cap_strike")), "open_ts": _ts(m.get("open_time")),
                "close_ts": _ts(m.get("close_time")),
                "settle_ts": _ts(m.get("settlement_ts")) or _ts(m.get("close_time")),
                "y": 1 if m["result"] == "yes" else 0,
                "value_raw": m.get("expiration_value"), "volume": m.get("volume") or 0.0,
            })
    df = pd.DataFrame(rows)
    df["value"] = df["value_raw"].map(_parse_value)
    df = _fix_values(df)
    return df, candles


def _fix_values(df: pd.DataFrame) -> pd.DataFrame:
    """Realized value per event: the parsed number when it agrees with every
    strike's result, else the midpoint of the bracket the results imply."""
    out = []
    for _, g in df.groupby("event"):
        g = g.copy()
        gr = g[g.strike_type == "greater"]
        v = g["value"].dropna()
        v = float(v.iloc[0]) if len(v) else None
        consistent = v is not None and all(
            (v > k) == bool(y) for k, y in zip(gr.strike, gr.y)
        )
        if not consistent and len(gr):
            lo = gr.loc[gr.y == 1, "strike"].max()  # value > lo
            hi = gr.loc[gr.y == 0, "strike"].min()  # value <= hi
            if pd.notna(lo) and pd.notna(hi):
                v = hi if g.series.iloc[0] in GRID_SERIES else (lo + hi) / 2
            elif pd.notna(lo):
                v = lo + 0.5 * _step(gr.strike)
            elif pd.notna(hi):
                v = hi if g.series.iloc[0] in GRID_SERIES else hi - 0.5 * _step(gr.strike)
            g["value_inferred"] = True
        else:
            g["value_inferred"] = False
        g["value"] = v
        out.append(g)
    return pd.concat(out, ignore_index=True)


def _step(strikes: pd.Series) -> float:
    s = np.sort(strikes.dropna().unique())
    return float(np.median(np.diff(s))) if len(s) > 1 else 0.1


def quote_at(c: np.ndarray, target_ts: float, open_ts: float | None) -> dict | None:
    """The daily candle a trader would have seen at ``target_ts``."""
    if c.size == 0 or (open_ts is not None and open_ts > target_ts):
        return None
    idx = np.where(c[:, 0] <= target_ts)[0]
    if not len(idx):
        return None
    row = c[idx[-1]]
    if target_ts - row[0] > MAX_STALE_DAYS * DAY:
        return None
    ts, bid, ask, last, oi, vol = row
    bid_ok = np.isfinite(bid) and bid > 0
    ask_ok = np.isfinite(ask) and ask < 1
    mid = None
    source = None
    if bid_ok and ask_ok and ask - bid <= MAX_SPREAD_FOR_MID:
        mid, source = (bid + ask) / 2, "mid"
    elif np.isfinite(last) and 0 < last < 1:
        mid, source = last, "last"
    elif bid_ok and ask_ok:
        mid, source = (bid + ask) / 2, "wide-mid"
    if mid is None:
        return None
    return {"p": float(mid), "src": source,
            "bid": float(bid) if bid_ok else None, "ask": float(ask) if ask_ok else None,
            "last": float(last) if np.isfinite(last) else None,
            "oi": float(oi) if np.isfinite(oi) else None, "ts": float(ts)}


# ============================================================= calibration
BUCKETS = [0, .05, .10, .20, .30, .40, .50, .60, .70, .80, .90, .95, 1.0001]


def calibration_rows(df: pd.DataFrame, candles: dict, h: int) -> pd.DataFrame:
    rows = []
    for r in df.itertuples():
        q = quote_at(candles[r.ticker], r.close_ts - h * DAY, r.open_ts)
        if q is None:
            continue
        rows.append({"series": r.series, "event": r.event, "ticker": r.ticker,
                     "p": q["p"], "src": q["src"], "y": r.y, "h": h})
    return pd.DataFrame(rows)


def _logit(p):
    p = np.clip(p, 0.005, 0.995)
    return np.log(p / (1 - p))


def recalibration(p: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """(a, b) of logit P(y) = a + b logit(p), by maximum likelihood."""
    x = _logit(p)

    def nll(th):
        z = th[0] + th[1] * x
        return float(np.sum(np.logaddexp(0, z) - y * z))
    res = minimize(nll, x0=[0.0, 1.0], method="BFGS")
    return float(res.x[0]), float(res.x[1])


def cluster_boot(cal: pd.DataFrame, stat: Callable[[pd.DataFrame], Any], n: int = 400,
                 seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    groups = {e: g for e, g in cal.groupby("event")}
    keys = list(groups)
    out = []
    for _ in range(n):
        pick = rng.choice(len(keys), size=len(keys), replace=True)
        out.append(stat(pd.concat([groups[keys[i]] for i in pick], ignore_index=True)))
    return np.array(out, dtype=float)


def calib_summary(cal: pd.DataFrame, boot: int = 400) -> dict:
    p, y = cal.p.to_numpy(), cal.y.to_numpy()
    brier = float(np.mean((p - y) ** 2))
    base = float(np.mean(y))
    logloss = float(-np.mean(y * np.log(np.clip(p, 1e-3, 1)) + (1 - y) * np.log(np.clip(1 - p, 1e-3, 1))))
    a, b = recalibration(p, y)
    contested = cal[(cal.p >= 0.05) & (cal.p <= 0.95)]
    bs = cluster_boot(cal, lambda d: [np.mean((d.p - d.y) ** 2), *recalibration(d.p.to_numpy(), d.y.to_numpy()),
                                       np.mean(d.p) - np.mean(d.y)], n=boot)
    ci = lambda j: (float(np.percentile(bs[:, j], 2.5)), float(np.percentile(bs[:, j], 97.5)))
    return {
        "n": len(cal), "events": cal.event.nunique(), "brier": brier,
        "brier_ci": ci(0), "brier_clim": base * (1 - base), "logloss": logloss,
        "a": a, "a_ci": ci(1), "b": b, "b_ci": ci(2),
        "bias": float(np.mean(p) - np.mean(y)), "bias_ci": ci(3),
        "n_contested": len(contested),
        "brier_contested": float(np.mean((contested.p - contested.y) ** 2)) if len(contested) else np.nan,
        "share_last": float(np.mean(cal.src != "mid")),
    }


def reliability(cal: pd.DataFrame, boot: int = 400) -> pd.DataFrame:
    cal = cal.copy()
    cal["bucket"] = pd.cut(cal.p, BUCKETS, right=False)
    out = []
    rng = np.random.default_rng(1)
    for b, g in cal.groupby("bucket", observed=True):
        ev = {e: gg.y.to_numpy() for e, gg in g.groupby("event")}
        keys = list(ev)
        freqs = []
        for _ in range(boot):
            pick = rng.choice(len(keys), size=len(keys), replace=True)
            ys = np.concatenate([ev[keys[i]] for i in pick])
            freqs.append(ys.mean())
        out.append({"bucket": f"{b.left:.2f}-{min(b.right, 1):.2f}", "n": len(g),
                    "events": len(keys), "mean_price": g.p.mean(), "freq_yes": g.y.mean(),
                    "lo": np.percentile(freqs, 2.5), "hi": np.percentile(freqs, 97.5),
                    "gap": g.y.mean() - g.p.mean()})
    return pd.DataFrame(out)


# ============================================================== personas
@dataclass(frozen=True)
class Persona:
    key: str
    label: str
    series: str
    wealth: float
    #: basis correlation segments.py assumes for this occupation
    basis_assumed: float
    #: dollars lost per unit of (realized - budget) above budget
    dollars_per_unit: float = 0.0
    #: for the job-loss persona: a fixed loss and a hazard model instead
    fixed_loss: float | None = None
    hazard: Callable[[float, float], float] | None = None
    note: str = ""


def contractor_hazard(u: float, budget: float, p0: float = 0.03, kappa: float = 1.0) -> float:
    """Monthly probability a contract worker loses their contract.

    3%/month at an unchanged unemployment rate, scaled by exp(kappa * du)
    where du is the realized rate minus the last print (pp). kappa = 1
    means a 0.3pp jump raises the hazard by 35%. Modelling choice; there is
    no single empirical number to anchor it to.
    """
    return float(np.clip(p0 * math.exp(kappa * (u - budget)), 0.0, 1.0))


PERSONAS = [
    Persona("rideshare", "Rideshare/delivery driver, 1,000 gal/month", "KXAAAGASM",
            wealth=15_000, basis_assumed=0.85, dollars_per_unit=1_000,
            note="W = one month's income ($3,750) + 3 months' savings; loss = 1,000 gal x (gas - budget)+"),
    Persona("retiree", "Retiree, $40k/yr spending", "KXCPIYOY",
            wealth=80_000, basis_assumed=0.90, dollars_per_unit=400,
            note="W = a year's income + a year of savings; loss = $40k x (CPI YoY - budget)+ / 100 over the coming year"),
    Persona("contractor", "Contract worker, $70k/yr", "KXU3",
            wealth=70_000 / 12 * 4, basis_assumed=0.30, fixed_loss=70_000 / 12 * 3,
            hazard=contractor_hazard,
            note="W = month's pay + 3 months' savings; loss = 3 months' pay if the contract ends; hazard 3%/mo x exp(du)"),
    Persona("realtor", "Real-estate agent, $80k/yr commission", "KXFED",
            wealth=100_000, basis_assumed=0.50, dollars_per_unit=16_000,
            note="W = year's commission x 1.25; loss = 20% of commission per +1pp in the Fed upper bound vs. budget"),
    # Thin-cushion versions: the same exposure with 40% of the wealth, to
    # show where hedging starts to pay for its fees. (The contract worker is
    # already thin: the loss is 75% of W.)
    Persona("rideshare_thin", "Driver, no savings beyond ~1.6 months' pay", "KXAAAGASM",
            wealth=6_000, basis_assumed=0.85, dollars_per_unit=1_000, note="W = $6,000"),
    Persona("retiree_thin", "Retiree, small savings", "KXCPIYOY",
            wealth=32_000, basis_assumed=0.90, dollars_per_unit=400, note="W = $32,000"),
    Persona("realtor_thin", "Agent, small savings", "KXFED",
            wealth=40_000, basis_assumed=0.50, dollars_per_unit=16_000, note="W = $40,000"),
]


def _ladder(df_ev: pd.DataFrame, candles: dict, ts: float) -> pd.DataFrame:
    """Strikes of one event quoted at ``ts`` (greater-type only)."""
    rows = []
    for r in df_ev[df_ev.strike_type == "greater"].itertuples():
        q = quote_at(candles[r.ticker], ts, r.open_ts)
        if q is None:
            continue
        rows.append({"ticker": r.ticker, "strike": r.strike, "y": r.y, **q})
    lad = pd.DataFrame(rows)
    if len(lad):
        lad = lad.sort_values("strike").drop_duplicates("strike").reset_index(drop=True)
        # survival must fall with the strike: enforce with a running minimum
        lad["S"] = np.minimum.accumulate(lad.p.to_numpy())
    return lad


def conditional_overrun(lad: pd.DataFrame, k: float, step: float) -> float:
    """Market-implied E[X - k | X > k] from the ladder's survival curve.

    Trapezoid over listed strikes above k; beyond the last strike the
    survival falls linearly to zero over one more step."""
    above = lad[lad.strike >= k]
    if not len(above) or above.S.iloc[0] <= 0:
        return step
    ks = list(above.strike) + [above.strike.iloc[-1] + step]
    ss = list(above.S) + [0.0]
    area = sum((ks[i + 1] - ks[i]) * (ss[i] + ss[i + 1]) / 2 for i in range(len(ks) - 1))
    return float(max(area / above.S.iloc[0], 0.25 * step))


def last_settled_value(df: pd.DataFrame, series: str, before_ts: float) -> float | None:
    ev = (df[(df.series == series) & (df.settle_ts <= before_ts)]
          .groupby("event").agg(settle=("settle_ts", "max"), value=("value", "first"))
          .dropna().sort_values("settle"))
    return float(ev.value.iloc[-1]) if len(ev) else None


def backtest_persona(per: Persona, df: pd.DataFrame, candles: dict, h: int) -> pd.DataFrame:
    """One row per (event, gamma, cap) for this persona at horizon h."""
    rows = []
    sdf = df[df.series == per.series]
    step = _step(sdf[sdf.strike_type == "greater"].strike)
    for event, ev in sdf.groupby("event"):
        close = ev.close_ts.max()
        entry = close - h * DAY
        budget = last_settled_value(df, per.series, entry)
        x = ev.value.iloc[0]
        if budget is None or x is None or not np.isfinite(x):
            continue
        lad = _ladder(ev, candles, entry)
        if not len(lad):
            continue
        cand = lad[lad.strike >= budget - 1e-9]
        if not len(cand):
            continue
        leg = cand.iloc[0]  # the cheapest-to-define "ends above budget" contract
        k, mid, pays = float(leg.strike), float(leg.p), int(leg.y)
        ask = leg.ask if leg.ask is not None and np.isfinite(leg.ask) else None
        bid = leg.bid if leg.bid is not None and np.isfinite(leg.bid) else None
        if ask is None:  # nothing on offer to buy: no hedge was possible this period
            continue
        price = float(ask)
        app_prob = implied_probability(bid, ask, leg["last"])
        if app_prob is None or not (0.01 <= app_prob <= 0.99) or not (0.01 <= price <= 0.99):
            continue
        if per.fixed_loss is not None:
            loss_model = per.fixed_loss
            p_loss = per.hazard(x, budget)
            loss_draws = [(p_loss, per.fixed_loss), (1 - p_loss, 0.0)]
            realized_loss_mean = p_loss * per.fixed_loss
        else:
            loss_model = per.dollars_per_unit * ((k - budget) + conditional_overrun(lad, k, step))
            realized = per.dollars_per_unit * max(x - budget, 0.0)
            loss_draws = [(1.0, realized)]
            realized_loss_mean = realized
            p_loss = float(realized > 0)
        loss_model = min(loss_model, 0.9 * per.wealth)
        oi = leg.oi
        sell_px = bid if bid is not None and bid > 0 else None
        for variant in VARIANTS:
            mprob = price if variant == "no_tilt" else app_prob
            for gamma in GAMMAS:
                for capped in (False, True):
                    liq = Liquidity(open_interest=oi if oi is not None else 0.0) if capped else None
                    plan = hedge_income(IncomeExposure(
                        wealth=per.wealth, loss=loss_model, price=price, gamma=gamma,
                        market_prob=mprob, basis_correlation=per.basis_assumed, liquidity=liq,
                        allow_selling=(variant == "app")))
                    n = plan.contracts
                    fee = plan.fee
                    if n >= 0:
                        pnl = n * (pays - price) - fee
                    else:
                        # A "sell" buys the other side. hedge_income books it at
                        # 1 - ask; the market only offers it at 1 - bid.
                        pnl = abs(n) * ((sell_px if sell_px is not None else 0.0) - pays) - fee
                    # what the position would have made at the fill the model assumed
                    pnl_model_fill = n * (pays - price) - fee
                    rows.append({
                        "persona": per.key, "series": per.series, "event": event, "h": h,
                        "variant": variant, "gamma": gamma, "capped": capped, "entry_ts": entry,
                        "budget": budget, "strike": k, "realized": x, "mid": app_prob,
                        "bid": bid, "price": price, "oi": oi, "pays": pays,
                        "loss_model": loss_model, "p_loss": p_loss,
                        "loss_realized": realized_loss_mean, "loss_draws": loss_draws,
                        "contracts_wanted": plan.contracts_wanted, "contracts": n,
                        "cost": plan.cost, "fee": fee, "pnl": pnl, "pnl_model_fill": pnl_model_fill,
                        "exp_premium": (n * (price - app_prob) + fee) if n > 0 else fee,
                        "ce_gain_model": plan.ce_gain,
                    })
    return pd.DataFrame(rows)


def history_ce(bt: pd.DataFrame, wealth: float, gamma: float) -> dict:
    """CE over the history: each period an equally likely draw; the job-loss
    persona's loss is a lottery within the period, integrated exactly."""
    ws_un, ws_hd, pr = [], [], []
    t = len(bt)
    for r in bt.itertuples():
        for prob, loss in r.loss_draws:
            if prob <= 0:
                continue
            ws_un.append(wealth - loss)
            ws_hd.append(wealth - loss + r.pnl)
            pr.append(prob / t)
    ws_un, ws_hd, pr = map(np.array, (ws_un, ws_hd, pr))
    def ce(w):
        if np.any(w <= 0):  # ruin in some period: CRRA utility is minus infinity
            return float("nan")
        return crra_inverse(float(np.sum(pr * crra_utility(w, gamma))), gamma)
    m = lambda w: float(np.sum(pr * w))
    sd = lambda w: float(np.sqrt(np.sum(pr * (w - m(w)) ** 2)))
    return {"ce_unhedged": ce(ws_un), "ce_hedged": ce(ws_hd), "ce_gain": ce(ws_hd) - ce(ws_un),
            "mean_unhedged": m(ws_un), "mean_hedged": m(ws_hd),
            "sd_unhedged": sd(ws_un), "sd_hedged": sd(ws_hd),
            "worst_unhedged": float(ws_un.min()), "worst_hedged": float(ws_hd.min())}


def measured_basis(bt: pd.DataFrame) -> dict:
    """corr(contract payoff, realized loss) over the periods (one row per event).

    For the job-loss persona the loss is Bernoulli(p_t) given the realized
    rate, so cov(B, D) = cov(B, p) and var(D) = pbar (1 - pbar)."""
    b = bt.pays.to_numpy(float)
    if bt.persona.iloc[0] == "contractor":
        p = bt.p_loss.to_numpy(float)
        cov = np.mean(b * p) - b.mean() * p.mean()
        sd = math.sqrt(b.var() * p.mean() * (1 - p.mean()))
        rho = cov / sd if sd > 0 else np.nan
        ind = rho
    else:
        L = bt.loss_realized.to_numpy(float)
        rho = float(np.corrcoef(b, L)[0, 1]) if b.std() > 0 and L.std() > 0 else np.nan
        D = (L > 0).astype(float)
        ind = float(np.corrcoef(b, D)[0, 1]) if D.std() > 0 and b.std() > 0 else np.nan
    # the variance-minimizing hedge per $ of model loss, vs. the model's rho
    if bt.persona.iloc[0] == "contractor":
        beta = (np.mean(b * bt.p_loss) - b.mean() * bt.p_loss.mean()) * bt.loss_model.iloc[0] / b.var() if b.var() > 0 else np.nan
    else:
        beta = np.cov(b, bt.loss_realized, bias=True)[0, 1] / b.var() if b.var() > 0 else np.nan
    return {"rho_payoff_loss": rho, "rho_payoff_lossevent": ind,
            "min_var_contracts": float(beta), "mean_model_pure_hedge": float(bt.loss_model.mean())}


# ================================================================== report
def fmt(df: pd.DataFrame, floatfmt: str = "{:,.3f}") -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, (float, np.floating)):
                cells.append("" if not np.isfinite(v) else floatfmt.format(v))
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--offline", action="store_true", help="use the cache only")
    ap.add_argument("--refresh", action="store_true", help="re-download everything")
    ap.add_argument("--fetch-only", action="store_true")
    ap.add_argument("--boot", type=int, default=400, help="bootstrap resamples")
    args = ap.parse_args()
    data = load_all(args.offline, args.refresh)
    if args.fetch_only:
        return 0
    df, candles = market_table(data)
    pd.set_option("display.width", 200)

    print("# Data\n")
    inv = df.groupby("series").agg(markets=("ticker", "size"), events=("event", "nunique"),
                                   first=("close_ts", "min"), last=("close_ts", "max"),
                                   no_candles=("ticker", lambda t: sum(candles[x].size == 0 for x in t)),
                                   inferred_value=("value_inferred", "mean")).reset_index()
    for c in ("first", "last"):
        inv[c] = pd.to_datetime(inv[c], unit="s").dt.strftime("%Y-%m-%d")
    print(fmt(inv))

    # ---------------------------------------------------- calibration
    print("\n# Calibration\n")
    cal_all = {h: calibration_rows(df, candles, h) for h in HORIZONS}
    summ = []
    for h, cal in cal_all.items():
        for s, g in ([("ALL", cal), ("ALL, quoted mid only", cal[cal.src == "mid"]),
                      ("ALL, 5-95c only", cal[(cal.p >= 0.05) & (cal.p <= 0.95)])]
                     + list(cal.groupby("series"))):
            if len(g) < 20:
                continue
            r = calib_summary(g, boot=args.boot if s.startswith("ALL") else max(args.boot // 2, 100))
            summ.append({"h": h, "series": s, "n": r["n"], "events": r["events"],
                         "brier": r["brier"], "brier_lo": r["brier_ci"][0], "brier_hi": r["brier_ci"][1],
                         "brier_clim": r["brier_clim"], "skill": 1 - r["brier"] / r["brier_clim"],
                         "logloss": r["logloss"], "bias(p-y)": r["bias"],
                         "bias_lo": r["bias_ci"][0], "bias_hi": r["bias_ci"][1],
                         "slope_b": r["b"], "b_lo": r["b_ci"][0], "b_hi": r["b_ci"][1],
                         "intercept_a": r["a"], "n_5_95": r["n_contested"],
                         "brier_5_95": r["brier_contested"], "share_last_px": r["share_last"]})
    summ = pd.DataFrame(summ)
    print(fmt(summ))
    for h in (7, 28):
        print(f"\n## Reliability, h = {h} days, all series pooled\n")
        print(fmt(reliability(cal_all[h], boot=args.boot)))
    print("\n## Reliability, h = 7, contested markets only, by series (5-95c)\n")
    for s, g in cal_all[7].groupby("series"):
        g = g[(g.p >= 0.05) & (g.p <= 0.95)]
        if len(g) < 30:
            continue
        print(f"\n### {s}\n")
        print(fmt(reliability(g, boot=200)))

    # ---------------------------------------------------- hedges
    print("\n# Hedge backtest\n")
    allbt = []
    summary_rows, basis_rows = [], []
    for per in PERSONAS:
        for h in (7, 28):
            bt = backtest_persona(per, df, candles, h)
            if not len(bt):
                print(f"{per.key} h={h}: no periods")
                continue
            allbt.append(bt)
            one = bt[(bt.gamma == GAMMAS[0]) & (~bt.capped) & (bt.variant == "no_tilt")]
            basis_rows.append({"persona": per.key, "h": h, "periods": len(one),
                               "assumed": per.basis_assumed, **measured_basis(one)})
            for (variant, gamma, capped), g in bt.groupby(["variant", "gamma", "capped"]):
                ce = history_ce(g, per.wealth, gamma)
                lossy = g[g.loss_realized > 0]
                w = g.p_loss.to_numpy()
                paid_when_loss = (float(np.sum(w * g.pays) / np.sum(w)) if per.fixed_loss is not None
                                  else float(lossy.pays.mean()) if len(lossy) else np.nan)
                held = g[g.contracts > 0]
                summary_rows.append({
                    "persona": per.key, "h": h, "variant": variant, "gamma": gamma,
                    "cap": "OI 10%" if capped else "none",
                    "periods": len(g), "hedged": int((g.contracts > 0).sum()),
                    "sold": int((g.contracts < 0).sum()),
                    "med_contracts": float(held.contracts.median()) if len(held) else 0.0,
                    "coverage": float((g.contracts / g.contracts_wanted.replace(0, np.nan)).median()),
                    "loss_periods": float(g.p_loss.sum()),
                    "P(pay|loss)": paid_when_loss,
                    "P(pay|big loss)": (float(lossy[lossy.loss_realized >= lossy.loss_realized.median()].pays.mean())
                                        if per.fixed_loss is None and len(lossy) else np.nan),
                    "P(pay|no loss)": float(np.sum((1 - w) * g.pays) / np.sum(1 - w)) if np.sum(1 - w) > 0 else np.nan,
                    "total_loss": float(g.loss_realized.sum()),
                    "total_cost": float(g.cost.sum()),
                    "net_pnl": float(g.pnl.sum()),
                    "pnl_at_model_fill": float(g.pnl_model_fill.sum()),
                    "exp_premium": float(g.exp_premium.sum()),
                    "loss_offset": float(g.pnl.sum() / g.loss_realized.sum()) if g.loss_realized.sum() > 0 else np.nan,
                    **ce,
                    "ce_gain_pct_w": ce["ce_gain"] / per.wealth * 100,
                })
    summary = pd.DataFrame(summary_rows)
    keep = ["persona", "h", "variant", "gamma", "cap", "periods", "hedged", "sold", "med_contracts", "coverage",
            "loss_periods", "P(pay|loss)", "P(pay|big loss)", "P(pay|no loss)", "total_loss", "total_cost", "net_pnl",
            "pnl_at_model_fill", "exp_premium", "ce_unhedged", "ce_hedged", "ce_gain", "ce_gain_pct_w",
            "sd_unhedged", "sd_hedged", "worst_unhedged", "worst_hedged"]
    print(fmt(summary[keep], "{:,.2f}"))
    print("\n# Basis: measured vs assumed\n")
    print(fmt(pd.DataFrame(basis_rows), "{:,.3f}"))

    if allbt:
        out = pd.concat(allbt, ignore_index=True).drop(columns=["loss_draws"])
        out["entry_date"] = pd.to_datetime(out.entry_ts, unit="s").dt.strftime("%Y-%m-%d")
        RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)
        out.to_csv(RESULTS_CSV, index=False, float_format="%.4f")
        print(f"\nper-period rows: {RESULTS_CSV.relative_to(ROOT)}")
        # per-period detail for the gamma = 4 uncapped case at h = 7
        det = out[(out.gamma == 4.0) & (~out.capped) & (out.h == 7) & (out.variant == "app")]
        print("\n# Period detail (app wiring, gamma 4, uncapped, h = 7)\n")
        for per in PERSONAS:
            d = det[det.persona == per.key][["entry_date", "budget", "strike", "realized", "mid", "price",
                                             "oi", "pays", "loss_model", "loss_realized", "p_loss",
                                             "contracts_wanted", "contracts", "cost", "pnl"]]
            if len(d):
                print(f"\n## {per.key}\n")
                print(fmt(d, "{:,.3f}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
