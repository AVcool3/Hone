"""The behaviour gap: capitulation, the panic rule, and what it costs."""

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from hone.backtest.behavior import (
    DEFAULT_REENTRY_RECOVERY,
    behavior_gap,
    matching_advantage,
    panic_threshold,
    simulate_holding,
)
from hone.backtest.engine import run_backtest
from hone.pipeline import synthetic_universe
from hone.web.app import create_app


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app())


def curve(values, start="2020-01-01"):
    idx = pd.date_range(start, periods=len(values), freq="B")
    return pd.Series(values, index=idx)


class TestPanicThreshold:
    def test_scales_inversely_with_risk_aversion(self):
        """sigma_target = S / gamma, so tolerance falls as gamma rises."""
        ts = [panic_threshold(g) for g in (0.5, 1.2, 2.5, 5.0, 8.0)]
        assert ts == sorted(ts, reverse=True)

    def test_bounded_at_both_ends(self):
        assert panic_threshold(0.001) == pytest.approx(0.60)  # cap
        assert panic_threshold(1000.0) == pytest.approx(0.08)  # floor

    def test_does_not_depend_on_realized_market_returns(self):
        """The bug this replaced: a sample premium made the threshold a
        function of how the last five years happened to go, and a negative
        one pinned every gamma to the same cap."""
        import inspect

        from hone.backtest import behavior

        src = inspect.signature(panic_threshold).parameters
        assert "reference_return" not in src
        assert "market_sharpe" in src
        assert behavior.TARGET_MARKET_SHARPE > 0

    def test_matches_the_merton_budget(self):
        from hone.backtest.behavior import TARGET_MARKET_SHARPE, VAR_Z

        assert panic_threshold(2.0) == pytest.approx(
            VAR_Z * TARGET_MARKET_SHARPE / 2.0
        )


