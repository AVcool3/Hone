"""Replaying research notes: scoring, the replay engine, and its guards."""

from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from hone.backtest.reports import (
    NoteOutcome,
    ResearchNote,
    analyst_scorecard,
    compile_notes,
    run_report_backtest,
    score_notes,
    summarize,
)


def panel(n_days=800, seed=0, drift=None):
    """A price panel with known, controllable drift per name."""
    rng = np.random.default_rng(seed)
    names = ["AAA", "BBB", "CCC", "DDD"]
    drift = drift or dict.fromkeys(names, 0.0003)
    idx = pd.bdate_range("2021-01-04", periods=n_days)
    cols = {}
    for nm in names:
        r = rng.normal(drift[nm], 0.015, n_days)
        cols[nm] = 100.0 * np.cumprod(1 + r)
    return pd.DataFrame(cols, index=idx)


class TestResearchNote:
    def test_parses_dates_and_validates(self):
        n = ResearchNote("aaa", "2022-03-01", target_price=150.0)
        assert n.ticker == "AAA" and n.published == date(2022, 3, 1)
        assert n.horizon_days == 365.0  # the standard 12-month target
        with pytest.raises(ValueError):
            ResearchNote("AAA", date(2022, 1, 1), target_price=0.0)
        with pytest.raises(ValueError):
            ResearchNote("AAA", date(2022, 1, 1), target_price=10.0, confidence=1.5)


class TestScoring:
    def test_a_reached_target_scores_a_hit(self):
        px = panel(drift={"AAA": 0.002, "BBB": 0, "CCC": 0, "DDD": 0})
        entry = float(px["AAA"].loc["2021-06-01"])
        note = ResearchNote("AAA", date(2021, 6, 1), target_price=entry * 1.05,
                            horizon_days=180)
        out = score_notes([note], px)[0]
        assert out.target_hit and out.direction_hit and out.touched
        assert out.implied_return == pytest.approx(0.05, abs=1e-9)

    def test_an_unreachable_target_is_a_miss(self):
        px = panel(drift={"AAA": 0.0006, "BBB": 0, "CCC": 0, "DDD": 0})
        entry = float(px["AAA"].loc["2021-06-01"])
        note = ResearchNote("AAA", date(2021, 6, 1), target_price=entry * 3.0,
                            horizon_days=180)
        out = score_notes([note], px)[0]
        assert not out.target_hit and not out.touched
        # a 200% target over six months captures a small fraction at best,
        # and may be negative if the path went the other way
        assert out.capture < 0.5

    def test_capture_separates_wrong_from_merely_greedy(self):
        """An analyst capturing 60% of their move is useful and optimistic.

        That is a different diagnosis from being wrong, and a hit/miss flag
        cannot tell them apart.
        """
        note = ResearchNote("AAA", date(2021, 1, 4), target_price=200.0)
        greedy = NoteOutcome(note, 100.0, 160.0, 160.0, 100.0,
                             False, False, True, 0.60, 1.00)
        wrong = NoteOutcome(note, 100.0, 90.0, 105.0, 90.0,
                            False, False, False, -0.10, 1.00)
        assert greedy.capture == pytest.approx(0.60)
        assert wrong.capture < 0

    def test_unfinished_windows_are_dropped_not_counted_as_misses(self):
        """A half-elapsed target is not a failed one."""
        px = panel(n_days=400)
        last = px.index[-1].date()
        fresh = ResearchNote("AAA", last - timedelta(days=10),
                             target_price=999.0, horizon_days=365)
        assert score_notes([fresh], px) == []

    def test_unknown_tickers_are_skipped(self):
        px = panel()
        assert score_notes(
            [ResearchNote("ZZZZ", date(2021, 6, 1), target_price=10.0)], px
        ) == []

    def test_bearish_notes_score_the_other_way(self):
        px = panel(drift={"AAA": -0.002, "BBB": 0, "CCC": 0, "DDD": 0})
        entry = float(px["AAA"].loc["2021-06-01"])
        note = ResearchNote("AAA", date(2021, 6, 1), target_price=entry * 0.95,
                            horizon_days=180)
        out = score_notes([note], px)[0]
        assert out.target_hit and out.direction_hit


