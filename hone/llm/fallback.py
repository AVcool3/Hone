"""Deterministic conviction parser — no network, no API key, no dependencies.

This is not a stub.  It is the backend Hone uses whenever ``ANTHROPIC_API_KEY``
is absent, which includes the whole test suite and any self-hosted deployment
that does not want to pay per compile.  It handles the sentence shapes people
actually type:

    "NVDA to $250 by year end, pretty confident"
    "I think Apple hits 300 in 6 months — 70% sure"
    "short TSLA down to 150 over the next quarter"
    "bitcoin 150k by Q4"

It is a parser, not a language model: it will miss phrasings the LLM catches.
Everything it produces lands in an editable form, and anything it guessed is
flagged in ``needs_review`` so the user knows which numbers to check.
"""

from __future__ import annotations

import re

from .schemas import CompiledView, CompileResult

#: Words that mean "I expect this to fall".
_BEARISH = (
    "short",
    "bearish",
    "puts",
    "put on",
    "drop",
    "fall",
    "crash",
    "decline",
    "sell off",
    "selloff",
    "downside",
    "tank",
    "dump",
    "overvalued",
    "collapse",
)

#: Confidence language, strongest phrasings first so "not very confident"
#: cannot match the "very confident" rule.
_CONFIDENCE_WORDS: tuple[tuple[str, float], ...] = (
    ("not confident", 30.0),
    ("not very confident", 30.0),
    ("not sure", 30.0),
    ("no idea", 25.0),
    ("long shot", 25.0),
    ("speculative", 30.0),
    ("lottery ticket", 20.0),
    ("might", 35.0),
    ("maybe", 35.0),
    ("could", 40.0),
    ("small chance", 30.0),
    ("worth a look", 40.0),
    ("leaning", 45.0),
    ("somewhat confident", 50.0),
    ("fairly confident", 60.0),
    ("pretty confident", 62.0),
    ("reasonably confident", 60.0),
    ("quite confident", 68.0),
    ("high conviction", 78.0),
    ("strong conviction", 78.0),
    ("very confident", 78.0),
    ("extremely confident", 82.0),
    ("certain", 85.0),
    ("no doubt", 85.0),
    ("guaranteed", 85.0),
    ("slam dunk", 82.0),
    ("confident", 65.0),
    ("convinced", 72.0),
    ("bullish", 60.0),
    ("bearish", 60.0),
)

#: Company names worth resolving without a network call.  Only the megacaps
#: retail investors actually type by name; anything else must be a ticker.
_NAME_TO_TICKER = {
    "apple": "AAPL",
    "microsoft": "MSFT",
    "nvidia": "NVDA",
    "amazon": "AMZN",
    "alphabet": "GOOGL",
    "google": "GOOGL",
    "meta": "META",
    "facebook": "META",
    "tesla": "TSLA",
    "netflix": "NFLX",
    "berkshire": "BRK.B",
    "broadcom": "AVGO",
    "amd": "AMD",
    "intel": "INTC",
    "palantir": "PLTR",
    "coinbase": "COIN",
    "walmart": "WMT",
    "costco": "COST",
    "disney": "DIS",
    "boeing": "BA",
    "jpmorgan": "JPM",
    "exxon": "XOM",
    "eli lilly": "LLY",
    "lilly": "LLY",
    "spy": "SPY",
    "s&p": "SPY",
    "sp500": "SPY",
    "nasdaq": "QQQ",
    "bitcoin": "BTC/USD",
    "btc": "BTC/USD",
    "ethereum": "ETH/USD",
    "ether": "ETH/USD",
    "eth": "ETH/USD",
    "solana": "SOL/USD",
    "sol": "SOL/USD",
    "dogecoin": "DOGE/USD",
    "doge": "DOGE/USD",
    "cardano": "ADA/USD",
    "litecoin": "LTC/USD",
    "avalanche": "AVAX/USD",
    "chainlink": "LINK/USD",
    "polkadot": "DOT/USD",
    "uniswap": "UNI/USD",
    "aave": "AAVE/USD",
}

#: Words that look like tickers (all caps, 1-5 letters) but never are.
_TICKER_STOPWORDS = {
    "A", "I", "AI", "AND", "THE", "TO", "BY", "IN", "IT", "IS", "AT", "ON",
    "OR", "IF", "SO", "BE", "DO", "GO", "UP", "MY", "WE", "US", "USD", "EPS",
    "CEO", "CFO", "IPO", "ETF", "PE", "YOY", "QOQ", "Q1", "Q2", "Q3", "Q4",
    "FY", "EOY", "ATH", "DD", "YOLO", "FOMO", "IMO", "IMHO", "TBH", "BUY",
    "SELL", "HOLD", "LONG", "SHORT", "CALL", "PUT", "OK", "NO", "YES", "NOT",
    "NEW", "OLD", "BIG", "ALL", "GDP", "CPI", "FED", "SEC", "NYSE", "USA",
}

