"""Offline tests for hone.prediction.labor (BLS data and labor-market basis).

A fake BLS session answers the API (POST) and the FRED mirror (GET) from
in-memory data, so nothing here touches the network.
"""

from __future__ import annotations

import gzip
import json
import math
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pytest

from hone.prediction import labor
from hone.prediction.labor import (
    BLSError, FetchReport, annual_prob_from_monthly, change_correlation, changes,
    deseasonalize, displacement_scale, fetch_series, job_loss_basis, layoff_summary,
    monthly_from_annual_prob, parse_observations, single_strike_basis, unemployment_rises,
    year_windows,
)


# ------------------------------------------------------------------ fakes
class _Resp:
    def __init__(self, data=None, text=None, status=200):
        self._d, self.text, self.status_code = data, text, status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._d


class FakeBLS:
    """Answers BLS API POSTs and FRED CSV GETs from ``data``:
    {series_id: {"YYYY-MM": value}}. ``limit_after`` = number of API
    queries served before answering with the daily-limit refusal."""

    def __init__(self, data, limit_after=None, fred=None):
        self.data, self.limit_after = data, limit_after
        self.fred = fred or {}           # {fred_id: {"YYYY-MM": value}}
        self.posts, self.gets = [], []

    def post(self, url, json=None, timeout=None):
        self.posts.append((url, json))
        if self.limit_after is not None and len(self.posts) > self.limit_after:
            return _Resp({"status": "REQUEST_NOT_PROCESSED", "message": [
                "Request could not be serviced, as the daily threshold for total number of requests "
                "allocated to the user has been reached."], "Results": {}})
        y0, y1 = int(json["startyear"]), int(json["endyear"])
        series = []
        for sid in json["seriesid"]:
            rows = [{"year": k[:4], "period": f"M{k[5:]}", "periodName": "", "value": str(v), "footnotes": [{}]}
                    for k, v in self.data.get(sid, {}).items() if y0 <= int(k[:4]) <= y1]
            # BLS also sends annual averages; the parser must skip them.
            if rows:
                rows.append({"year": str(y1), "period": "M13", "value": "99.9", "footnotes": []})
            series.append({"seriesID": sid, "data": rows})
        return _Resp({"status": "REQUEST_SUCCEEDED", "message": [], "Results": {"series": series}})

    def get(self, url, params=None, timeout=None):
        self.gets.append((url, params))
        obs = self.fred.get(params["id"])
        if obs is None:
            return _Resp(text="<!DOCTYPE html><html>not found</html>")
        lines = [f"observation_date,{params['id']}"] + [f"{k}-01,{v}" for k, v in sorted(obs.items())]
        return _Resp(text="\n".join(lines) + "\n2026-12-01,.\n")


def _monthly(start="2001-01", end="2026-09", fn=lambda i, d: float(i)):
    idx = pd.date_range(f"{start}-01", f"{end}-01", freq="MS")
    return {d.strftime("%Y-%m"): fn(i, d) for i, d in enumerate(idx)}


