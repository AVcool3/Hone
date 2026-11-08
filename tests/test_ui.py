"""Layout and copy invariants for the React frontend.

Every assertion here corresponds to a defect that was shipped once and found
by opening the app on a phone-sized viewport rather than by reading the code.
They are cheap to check and expensive to notice. (Ported from the single-file
UI to the React source in frontend/src — see tests/frontend_source.py.)
"""

import re

from fastapi.testclient import TestClient

from hone.web.app import create_app

from frontend_source import SRC, built_index, css, source


def rules(css_text):
    """(selector, body) for every rule, media queries flattened out."""
    stripped = re.sub(r"/\*.*?\*/", "", css_text, flags=re.S)
    stripped = re.sub(r"@media[^{]*\{", "", stripped)
    return re.findall(r"([^{}]+)\{([^{}]*)\}", stripped)


class TestNoIosZoomTrap:
    """A focused field under 16px makes mobile Safari zoom the whole page.

    The user then has to pinch back out after every single input.
    """

    def test_every_text_control_is_at_least_16px(self):
        offenders = []
        for selector, body in rules(css()):
            if not re.search(r"\b(input|textarea|select)\b", selector):
                continue
            for size in re.findall(r"font(?:-size)?:[^;]*?([\d.]+)px", body):
                if float(size) < 16:
                    offenders.append((selector.strip(), size))
        assert offenders == []

    def test_the_base_control_rule_sets_16px(self):
        assert "font: 400 16px/1.4 var(--font-ui);" in css()


class TestNoHorizontalOverflow:
    def test_tables_are_wrapped_in_a_scroll_container(self):
        """A table wider than the viewport scrolls the whole document."""
        assert ".tscroll { overflow-x: auto" in css()
        # Every JSX file that renders a <table> also renders the wrapper.
        for p in SRC.rglob("*.jsx"):
            text = p.read_text(encoding="utf-8")
            if "<table" in text:
                assert "tscroll" in text, f"{p.name} renders a bare <table>"

    def test_markdown_tables_are_wrapped_too(self):
        assert '<div className="tscroll"><table>' in source("Markdown.jsx")

    def test_grids_can_shrink(self):
        """`1fr` alone refuses to shrink below its content on a phone."""
        assert "grid-template-columns: minmax(0, 1fr); padding-top" in css()


class TestResponsive:
    def test_the_page_has_real_mobile_breakpoints(self):
        widths = {int(w) for w in re.findall(r"@media\s*\(max-width:\s*(\d+)px\)", css())}
        assert len(widths) >= 3
        assert any(w >= 600 for w in widths), "no breakpoint for phones in general"
        assert any(w <= 420 for w in widths), "no breakpoint for small phones"

    def test_primary_buttons_do_not_wrap_to_two_lines(self):
        btn = [b for s, b in rules(css()) if s.strip() == ".btn"]
        assert btn and "white-space: nowrap" in btn[0]

    def test_sliders_are_never_the_only_way_in(self):
        """Every slider is paired with a number box (components/ui.jsx)."""
        ns = source("components/ui.jsx")
        assert 'type="range"' in ns and 'type="number"' in ns
        assert "<NumberSlider" in source("ThesisEditor.jsx")


class TestCopyMatchesTheProduct:
    def test_the_landing_page_describes_the_questionnaire_it_actually_ships(self):
        """The adaptive route asks eight questions; the page once said thirty."""
        # The front page is now the waitlist page; the questionnaire is
        # described on the product overview (Home.jsx).
        html = built_index()
        assert "30 quick either/or choices" not in html
        assert "Eight choices, one honest estimate." in source("marketing/Home.jsx")

    def test_no_dead_self_replacements(self):
        """`.replace("x", "x")` is a copy edit someone forgot to finish."""
        for a, b in re.findall(r"\.replace\(\s*['\"]([^'\"]*)['\"]\s*,\s*['\"]([^'\"]*)['\"]\s*\)", source()):
            assert a != b, f"no-op replace of {a!r}"

    def test_greek_stays_out_of_button_labels(self):
        """γ is fine to show; it is not fine to ask someone to press it
        before anything has explained it."""
        labels = re.findall(r"<(?:button|Button)\b[^>]*>(.*?)</(?:button|Button)>", source(), re.S)
        bad = [x.strip() for x in labels if "γ" in x]
        assert bad == []

    def test_crypto_never_borrows_stock_examples(self):
        """The crypto page once showed TSLA/AAPL/MSFT copy."""
        products = source("lib/products.js")
        crypto = products.split("crypto: {", 1)[1].split("'prediction-markets'", 1)[0]
        for ticker in ("TSLA", "AAPL", "MSFT"):
            assert ticker not in crypto

    def test_outputs_are_labelled_model_proposed(self):
        assert "Model-proposed" in source("AllocationBars.jsx")


class TestSignedFiguresKeepTheirSign:
    def test_expected_return_in_dollars_is_not_absolute(self):
        """fmtMoney takes an absolute value, so a portfolio expected to lose
        money rendered its loss as a gain."""
        assert "export const fmtSMoney" in source("format.js")
        app = source()
        assert "fmtMoney(r.expected_return" not in app
        assert "fmtSMoney(r.expected_return" in app

    def test_a_return_rounding_to_zero_is_not_shown_as_negative_zero(self):
        assert "-0.0004 -> -0, prints" in source("format.js")


class TestTheHedgePageDoesNotContradictItself:
    def test_no_risk_budget_is_shown_when_it_cannot_be_computed(self):
        """The degenerate fallback made the budget equal the exposure it is
        meant to constrain, printed under a line saying it can't be computed."""
        assert "const budget = (value && !plan?.premium_is_negative)" in source("HedgingPage.jsx")


class TestSpaServing:
    """Every page URL loads the app; assets are served and cached forever."""

    def test_deep_links_load_the_app(self):
        c = TestClient(create_app())
        for path in (
            "/", "/stocks", "/crypto", "/prediction-markets",
            "/stocks/app/theses", "/crypto/methodology/calibration",
            "/prediction-markets/app/hedge",
        ):
            r = c.get(path)
            assert r.status_code == 200, path
            assert '<div id="root">' in r.text

    def test_unknown_prefix_is_a_404_not_the_app(self):
        assert TestClient(create_app()).get("/nonsense/page").status_code == 404

    def test_api_routes_are_not_shadowed_by_the_catch_all(self):
        assert TestClient(create_app()).get("/api/menu").headers["content-type"].startswith("application/json")

    def test_built_assets_are_served_and_immutable(self):
        html = built_index()
        js = re.search(r'src="/assets/([^"]+\.js)"', html)
        assert js, "index.html does not reference a built bundle — run `npm run build` in frontend/"
        r = TestClient(create_app()).get(f"/assets/{js.group(1)}")
        assert r.status_code == 200
        assert "javascript" in r.headers["content-type"]
        assert "immutable" in r.headers["cache-control"]

    def test_index_is_not_cached(self):
        r = TestClient(create_app()).get("/")
        assert r.headers["cache-control"] == "no-cache"