_MONTHS = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
    "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
    "august": 8, "aug": 8, "september": 9, "sep": 9, "sept": 9, "october": 10,
    "oct": 10, "november": 11, "nov": 11, "december": 12, "dec": 12,
}

_DEFAULT_HORIZON_DAYS = 365.0
_DEFAULT_CONFIDENCE_PCT = 50.0


# --------------------------------------------------------------------- prices
def _parse_money(raw: str) -> float:
    """'$1,250.50' -> 1250.5, '150k' -> 150000, '1.2m' -> 1200000."""
    text = raw.strip().lower().replace("$", "").replace(",", "")
    mult = 1.0
    if text.endswith("k"):
        mult, text = 1_000.0, text[:-1]
    elif text.endswith("m"):
        mult, text = 1_000_000.0, text[:-1]
    elif text.endswith("b"):
        mult, text = 1_000_000_000.0, text[:-1]
    return float(text) * mult


#: A number that could be a price: optional $, digits, optional k/m/b suffix.
_MONEY = r"\$?\d[\d,]*(?:\.\d+)?\s*[kmb]?\b"


def _extract_prices(text: str) -> tuple[float | None, float | None]:
    """Return ``(entry, target)`` from one conviction's text.

    Distinguishes the two by the preposition: "from 100 to 150" gives both;
    "to $150" or "hits 150" gives only a target.
    """
    low = text.lower()

    both = re.search(rf"from\s+({_MONEY})\s+(?:to|up to|down to)\s+({_MONEY})", low)
    if both:
        return _parse_money(both.group(1)), _parse_money(both.group(2))

    target_cues = (
        rf"(?:price\s+)?target(?:\s+of|\s+is|:)?\s+({_MONEY})",
        rf"(?:to|hits?|hit|reach(?:es|ing)?|reaching|towards?|至)\s+({_MONEY})",
        rf"(?:goes?|going|run(?:s|ning)?|rally(?:ing)?|climb(?:s|ing)?)\s+"
        rf"(?:up\s+)?to\s+({_MONEY})",
        rf"({_MONEY})\s+(?:price\s+)?target",
        rf"(?:worth|valued at)\s+({_MONEY})",
    )
    target = None
    for pattern in target_cues:
        m = re.search(pattern, low)
        if m:
            target = _parse_money(m.group(1))
            break

    entry = None
    entry_cues = (
        rf"(?:currently|now|trading|trades|it'?s|its|at)\s+(?:at\s+)?({_MONEY})",
        rf"(?:bought|buying|entry|cost basis|paid)\s+(?:at\s+|of\s+)?({_MONEY})",
        rf"from\s+({_MONEY})",
    )
    for pattern in entry_cues:
        m = re.search(pattern, low)
        if m:
            candidate = _parse_money(m.group(1))
            if candidate != target:
                entry = candidate
                break

    # A bare number with no cue at all is still probably the target.
    if target is None and entry is None:
        bare = re.search(rf"({_MONEY})", low)
        if bare and not re.match(r"^\d{1,2}$", bare.group(1).strip()):
            target = _parse_money(bare.group(1))

    return entry, target


# -------------------------------------------------------------------- horizon
_UNIT_DAYS = {
    "day": 1.0, "days": 1.0, "week": 7.0, "weeks": 7.0,
    "month": 30.44, "months": 30.44, "quarter": 91.31, "quarters": 91.31,
    "year": 365.0, "years": 365.0,
}

_WORD_NUMBERS = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "twelve": 12,
    "eighteen": 18, "couple": 2, "couple of": 2, "few": 3, "several": 4,
}


def _extract_horizon(text: str, today_month: int = 1) -> float | None:
    """Days until the target, or None when the text says nothing about time."""
    low = text.lower()

    m = re.search(
        r"\b(\d+(?:\.\d+)?)\s*[-\s]?\s*"
        r"(days?|weeks?|months?|quarters?|years?)\b",
        low,
    )
    if m:
        return float(m.group(1)) * _UNIT_DAYS[m.group(2)]

    words = "|".join(sorted(_WORD_NUMBERS, key=len, reverse=True))
    m = re.search(
        rf"\b({words})\s+(days?|weeks?|months?|quarters?|years?)\b", low
    )
    if m:
        return float(_WORD_NUMBERS[m.group(1)]) * _UNIT_DAYS[m.group(2)]

    if re.search(r"\b(year[\s-]?end|eoy|end of (?:the )?year|by december)\b", low):
        # Months left in the calendar year, floored at a month so a
        # December thesis does not compile to a zero-day horizon.
        return max(30.44, (12 - today_month) * 30.44)

    m = re.search(r"\bq([1-4])\b", low)
    if m:
        quarter_end_month = int(m.group(1)) * 3
        months = quarter_end_month - today_month
        if months <= 0:
            months += 12
        return max(30.44, months * 30.44)

    m = re.search(rf"\b(?:by|in|before|until)\s+({'|'.join(_MONTHS)})\b", low)
    if m:
        months = _MONTHS[m.group(1)] - today_month
        if months <= 0:
            months += 12
        return max(15.0, months * 30.44)

    if re.search(r"\b(next year|12 ?months?|a year)\b", low):
        return 365.0
    if re.search(r"\b(long[\s-]?term|multi[\s-]?year)\b", low):
        return 730.0
    if re.search(r"\b(short[\s-]?term|near[\s-]?term|soon|this month)\b", low):
        return 30.44

    return None


