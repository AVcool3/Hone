"""Hone command-line interface.

Subcommands
-----------
questionnaire
    Run the Holt-Laury questionnaire, estimate gamma, show the 50-tier
    placement.
optimize
    Reweight a portfolio with Black-Litterman + MVO given a gamma and
    optional views ("TICKER:TARGET_PRICE:CONFIDENCE[:HORIZON_DAYS]").
    Pulls holdings/prices from Alpaca, or uses synthetic data with
    --demo.
hedge
    Show hedge suggestions (short / puts / collar) for the current
    portfolio at a given gamma.
demo
    Full pipeline end to end on synthetic data: questionnaire choices
    are simulated, then the portfolio is reweighted and hedged.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date, timedelta

import pandas as pd

from .optimization.views import View
from .pipeline import rebalance, synthetic_universe
from .risk_profile.questionnaire import profile_from_choices, run_questionnaire
from .risk_profile.tiers import gamma_to_tier


def _parse_view(spec: str, prices: pd.DataFrame) -> View:
    """Parse TICKER:TARGET[:CONFIDENCE[:HORIZON_DAYS]]."""
    parts = spec.split(":")
    if len(parts) < 2:
        raise argparse.ArgumentTypeError(
            f"bad view {spec!r}; expected TICKER:TARGET_PRICE[:CONFIDENCE[:DAYS]]"
        )
    ticker = parts[0].upper()
    target = float(parts[1])
    confidence = float(parts[2]) if len(parts) > 2 else 0.5
    horizon = float(parts[3]) if len(parts) > 3 else 365.25
    if ticker not in prices.columns:
        raise SystemExit(
            f"error: no price history for view ticker {ticker!r}; include it "
            "in the universe"
        )
    current = float(prices[ticker].dropna().iloc[-1])
    return View(
        ticker=ticker,
        current_price=current,
        target_price=target,
        confidence=confidence,
        horizon_days=horizon,
    )


def _load_market(args) -> tuple[pd.DataFrame, pd.Series]:
    """Prices + current weights, from Alpaca or synthetic demo data."""
    if args.demo:
        return synthetic_universe()
    from .market_data.alpaca_client import AlpacaClient

    client = AlpacaClient()
    weights = client.portfolio_weights()
    if weights.empty:
        raise SystemExit("error: no positions in the Alpaca paper account")
    symbols = sorted(set(weights.index) | {t.split(":")[0].upper() for t in args.view})
    if args.hedge_instrument not in symbols:
        symbols.append(args.hedge_instrument)
    start = date.today() - timedelta(days=int(args.lookback_days * 1.6))
    prices = client.get_bars(symbols, start=start)
    return prices.tail(args.lookback_days), weights


def cmd_questionnaire(args) -> int:
    profile = run_questionnaire(error_spec=args.error_spec)
    if args.json:
        import json

        print(json.dumps(profile.to_dict(), indent=2, default=str))
    return 0


def cmd_optimize(args) -> int:
    prices, weights = _load_market(args)
    views = [_parse_view(v, prices) for v in args.view]
    report = rebalance(
        prices,
        weights,
        gamma=args.gamma,
        views=views,
        covariance_method=args.cov_method,
        long_only=not args.allow_short,
        max_weight=args.max_weight,
        hedge_instrument=args.hedge_instrument,
    )
    tier = gamma_to_tier(args.gamma)
    print(f"Risk placement: {tier.describe()}\n")
    print(report.summary())
    return 0


def cmd_hedge(args) -> int:
    prices, weights = _load_market(args)
    report = rebalance(
        prices,
        weights,
        gamma=args.gamma,
        views=[],
        covariance_method=args.cov_method,
        hedge_instrument=args.hedge_instrument,
    )
    print(report.hedge_plan.summary())
    return 0


def cmd_demo(args) -> int:
    print("=== Step 1: risk questionnaire (simulated consistent subject) ===")
    vec = ["A"] * 7 + ["B"] * 3  # switches after row 7 at every scale
    profile = profile_from_choices([vec, vec, vec])
    print(profile.summary())

    print("\n=== Step 2-4: covariance, view, Black-Litterman + MVO, hedges ===")
    prices, weights = synthetic_universe()
    tsla = float(prices["TSLA"].iloc[-1])
    view = View(
        ticker="TSLA",
        current_price=tsla,
        target_price=tsla * 1.3,
        confidence=0.6,
        horizon_days=365,
    )
    print(f"\nUser view: {view.describe()}\n")
    report = rebalance(
        prices, weights, gamma=profile.gamma, views=[view], max_weight=0.35
    )
    print(report.summary())

    print("\n=== For comparison: hedge plan at a highly risk-averse tier ===")
    from .hedging.hedge import suggest_hedges
    from .risk_profile.tiers import tier_gamma

    averse_gamma = tier_gamma(40)
    plan = suggest_hedges(
        report.optimized.weights,
        report.covariance.covariance,
        report.covariance.mean_returns,
        averse_gamma,
        hedge_instrument="SPY",
        hedge_spot=float(prices["SPY"].iloc[-1]),
    )
    print(plan.summary())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hone",
        description="Hedge-fund-grade risk tools for retail investors.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    q = sub.add_parser("questionnaire", help="elicit your risk-aversion gamma")
    q.add_argument(
        "--error-spec",
        choices=["fechner", "luce"],
        default="fechner",
        help="MLE noise specification (default: fechner)",
    )
    q.add_argument("--json", action="store_true", help="print the profile as JSON")
    q.set_defaults(func=cmd_questionnaire)

    def add_market_args(p):
        p.add_argument("--demo", action="store_true", help="use synthetic data")
        p.add_argument("--gamma", type=float, required=True, help="risk-aversion gamma")
        p.add_argument(
            "--cov-method",
            choices=["sample", "ewma", "shrinkage"],
            default="shrinkage",
        )
        p.add_argument("--lookback-days", type=int, default=504)
        p.add_argument("--hedge-instrument", default="SPY")
        p.add_argument(
            "--view",
            action="append",
            default=[],
            metavar="TICKER:TARGET[:CONF[:DAYS]]",
            help="view spec, repeatable (e.g. TSLA:400:0.6:180)",
        )

    o = sub.add_parser("optimize", help="reweight with Black-Litterman + MVO")
    add_market_args(o)
    o.add_argument("--allow-short", action="store_true")
    o.add_argument(
        "--max-weight",
        type=float,
        default=0.35,
        help="per-name position cap (default 0.35; use 1.0 to disable)",
    )
    o.set_defaults(func=cmd_optimize)

    h = sub.add_parser("hedge", help="hedge suggestions for your gamma")
    add_market_args(h)
    h.set_defaults(func=cmd_hedge)

    d = sub.add_parser("demo", help="full pipeline on synthetic data")
    d.set_defaults(func=cmd_demo)

    w = sub.add_parser("serve", help="run the web app (UI + JSON API)")
    w.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    w.add_argument(
        "--port", type=int, default=int(os.environ.get("PORT", "8000"))
    )
    w.set_defaults(func=cmd_serve)

    return parser


def cmd_serve(args) -> int:
    try:
        import uvicorn
    except ImportError:
        raise SystemExit(
            "error: web dependencies missing — install with pip install 'hone[web]' "
            "or pip install fastapi 'uvicorn[standard]'"
        )
    print(f"Hone web app on http://{args.host}:{args.port}")
    uvicorn.run("hone.web.app:app", host=args.host, port=args.port)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
