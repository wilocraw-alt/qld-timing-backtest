#!/usr/bin/env python3
"""
Run all 5 contribution strategies × 2 cost levels on real QLD/QQQ/TQQQ data.
Outputs: results_contrib.csv, equity_contrib.png, report_contrib_ko.txt
"""
import os, sys, logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("contrib_run")

import numpy as np
import pandas as pd

from backtest.data.loader import load_prices
from backtest.contrib import run_contrib, decide_immediate, decide_daily, make_decide_rule_v1
from backtest.contrib_v3_alloc import decide_v3_regime, decide_dual_momentum, reset_dual_momentum_state

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ── Data ──────────────────────────────────────────────────────────────
logger.info("Loading QLD, QQQ, TQQQ ...")
qld  = load_prices("QLD",  start="2000-01-01", end="2026-06-19")
qqq  = load_prices("QQQ",  start="2000-01-01", end="2026-06-19")
tqqq = load_prices("TQQQ", start="2000-01-01", end="2026-06-19")

mdf = pd.DataFrame({
    "QLD":  qld["close"],
    "QQQ":  qqq["close"],
    "TQQQ": tqqq["close"],
}).dropna()
mdf = mdf.loc["2011-01-01":"2026-06-19"]
logger.info("mdf: %d rows, %s .. %s", len(mdf), mdf.index[0].date(), mdf.index[-1].date())

qdf = mdf[["QLD"]]


# ── Metrics helpers ────────────────────────────────────────────────────

def compute_mwrr(contrib_dates, final_value, monthly=300.0):
    """Money-weighted (dollar-weighted) IRR via bisection. Returns annualized."""
    if final_value <= 0:
        return 0.0
    cf = np.array([-monthly] * len(contrib_dates), dtype=float)
    cf = np.append(cf, final_value)
    w = np.arange(len(contrib_dates) + 1, dtype=float)
    lo, hi = -0.999, 5.0
    for _ in range(100):
        mid = (lo + hi) / 2
        npv = np.sum(cf / (1 + mid) ** w)
        if npv > 0:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-10:
            break
    r_monthly = (lo + hi) / 2
    return (1 + r_monthly) ** 12 - 1


def compute_mdd(equity):
    if len(equity) < 2:
        return 0.0
    peak = equity.cummax()
    dd = (equity - peak) / peak
    return float(-dd.min())


def compute_ann_vol(equity):
    if len(equity) < 10:
        return 0.0
    daily_ret = equity.pct_change().dropna()
    return float(daily_ret.std() * np.sqrt(252))


def get_contrib_dates(prices_df, monthly=300.0):
    """Return list of dates where contribution is made (first trading day of each month)."""
    from backtest.contrib import make_contributions
    contrib = make_contributions(prices_df.index, monthly)
    return list(contrib[contrib > 0].index)


def run_one(prices_df, decide_fn, name, monthly=300.0, cost=0.0):
    """Run one strategy variant and return (BacktestResult, contrib_dates)."""
    contrib_dates = get_contrib_dates(prices_df, monthly)
    r = run_contrib(prices_df, decide_fn, monthly=monthly, name=name, cost=cost)
    return r, contrib_dates


# ── Run all ────────────────────────────────────────────────────────────
COSTS = [0.0, 0.0005]

strategy_configs = [
    ("immediate",   qdf, lambda: decide_immediate),
    ("daily",       qdf, lambda: decide_daily),
    ("rule_v1",     qdf, lambda: make_decide_rule_v1()),
    ("v3_regime",   mdf, lambda: decide_v3_regime),
    ("v3_dualmom",  mdf, lambda: (reset_dual_momentum_state(), decide_dual_momentum)[1]),
]

all_rows = []
all_equities = {}

for cost in COSTS:
    for slug, pdf, fn_factory in strategy_configs:
        label = f"{slug}_cost{cost}" if cost > 0 else slug
        logger.info("Running %s ...", label)
        decide_fn = fn_factory()
        r, cdates = run_one(pdf, decide_fn, label, cost=cost)
        all_equities[label] = r.equity

        total_in = len(cdates) * 300.0
        final_val = r.equity.iloc[-1]
        row = {
            "variant": slug,
            "cost": cost,
            "total_contributed": total_in,
            "final_value": round(final_val, 2),
            "profit": round(final_val - total_in, 2),
            "MWRR_annual": round(compute_mwrr(cdates, final_val), 6),
            "MDD": round(compute_mdd(r.equity), 6),
            "ann_vol": round(compute_ann_vol(r.equity), 6),
            "end_cash": round(r.cash.iloc[-1], 2),
            "n_trades": len(r.trades),
        }
        all_rows.append(row)
        logger.info("  final=%.2f  MWRR=%.4f  MDD=%.4f  vol=%.4f  trades=%d",
                     final_val, row["MWRR_annual"], row["MDD"], row["ann_vol"], row["n_trades"])

