import numpy as np
import pandas as pd
import pytest

from hone.backtest import conviction as cv
from hone.optimization.views import DAYS_PER_YEAR
from hone.pipeline import synthetic_universe

# Small panels: the pytest suite proves the machinery is correct and
# reproducible; the statistical claims come from the full sweep that
# scratchpad/run_conviction_backtest.py drives.
EQUITY = cv.equities(n_days=600)
CRYPTO = cv.crypto(n_days=800)


def _run(asset_class, seed=1000, **kwargs):
    prices = asset_class.prices(seed)
    grid = cv.build_grid(
        prices, asset_class.lookback, 21, asset_class.periods_per_year
    )
    return cv.run_investor_backtest(
        prices,
        seed=seed,
        grid=grid,
        lookback=asset_class.lookback,
        market=asset_class.market,
        periods_per_year=asset_class.periods_per_year,
        **kwargs,
    )


class TestSkillMapping:
    def test_zero_skill_is_a_coin_flip(self):
        assert cv.hit_rate_from_skill(0.0) == pytest.approx(0.5)

    def test_hit_rate_is_monotone_and_modest(self):
        assert cv.hit_rate_from_skill(0.2) == pytest.approx(0.5641, abs=1e-3)
        assert cv.hit_rate_from_skill(0.4) == pytest.approx(0.6310, abs=1e-3)
        assert cv.hit_rate_from_skill(0.4) > cv.hit_rate_from_skill(0.2)

    def test_perfect_skill_never_misses(self):
        assert cv.hit_rate_from_skill(1.0) > 0.98

    def test_coin_flipper_earns_no_tilt(self):
        assert cv.confidence_from_hit_rate(0.5) == cv.CONFIDENCE_FLOOR
        assert cv.confidence_from_hit_rate(0.2) == cv.CONFIDENCE_FLOOR

    def test_confidence_scales_with_edge(self):
        assert cv.confidence_from_hit_rate(1.0) == pytest.approx(1.0)
        assert cv.confidence_from_hit_rate(0.75) == pytest.approx(0.5)

    def test_stated_confidence_is_anchored_above_the_floor(self):
        # A no-skill investor still says ~30%: that is how people talk, and
        # it is why "stated" is not a proxy for "true".
        assert cv.stated_confidence(0.0) > 0.25
        assert cv.stated_confidence(0.4) > cv.stated_confidence(0.0)

    def test_overconfidence_raises_and_clips(self):
        assert cv.stated_confidence(0.0, 2.0) > cv.stated_confidence(0.0, 1.0)
        assert cv.stated_confidence(0.4, 10.0) == pytest.approx(1.0)


class TestViewConstruction:
    def test_horizon_is_converted_to_calendar_days(self):
        f = cv.Forecast(
            ticker="AAPL",
            current_price=100.0,
            target_price=110.0,
            forecast_log_return=float(np.log(1.1)),
            realized_log_return=0.0,
            prior_log_return=0.0,
            resolves_at=0,
        )
        equity_view = cv._to_views([f], 0.5, 63, 252)[0]
        crypto_view = cv._to_views([f], 0.5, 63, 365)[0]
        # 63 *trading* days is a calendar quarter; 63 crypto days is 63 days.
        assert equity_view.horizon_days == pytest.approx(63 * DAYS_PER_YEAR / 252)
        assert crypto_view.horizon_days == pytest.approx(63 * DAYS_PER_YEAR / 365)
        # Same target, either clock: a sub-annual view asserts a one-off
        # move, so Q is the move itself and does not diverge with the
        # calendar. Only the *compounded* reading (kept for warnings) does.
        assert equity_view.expected_return == pytest.approx(0.10)
        assert crypto_view.expected_return == pytest.approx(0.10)
        assert equity_view.implied_cagr < crypto_view.implied_cagr

    def test_perfect_skill_reproduces_the_realized_price(self):
        prices = EQUITY.prices(7)
        grid = cv.build_grid(prices, EQUITY.lookback, 21, EQUITY.periods_per_year)
        rng = np.random.default_rng(0)
        forecasts = cv._make_forecasts(grid[0], prices, rng, 1.0, 3, 63, 252)
        assert forecasts
        for f in forecasts:
            realized_price = float(prices[f.ticker].iloc[f.resolves_at])
            assert f.target_price == pytest.approx(realized_price, rel=1e-9)

    def test_zero_skill_ignores_the_realized_path(self):
        """The skill=0 null must be pure noise, not a peek at the future."""
        prices = EQUITY.prices(7)
        grid = cv.build_grid(prices, EQUITY.lookback, 21, EQUITY.periods_per_year)
        tampered = prices.copy()
        tampered.iloc[grid[0].t + 10 :] *= 3.0  # rewrite the future entirely
        a = cv._make_forecasts(grid[0], prices, np.random.default_rng(0), 0.0, 3, 63, 252)
        b = cv._make_forecasts(grid[0], tampered, np.random.default_rng(0), 0.0, 3, 63, 252)
        assert [f.target_price for f in a] == pytest.approx([f.target_price for f in b])

    def test_no_views_issued_without_a_resolvable_horizon(self):
        prices = EQUITY.prices(7)
        grid = cv.build_grid(prices, EQUITY.lookback, 21, EQUITY.periods_per_year)
        assert cv._make_forecasts(
            grid[-1], prices, np.random.default_rng(0), 0.3, 2, 63, 252
        ) == []