class TestSimulateHolding:
    def test_a_calm_path_is_never_sold(self):
        rising = curve(np.linspace(1.0, 2.0, 300))
        realized, panics, cash, drag = simulate_holding(
            rising.pct_change().dropna(), threshold=0.20
        )
        assert panics == [] and cash == 0 and drag == 0.0
        assert realized.iloc[-1] == pytest.approx(rising.iloc[-1], rel=1e-9)

    def test_a_deep_drawdown_triggers_a_sale(self):
        # up, then a 40% fall, then a full recovery
        path = np.concatenate([
            np.linspace(1.0, 1.5, 60),
            np.linspace(1.5, 0.9, 60),
            np.linspace(0.9, 1.8, 120),
        ])
        realized, panics, cash, drag = simulate_holding(
            curve(path).pct_change().dropna(), threshold=0.20
        )
        assert len(panics) >= 1
        assert cash > 0 and drag > 0
        assert len(realized) == len(path) - 1

    def test_a_slow_v_shaped_decline_can_reward_selling(self):
        """Honest about what the model does and does not claim.

        On a gentle, straight-line fall the 20% trigger fires long before
        the bottom, so the investor sells high and buys back low: a good
        trade. Capitulation is not a law of nature that always costs
        money, and a simulation rigged so that it always did would be
        worthless as evidence. Real crashes are fast — see the next test.
        """
        path = np.concatenate([
            np.linspace(1.0, 1.5, 60),
            np.linspace(1.5, 0.9, 60),
            np.linspace(0.9, 1.8, 120),
        ])
        realized, _, _, _ = simulate_holding(
            curve(path).pct_change().dropna(), threshold=0.20
        )
        assert realized.iloc[-1] > path[-1] / path[0]

    def test_a_sharp_crash_and_snapback_punishes_selling(self):
        """The realistic shape, and the one the behaviour gap is about.

        A gentle decline hands the trigger a good exit — it fires on the
        way down, far above the bottom. What actually hurts people is the
        drop that *overshoots* the threshold in a session or two, so they
        sell at the low, and then rebounds before waiting for
        confirmation lets them back in.
        """
        path = np.concatenate([
            np.linspace(1.0, 1.20, 120),
            [1.05, 0.78],                   # two brutal sessions, past the trigger
            np.linspace(0.80, 1.45, 30),    # V-shaped snapback
            np.linspace(1.45, 1.60, 150),
        ])
        realized, panics, cash, _ = simulate_holding(
            curve(path).pct_change().dropna(), threshold=0.20, min_wait=3
        )
        assert panics and cash > 0
        assert realized.iloc[-1] < path[-1] / path[0]

    def test_reentry_waits_for_confirmation(self):
        """Selling and buying back at the bottom would be a good trade.

        The model must not accidentally reward panicking, which is what an
        unconditional fixed cooldown did.
        """
        path = np.concatenate([
            np.linspace(1.0, 1.0, 5),
            np.linspace(1.0, 0.6, 40),   # crash
            np.linspace(0.6, 0.62, 200),  # long flat bottom
        ])
        _, panics, cash, _ = simulate_holding(
            curve(path).pct_change().dropna(), threshold=0.20, min_wait=5
        )
        assert panics
        # never recovers 10% off the low, so the investor stays out
        assert cash > 150

    def test_peak_resets_on_reentry(self):
        """Without the reset the investor is parked in cash forever."""
        rng = np.random.default_rng(0)
        path = np.cumprod(1 + rng.normal(0.0003, 0.02, 900))
        realized, panics, cash, _ = simulate_holding(
            curve(path).pct_change().dropna(), threshold=0.10
        )
        assert cash < len(path) * 0.95  # not permanently out
        assert len(realized) == len(path) - 1

    def test_costs_are_charged_on_every_switch(self):
        path = np.concatenate([
            np.linspace(1.0, 0.7, 40), np.linspace(0.7, 1.4, 200)
        ])
        rets = curve(path).pct_change().dropna()
        free = simulate_holding(rets, 0.20, cost_bps=0.0)[0]
        costly = simulate_holding(rets, 0.20, cost_bps=50.0)[0]
        assert costly.iloc[-1] < free.iloc[-1]

    def test_cash_earns_the_cash_rate_not_zero(self):
        path = np.concatenate([
            np.linspace(1.0, 0.7, 40), np.full(400, 0.7)
        ])
        rets = curve(path).pct_change().dropna()
        zero = simulate_holding(rets, 0.20, cash_rate=0.0, cost_bps=0.0)[0]
        paid = simulate_holding(rets, 0.20, cash_rate=0.05, cost_bps=0.0)[0]
        assert paid.iloc[-1] > zero.iloc[-1]

    def test_reentry_recovery_default_is_a_real_threshold(self):
        assert 0.0 < DEFAULT_REENTRY_RECOVERY < 0.5


class TestBehaviorGap:
    @pytest.fixture(scope="class")
    def curves(self):
        prices, _ = synthetic_universe(n_days=1400, seed=3)
        r = run_backtest(prices, gamma=2.5, max_weight=0.35)
        dates = pd.to_datetime(r.strategies[0].dates)
        return {s.name: pd.Series(s.equity_curve, index=dates) for s in r.strategies}

    def test_one_threshold_for_every_strategy(self, curves):
        """It is the same person holding each of them.

        A per-strategy threshold made tolerance a function of the
        strategy's own Sharpe ratio — the same person tolerating 60% in a
        bad fund and 8% in a good one.
        """
        res = behavior_gap(curves, gamma=2.5)
        thresholds = {b.panic_threshold for b in res.values()}
        assert len(thresholds) == 1

    def test_a_tolerant_investor_never_sells(self, curves):
        res = behavior_gap(curves, gamma=0.4)
        assert all(len(b.panics) == 0 for b in res.values())
        assert all(abs(b.behavior_gap) < 0.01 for b in res.values())

    def test_an_anxious_investor_sells_often_and_pays_for_it(self, curves):
        res = behavior_gap(curves, gamma=8.0)
        assert sum(len(b.panics) for b in res.values()) > 0
        assert max(b.behavior_gap for b in res.values()) > 0.01

    def test_paper_curve_is_untouched_by_the_simulation(self, curves):
        res = behavior_gap(curves, gamma=8.0)
        for name, b in res.items():
            expected = curves[name] / curves[name].iloc[0]
            pd.testing.assert_series_equal(
                b.paper_equity, expected, check_names=False
            )

    def test_matching_advantage_reports_both_winners(self, curves):
        adv = matching_advantage(behavior_gap(curves, gamma=8.0))
        assert adv["best_on_paper"] in curves
        assert adv["best_as_held"] in curves
        assert isinstance(adv["ranking_changed"], bool)
        assert adv["total_panics"] >= 0

    def test_empty_input(self):
        assert behavior_gap({}, gamma=2.0) == {}
        assert matching_advantage({}) == {}

    def test_summary_reads(self, curves):
        text = list(behavior_gap(curves, gamma=8.0).values())[0].summary()
        assert "behaviour gap" in text and "capitulation" in text


