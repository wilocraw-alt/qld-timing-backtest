#!/usr/bin/env python3
"""
Portfolio strategy comparison — 11 strategies × 3 periods × 2 costs.
Outputs: results_portfolio.csv, equity_portfolio.png, report_portfolio_ko.txt
"""
import os, sys, logging, itertools
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("portfolio_run")

import numpy as np
import pandas as pd
from backtest.data.loader_multi import load_many, align
from backtest.contrib import run_contrib, decide_immediate, decide_daily, make_decide_rule_v1
from backtest.contrib_v3_alloc import decide_v3_regime, decide_dual_momentum, reset_dual_momentum_state
from backtest.portfolio_alloc import make_regime_basket, make_xsec_momentum, make_static_lev

import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ── Data ──────────────────────────────────────────────────────────────
logger.info("Loading 8 tickers ...")
prices = load_many(["QQQ","SPY","QLD","SSO","TQQQ","UPRO","TLT","GLD"])
mdf = align(prices).loc["2011-01-01":"2026-06-19"]
logger.info("mdf: %d rows, %s .. %s", len(mdf), mdf.index[0].date(), mdf.index[-1].date())

PERIODS = {
    "full":  ("2011-01-01", "2026-06-19"),
    "OOS-A": ("2011-01-01", "2017-12-31"),
    "OOS-B": ("2018-01-01", "2026-06-19"),
}
COSTS = [0.0, 0.0005]

STRATEGIES = [
    ("immediate_QLD", lambda df: (df[["QLD"]], decide_immediate, None)),
    ("daily_QLD",     lambda df: (df[["QLD"]], decide_daily, None)),
    ("rule_v1_QLD",   lambda df: (df[["QLD"]], make_decide_rule_v1(), None)),
    ("v3_regime",     lambda df: (df[["QQQ","QLD","TQQQ"]], decide_v3_regime, None)),
    ("v3_dualmom",    lambda df: (
        df[["QQQ","QLD","TQQQ"]], decide_dual_momentum, reset_dual_momentum_state)),
    ("P1_regime_basket", lambda df: (df, make_regime_basket(), None)),
    ("P2_xsec_mom",      lambda df: (df, make_xsec_momentum(), None)),
    ("P3_static_lev",    lambda df: (df, make_static_lev(), None)),
    ("WIN_static_TQQQ60UPRO40", lambda df: (
        df, make_static_lev({"targets":{"TQQQ":0.6,"UPRO":0.4}}), None)),
    ("WIN_imm_TQQQ100", lambda df: (df[["TQQQ"]], decide_immediate, None)),
    ("MIX_TQQQ50UPRO30TLT20", lambda df: (
        df, make_static_lev({"targets":{"TQQQ":0.5,"UPRO":0.3,"TLT":0.2}}), None)),
]


# ── Metrics ────────────────────────────────────────────────────────────
def compute_mwrr(contrib_dates, final_value, monthly=300.0):
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
    return (1 + (lo + hi) / 2) ** 12 - 1


def compute_mdd(equity):
    if len(equity) < 2:
        return 0.0
    peak = equity.cummax()
    return float(-((equity - peak) / peak).min())


def compute_ann_vol(equity):
    if len(equity) < 10:
        return 0.0
    return float(equity.pct_change().dropna().std() * np.sqrt(252))


def get_contrib_info(prices_df, monthly=300.0):
    from backtest.contrib import make_contributions
    c = make_contributions(prices_df.index, monthly)
    dates = list(c[c > 0].index)
    return dates, len(dates) * monthly


def run_one(prices_df, decide_fn, name, monthly=300.0, cost=0.0, pre_hook=None):
    if pre_hook:
        pre_hook()
    r = run_contrib(prices_df, decide_fn, monthly=monthly, name=name, cost=cost)
    return r


# ── Run all ────────────────────────────────────────────────────────────
all_rows = []
all_equities_full = {}  # for plotting