class TestInvestorBacktest:
    def test_runs_all_six_strategies(self):
        run = _run(EQUITY, gamma=2.5, skill=0.2)
        assert set(run.metrics) == set(cv.STRATEGIES)
        for name, m in run.metrics.items():
            assert m, name
            assert np.isfinite(m["sharpe"])
            assert m["max_drawdown"] <= 0.0

    def test_structure_metrics_are_sane(self):
        run = _run(EQUITY, gamma=2.5, skill=0.2)
        n_assets = 6
        assert run.metrics["equal_weight"]["effective_n"] == pytest.approx(n_assets)
        assert run.metrics["equal_weight"]["turnover"] == pytest.approx(0.0)
        assert run.metrics["market_hold"]["effective_n"] == pytest.approx(1.0)
        for name in cv.VIEW_STRATEGIES:
            assert 1.0 <= run.metrics[name]["effective_n"] <= n_assets
            assert run.metrics[name]["turnover"] > 0.0

    def test_deterministic(self):
        a = _run(EQUITY, gamma=2.5, skill=0.2)
        b = _run(EQUITY, gamma=2.5, skill=0.2)
        assert a.metrics == b.metrics
        assert a.diagnostics == b.diagnostics

    def test_different_seed_gives_a_different_path(self):
        a = _run(EQUITY, seed=1000, gamma=2.5, skill=0.2)
        b = _run(EQUITY, seed=1001, gamma=2.5, skill=0.2)
        assert a.metrics["views_stated_conf"] != b.metrics["views_stated_conf"]

    def test_perfect_forecaster_hits_every_call(self):
        run = _run(EQUITY, gamma=2.5, skill=1.0)
        assert run.diagnostics["directional_hit_rate"] == pytest.approx(1.0)
        assert run.diagnostics["surprise_hit_rate"] == pytest.approx(1.0)
        # ...and the machinery must actually pay them for it.
        assert (
            run.metrics["views_full_conf"]["cagr"] > run.metrics["risk_only"]["cagr"]
        )

    def test_no_skill_calibrates_down_toward_the_floor(self):
        run = _run(EQUITY, gamma=2.5, skill=0.0)
        assert run.diagnostics["surprise_hit_rate"] == pytest.approx(0.5, abs=0.12)
        assert run.diagnostics["mean_calibrated_confidence"] < cv.stated_confidence(0.0)

    def test_only_omega_differs_between_view_strategies(self):
        """Pin the design claim: at equal confidence the three view
        strategies are the same portfolio, so any gap between them is
        attributable to the confidence mapping alone."""
        run = _run(EQUITY, gamma=2.5, skill=0.3, overconfidence=8.0)
        assert cv.stated_confidence(0.3, 8.0) == pytest.approx(1.0)
        assert run.metrics["views_stated_conf"] == run.metrics["views_full_conf"]

    def test_overconfidence_only_moves_the_stated_strategy(self):
        a = _run(EQUITY, gamma=2.5, skill=0.2, overconfidence=1.0)
        b = _run(EQUITY, gamma=2.5, skill=0.2, overconfidence=2.0)
        for name in ("equal_weight", "market_hold", "risk_only",
                     "views_calibrated_conf", "views_full_conf"):
            assert a.metrics[name] == b.metrics[name], name
        assert a.metrics["views_stated_conf"] != b.metrics["views_stated_conf"]

    def test_higher_gamma_lowers_view_free_volatility(self):
        lo = _run(EQUITY, gamma=0.5, skill=0.0)
        hi = _run(EQUITY, gamma=8.0, skill=0.0)
        assert (
            hi.metrics["risk_only"]["volatility"]
            <= lo.metrics["risk_only"]["volatility"] + 1e-9
        )

    def test_rejects_a_history_too_short_to_walk_forward(self):
        prices, _ = synthetic_universe(n_days=280)
        with pytest.raises(ValueError, match="rebalance dates"):
            cv.run_investor_backtest(prices, gamma=1.2, skill=0.0, lookback=252)


class TestCrypto:
    def test_crypto_uses_its_own_calendar_and_proxy(self):
        assert CRYPTO.periods_per_year == 365
        assert CRYPTO.market == "BTC/USD"

    def test_runs_end_to_end_on_crypto(self):
        run = _run(CRYPTO, gamma=2.5, skill=0.2)
        assert set(run.metrics) == set(cv.STRATEGIES)
        # Crypto is the higher-volatility asset class by construction; the
        # backtest should reflect that rather than smooth it away.
        assert run.metrics["market_hold"]["volatility"] > 0.4


class TestPanel:
    def test_panel_and_summary_shape(self):
        panel = cv.run_panel(
            EQUITY,
            gammas=[1.2, 5.0],
            skills=[0.0],
            overconfidences=[1.0],
            n_investors=2,
        )
        assert len(panel) == 2 * 2 * len(cv.STRATEGIES)
        summary = cv.summarize(panel)
        assert len(summary) == 2 * len(cv.STRATEGIES)
        assert summary["beat_risk_only"].between(0.0, 1.0).all()
        # A strategy never beats itself.
        self_row = summary[summary["strategy"] == "risk_only"]
        assert (self_row["beat_risk_only"] == 0.0).all()

    def test_paired_design_holds_the_path_fixed_across_cells(self):
        """Gamma must not change which market the investor lived through."""
        panel = cv.run_panel(
            EQUITY,
            gammas=[1.2, 5.0],
            skills=[0.0],
            overconfidences=[1.0],
            n_investors=2,
        )
        hold = panel[panel["strategy"] == "market_hold"]
        for _, group in hold.groupby("investor"):
            assert group["cagr"].nunique() == 1

    def test_diagnostics_table(self):
        panel = cv.run_panel(
            EQUITY,
            gammas=[2.5],
            skills=[0.0, 0.4],
            overconfidences=[1.0],
            n_investors=2,
        )
        diag = cv.diagnostics_table(panel)
        assert len(diag) == 2
        by_skill = diag.set_index("skill")["diag_directional_hit_rate"]
        assert by_skill[0.4] > by_skill[0.0]
        assert isinstance(diag, pd.DataFrame)
