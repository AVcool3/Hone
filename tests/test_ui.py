"""Layout and copy invariants for the single-page app.

Every assertion here corresponds to a defect that was shipped and found by
opening the app on a phone-sized viewport rather than by reading the code.
They are cheap to check and expensive to notice.
"""

import re

import pytest
from fastapi.testclient import TestClient

from hone.web.app import create_app


@pytest.fixture(scope="module")
def html():
    return TestClient(create_app()).get("/").text


@pytest.fixture(scope="module")
def css(html):
    m = re.search(r"<style>(.*?)</style>", html, re.S)
    assert m, "the page has no stylesheet"
    return m.group(1)


def rules(css_text):
    """(selector, body) for every rule, media queries flattened out."""
    stripped = re.sub(r"/\*.*?\*/", "", css_text, flags=re.S)
    stripped = re.sub(r"@media[^{]*\{", "", stripped)
    return re.findall(r"([^{}]+)\{([^{}]*)\}", stripped)


class TestNoIosZoomTrap:
    """A focused field under 16px makes mobile Safari zoom the whole page.

    The user then has to pinch back out after every single input. It is not
    a styling preference; it is the difference between a usable form and an
    unusable one, and it is invisible on a desktop browser.
    """

    def test_every_text_control_is_at_least_16px(self, css):
        offenders = []
        for selector, body in rules(css):
            if not re.search(r"\b(input|textarea|select)\b", selector):
                continue
            for size in re.findall(r"font-size:\s*([\d.]+)px", body):
                if float(size) < 16:
                    offenders.append((selector.strip(), size))
        assert offenders == []


class TestNoHorizontalOverflow:
    def test_tables_are_wrapped_in_a_scroll_container(self, html):
        """A table wider than the viewport scrolls the whole document.

        Tables are emitted from a dozen async render paths, so the guard is
        an observer rather than a wrapper remembered at each call site.
        """
        assert "function wrapTables" in html
        assert "new MutationObserver(() => wrapTables())" in html
        assert ".tscroll { overflow-x: auto" in html

    def test_no_bare_inline_overflow_wrappers(self, html):
        """Two ways of doing this means one of them drifts."""
        assert 'style="overflow-x:auto"><table>' not in html


class TestResponsive:
    def test_the_page_has_real_mobile_breakpoints(self, css):
        widths = [int(w) for w in re.findall(r"@media\s*\(max-width:\s*(\d+)px\)", css)]
        assert len(widths) >= 3
        assert any(w >= 600 for w in widths), "no breakpoint for phones in general"

    def test_view_fields_are_not_five_stacked_boxes_on_a_phone(self, css):
        assert ".view-row .row { display: grid; grid-template-columns: 1fr 1fr" in css

    def test_primary_buttons_do_not_wrap_to_two_lines(self, css):
        primary = [b for s, b in rules(css) if s.strip() == "button.primary"]
        assert primary and "white-space: nowrap" in primary[0]


class TestCopyMatchesTheProduct:
    def test_the_landing_page_describes_the_questionnaire_it_actually_ships(self, html):
        """The adaptive route asks eight questions; the page said thirty.

        The full menu is still offered, but it is the alternative, not the
        default, and the first thing a visitor reads must be true.
        """
        body = html.split("<script", 1)[0]
        assert "30 quick either/or choices" not in body
        assert "Eight either/or choices" in body

    def test_no_dead_self_replacements(self, html):
        """`.replace("x", "x")` is a copy edit someone forgot to finish."""
        for a, b in re.findall(r'\.replace\(\s*"([^"]*)"\s*,\s*"([^"]*)"\s*\)', html):
            assert a != b, f"no-op replace of {a!r}"

    def test_greek_stays_out_of_button_labels(self, html):
        """gamma is a fine thing to show; it is not a fine thing to ask
        someone to press before anything has explained it."""
        labels = re.findall(r"<button[^>]*>(.*?)</button>", html, re.S)
        bad = [x.strip() for x in labels if "γ" in x and "(γ" not in x]
        assert bad == []


class TestSignedFiguresKeepTheirSign:
    def test_expected_return_in_dollars_is_not_absolute(self, html):
        """fmtMoney takes an absolute value, so a portfolio expected to lose
        money rendered its loss as a gain."""
        assert "const fmtSMoney" in html
        assert "fmtMoney(r.expected_return" not in html
        assert "fmtSMoney(r.expected_return" in html

    def test_a_return_rounding_to_zero_is_not_shown_as_negative_zero(self, html):
        assert "-0.0004 -> -0, prints" in html  # the fmtSPct guard


class TestTheHedgePageDoesNotContradictItself:
    def test_no_risk_budget_is_shown_when_it_cannot_be_computed(self, html):
        """The degenerate fallback makes the budget equal the exposure it is
        meant to constrain, printed directly under a line saying it cannot
        be computed."""
        assert "const budget = (value && !plan.premium_is_negative)" in html