class TestCompileNotes:
    def test_extracts_a_note_from_report_prose(self):
        text = ("We initiate coverage of AAA with a 12-month price target of "
                "$150, implying meaningful upside from current levels.")
        notes = compile_notes(text, ["AAA"], published=date(2022, 5, 1))
        assert len(notes) == 1
        assert notes[0].ticker == "AAA"
        assert notes[0].target_price == pytest.approx(150.0)
        assert notes[0].published == date(2022, 5, 1)

    def test_defaults_to_the_offline_parser(self):
        """The LLM has read the future; extraction must not depend on it."""
        import inspect

        sig = inspect.signature(compile_notes)
        assert sig.parameters["use_llm"].default is False

    def test_notes_without_a_target_are_dropped(self):
        assert compile_notes("We like AAA here.", ["AAA"]) == []


class TestReplay:
    @pytest.fixture(scope="class")
    def prices(self):
        return panel(n_days=900, seed=5,
                     drift={"AAA": 0.0010, "BBB": 0.0002,
                            "CCC": 0.0002, "DDD": -0.0002})

    def prescient(self, prices):
        """Notes that correctly call the one name that actually rises."""
        out = []
        for d in ("2022-01-04", "2022-07-01", "2023-01-03"):
            entry = float(prices["AAA"].loc[d])
            out.append(ResearchNote("AAA", d, target_price=entry * 1.30,
                                    horizon_days=200, confidence=0.7))
        return out

    def test_runs_and_returns_a_result_per_gamma_plus_benchmarks(self, prices):
        res = run_report_backtest(self.prescient(prices), prices,
                                  gammas=(1.2, 5.0))
        assert set(res) == {"gamma_1.2", "gamma_5", "no_views_1.2", "no_views_5",
                            "equal_weight", "start_hold"}
        for r in res.values():
            assert len(r.equity) > 100
            assert np.isfinite(r.net_return)

    def perfect(self, prices, horizon=200):
        """Notes on every name with the realized forward price as target."""
        out = []
        for d in ("2022-01-04", "2022-07-01", "2023-01-03"):
            i = prices.index.get_loc(pd.Timestamp(d))
            j = min(i + horizon, len(prices) - 1)
            for name in prices.columns:
                out.append(ResearchNote(name, d, horizon_days=horizon,
                                        confidence=0.7,
                                        target_price=float(prices[name].iloc[j])))
        return out

    def test_views_move_weight_toward_the_covered_name(self, prices):
        """The mechanism guarantee. P&L is empirical; this is not."""
        from hone.backtest.reports import _active_views

        views = _active_views(self.prescient(prices), pd.Timestamp("2022-03-01"),
                              prices.loc["2022-03-01"], 0.5)
        assert [v.ticker for v in views] == ["AAA"]
        assert views[0].expected_return > 0

    def test_research_that_is_right_everywhere_shows_positive_alpha(self, prices):
        """If perfect foresight doesn't register, the harness is broken."""
        df = summarize(run_report_backtest(self.perfect(prices), prices,
                                           gammas=(1.2, 5.0)))
        assert df.loc["gamma_1.2", "research_alpha"] > 0
        assert df.loc["gamma_5", "research_alpha"] > 0
        assert df.loc["gamma_1.2", "sharpe"] > df.loc["no_views_1.2", "sharpe"]

    def test_one_good_call_in_a_small_universe_is_not_detectable(self, prices):
        """A finding, pinned so nobody later mistakes it for a bug.

        With four names and a 35% cap, a single covered name is at most a
        third of the book and Black-Litterman's covariance spillover
        reshuffles the other two thirds. That reshuffle is the same order of
        magnitude as the direct effect, so the sign of `research_alpha` on
        one call is noise. Archives covering a handful of tickers cannot
        answer "was this research any good".
        """
        df = summarize(run_report_backtest(self.prescient(prices), prices,
                                           gammas=(1.2, 5.0)))
        alphas = [df.loc["gamma_1.2", "research_alpha"],
                  df.loc["gamma_5", "research_alpha"]]
        assert min(alphas) < 0 < max(alphas)   # disagrees with itself
        assert all(abs(a) < 0.10 for a in alphas)

    def test_research_alpha_is_only_defined_against_a_matched_run(self, prices):
        df = summarize(run_report_backtest(self.prescient(prices), prices,
                                           gammas=(1.2,)))
        assert np.isnan(df.loc["equal_weight", "research_alpha"])
        assert np.isfinite(df.loc["gamma_1.2", "research_alpha"])

    def test_risk_aversion_lowers_volatility(self, prices):
        res = run_report_backtest(self.prescient(prices), prices,
                                  gammas=(0.5, 8.0))
        bold = res["gamma_0.5"].metrics["volatility"]
        timid = res["gamma_8"].metrics["volatility"]
        assert timid < bold

    def test_costs_are_charged_and_reduce_the_result(self, prices):
        notes = self.prescient(prices)
        free = run_report_backtest(notes, prices, gammas=(1.2,), cost_bps=0.0)
        dear = run_report_backtest(notes, prices, gammas=(1.2,), cost_bps=200.0)
        assert dear["gamma_1.2"].net_return < free["gamma_1.2"].net_return
        assert dear["gamma_1.2"].cost_drag > 0
        assert free["gamma_1.2"].cost_drag == 0.0

    def test_no_notes_still_runs_as_a_pure_risk_rebalance(self, prices):
        res = run_report_backtest([], prices, gammas=(2.5,))
        assert np.isfinite(res["gamma_2.5"].net_return)

    def test_position_cap_is_enforced_through_the_replay(self, prices):
        """Strong views on one name would otherwise take the whole book."""
        loud = [ResearchNote("AAA", "2022-01-04", target_price=1e4,
                             horizon_days=400, confidence=0.95)]
        res = run_report_backtest(loud, prices, gammas=(0.5,), max_weight=0.30)
        # a capped book cannot compound like a single stock
        solo = prices["AAA"].iloc[-1] / prices["AAA"].iloc[252] - 1
        assert res["gamma_0.5"].net_return < solo

    def test_superseded_notes_do_not_keep_voting(self, prices):
        """Two notes on one name mean the house changed its mind."""
        from hone.backtest.reports import _active_views

        notes = [
            ResearchNote("AAA", "2022-01-04", target_price=500.0, horizon_days=400),
            ResearchNote("AAA", "2022-03-01", target_price=120.0, horizon_days=400),
        ]
        views = _active_views(notes, pd.Timestamp("2022-06-01"),
                              prices.loc["2022-06-01"], 0.5)
        assert len(views) == 1
        assert views[0].target_price == pytest.approx(120.0)

    def test_expired_notes_stop_voting(self, prices):
        from hone.backtest.reports import _active_views

        notes = [ResearchNote("AAA", "2022-01-04", target_price=500.0,
                              horizon_days=30)]
        assert _active_views(notes, pd.Timestamp("2022-06-01"),
                             prices.loc["2022-06-01"], 0.5) == []

    def test_refuses_a_panel_too_short_for_a_trailing_window(self):
        with pytest.raises(ValueError, match="trailing window"):
            run_report_backtest([], panel(n_days=100), gammas=(1.0,))

    def test_summary_table_puts_benchmarks_last(self, prices):
        df = summarize(run_report_backtest(self.prescient(prices), prices,
                                           gammas=(1.2, 5.0)))
        assert list(df.index)[-2:] == ["equal_weight", "start_hold"]
        assert "gamma_1.2" in df.index and "no_views_1.2" in df.index
        assert "cost_drag_pa" in df.columns


class TestScorecard:
    def test_scores_the_publication_itself(self):
        px = panel(drift={"AAA": 0.002, "BBB": 0.002, "CCC": 0, "DDD": 0})
        notes = [
            ResearchNote("AAA", date(2021, 6, 1),
                         target_price=float(px["AAA"].loc["2021-06-01"]) * 1.03,
                         horizon_days=180, confidence=0.7),
            ResearchNote("CCC", date(2021, 6, 1),
                         target_price=float(px["CCC"].loc["2021-06-01"]) * 3.0,
                         horizon_days=180, confidence=0.8),
        ]
        card = analyst_scorecard(score_notes(notes, px))
        assert card["n"] == 2
        assert 0.0 <= card["target_hit_rate"] <= 1.0
        assert "median_capture" in card

    def test_empty_input(self):
        assert analyst_scorecard([])["n"] == 0