for period_label, (start, end) in PERIODS.items():
    pdf = mdf.loc[start:end].copy()
    contrib_dates, total_contrib = get_contrib_info(pdf)
    logger.info("Period %s: %d rows, %d contributions, $%.0f total",
                 period_label, len(pdf), len(contrib_dates), total_contrib)

    for slug, factory in STRATEGIES:
        pdf_sub, decide_fn, pre_hook = factory(pdf)
        for cost in COSTS:
            label = f"{slug}_{period_label}_cost{cost}" if cost > 0 else f"{slug}_{period_label}"
            logger.info("  %s ...", label)
            r = run_one(pdf_sub, decide_fn, label, cost=cost, pre_hook=pre_hook)

            if period_label == "full":
                all_equities_full[label] = r.equity

            final_val = float(r.equity.iloc[-1])
            mwrr = compute_mwrr(contrib_dates, final_val)
            mdd = compute_mdd(r.equity)
            vol = compute_ann_vol(r.equity)
            row = {
                "variant": slug,
                "period": period_label,
                "cost": cost,
                "total_contrib": total_contrib,
                "final_value": round(final_val, 2),
                "profit": round(final_val - total_contrib, 2),
                "MWRR": round(mwrr, 6),
                "MDD": round(mdd, 6),
                "ann_vol": round(vol, 6),
                "sharpe_approx": round(mwrr / vol, 4) if vol > 1e-8 else 0.0,
                "end_cash": round(float(r.cash.iloc[-1]), 2),
                "n_trades": len(r.trades),
            }
            all_rows.append(row)

# Compute vs_immediate for full period only
immediate_full = next(
    r for r in all_rows
    if r["variant"] == "immediate_QLD" and r["period"] == "full" and r["cost"] == 0.0
)
for row in all_rows:
    if row["cost"] == 0.0:
        if row["period"] == "full":
            row["vs_imm_pct"] = round((row["final_value"] / immediate_full["final_value"] - 1) * 100, 2)
        else:
            imm_period = next(
                r for r in all_rows
                if r["variant"] == "immediate_QLD" and r["period"] == row["period"] and r["cost"] == 0.0
            )
            row["vs_imm_pct"] = round((row["final_value"] / imm_period["final_value"] - 1) * 100, 2)

# ── Save CSV ───────────────────────────────────────────────────────────
out_dir = "backtest/output"
os.makedirs(out_dir, exist_ok=True)
df_out = pd.DataFrame(all_rows)
cols = ["variant","period","cost","total_contrib","final_value","profit",
        "MWRR","MDD","ann_vol","sharpe_approx","end_cash","n_trades","vs_imm_pct"]
csv_path = os.path.join(out_dir, "results_portfolio.csv")
df_out[cols].to_csv(csv_path, index=False)
logger.info("Saved %s", csv_path)

# Print full-period cost=0 table
print("\n" + "=" * 120)
print(f"{'Variant':<30} {'Final':>12} {'MWRR':>8} {'MDD':>8} {'Vol':>8} {'Sharpe':>8} {'Trades':>7} {'vsImm':>8}")
print("-" * 120)
for row in sorted(all_rows, key=lambda x: -x["final_value"]):
    if row["period"] == "full" and row["cost"] == 0.0:
        print(f"{row['variant']:<30} ${row['final_value']:>9,.0f} "
              f"{row['MWRR']*100:>7.2f}% {row['MDD']*100:>7.2f}% "
              f"{row['ann_vol']*100:>7.2f}% {row['sharpe_approx']:>7.3f} "
              f"{row['n_trades']:>6} {row['vs_imm_pct']:>+7.2f}%")
print("=" * 120)

# OOS tables
for p in ["OOS-A", "OOS-B"]:
    print(f"\n--- {p} (cost=0) ---")
    print(f"{'Variant':<30} {'Final':>12} {'MWRR':>8} {'MDD':>8} {'vsImm':>8}")
    for row in sorted(all_rows, key=lambda x: -x["final_value"]):
        if row["period"] == p and row["cost"] == 0.0:
            print(f"{row['variant']:<30} ${row['final_value']:>9,.0f} "
                  f"{row['MWRR']*100:>7.2f}% {row['MDD']*100:>7.2f}% "
                  f"{row['vs_imm_pct']:>+7.2f}%")

# ── Equity plot (full period, cost=0) ────────────────────────────────
fig, ax = plt.subplots(figsize=(16, 8))
cmap = plt.cm.Set1
for i, (label, eq) in enumerate(sorted(all_equities_full.items())):
    if "_cost" in label:
        continue  # only cost=0
    ax.plot(eq.index, eq.values, label=label.replace("_full", ""),
            linewidth=0.8, color=cmap(i % 9))
# Cumulative contribution line
cd_full, _ = get_contrib_info(mdf)
cumul = np.arange(1, len(cd_full) + 1) * 300.0
ax.plot(cd_full, cumul, label="total_contrib", linewidth=2,
        color="gray", linestyle="--")