# Add immediate_without_cost as benchmark column
base_val = next(r["final_value"] for r in all_rows if r["variant"] == "immediate" and r["cost"] == 0.0)
for row in all_rows:
    row["vs_immediate_pct"] = round((row["final_value"] / base_val - 1.0) * 100, 2)

df_out = pd.DataFrame(all_rows)
out_dir = "backtest/output"
os.makedirs(out_dir, exist_ok=True)
csv_path = os.path.join(out_dir, "results_contrib.csv")
df_out.to_csv(csv_path, index=False)
logger.info("Saved %s", csv_path)
print(df_out.to_string(index=False))


# ── Equity plot ────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 7))
cmap = plt.cm.tab10
for i, (label, eq) in enumerate(sorted(all_equities.items())):
    ax.plot(eq.index, eq.values, label=label, linewidth=0.8, color=cmap(i % 10))
# Cumulative contribution line
cdates = get_contrib_dates(pdf, 300.0)
cumul = np.arange(1, len(cdates) + 1) * 300.0
ax.plot(cdates, cumul, label="total_contrib", linewidth=2, color="gray", linestyle="--")
ax.set_title("Contribution Strategy Equity Curves ($300/month)")
ax.set_xlabel("Date")
ax.set_ylabel("Portfolio Value ($)")
ax.legend(loc="best", fontsize=7)
ax.grid(True, alpha=0.3)
fig.savefig(os.path.join(out_dir, "equity_contrib.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
logger.info("Saved equity_contrib.png")


# ── Korean report ──────────────────────────────────────────────────────
cost0 = [r for r in all_rows if r["cost"] == 0.0]
best_cost0 = max(cost0, key=lambda x: x["final_value"])

immediate_row = next(r for r in cost0 if r["variant"] == "immediate")
daily_row     = next(r for r in cost0 if r["variant"] == "daily")
rule_v1_row   = next(r for r in cost0 if r["variant"] == "rule_v1")
regime_row    = next(r for r in cost0 if r["variant"] == "v3_regime")
dualmom_row   = next(r for r in cost0 if r["variant"] == "v3_dualmom")

total_contrib = int(immediate_row["total_contributed"])

lines = []
def w(s):
    lines.append(s)

w("정기납입(월 $300) 전략 비교 — 2011~2026 백테스트 리포트")
w("=" * 55)
w("")
w("■ 가정")
w(f"  납입액   : 매월 첫 거래일에 $300 (총납입 ${total_contrib:,})")
w(f"  기간     : 2011-01-01 ~ 2026-06-19 (약 15.5년)")
w(f"  초기자본 : $0 (적립식)")
w(f"  거래비용 : 0% 및 0.05% 각 1세트")
w("")
w("■ 5개 전략")
w("  1. 즉시(immediate) : 납입일에 전액 QLD 매수")
w("  2. 일분할(daily)    : 월 $300을 잔여 거래일에 균등분할 매수")
w("  3. v1타이밍(rule_v1) : v1 타이밍 규칙(ATH하락·저점반등 매수, 200MA·익절 매도)")
w("  4. v3레짐(v3_regime) : QQQ 200MA 대비 비율로 QLD/TQQQ/현금 레짐 전환")
w("  5. v3듀얼모멘텀(v3_dualmom) : 매월 12개월 수익률 1위 자산(QQQ/QLD/TQQQ)으로 전환")
w("")
w("■ 결과 (cost=0 기준)")
w("")

def block(name, d):
    w(f"  ◆ {name}")
    w(f"    최종자산      : ${d['final_value']:,.2f}")
    w(f"    수익          : ${d['profit']:,.2f} (+{d['vs_immediate_pct']:.1f}% vs 즉시)")
    w(f"    MWRR(연)      : {d['MWRR_annual']*100:.2f}%")
    w(f"    MDD           : {d['MDD']*100:.2f}%")
    w(f"    연변동성      : {d['ann_vol']*100:.2f}%")
    w(f"    거래수        : {d['n_trades']}회")
    w(f"    최종현금      : ${d['end_cash']:.2f}")
    w("")

block("immediate (기준)", immediate_row)
block("daily (일분할)", daily_row)
block("rule_v1 (v1 타이밍)", rule_v1_row)
block("v3_regime (QQQ레짐스택)", regime_row)
block("v3_dualmom (듀얼모멘텀)", dualmom_row)

w("■ 순위 (최종자산 기준)")
sorted_strats = sorted(cost0, key=lambda x: -x["final_value"])
for rank, d in enumerate(sorted_strats, 1):
    w(f"  {rank}위: {d['variant']}  ${d['final_value']:,.2f}  "
      f"(MWRR {d['MWRR_annual']*100:.2f}%  MDD {d['MDD']*100:.2f}%)")
w("")

w("■ 거래비용 영향 (0% vs 0.05%)")
for slug in ["immediate", "daily", "rule_v1", "v3_regime", "v3_dualmom"]:
    r0 = next(x for x in all_rows if x["variant"] == slug and x["cost"] == 0.0)
    r1 = next(x for x in all_rows if x["variant"] == slug and x["cost"] == 0.0005)
    diff = r1["final_value"] / r0["final_value"] - 1.0
    w(f"  {slug}: ${r0['final_value']:,.2f} → ${r1['final_value']:,.2f} ({diff*100:+.2f}%)")
w("")

w("■ 해석")
w("")
best_name = best_cost0["variant"]
best_val = best_cost0["final_value"]
w(f"  ● 1위: {best_name} (${best_val:,.2f}).")

# Key interpretations
w("")
if best_name == "v3_dualmom" or best_name == "v3_regime":
    w("  ● v3 전략(v3_regime, v3_dualmom)이 단순 적립(immediate/daily)을 이겼다.")
    w("    레버리지(TQQQ)와 레짐 스위칭으로 >100% 노출이 가능했고, 약세장 회피 효과.")
else:
    w("  ● v3 전략이 단순 적립을 이기지 못했다. 2011~2026 QLD 강세장에서는")
    w("    레짐 스위칭이 오히려 타이밍 리스크로 작용.")

if immediate_row["final_value"] > daily_row["final_value"]:
    w("  ● 즉시 vs 일분할: 즉시가 약간 우위. 월초 전액 매수가 월분할보다 효율적.")
else:
    w("  ● 즉시 vs 일분할: 일분할이 근소 우위. 분할효과가 가격변동성을 줄임.")

w(f"  ● rule_v1(즉시 타이밍)은 {rule_v1_row['final_value']:,.0f}로 즉시의 "
  f"{rule_v1_row['final_value']/immediate_row['final_value']*100:.0f}% 수준.")
w("    v1의 현금보유 편향이 적립식에서는 덜 치명적이지만, 여전히 즉시보다 낮음.")

if regime_row["final_value"] > 0 and dualmom_row["final_value"] > 0:
    w("")
    w("  ● v3_regime은 QQQ 200MA 기반 레짐 전환, v3_dualmom은 12개월 모멘텀 기반.")
    w("    두 전략 모두 TQQQ를 포함해 강세장에서 3배 레버리지를 활용할 수 있어")
    w("    구조적으로 lumpsum(2x)보다 높은 수익이 가능한 환경이 있었다.")

w("")
w("■ 주의사항")
w("  - 2011~2026 QLD/QQQ/TQQQ는 역사적 강세장. 미래 수익률 보장 없음.")
w("  - TQQQ(3x)는 변동성 decay가 심해 장기 약세장·횡보장에 취약.")
w("  - v3 전략의 파라미터(QQQ 200MA, 과열 ratio 1.15)는 해당 기간에 과적합 가능성.")
w("  - 듀얼모멘텀은 월 1회 리밸런싱으로 거래비용 낮으나, 12개월 모멘텀은")
w("    급변 시장(2020 COVID)에서 대응이 느릴 수 있음.")
w("  - 거래비용 0.05%는 저비용 브로커 기준. 현실은 이보다 낮거나 유사.")

report_path = os.path.join(out_dir, "report_contrib_ko.txt")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
logger.info("Saved %s", report_path)

# Print summary
print("\n" + "=" * 55)
for line in lines:
    print(line)
print("=" * 55)
print(f"\n산출물: {csv_path}, equity_contrib.png, {report_path}")
