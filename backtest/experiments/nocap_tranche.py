import os, yaml, pandas as pd
from backtest.data.loader import load_prices
from backtest.engine.indicators import annotate_signals
from backtest.engine.strategy import run_strategy
from backtest.analyze.metrics import compute_metrics

rows = []
for ts in [1000, 2500, 5000]:
    p = yaml.safe_load(open("backtest/config.yaml"))
    p["tranche_size"] = ts
    p["daily_buy_limit"] = 10**12   # 무제한(아주 큰 값)
    dfa = annotate_signals(load_prices(p.get("ticker", "QLD")), p)
    r = run_strategy(dfa, p, {"_name": f"nocap-ts{ts}"})
    m = compute_metrics(r); m["tranche_size"] = ts; m["variant"] = f"nocap-ts{ts}"
    rows.append(m)

out = pd.DataFrame(rows).set_index("variant")
os.makedirs("backtest/output", exist_ok=True)
out.to_csv("backtest/output/exp_nocap_tranche.csv")
print(out[["tranche_size","total_return","cagr","mdd","sharpe","avg_cash","trades","final_value"]].to_string())