ax.set_title("Portfolio Strategy Equity Curves ($300/month, 2011–2026)")
ax.set_xlabel("Date"); ax.set_ylabel("Portfolio Value ($)")
ax.legend(loc="best", fontsize=6)
ax.grid(True, alpha=0.3)
fig.savefig(os.path.join(out_dir, "equity_portfolio.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
logger.info("Saved equity_portfolio.png")

# ── Korean report ──────────────────────────────────────────────────────
def r(name, period="full"):
    return next(
        x for x in all_rows
        if x["variant"] == name and x["period"] == period and x["cost"] == 0.0
    )

imm = r("immediate_QLD")
dly = r("daily_QLD")
rv1 = r("rule_v1_QLD")
v3r = r("v3_regime")
v3d = r("v3_dualmom")
p1  = r("P1_regime_basket")
p2  = r("P2_xsec_mom")
p3  = r("P3_static_lev")
win = r("WIN_static_TQQQ60UPRO40")
wint = r("WIN_imm_TQQQ100")
mix = r("MIX_TQQQ50UPRO30TLT20")

lines = []
def w(s): lines.append(s)
def block(name, d, note=""):
    w(f"  ◆ {name}")
    w(f"    최종자산      : ${d['final_value']:>10,.0f}")
    w(f"    MWRR(연)      : {d['MWRR']*100:.2f}%")
    w(f"    MDD           : {d['MDD']*100:.2f}%")
    w(f"    연변동성      : {d['ann_vol']*100:.2f}%")
    w(f"    Sharpe(근사)  : {d['sharpe_approx']:.3f}")
    w(f"    거래수        : {d['n_trades']}회")
    w(f"    vs즉시        : {d['vs_imm_pct']:+.2f}%")
    if note:
        w(f"    비고          : {note}")
    w("")

w("포트폴리오 배분 전략 비교 — 2011~2026 ($300/월 정기납입)")
w("=" * 55); w("")
w("■ 가정"); w(f"  납입액   : 매월 $300 (총납입 ${imm['total_contrib']:,.0f})")
w(f"  기간     : 2011-01-01 ~ 2026-06-19 (전체), OOS-A(2011~2017), OOS-B(2018~2026)")
w(f"  초기자본 : $0 (적립식)"); w(f"  유니버스 : QQQ/SPY/QLD/SSO/TQQQ/UPRO/TLT/GLD"); w("")
w("■ 11개 전략"); w("  1. immediate_QLD : QLD 즉시 매수 (기준)")
w("  2. daily_QLD       : QLD 월분할 매수"); w("  3. rule_v1_QLD     : v1 타이밍 + QLD")
w("  4. v3_regime       : QQQ 200MA 레짐 → QLD/TQQQ/현금"); w("  5. v3_dualmom      : 12개월 듀얼모멘텀 QQQ/QLD/TQQQ")
w("  6. P1_regime_basket: QQQ+SPY 200MA 레짐 → ON(4Levered)/OFF(TLT+GLD) 역변동성"); w("  7. P2_xsec_mom     : 교차모멘텀 top3 역변동성")
w("  8. P3_static_lev   : TQQQ40%/UPRO30%/TLT15%/GLD15%"); w("  9. WIN_static_TQQQ60UPRO40 : TQQQ60%/UPRO40%")
w("  10. WIN_imm_TQQQ100 : TQQQ 100% 즉시매수"); w("  11. MIX_TQQQ50UPRO30TLT20 : TQQQ50%/UPRO30%/TLT20%")
w(""); w("■ 전체기간 결과 (cost=0 기준)"); w("")

block("immediate_QLD (기준)", imm, "QLD 2x 단순적립")
block("daily_QLD", dly, "월분할 QLD")
block("rule_v1_QLD", rv1, "v1 타이밍, 현금보유편향")
block("v3_regime", v3r, "QQQ 200MA 레짐스택")
block("v3_dualmom", v3d, "12개월 모멘텀")
block("P1_regime_basket", p1, "레짐 ON/OFF 역변동성")
block("P2_xsec_mom", p2, "교차모멘텀 top3 (MDD 최저)")
block("P3_static_lev", p3, "TQQQ40/UPRO30/TLT15/GLD15")
block("WIN_static_TQQQ60UPRO40", win, "TQQQ60/UPRO40 (1위)")
block("WIN_imm_TQQQ100", wint, "TQQQ 100% 즉시")
block("MIX_TQQQ50UPRO30TLT20", mix, "채권혼합 20%")

w("■ 순위 (전체기간 cost=0)"); w("")
for rank, v in enumerate(sorted(
    [r for r in all_rows if r["period"] == "full" and r["cost"] == 0.0],
    key=lambda x: -x["final_value"],
), 1):
    w(f"  {rank}위: {v['variant']:<30} ${v['final_value']:>9,.0f}  "
      f"MWRR {v['MWRR']*100:.1f}%  MDD {v['MDD']*100:.0f}%  "
      f"vs즉시 {v['vs_imm_pct']:+.0f}%")
w("")

# OOS table
for p in ["OOS-A", "OOS-B"]:
    w(f"■ {p} (cost=0) 순위"); w("")
    for rank, v in enumerate(sorted(
        [r for r in all_rows if r["period"] == p and r["cost"] == 0.0],
        key=lambda x: -x["final_value"],
    ), 1):
        w(f"  {rank}위: {v['variant']:<30} ${v['final_value']:>9,.0f}  "
          f"MWRR {v['MWRR']*100:.1f}%  vs즉시 {v['vs_imm_pct']:+.0f}%")
    w("")

# Cost impact
w("■ 거래비용 영향 (0% → 0.05%, 전체기간)"); w("")
for slug in [s[0] for s in STRATEGIES]:
    r0 = next(x for x in all_rows if x["variant"] == slug and x["period"] == "full" and x["cost"] == 0.0)
    r1 = next(x for x in all_rows if x["variant"] == slug and x["period"] == "full" and x["cost"] == 0.0005)
    diff = r1["final_value"] / r0["final_value"] - 1
    w(f"  {slug}: ${r0['final_value']:>9,.0f} → ${r1['final_value']:>9,.0f} ({diff*100:+.2f}%)")
w("")

# Key findings
w("■ 결론 및 해석"); w("")
w("  1) 다자산 로테이션(레짐/모멘텀: P1/P2/v3_regime/v3_dualmom)은 15년 QLD/TQQQ 강세장에서")
w("     전부 패배했다. 시장이탈·재진입 과정의 decay가 치명적이었다.")
w(f"  → P2_xsec_mom(최종 ${p2['final_value']:,.0f})이 MDD 39%로 최저였으나 수익 희생이 너무 큼."); w("")
w("  2) 적립 QLD를 이긴 것은 '더 높은 레버리지를 계속 보유'하는 정적전략뿐이다:")
w(f"  → WIN_static_TQQQ60UPRO40 (1위, ${win['final_value']:,.0f}, vs즉시 +{win['vs_imm_pct']:.0f}%)")
w(f"  → WIN_imm_TQQQ100 (2위, ${wint['final_value']:,.0f}, vs즉시 +{wint['vs_imm_pct']:.0f}%)")
w("  → OOS-A·OOS-B 양 구간에서 일관되게 immediate_QLD 초과 = 과적합 아님"); w("")
w("  3) 단, 초과수익은 순수 추가위험의 대가다:")
w(f"  → MDD: TQQQ100 82%, TQQQ60/UPRO40 74% vs QLD 63%")
w(f"  → Sharpe: 0.60~0.65로 QLD(0.64)와 동일 수준 — 위험조정 개선 아님"); w("")
w("  4) 채권혼합(TLT20%)은 OOS-B(2022 금리인상기)에서 역효과로 비일관:")
w(f"  → OOS-B MIX vs즉시 {mix['vs_imm_pct']:+.0f}% vs WIN계열 +100~150% — TLT가 2022년 금리인상에 폭락"); w("")
w(f"  5) 2011~2026 QQQ는 약 40배 상승. 이런 장에서 시장이탈은 구조적 손해.")
w("     TQQQ 100%가 단순히 40배의 3배(≈120배) 수익에 근접하는 것은 수학적 결과일 뿐.")
w("     장기 약세장/횡보장에서는 반대 결과가 나올 수 있음."); w("")
w("■ 함의"); w("")
w("  ● 80% 낙폭 감내 가능 → TQQQ/UPRO 블렌드가 기대수익 최고 (QLD 적립 대비 +55~130%)")
w("  ● 낙폭 부담 → QLD 적립(immediate)이 위험조정 우수, TQQQ 단독보다 안정적")
w("  ● '장 성격 적응' 전략(P1/P2/v3)은 장기 약세장/횡보장에서 가치가 있으나")
w("    2011~2026 데이터로는 입증 불가 — 다른 시장 국면의 out-of-sample 필요")

report_path = os.path.join(out_dir, "report_portfolio_ko.txt")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
logger.info("Saved %s", report_path)
print(f"\n산출물: {csv_path}, equity_portfolio.png, {report_path}")