# ----------------------------------------------------------------- confidence
def _extract_confidence(text: str) -> float | None:
    low = text.lower()

    m = re.search(
        r"(\d{1,3})\s*%\s*(?:confiden\w*|sure|certain|conviction|probability|odds|chance)",
        low,
    )
    if not m:
        m = re.search(
            r"(?:confiden\w*|sure|certain|conviction|probability|odds|chance)"
            r"[^.\d]{0,20}?(\d{1,3})\s*%",
            low,
        )
    if m:
        return max(1.0, min(99.0, float(m.group(1))))

    # "8 out of 10", "7/10 conviction"
    m = re.search(r"\b(\d{1,2})\s*(?:/|out of)\s*10\b", low)
    if m:
        return max(1.0, min(99.0, float(m.group(1)) * 10.0))

    best: float | None = None
    best_len = -1
    for phrase, value in _CONFIDENCE_WORDS:
        if phrase in low and len(phrase) > best_len:
            best, best_len = value, len(phrase)
    return best


# --------------------------------------------------------------------- ticker
def _resolve_ticker(text: str, universe: list[str] | None) -> str | None:
    """Best ticker in ``text``.  Symbols in ``universe`` win over guesses."""
    upper_universe = {u.upper() for u in (universe or [])}

    # $-prefixed is unambiguous and always wins.
    m = re.search(r"\$([A-Za-z][A-Za-z.\-]{0,5})(?![\d.])", text)
    if m:
        return m.group(1).upper()

    # Crypto pairs written out: BTC/USD, ETH-USD.
    m = re.search(r"\b([A-Z]{2,5})[/-](USD|USDT|USDC)\b", text.upper())
    if m:
        return f"{m.group(1)}/USD"

    words = re.findall(r"\b[A-Za-z][A-Za-z.\-]{0,5}\b", text)
    caps = [w for w in words if w.isupper() and w not in _TICKER_STOPWORDS]

    for w in caps:  # a capitalized word that is in the universe is certain
        if w in upper_universe:
            return w

    low = text.lower()
    for name, ticker in _NAME_TO_TICKER.items():
        if re.search(rf"\b{re.escape(name)}\b", low):
            return ticker

    return caps[0].upper() if caps else None


# ---------------------------------------------------------------------- split
_SPLIT = re.compile(r"(?:\n+|(?<=[.!?;])\s+|\s+(?:and )?also\b|\s*\|\s*)")


def _segments(text: str) -> list[str]:
    """Split a block of text into candidate one-conviction chunks."""
    parts = [p.strip() for p in _SPLIT.split(text) if p and p.strip()]
    return parts or [text.strip()]


# --------------------------------------------------------------------- public
def compile_offline(
    text: str,
    universe: list[str] | None = None,
    *,
    today_month: int = 1,
) -> CompileResult:
    """Compile ``text`` into structured views without calling any model."""
    notes: list[str] = []
    by_ticker: dict[str, CompiledView] = {}

    for segment in _segments(text):
        ticker = _resolve_ticker(segment, universe)
        if not ticker:
            continue

        entry, target = _extract_prices(segment)
        horizon = _extract_horizon(segment, today_month=today_month)
        confidence = _extract_confidence(segment)
        low = segment.lower()
        bearish = any(w in low for w in _BEARISH)

        guessed: list[str] = []
        if horizon is None:
            horizon = _DEFAULT_HORIZON_DAYS
            guessed.append("horizon_days")
        if confidence is None:
            confidence = _DEFAULT_CONFIDENCE_PCT
            guessed.append("confidence_pct")
        if target is None:
            guessed.append("target_price")

        view = CompiledView(
            ticker=ticker,
            direction="bearish" if bearish else "bullish",
            entry_price=entry,
            target_price=target,
            horizon_days=horizon,
            confidence_pct=confidence,
            thesis=segment.strip()[:280],
            catalysts=[],
            risks=[],
            needs_review=guessed,
        )

        if ticker in by_ticker:  # keep the richer of two mentions
            existing = by_ticker[ticker]
            if len(existing.needs_review) <= len(view.needs_review):
                continue
        by_ticker[ticker] = view

    views = list(by_ticker.values())
    if not views:
        notes.append(
            "No ticker found. Name the symbol directly — $NVDA, NVDA, or "
            "a company name like Nvidia."
        )
    if universe:
        known = {u.upper() for u in universe}
        unknown = [v.ticker for v in views if v.ticker not in known]
        if unknown:
            notes.append(
                "Not in the current universe: "
                + ", ".join(unknown)
                + ". They will be added if price history exists."
            )
    for v in views:
        if v.target_price is None:
            notes.append(f"{v.ticker}: no price target found — enter one below.")

    return CompileResult(views=views, engine="fallback", notes=notes)
