"""Conviction Compiler: offline parser, sanity checks, and the API surface.

These run with no network and no ANTHROPIC_API_KEY — the deterministic
backend is a first-class implementation, not a stub, so it is tested as one.
"""

import pytest
from fastapi.testclient import TestClient

from hone.llm.compiler import compile_convictions, sanity_check
from hone.llm.fallback import (
    _extract_confidence,
    _extract_horizon,
    _extract_prices,
    _resolve_ticker,
    compile_offline,
)
from hone.llm.schemas import CompiledView
from hone.web.app import create_app


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app())


class TestPriceExtraction:
    @pytest.mark.parametrize(
        "text,target",
        [
            ("NVDA to $250 by year end", 250.0),
            ("I think it hits 300", 300.0),
            ("price target of 1,250.50", 1250.5),
            ("bitcoin 150k by Q4", 150_000.0),
            ("AAPL reaches $412.75", 412.75),
            ("TSLA runs up to 500", 500.0),
        ],
    )
    def test_targets(self, text, target):
        assert _extract_prices(text)[1] == pytest.approx(target)

    def test_from_to_gives_both(self):
        entry, target = _extract_prices("MSFT from 400 to 520")
        assert entry == pytest.approx(400.0)
        assert target == pytest.approx(520.0)

    def test_entry_and_target_are_distinguished(self):
        entry, target = _extract_prices("it's trading at 100, I think it hits 180")
        assert entry == pytest.approx(100.0)
        assert target == pytest.approx(180.0)


class TestHorizonExtraction:
    @pytest.mark.parametrize(
        "text,days",
        [
            ("in 6 months", 6 * 30.44),
            ("over the next 90 days", 90.0),
            ("in two years", 730.0),
            ("a couple of quarters", 2 * 91.31),
            ("over 3 weeks", 21.0),
        ],
    )
    def test_explicit_durations(self, text, days):
        assert _extract_horizon(text) == pytest.approx(days, rel=1e-3)

    def test_year_end_depends_on_today(self):
        assert _extract_horizon("by year end", today_month=1) == pytest.approx(
            11 * 30.44
        )
        # A December thesis must not compile to a zero-day horizon.
        assert _extract_horizon("by year end", today_month=12) >= 30.0

    def test_quarter_wraps_to_next_year(self):
        # In November, "Q1" means next year's Q1, not a negative horizon.
        assert _extract_horizon("by Q1", today_month=11) > 0

    def test_silence_is_none(self):
        assert _extract_horizon("NVDA to 250") is None


class TestConfidenceExtraction:
    @pytest.mark.parametrize(
        "text,pct",
        [
            ("70% confident", 70.0),
            ("I'm 85% sure", 85.0),
            ("8 out of 10 conviction", 80.0),
            ("7/10", 70.0),
        ],
    )
    def test_numeric(self, text, pct):
        assert _extract_confidence(text) == pytest.approx(pct)

    def test_hedged_language_scores_lower_than_emphatic(self):
        tentative = _extract_confidence("it might work out")
        emphatic = _extract_confidence("very confident in this one")
        assert tentative is not None and emphatic is not None
        assert tentative < 50 < emphatic

    def test_negation_does_not_read_as_confidence(self):
        """'not confident' must not match the 'confident' rule."""
        assert _extract_confidence("not confident at all") < 50

    def test_silence_is_none(self):
        assert _extract_confidence("NVDA to 250") is None


class TestTickerResolution:
    @pytest.mark.parametrize(
        "text,ticker",
        [
            ("$NVDA looks good", "NVDA"),
            ("I like NVDA here", "NVDA"),
            ("apple is cheap", "AAPL"),
            ("bitcoin to 200k", "BTC/USD"),
            ("ETH/USD breaks out", "ETH/USD"),
            ("long solana", "SOL/USD"),
        ],
    )
    def test_resolves(self, text, ticker):
        assert _resolve_ticker(text, None) == ticker

    def test_stopwords_are_not_tickers(self):
        assert _resolve_ticker("I think AI is a big deal", None) is None

    def test_universe_symbol_wins(self):
        assert _resolve_ticker("CEO says XYZ is fine", ["XYZ"]) == "XYZ"


class TestOfflineCompile:
    def test_full_sentence(self):
        res = compile_offline(
            "I think NVDA runs to $250 by year end, I'm 70% confident",
            ["NVDA", "AAPL"],
            today_month=1,
        )
        assert res.engine == "fallback"
        assert len(res.views) == 1
        v = res.views[0]
        assert v.ticker == "NVDA"
        assert v.direction == "bullish"
        assert v.target_price == pytest.approx(250.0)
        assert v.confidence_pct == pytest.approx(70.0)
        assert 300 < v.horizon_days < 350
        assert v.needs_review == []  # everything was stated

    def test_bearish_thesis(self):
        res = compile_offline("short TSLA down to 150 over the next quarter")
        v = res.views[0]
        assert v.ticker == "TSLA"
        assert v.direction == "bearish"
        assert v.target_price == pytest.approx(150.0)

    def test_multiple_convictions_split(self):
        res = compile_offline(
            "NVDA to 250 by June. Also AAPL hits 300 in 6 months.",
            ["NVDA", "AAPL"],
        )
        assert {v.ticker for v in res.views} == {"NVDA", "AAPL"}

    def test_guessed_fields_are_flagged(self):
        res = compile_offline("I like NVDA", ["NVDA"])
        v = res.views[0]
        assert "horizon_days" in v.needs_review
        assert "confidence_pct" in v.needs_review
        assert "target_price" in v.needs_review
        # defaults are still populated so the form is never empty
        assert v.horizon_days and v.confidence_pct

    def test_no_ticker_gives_actionable_note(self):
        res = compile_offline("the market feels toppy")
        assert res.views == []
        assert any("ticker" in n.lower() for n in res.notes)

    def test_empty_text(self):
        res = compile_convictions("", prefer_llm=False)
        assert res.views == []