class TestTheProductClaim:
    def test_matched_portfolio_loses_less_to_capitulation(self):
        """The thesis, stated as a test rather than a slogan.

        A portfolio sized to what someone can tolerate should be one they
        keep holding. Measured across several paths because a single one
        is noise — and the assertion is deliberately weak (better than the
        median alternative, not better than all of them), because that is
        what the evidence actually supports.
        """
        gaps: dict[str, list[float]] = {}
        for seed in range(8):
            prices, _ = synthetic_universe(n_days=1400, seed=seed)
            r = run_backtest(prices, gamma=2.5, max_weight=0.35)
            dates = pd.to_datetime(r.strategies[0].dates)
            curves = {
                s.name: pd.Series(s.equity_curve, index=dates)
                for s in r.strategies
            }
            for name, b in behavior_gap(curves, gamma=2.5).items():
                gaps.setdefault(name, []).append(b.behavior_gap)

        median = {k: float(np.median(v)) for k, v in gaps.items()}
        diversified = {
            k: v for k, v in median.items()
            if k in ("tier_matched", "equal_weight", "sixty_forty")
        }
        assert median["tier_matched"] == min(diversified.values())


class TestBacktestEndpoint:
    def test_behavior_block_is_returned(self, client):
        body = client.post("/api/backtest", json={"gamma": 8.0, "demo": True}).json()
        b = body["behavior"]
        assert b is not None
        assert 0.08 <= b["panic_threshold"] <= 0.60
        assert len(b["rows"]) == len(body["strategies"])
        assert all(r["label"] for r in b["rows"])
        assert b["summary"]

    def test_gap_is_paper_minus_realized(self, client):
        body = client.post("/api/backtest", json={"gamma": 8.0, "demo": True}).json()
        for r in body["behavior"]["rows"]:
            assert r["behavior_gap"] == pytest.approx(
                r["paper_cagr"] - r["realized_cagr"], abs=1e-9
            )

    def test_a_tolerant_investor_barely_sells(self, client):
        """At gamma 0.4 the threshold is the 60% cap.

        The diversified books never come close; only the deliberately
        awful performance-chasing comparator, which drew down 68%, trips
        it — and that it does is the point of including it.
        """
        body = client.post("/api/backtest", json={"gamma": 0.4, "demo": True}).json()
        rows = {r["name"]: r for r in body["behavior"]["rows"]}
        assert body["behavior"]["panic_threshold"] == pytest.approx(0.60)
        for name in ("tier_matched", "equal_weight", "sixty_forty"):
            assert rows[name]["panics"] == 0

    def test_crypto_mode_uses_the_crypto_calendar(self, client):
        body = client.post(
            "/api/backtest?asset_class=crypto", json={"gamma": 5.0, "demo": True}
        ).json()
        assert body["behavior"] is not None

    def test_page_shows_it_without_overclaiming(self, client):
        html = client.get("/").text
        assert "What you'd actually have got" in html
        assert "behaviorHTML" in html
        # the honest caveat has to be present, not just the flattering read
        assert "single paths are" in html
        assert "The sell rule isn't invented" in html
