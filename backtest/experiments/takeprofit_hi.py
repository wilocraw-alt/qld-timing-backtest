import os, yaml, pandas as pd
from backtest.data.loader import load_prices
from backtest.engine.indicators import annotate_signals
from backtest.engine.strategy import run_strategy
from backtest.analyze.metrics import compute_metrics

cfg = yaml.safe_load(open("backtest/config.yaml"))
df = annotate_signals(load_prices(cfg.get("ticker", "QLD")), cfg)

rows = []
for label, c, d in [("full_c20_d40", 20, 40), ("full_c100_d200", 100, 200)]:
    p = yaml.safe_load(open("backtest/config.yaml"))
    p["strategy"]["c"] = c
    p["strategy"]["d"] = d
    dfa = annotate_signals(load_prices(p.get("ticker", "QLD")), p)
    r = run_strategy(dfa, p, {"_name": label})
    m = compute_metrics(r)
    m["variant"] = label
    rows.append(m)

out = pd.DataFrame(rows).set_index("variant")
os.makedirs("backtest/output", exist_ok=True)
out.to_csv("backtest/output/exp_takeprofit.csv")
print(out[["total_return", "cagr", "mdd", "sharpe", "avg_cash", "trades", "final_value"]].to_string())