class TestLivePriceFill:
    def test_entry_price_comes_from_the_server(self):
        res = compile_convictions(
            "NVDA to 250 in 6 months",
            ["NVDA"],
            prices={"NVDA": 180.0},
            prefer_llm=False,
        )
        v = res.views[0]
        assert v.entry_price == pytest.approx(180.0)
        assert v.implied_return() == pytest.approx(250 / 180 - 1)

    def test_user_stated_basis_is_not_overwritten(self):
        res = compile_convictions(
            "I bought NVDA at 120, it goes to 250 in 6 months",
            ["NVDA"],
            prices={"NVDA": 180.0},
            prefer_llm=False,
        )
        assert res.views[0].entry_price == pytest.approx(120.0)


class TestSanityCheck:
    def test_absurd_target_is_flagged(self):
        v = CompiledView(
            ticker="NVDA", entry_price=180, target_price=1800, horizon_days=30
        )
        assert any("decimal" in w or "/yr" in w for w in sanity_check(v))

    def test_direction_contradiction_flagged(self):
        v = CompiledView(
            ticker="NVDA",
            direction="bullish",
            entry_price=180,
            target_price=120,
            horizon_days=365,
        )
        assert any("bullish" in w for w in sanity_check(v))

    def test_overconfidence_flagged(self):
        v = CompiledView(
            ticker="NVDA",
            entry_price=180,
            target_price=200,
            horizon_days=365,
            confidence_pct=95,
        )
        assert any("confidence" in w for w in sanity_check(v))

    def test_reasonable_view_is_quiet(self):
        v = CompiledView(
            ticker="NVDA",
            entry_price=180,
            target_price=210,
            horizon_days=365,
            confidence_pct=60,
        )
        assert sanity_check(v) == []


class TestCompileEndpoint:
    def test_compiles_and_prices_from_demo_universe(self, client):
        res = client.post(
            "/api/compile-view",
            json={
                "text": "I think TSLA runs to $250 by year end, 65% confident",
                "demo": True,
            },
        )
        assert res.status_code == 200
        body = res.json()
        assert body["engine"] in ("claude", "fallback")
        assert "TSLA" in body["universe"]
        v = body["views"][0]
        assert v["ticker"] == "TSLA"
        assert v["target_price"] == pytest.approx(250.0)
        assert v["confidence_pct"] == pytest.approx(65.0)
        # entry price is filled from the demo market, not invented by a model
        assert v["entry_price"] > 0
        assert v["live_price"] == pytest.approx(v["entry_price"])
        assert v["implied_annual_return"] is not None

    def test_offline_flag_forces_deterministic_engine(self, client):
        res = client.post(
            "/api/compile-view",
            json={"text": "NVDA to 250", "demo": True, "offline": True},
        )
        assert res.json()["engine"] == "fallback"

    def test_no_conviction_returns_notes_not_an_error(self, client):
        res = client.post(
            "/api/compile-view", json={"text": "hello there", "demo": True}
        )
        assert res.status_code == 200
        assert res.json()["views"] == []
        assert res.json()["notes"]

    def test_compiled_view_feeds_optimize_unchanged(self, client):
        """The whole point: what the compiler emits is a valid optimizer view."""
        compiled = client.post(
            "/api/compile-view",
            json={"text": "TSLA to 250 in 6 months, 60% sure", "demo": True},
        ).json()["views"][0]

        res = client.post(
            "/api/optimize",
            json={
                "gamma": 1.2,
                "demo": True,
                "views": [
                    {
                        "ticker": compiled["ticker"],
                        "target_price": compiled["target_price"],
                        "confidence": compiled["confidence_pct"] / 100.0,
                        "horizon_days": compiled["horizon_days"],
                    }
                ],
            },
        )
        assert res.status_code == 200
        assert res.json()["returns"] is not None

    def test_crypto_mode_compiles_crypto_symbols(self, client):
        res = client.post(
            "/api/compile-view?asset_class=crypto",
            json={"text": "bitcoin to 150k by year end, pretty confident",
                  "demo": True},
        )
        assert res.status_code == 200
        v = res.json()["views"][0]
        assert v["ticker"] == "BTC/USD"
        assert v["target_price"] == pytest.approx(150_000.0)


class TestCompilerUI:
    def test_views_page_has_the_compiler(self, client):
        html = client.get("/").text
        assert "Describe your thesis" in html
        assert "/api/compile-view" in html
        assert "Compile my thesis" in html

    def test_every_compiled_field_is_an_input(self, client):
        """The user must be able to edit each field before it's used."""
        html = client.get("/").text
        for cls in ("v-ticker", "v-entry", "v-target", "v-conf", "v-days"):
            assert f'class="{cls}"' in html

    def test_guessed_fields_are_visually_marked(self, client):
        html = client.get("/").text
        assert "needs_review" in html
        assert ".field.guessed" in html

    def test_user_text_is_escaped_before_reaching_innerhtml(self, client):
        html = client.get("/").text
        assert "const esc" in html
        assert "esc(v.thesis)" in html