NOW = datetime(2026, 11, 8, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    # Fail loudly if anything reaches for the real network.
    def _no_network(*a, **k):
        raise AssertionError("test tried to use the network")
    monkeypatch.setattr(labor.requests, "get", _no_network)
    monkeypatch.setattr(labor.requests, "post", _no_network)
    labor.clear_memory_cache()
    monkeypatch.delenv(labor.API_KEY_ENV, raising=False)
    monkeypatch.setattr(labor.time, "sleep", lambda s: None)
    yield
    labor.clear_memory_cache()


# ------------------------------------------------------------ series IDs
def test_series_id_formats_match_bls_docs():
    assert labor.laus_state_id("CA") == "LASST060000000000003"
    assert labor.laus_state_id("ny", seasonally_adjusted=False) == "LAUST360000000000003"
    assert labor.laus_metro_id("06", "31080") == "LAUMT063108000000003"
    assert labor.jolts_id("000000") == "JTS000000000000000LDR"
    assert labor.jolts_id("540099", seasonally_adjusted=False) == "JTU540099000000000LDR"
    assert labor.jolts_id("000000", rate=False) == "JTS000000000000000LDL"
    assert labor.cpi_id("0100") == "CUUR0100SA0" and labor.cpi_id("S49A") == "CUURS49ASA0"
    for sid in (labor.laus_state_id("AK"), labor.laus_metro_id("36", "35620")):
        assert len(sid) == 20
    assert len(labor.jolts_id("230000")) == 21


def test_fred_mirror_ids():
    m = labor.FRED_MIRROR
    assert m["LNS14000000"] == "UNRATE"
    assert m[labor.laus_state_id("TX")] == "TXUR"
    assert m[labor.jolts_id("230000", seasonally_adjusted=False)] == "JTU2300LDR"
    assert m[labor.jolts_id("540099", seasonally_adjusted=False)] == "JTU540099LDR"
    assert m[labor.jolts_id("000000", seasonally_adjusted=False)] == "JTULDR"


# ---------------------------------------------------------------- parsing
def test_parse_observations_keeps_months_only():
    obs = parse_observations({"data": [
        {"year": "2024", "period": "M01", "value": "3.7"},
        {"year": "2024", "period": "M13", "value": "3.9"},     # annual average
        {"year": "2024", "period": "S01", "value": "300.1"},   # half-year
        {"year": "2025", "period": "M10", "value": "-"},       # not collected (shutdown)
        {"year": "2025", "period": "M11", "value": "(NA)"},
        {"year": "2025", "period": "M12", "value": "1,234.5"},
    ]})
    assert obs == {"2024-01": 3.7, "2025-12": 1234.5}
    s = labor.to_series(obs)
    assert list(s.index) == [pd.Timestamp("2024-01-01"), pd.Timestamp("2025-12-01")]


def test_year_windows():
    assert year_windows(2001, 2026, 10) == [(2001, 2010), (2011, 2020), (2021, 2026)]
    assert year_windows(2020, 2020, 10) == [(2020, 2020)]
    with pytest.raises(ValueError):
        year_windows(2026, 2001, 10)


# ------------------------------------------------------- fetching / caching
def test_fetch_batches_to_v1_limits_and_returns_values(tmp_path):
    ids = [f"FAKE{i:02d}" for i in range(30)]
    data = {sid: _monthly(fn=lambda i, d, k=k: k + i / 1000) for k, sid in enumerate(ids)}
    sess = FakeBLS(data)
    out = fetch_series(ids, 2001, 2026, session=sess, cache_dir=tmp_path, now=NOW, mirror=False)
    # 30 series -> 2 batches (25 + 5), x 3 ten-year windows = 6 queries
    assert len(sess.posts) == 6
    for url, payload in sess.posts:
        assert url == labor.API_V1_URL
        assert len(payload["seriesid"]) <= 25
        assert int(payload["endyear"]) - int(payload["startyear"]) < 10
        assert "registrationkey" not in payload
    s = out["FAKE03"]
    assert s.index[0] == pd.Timestamp("2001-01-01") and s.index[-1] == pd.Timestamp("2026-09-01")
    assert s.iloc[0] == pytest.approx(3.0) and len(s) == len(data["FAKE03"])
    assert 99.9 not in s.values   # M13 skipped


def test_cache_memory_then_disk_then_offline(tmp_path):
    data = {"A": _monthly(), "B": _monthly(fn=lambda i, d: 2.0 * i)}
    sess = FakeBLS(data)
    fetch_series(["A", "B"], 2001, 2026, session=sess, cache_dir=tmp_path, now=NOW)
    n = len(sess.posts)
    # same process: memory cache, no queries
    rep = FetchReport()
    fetch_series(["A", "B"], 2001, 2026, session=sess, cache_dir=tmp_path, now=NOW, report=rep)
    assert len(sess.posts) == n and rep.queries_sent == 0
    # new process: disk cache, no queries, same values
    labor.clear_memory_cache()
    out = fetch_series(["A", "B"], 2001, 2026, session=sess, cache_dir=tmp_path, now=NOW)
    assert len(sess.posts) == n
    assert out["B"].iloc[10] == 20.0
    assert (tmp_path / "series" / "A.json").exists()
    raws = list((tmp_path / "raw").glob("*.json.gz"))
    assert len(raws) == n
    # a sub-range is cut from the cache
    labor.clear_memory_cache()
    sub = fetch_series(["A"], 2010, 2011, session=sess, cache_dir=tmp_path, now=NOW, offline=True)["A"]
    assert sub.index.min() == pd.Timestamp("2010-01-01") and sub.index.max() == pd.Timestamp("2011-12-01")


def test_offline_with_empty_cache_sends_nothing(tmp_path):
    sess = FakeBLS({"A": _monthly()})
    rep = FetchReport()
    out = fetch_series(["A"], 2001, 2026, session=sess, cache_dir=tmp_path, offline=True, report=rep)
    assert sess.posts == [] and sess.gets == []
    assert out["A"].empty and rep.missing == ["A"]


def test_open_window_refetched_when_stale_past_windows_never(tmp_path):
    sess = FakeBLS({"A": _monthly()})
    fetch_series(["A"], 2001, 2026, session=sess, cache_dir=tmp_path, now=NOW)
    assert len(sess.posts) == 3
    labor.clear_memory_cache()
    later = NOW + timedelta(days=labor.OPEN_WINDOW_MAX_AGE_DAYS + 1)
    fetch_series(["A"], 2001, 2026, session=sess, cache_dir=tmp_path, now=later)
    assert len(sess.posts) == 4                      # only the 2021-2026 window again
    assert sess.posts[-1][1]["startyear"] == "2021"


def test_daily_limit_stops_and_falls_back_to_fred(tmp_path):
    u = _monthly(fn=lambda i, d: 4.0 + (i % 7) / 10)
    sess = FakeBLS({"LNS14000000": u}, limit_after=0, fred={"UNRATE": u})
    rep = FetchReport()
    out = fetch_series(["LNS14000000"], 2001, 2026, session=sess, cache_dir=tmp_path, now=NOW, report=rep)
    assert rep.limit_hit and len(sess.posts) == 1     # refusal is not retried, later windows skipped
    assert rep.mirrored == ["LNS14000000"]
    assert sess.gets and sess.gets[0][1]["id"] == "UNRATE"   # served by the fake, not the network
    assert len(out["LNS14000000"]) == len(u)          # the trailing "." row is skipped
    entry = json.loads((tmp_path / "series" / "LNS14000000.json").read_text())
    assert set(entry["source"].values()) == {"fred:UNRATE"}


def test_daily_limit_without_mirror_returns_what_is_cached(tmp_path):
    sess = FakeBLS({"A": _monthly()}, limit_after=1)
    rep = FetchReport()
    out = fetch_series(["A"], 2001, 2026, session=sess, cache_dir=tmp_path, now=NOW, report=rep, mirror=False)
    assert rep.limit_hit and rep.queries_sent == 1
    assert out["A"].index.max() == pd.Timestamp("2010-12-01")  # only the first window arrived


def test_fred_mirror_only_marks_windows_it_had_data_for(tmp_path):
    # A FRED copy that stops in 2017 (like LA CPI's old area code)
    la = labor.cpi_id("S49A")
    old = _monthly("2001-01", "2017-12", fn=lambda i, d: 100 + i)
    sess = FakeBLS({}, limit_after=0, fred={labor.FRED_MIRROR[la]: old})
    fetch_series([la], 2001, 2026, session=sess, cache_dir=tmp_path, now=NOW)
    entry = json.loads((tmp_path / "series" / f"{la}.json").read_text())
    assert set(entry["windows"]) == {"2001-2010", "2011-2020"}   # 2021-2026 left for the API
    assert len(sess.gets) == 1


def test_fred_unknown_series_raises():
    with pytest.raises(BLSError):
        labor.fetch_fred_mirror("NOT_A_SERIES", 2001, 2026, session=FakeBLS({}))
    with pytest.raises(BLSError, match="no series"):
        labor.fetch_fred_mirror("LNS14000000", 2001, 2026, session=FakeBLS({}, fred={}))


def test_retries_transient_errors_then_succeeds(tmp_path):
    class Flaky(FakeBLS):
        fails = 2

        def post(self, url, json=None, timeout=None):
            if Flaky.fails:
                Flaky.fails -= 1
                raise ConnectionError("reset")
            return super().post(url, json=json, timeout=timeout)

    sess = Flaky({"A": _monthly("2021-01", "2026-09")})
    out = fetch_series(["A"], 2021, 2026, session=sess, now=NOW)
    assert len(out["A"]) == 69


def test_gives_up_after_retries():
    class Down:
        calls = 0

        def post(self, *a, **k):
            Down.calls += 1
            raise ConnectionError("down")

    with pytest.raises(BLSError, match="BLS request failed"):
        fetch_series(["A"], 2021, 2026, session=Down(), now=NOW, mirror=False)
    assert Down.calls == labor.RETRIES + 1


def test_api_key_switches_to_v2_and_never_hits_disk(tmp_path, monkeypatch):
    monkeypatch.setenv(labor.API_KEY_ENV, "secret-key-123")
    ids = [f"S{i:02d}" for i in range(60)]
    sess = FakeBLS({sid: _monthly() for sid in ids})
    fetch_series(ids, 2001, 2026, session=sess, cache_dir=tmp_path, now=NOW)
    # 60 series -> 2 batches of <= 50, x 2 twenty-year windows
    assert len(sess.posts) == 4
    assert all(url == labor.API_V2_URL and p["registrationkey"] == "secret-key-123" for url, p in sess.posts)
    assert max(len(p["seriesid"]) for _, p in sess.posts) == 50
    for raw in (tmp_path / "raw").glob("*.json.gz"):
        with gzip.open(raw, "rt") as fh:
            assert "secret-key-123" not in fh.read()


# --------------------------------------------------- monthly -> annual odds
def test_annual_prob_from_monthly():
    assert annual_prob_from_monthly(0.012) == pytest.approx(1 - 0.988 ** 12)
    assert annual_prob_from_monthly(0.012) == pytest.approx(0.1349, abs=1e-4)
    assert annual_prob_from_monthly(0.012) < 12 * 0.012          # can't lose the same job twice
    assert annual_prob_from_monthly(0.0) == 0.0
    assert annual_prob_from_monthly(0.05, months=1) == pytest.approx(0.05)
    assert monthly_from_annual_prob(annual_prob_from_monthly(0.013)) == pytest.approx(0.013)
    with pytest.raises(ValueError):
        annual_prob_from_monthly(1.2)   # percent passed instead of a fraction


def test_layoff_summary_excludes_pandemic_and_reads_recessions():
    def rate(i, d):
        if pd.Timestamp("2020-03-01") <= d <= pd.Timestamp("2020-05-01"):
            return 10.0
        if pd.Timestamp("2008-01-01") <= d <= pd.Timestamp("2009-06-01"):
            return 2.0
        return 1.0
    s = labor.to_series(_monthly(fn=rate))
    out = layoff_summary(s, scale=0.1)
    assert out["monthly_median"] == pytest.approx(0.01)
    # recession months: Apr-Nov 2001 (8, at 1%) and Jan 2008-Jun 2009 (18, at 2%)
    assert out["monthly_recession"] == pytest.approx((8 * 0.01 + 18 * 0.02) / 26)
    assert out["monthly_pandemic_peak"] == pytest.approx(0.10)
    assert 0.01 < out["monthly_typical"] < 0.0108       # recession months lift the mean a little
    assert out["annual_any"] == pytest.approx(annual_prob_from_monthly(out["monthly_typical"]))
    assert out["annual_displacement"] == pytest.approx(annual_prob_from_monthly(out["monthly_typical"] * 0.1))
    assert out["annual_recession"] > out["annual_any"] > out["annual_displacement"]


def test_displacement_scale():
    assert displacement_scale(2.1e6, 18.2e6) == pytest.approx(0.1154, abs=1e-4)
    with pytest.raises(ValueError):
        displacement_scale(1, 0)


# ------------------------------------------------------------ correlations
def _idx(n=300):
    return pd.date_range("2001-01-01", periods=n, freq="MS")


def test_changes_diff_log_and_gaps():
    s = pd.Series([4.0, 4.2, np.nan, 4.1, 4.5], index=_idx(5))
    d = changes(s, 1)
    assert d.round(6).tolist() == [0.2, 0.4]     # no change across the missing month
    p = pd.Series([100.0, 110.0], index=_idx(2))
    assert changes(p, 1, log=True).iloc[0] == pytest.approx(math.log(1.1))


def test_change_correlation_recovers_corr_and_beta():
    rng = np.random.default_rng(0)
    nat_steps = rng.normal(0, 0.1, 300)
    loc_steps = 2.0 * nat_steps + rng.normal(0, 0.1, 300)
    nat = pd.Series(5 + nat_steps.cumsum(), index=_idx())
    loc = pd.Series(5 + loc_steps.cumsum(), index=_idx())
    out = change_correlation(loc, nat, months=1)
    assert out["corr"] == pytest.approx(2 / math.sqrt(5), abs=0.05)     # 0.894
    assert out["beta"] == pytest.approx(2.0, abs=0.15)
    assert out["n"] == 299
    indep = pd.Series(5 + rng.normal(0, 0.1, 300).cumsum(), index=_idx())
    assert abs(change_correlation(indep, nat)["corr"]) < 0.15
    # too few observations -> NaN, not a misleading number
    short = change_correlation(loc.iloc[:10], nat.iloc[:10])
    assert math.isnan(short["corr"]) and short["n"] == 9


def test_change_correlation_exclude_drops_changes_touching_period():
    rng = np.random.default_rng(1)
    nat = pd.Series(rng.normal(0, 1, 300).cumsum(), index=_idx())
    loc = nat + rng.normal(0, 0.5, 300)
    full = change_correlation(loc, nat, months=12)
    ex = change_correlation(loc, nat, months=12, exclude=[("2010-01-01", "2010-12-01")])
    # 12 changes end in 2010 and 12 more start in 2010
    assert full["n"] - ex["n"] == 24


def test_deseasonalize_removes_shared_seasonal_rhythm():
    rng = np.random.default_rng(2)
    idx = _idx()
    season = np.tile([0.5, 0.4, 0.3, 0.2, 0.1, 0.0, -0.1, -0.2, -0.3, -0.4, -0.5, 0.0], 25)
    nat = pd.Series(np.exp((season + rng.normal(0, 0.05, 300)).cumsum() / 100), index=idx)
    loc = pd.Series(np.exp((season + rng.normal(0, 0.05, 300)).cumsum() / 100), index=idx)
    raw = change_correlation(loc, nat, months=1, log=True)
    clean = change_correlation(loc, nat, months=1, log=True, deseason=True)
    assert raw["corr"] > 0.9            # the calendar alone makes them look alike
    assert abs(clean["corr"]) < 0.2     # the surprises are independent
    ch = deseasonalize(changes(nat, 1, log=True))
    assert ch.groupby(ch.index.month).mean().abs().max() < 1e-12


def test_single_strike_basis_matches_monte_carlo():
    assert labor.SINGLE_STRIKE_CEILING == pytest.approx(0.6833, abs=1e-4)
    rng = np.random.default_rng(3)
    r = 0.8
    n = rng.normal(size=400_000)
    l_ = r * n + math.sqrt(1 - r * r) * rng.normal(size=400_000)
    mc = np.corrcoef((n > 0).astype(float), np.maximum(l_, 0))[0, 1]
    assert single_strike_basis(r) == pytest.approx(mc, abs=0.01)
    assert single_strike_basis(-0.3) == 0.0


# ------------------------------------------------- job loss vs U3 contract
def test_unemployment_rises():
    u = pd.Series([4.0, 4.1, 4.1, 4.0, 4.3], index=_idx(5))
    assert unemployment_rises(u, 1).tolist() == [1.0, 0.0, 0.0, 1.0]
    assert unemployment_rises(u, 1, threshold_pp=0.15).tolist() == [0.0, 0.0, 0.0, 1.0]
    assert unemployment_rises(u, 3).tolist() == [0.0, 1.0]


def test_job_loss_basis_formula_and_signs():
    rng = np.random.default_rng(4)
    idx = _idx()
    steps = rng.choice([-0.1, 0.0, 0.1], size=300)
    u = pd.Series(4 + steps.cumsum(), index=idx)
    rising_next = (u.shift(-1) > u + 1e-9).astype(float)
    # Layoffs (percent) high exactly in months the rate rose into.
    rate = pd.Series(np.where(rising_next.shift(1) == 1, 3.0, 1.0), index=idx)
    out = job_loss_basis(rate, u, months=1)
    # recompute by hand
    pays = unemployment_rises(u, 1)
    p_t = (rate / 100).shift(-1).reindex(pays.index)
    df = pd.concat([pays, p_t], axis=1).dropna()
    q, p = df.iloc[:, 0].mean(), df.iloc[:, 1].mean()
    both = (df.iloc[:, 0] * df.iloc[:, 1]).mean()
    assert out["corr"] == pytest.approx((both - p * q) / math.sqrt(p * (1 - p) * q * (1 - q)))
    assert out["p_pay_given_loss"] == pytest.approx(both / p)
    assert out["corr"] > 0.05 and out["p_pay_given_loss"] > out["q"]
    # a personal hazard 1/10 of the industry's: corr shrinks by about sqrt(0.1)
    small = job_loss_basis(rate, u, months=1, hazard_scale=0.1)
    assert small["corr"] == pytest.approx(out["corr"] * math.sqrt(0.1), rel=0.1)
    # layoffs unrelated to the contract -> about zero
    flat = job_loss_basis(pd.Series(1.0, index=idx), u, months=12)
    assert abs(flat["corr"]) < 1e-9 and flat["p"] == pytest.approx(annual_prob_from_monthly(0.01))


# ------------------------------------------------------------ lookup API
def test_resolve_industry_and_state():
    assert labor.resolve_industry("restaurant server") == "accommodation_food"
    assert labor.resolve_industry("Construction") == "construction"
    assert labor.resolve_industry("real estate agent") == "financial"
    assert labor.resolve_industry("") == labor.DEFAULT_INDUSTRY
    assert labor.resolve_industry("astronaut") == labor.DEFAULT_INDUSTRY
    assert labor.resolve_state("Austin, TX") == "TX"
    assert labor.resolve_state("california") == "CA"
    assert labor.resolve_state("Kansas City, MO") == "MO"
    assert labor.resolve_state("Washington, D.C.") == "DC"
    assert labor.resolve_state("Washington") == "WA"
    assert labor.resolve_state("Denver") == "CO"
    assert labor.resolve_state("Atlantis") is None


def test_job_loss_prob_lookup():
    con = labor.job_loss_prob("construction")
    gov = labor.job_loss_prob("government")
    assert 0 < gov < con < 0.2
    assert labor.job_loss_prob("construction", kind="any") > con
    assert labor.job_loss_prob("construction", scenario="recession") > con
    one = labor.job_loss_prob("construction", horizon_months=1)
    assert one == pytest.approx(monthly_from_annual_prob(con))
    assert labor.job_loss_prob("unknown job") == labor.job_loss_prob(labor.DEFAULT_INDUSTRY)
    with pytest.raises(ValueError):
        labor.job_loss_prob("retail", kind="sometimes")


def test_basis_to_national_fallbacks():
    tx = labor.basis_to_national("TX")
    assert tx["matched"] == "TX" and tx["source"] == "measured"
    assert tx["basis"] == pytest.approx(single_strike_basis(tx["corr"]), abs=1e-3)
    assert labor.basis_to_national("MI")["matched"] == "MI"           # not "miami"
    assert labor.basis_to_national("west")["matched"].startswith("region:west")
    unknown = labor.basis_to_national("Narnia")
    assert unknown["source"] == "fallback"
    assert labor.basis_to_national("Los Angeles", "cpi")["matched"] == "metro:los_angeles"
    assert labor.basis_to_national("Phoenix, AZ", "cpi")["matched"] == "AZ -> west"
    assert labor.basis_to_national("south", "cpi")["matched"] == "south"
    raw = labor.basis_to_national("south", "cpi", single_strike=False)
    assert raw["basis"] == pytest.approx(raw["corr"], abs=1e-3)
    with pytest.raises(ValueError):
        labor.basis_to_national("TX", "gdp")


def test_hedge_defaults():
    job = labor.hedge_defaults("construction", "CO", contract="unemployment")
    assert 0 < job["loss_prob"] < 0.02                  # one month
    assert 0 <= job["basis_correlation"] < 0.05         # U3 barely tracks one job
    assert "Construction" in job["evidence"]
    biz = labor.hedge_defaults(place="FL", exposure="local_economy")
    assert biz["loss_prob"] is None and 0.2 < biz["basis_correlation"] < 0.7
    retiree = labor.hedge_defaults(place="Ohio", contract="cpi", exposure="cost")
    assert retiree["loss_prob"] is None and 0.4 < retiree["basis_correlation"] <= labor.SINGLE_STRIKE_CEILING


def test_frozen_tables_are_complete_and_in_range():
    assert set(labor.JOB_LOSS) == set(labor.INDUSTRIES)
    for row in labor.JOB_LOSS.values():
        assert 0 < row["annual_displacement"] < row["annual_any"] < 1
        assert row["annual_recession"] >= row["annual_any"] * 0.95
        assert abs(row["basis_u3_1m"]) < 0.1
    assert set(labor.STATE_UNEMPLOYMENT_BASIS) == set(labor.STATE_FIPS)
    for row in labor.STATE_UNEMPLOYMENT_BASIS.values():
        assert -1 <= row["monthly"] <= row["annual"] <= 1
    assert set(labor.CPI_BASIS) >= {"northeast", "midwest", "south", "west"}
    for row in {**labor.CPI_BASIS, **labor.CPI_METRO_BASIS}.values():
        assert row["annual"] is None or 0 < row["annual"] <= 1
    assert 0.05 < labor.DISPLACEMENT_SCALE < 0.3
