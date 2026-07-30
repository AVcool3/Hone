"""Does the 35% per-name cap absorb whatever the confidence number does?

If long-only + a position cap already bounds how far a view can move the
book, Omega has little left to control.  Re-run one slice at the shipped
cap and with the cap effectively removed.
"""
from concurrent.futures import ProcessPoolExecutor
import pandas as pd
from hone.backtest import conviction as cv

ASSET = cv.equities()

def one(job):
    cap, i = job
    p = cv.run_panel(ASSET, [2.5], [0.0, 0.4], [1.0], n_investors=1,
                     base_seed=1_000 + i, max_weight=cap)
    p["investor"] = i
    p["max_weight"] = cap
    return p

if __name__ == "__main__":
    jobs = [(cap, i) for cap in (0.35, 1.0) for i in range(24)]
    with ProcessPoolExecutor(max_workers=4) as pool:
        panel = pd.concat(pool.map(one, jobs), ignore_index=True)
    out = (panel.groupby(["max_weight", "skill", "strategy"])
           .agg(sharpe=("sharpe", "median"), cagr=("cagr", "median"),
                vol=("volatility", "median"), eff_n=("effective_n", "median"),
                turnover=("turnover", "median")).reset_index())
    out["strategy"] = pd.Categorical(out["strategy"], list(cv.STRATEGIES), ordered=True)
    print(out.sort_values(["max_weight", "skill", "strategy"]).to_string(index=False))
