"""Labor-market and regional-price data from BLS, turned into hedge inputs.

Questions (findings in findings/08_labor.md):

1. How likely is an involuntary job loss in a year, by industry?
   (JOLTS layoffs and discharges, Dec 2000 on.)
2. How well does a national-unemployment contract track one worker's job
   loss in each industry? (The backtest in 02_history.md measured ~0.02
   for a generic worker; this redoes it with industry layoff data.)
3. How closely does each state's (and big metro's) unemployment move with
   the national rate? (LAUS.)
4. How closely does regional CPI track national CPI? (For a retiree.)

Usage::

    python research/prediction/labor_study.py            # fetch what's missing, then analyse
    python research/prediction/labor_study.py --offline  # cached data only

Data pulls go through hone.prediction.labor.fetch_series, which caches every
response under research/prediction/data/bls/ — a second run sends no
queries. Without a key BLS allows ~25 queries a day; the full pull needs
15 (117 series x 3 ten-year windows, 25 series a query). Set BLS_API_KEY
(free registration) to use v2 and cut that to 3.

At the end it prints the Python tables to paste into hone/prediction/labor.py.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from hone.prediction import labor  # noqa: E402
from hone.prediction.labor import (  # noqa: E402
    INDUSTRIES, PANDEMIC_WINDOW, STATE_FIPS, change_correlation, cpi_id,
    displacement_scale, jolts_id, job_loss_basis, laus_metro_id, laus_state_id,
    layoff_summary, single_strike_basis,
)

DATA = ROOT / "research" / "prediction" / "data" / "bls"
START_YEAR, END_YEAR = 2001, 2026

# --- Displaced Worker Survey anchor (BLS news release USDL-24-1777, Aug 29 2024,
# https://www.bls.gov/news.release/disp.nr0.htm): 6.3 million workers aged 20+
# were displaced (plant/company closed or moved, position or shift abolished,
# insufficient work) from January 2021 through December 2023 — all tenures.
DWS_DISPLACED_2021_2023 = 6.3e6
DWS_YEARS = (2021, 2023)

# Large metros: name -> (principal-state FIPS, CBSA code) for LAUS.
LAUS_METROS = {
    "new_york": ("36", "35620"), "los_angeles": ("06", "31080"), "chicago": ("17", "16980"),
    "dallas": ("48", "19100"), "houston": ("48", "26420"), "washington_dc": ("11", "47900"),
    "miami": ("12", "33100"), "philadelphia": ("42", "37980"), "atlanta": ("13", "12060"),
    "phoenix": ("04", "38060"), "san_francisco": ("06", "41860"), "seattle": ("53", "42660"),
    "denver": ("08", "19740"), "detroit": ("26", "19820"), "las_vegas": ("32", "29820"),
}
# CPI areas (codes from cu.area).
CPI_REGIONS = {"northeast": "0100", "midwest": "0200", "south": "0300", "west": "0400"}
CPI_DIVISIONS = {
    "new_england": "0110", "middle_atlantic": "0120", "east_north_central": "0230",
    "west_north_central": "0240", "south_atlantic": "0350", "east_south_central": "0360",
    "west_south_central": "0370", "mountain": "0480", "pacific": "0490",
}
CPI_METROS = {
    "new_york": "S12A", "los_angeles": "S49A", "chicago": "S23A", "dallas": "S37A",
    "houston": "S37B", "washington_dc": "S35A", "miami": "S35B", "atlanta": "S35C",
    "phoenix": "S48A", "san_francisco": "S49B", "seattle": "S49D", "denver": "S48B",
    "boston": "S11A", "philadelphia": "S12B", "detroit": "S23B",
}

# JOLTS industries analysed (all of INDUSTRIES) and the total-nonfarm level
# (thousands of layoffs per month) needed for the DWS scale.
# Unadjusted (JTU...): FRED mirrors only the unadjusted industry series, and
# averages over whole years are unaffected by seasonality anyway.
JOLTS_RATES = {k: jolts_id(v["code"], seasonally_adjusted=False) for k, v in INDUSTRIES.items()}
JOLTS_TOTAL_LEVEL = jolts_id("000000", rate=False, seasonally_adjusted=False)


def all_series_ids() -> list[str]:
    """Everything the study needs, MOST IMPORTANT FIRST: if the daily quota
    runs out, fetch_series completes the early batches before the late ones."""
    ids = [labor.NATIONAL_UNRATE_SA, labor.NATIONAL_EMPLOYMENT_SA, labor.NATIONAL_UNRATE_NSA]
    ids += list(JOLTS_RATES.values()) + [JOLTS_TOTAL_LEVEL]
    ids += [labor.NATIONAL_CPI_NSA] + [cpi_id(c) for c in CPI_REGIONS.values()]
    ids += [cpi_id(c) for c in CPI_DIVISIONS.values()]
    ids += [laus_state_id(s) for s in STATE_FIPS]
    ids += [laus_metro_id(f, c) for f, c in LAUS_METROS.values()]
    ids += [cpi_id(c) for c in CPI_METROS.values()]
    return ids


def pull(offline: bool) -> dict[str, pd.Series]:
    report = labor.FetchReport()
    data = labor.fetch_series(all_series_ids(), START_YEAR, END_YEAR, cache_dir=DATA,
                              offline=offline, report=report)
    print(f"BLS: {report.queries_sent} queries sent, {report.served_from_cache} series-windows from cache.")
    if report.limit_hit:
        print("!! Daily query limit reached — analysing what is cached. Re-run tomorrow (or set BLS_API_KEY) to finish.")
    if report.mirrored:
        print(f"   Filled {len(report.mirrored)} series from the FRED mirror of the same BLS data.")
    if report.stale_used:
        print(f"   Used older cached copies for {len(set(report.stale_used))} series.")
    if report.missing:
        print(f"   No data for {len(report.missing)} series: {', '.join(report.missing)}")
    notes = [m for m in report.messages if "No Data Available" not in m and "Catalog Data" not in m]
    for m in notes[:10]:
        print(f"   BLS says: {m}")
    return data


def fmt(x: float | None, pct: bool = False, digits: int = 2) -> str:
    if x is None or not np.isfinite(x):
        return "—"
    return f"{x * 100:.{max(digits - 1, 1)}f}%" if pct else f"{x:.{digits}f}"


def md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(v) for v in row.values) + " |")
    return "\n".join(lines)


# --------------------------------------------------------------------- 1, 2
def jobs(data: dict[str, pd.Series]) -> tuple[pd.DataFrame, float]:
    u = data[labor.NATIONAL_UNRATE_SA]
    level = data[JOLTS_TOTAL_LEVEL]
    yrs = level[(level.index.year >= DWS_YEARS[0]) & (level.index.year <= DWS_YEARS[1])]
    n_years = DWS_YEARS[1] - DWS_YEARS[0] + 1
    if len(yrs) >= 30:
        # JOLTS level is in thousands per month; annual people-count = sum / years.
        jolts_per_year = yrs.sum() * 1000 / n_years * (36 / len(yrs))
        scale = displacement_scale(DWS_DISPLACED_2021_2023 / n_years, jolts_per_year)
        print(f"\nDisplacement scale: DWS {DWS_DISPLACED_2021_2023 / n_years / 1e6:.2f}M/yr vs JOLTS "
              f"L&D {jolts_per_year / 1e6:.1f}M/yr (2021-23) -> {scale:.3f}")
    else:
        scale = labor.DISPLACEMENT_SCALE
        print(f"\nJOLTS level missing; using stored displacement scale {scale}")

    rows = []
    for key, sid in JOLTS_RATES.items():
        s = data.get(sid)
        if s is None or s.dropna().empty:
            continue
        summ = layoff_summary(s, scale=scale)
        # Basis for a SETTLED worker in this industry (hazard scaled by DWS)...
        b1 = job_loss_basis(s, u, months=1, hazard_scale=scale, exclude=[PANDEMIC_WINDOW])
        b12 = job_loss_basis(s, u, months=12, hazard_scale=scale, exclude=[PANDEMIC_WINDOW])
        # ...and for a worker exposed to every layoff (seasonal/temp/gig).
        b1_any = job_loss_basis(s, u, months=1, exclude=[PANDEMIC_WINDOW])
        b12_any = job_loss_basis(s, u, months=12, exclude=[PANDEMIC_WINDOW])
        # Including the pandemic, for reference.
        b12_all = job_loss_basis(s, u, months=12, hazard_scale=scale)
        # A deeper strike: "U3 up at least 0.5 points within a year", the
        # recession signal (Sahm-rule territory). Ex-pandemic, settled worker.
        b12_deep = job_loss_basis(s, u, months=12, hazard_scale=scale, exclude=[PANDEMIC_WINDOW],
                                  threshold_pp=0.5)
        rows.append({
            "key": key, "label": INDUSTRIES[key]["label"], **summ,
            "basis_u3_1m": b1["corr"], "basis_u3_12m": b12["corr"],
            "basis_u3_1m_any": b1_any["corr"], "basis_u3_12m_any": b12_any["corr"],
            "basis_u3_12m_incl_covid": b12_all["corr"],
            "basis_u3_12m_deep": b12_deep["corr"], "p_pay_given_loss_12m_deep": b12_deep["p_pay_given_loss"],
            "q_12m_deep": b12_deep["q"],
            "p_pay_given_loss_1m": b1["p_pay_given_loss"], "q_1m": b1["q"],
            "p_pay_given_loss_12m": b12["p_pay_given_loss"], "q_12m": b12["q"],
            "first": s.dropna().index.min().strftime("%Y-%m"), "last": s.dropna().index.max().strftime("%Y-%m"),
        })
    df = pd.DataFrame(rows).set_index("key")
    df.to_csv(DATA / "job_loss_by_industry.csv", float_format="%.5f")

    show = df.sort_values("annual_any", ascending=False)
    print("\n## 1. Job-loss probability by industry (JOLTS layoffs & discharges)\n")
    print(md_table(pd.DataFrame({
        "Industry": show["label"],
        "Monthly L&D (typical)": show["monthly_typical"].map(lambda x: fmt(x, True, 3)),
        "Any layoff, 1 yr": show["annual_any"].map(lambda x: fmt(x, True)),
        "…in a recession": show["annual_recession"].map(lambda x: fmt(x, True)),
        "Settled worker, 1 yr": show["annual_displacement"].map(lambda x: fmt(x, True)),
        "…in a recession ": show["annual_displacement_recession"].map(lambda x: fmt(x, True)),
        "Worst 2020 month": show["monthly_pandemic_peak"].map(lambda x: fmt(x, True)),
    })))
    print("\n## 2. Basis: national 'U3 rises' contract vs a job loss in the industry (ex-pandemic)\n")
    print(md_table(pd.DataFrame({
        "Industry": show["label"],
        "1-mo basis (settled)": show["basis_u3_1m"].map(lambda x: fmt(x, digits=3)),
        "12-mo basis (settled)": show["basis_u3_12m"].map(lambda x: fmt(x, digits=3)),
        "1-mo basis (any layoff)": show["basis_u3_1m_any"].map(lambda x: fmt(x, digits=3)),
        "12-mo basis (any layoff)": show["basis_u3_12m_any"].map(lambda x: fmt(x, digits=3)),
        "P(pays | loss), 1 mo": show["p_pay_given_loss_1m"].map(lambda x: fmt(x, True)),
        "P(pays), 1 mo": show["q_1m"].map(lambda x: fmt(x, True)),
        "P(pays | loss), 12 mo": show["p_pay_given_loss_12m"].map(lambda x: fmt(x, True)),
        "P(pays), 12 mo": show["q_12m"].map(lambda x: fmt(x, True)),
    })))
    print("\n### Deeper strike: U3 up >= 0.5 points within 12 months (settled worker, ex-pandemic)\n")
    print(md_table(pd.DataFrame({
        "Industry": show["label"],
        "Basis": show["basis_u3_12m_deep"].map(lambda x: fmt(x, digits=3)),
        "P(pays | loss)": show["p_pay_given_loss_12m_deep"].map(lambda x: fmt(x, True)),
        "P(pays)": show["q_12m_deep"].map(lambda x: fmt(x, True)),
        "Basis incl. 2020-21 (12-mo, ATM)": show["basis_u3_12m_incl_covid"].map(lambda x: fmt(x, digits=3)),
    })))
    return df, scale


# ------------------------------------------------------------------------ 3
def states(data: dict[str, pd.Series]) -> tuple[pd.DataFrame, pd.DataFrame]:
    nat = data[labor.NATIONAL_UNRATE_SA]
    rows = []
    for st in STATE_FIPS:
        s = data.get(laus_state_id(st))
        if s is None or s.dropna().empty:
            continue
        m1 = change_correlation(s, nat, months=1, exclude=[PANDEMIC_WINDOW])
        m12 = change_correlation(s, nat, months=12, exclude=[PANDEMIC_WINDOW])
        m1a = change_correlation(s, nat, months=1)
        m12a = change_correlation(s, nat, months=12)
        rows.append({"state": st, "name": labor.STATE_NAMES[st], "region": labor.STATE_REGION[st],
                     "monthly": m1["corr"], "annual": m12["corr"], "beta_annual": m12["beta"],
                     "monthly_incl_covid": m1a["corr"], "annual_incl_covid": m12a["corr"],
                     "n_monthly": m1["n"], "latest": s.dropna().iloc[-1]})
    df = pd.DataFrame(rows).set_index("state")
    df.to_csv(DATA / "state_unemployment_basis.csv", float_format="%.4f")

    natn = data[labor.NATIONAL_UNRATE_NSA]
    mrows = []
    for name, (f, c) in LAUS_METROS.items():
        s = data.get(laus_metro_id(f, c))
        if s is None or s.dropna().empty:
            continue
        m12 = change_correlation(s, natn, months=12, exclude=[PANDEMIC_WINDOW])
        m12a = change_correlation(s, natn, months=12)
        mrows.append({"metro": name, "annual": m12["corr"], "beta_annual": m12["beta"],
                      "annual_incl_covid": m12a["corr"], "n": m12["n"]})
    mdf = pd.DataFrame(mrows).set_index("metro") if mrows else pd.DataFrame()
    if len(mdf):
        mdf.to_csv(DATA / "metro_unemployment_basis.csv", float_format="%.4f")

    show = df.sort_values("annual", ascending=False)
    print("\n## 3. State unemployment vs national U3 (correlation of changes, ex Mar 2020-Dec 2021)\n")
    print(md_table(pd.DataFrame({
        "State": show.index, "Region": show["region"],
        "Monthly": show["monthly"].map(fmt), "12-month": show["annual"].map(fmt),
        "Beta (12-mo)": show["beta_annual"].map(fmt),
        "Monthly incl. 2020-21": show["monthly_incl_covid"].map(fmt),
        "12-mo incl. 2020-21": show["annual_incl_covid"].map(fmt),
        "Single-strike basis (monthly)": show["monthly"].map(lambda r: fmt(single_strike_basis(r))),
    })))
    print(f"\nMedian across states: monthly {df['monthly'].median():.2f}, 12-month {df['annual'].median():.2f}")
    if len(mdf):
        print("\n### Metros (unadjusted, 12-month changes vs unadjusted national)\n")
        ms = mdf.sort_values("annual", ascending=False)
        print(md_table(pd.DataFrame({"Metro": ms.index, "12-month": ms["annual"].map(fmt),
                                     "Beta": ms["beta_annual"].map(fmt),
                                     "12-mo incl. 2020-21": ms["annual_incl_covid"].map(fmt)})))
    return df, mdf


# ------------------------------------------------------------------------ 4
def cpi(data: dict[str, pd.Series]) -> tuple[pd.DataFrame, pd.DataFrame]:
    nat = data[labor.NATIONAL_CPI_NSA]

    def measure(s: pd.Series) -> dict:
        m1 = change_correlation(s, nat, months=1, log=True, deseason=True)
        m12 = change_correlation(s, nat, months=12, log=True)
        m1x = change_correlation(s, nat, months=1, log=True, deseason=True, exclude=[PANDEMIC_WINDOW])
        return {"monthly": m1["corr"], "annual": m12["corr"], "beta_monthly": m1["beta"],
                "beta_annual": m12["beta"], "monthly_ex_covid": m1x["corr"],
                "n_monthly": m1["n"], "n_annual": m12["n"],
                "first": s.dropna().index.min().strftime("%Y-%m")}

    rows = []
    for name, code in {**CPI_REGIONS, **CPI_DIVISIONS}.items():
        s = data.get(cpi_id(code))
        if s is None or s.dropna().empty:
            continue
        rows.append({"area": name, "kind": "region" if name in CPI_REGIONS else "division", **measure(s)})
    df = pd.DataFrame(rows).set_index("area")
    mrows = []
    for name, code in CPI_METROS.items():
        s = data.get(cpi_id(code))
        if s is None or s.dropna().empty:
            continue
        mrows.append({"area": name, "kind": "metro", **measure(s)})
    mdf = pd.DataFrame(mrows).set_index("area") if mrows else pd.DataFrame()
    pd.concat([df, mdf]).to_csv(DATA / "cpi_basis.csv", float_format="%.4f")

    print("\n## 4. Regional CPI vs national CPI-U (log changes; monthly ones deseasonalized)\n")
    both = pd.concat([df, mdf])
    print(md_table(pd.DataFrame({
        "Area": both.index, "Kind": both["kind"], "Since": both["first"],
        "Monthly": both["monthly"].map(fmt), "Monthly ex 2020-21": both["monthly_ex_covid"].map(fmt),
        "12-month": both["annual"].map(fmt), "Beta (monthly)": both["beta_monthly"].map(fmt),
        "Single-strike basis (monthly)": both["monthly"].map(lambda r: fmt(single_strike_basis(r))),
        "n (monthly)": both["n_monthly"],
    })))
    return df, mdf


# ----------------------------------------------------------------- tables out
def _r(x, d=4):
    return None if x is None or not np.isfinite(x) else round(float(x), d)


def print_constants(jobs_df, scale, st_df, metro_df, cpi_df, cpi_metro_df) -> None:
    print("\n# ---- paste into hone/prediction/labor.py ----")
    print(f"DISPLACEMENT_SCALE = {scale:.4f}\n")
    print("JOB_LOSS: dict[str, dict[str, float]] = {")
    keys = ["monthly_typical", "monthly_recession", "annual_any", "annual_recession",
            "annual_displacement", "annual_displacement_recession", "basis_u3_1m", "basis_u3_12m",
            "basis_u3_1m_any", "basis_u3_12m_any", "basis_u3_12m_deep", "p_pay_given_loss_1m", "q_1m",
            "p_pay_given_loss_12m", "q_12m"]
    for k, row in jobs_df.iterrows():
        inner = ", ".join(f'"{c}": {_r(row[c])}' for c in keys)
        print(f'    "{k}": {{{inner}}},')
    print("}\n")
    print("STATE_UNEMPLOYMENT_BASIS: dict[str, dict[str, float]] = {")
    for k, row in st_df.iterrows():
        print(f'    "{k}": {{"monthly": {_r(row.monthly, 3)}, "annual": {_r(row.annual, 3)}, "beta_annual": {_r(row.beta_annual, 3)}}},')
    print("}\n")
    print("METRO_UNEMPLOYMENT_BASIS: dict[str, dict[str, float | None]] = {")
    for k, row in metro_df.iterrows():
        print(f'    "{k}": {{"monthly": None, "annual": {_r(row.annual, 3)}, "beta_annual": {_r(row.beta_annual, 3)}}},')
    print("}\n")
    print("CPI_BASIS: dict[str, dict[str, float | None]] = {")
    for k, row in cpi_df.iterrows():
        print(f'    "{k}": {{"monthly": {_r(row.monthly, 3)}, "annual": {_r(row.annual, 3)}, "beta_monthly": {_r(row.beta_monthly, 3)}}},')
    print("}\n")
    print("CPI_METRO_BASIS: dict[str, dict[str, float | None]] = {")
    for k, row in cpi_metro_df.iterrows():
        print(f'    "{k}": {{"monthly": {_r(row.monthly, 3)}, "annual": {_r(row.annual, 3)}, "beta_monthly": {_r(row.beta_monthly, 3)}}},')
    print("}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--offline", action="store_true", help="use cached data only")
    args = ap.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)
    data = pull(args.offline)
    if data[labor.NATIONAL_UNRATE_SA].empty:
        print("No national unemployment data cached; nothing to analyse.")
        return
    jobs_df, scale = jobs(data)
    st_df, metro_df = states(data)
    cpi_df, cpi_metro_df = cpi(data)
    print_constants(jobs_df, scale, st_df, metro_df, cpi_df, cpi_metro_df)


if __name__ == "__main__":
    main()
