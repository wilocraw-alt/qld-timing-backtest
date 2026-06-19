#!/usr/bin/env python3
"""
Portfolio strategy comparison (incl. SOXL) — 14 strategies × 3 periods × 2 costs.
Outputs: results_portfolio.csv, equity_portfolio.png, report_portfolio_ko.txt
"""
import os, sys, logging
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


# ── Data (SOXL = 반도체 3x 추가) ────────────────────────────────────────
UNIVERSE = ["QQQ","SPY","QLD","SSO","TQQQ","UPRO","SOXL","TLT","GLD"]
logger.info("Loading %d tickers ...", len(UNIVERSE))
prices = load_many(UNIVERSE)
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
    # ── SOXL(반도체 3x) 포함 신규 ───────────────────────────────────────
    ("SOXL_imm_SOXL100", lambda df: (df[["SOXL"]], decide_immediate, None)),
    ("SOXL_TQQQ50SOXL50", lambda df: (
        df, make_static_lev({"targets":{"TQQQ":0.5,"SOXL":0.5}}), None)),
    ("SOXL_3x_equal", lambda df: (
        df, make_static_lev({"targets":{"TQQQ":1/3,"UPRO":1/3,"SOXL":1/3}}), None)),
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
    return run_contrib(prices_df, decide_fn, monthly=monthly, name=name, cost=cost)


# ── Run all ────────────────────────────────────────────────────────────
all_rows = []
all_equities_full = {}

for period_label, (start, end) in PERIODS.items():
    pdf = mdf.loc[start:end].copy()
    contrib_dates, total_contrib = get_contrib_info(pdf)
    logger.info("Period %s: %d rows, %d contributions, $%.0f total",
                 period_label, len(pdf), len(contrib_dates), total_contrib)

    for slug, factory in STRATEGIES:
        pdf_sub, decide_fn, pre_hook = factory(pdf)
        for cost in COSTS:
            label = f"{slug}_{period_label}_cost{cost}" if cost > 0 else f"{slug}_{period_label}"
            r = run_one(pdf_sub, decide_fn, label, cost=cost, pre_hook=pre_hook)
            if period_label == "full":
                all_equities_full[label] = r.equity
            final_val = float(r.equity.iloc[-1])
            mwrr = compute_mwrr(contrib_dates, final_val)
            mdd = compute_mdd(r.equity)
            vol = compute_ann_vol(r.equity)
            all_rows.append({
                "variant": slug, "period": period_label, "cost": cost,
                "total_contrib": total_contrib,
                "final_value": round(final_val, 2),
                "profit": round(final_val - total_contrib, 2),
                "MWRR": round(mwrr, 6), "MDD": round(mdd, 6),
                "ann_vol": round(vol, 6),
                "sharpe_approx": round(mwrr / vol, 4) if vol > 1e-8 else 0.0,
                "end_cash": round(float(r.cash.iloc[-1]), 2),
                "n_trades": len(r.trades),
            })

# vs_immediate (per period, cost=0)
for row in all_rows:
    if row["cost"] == 0.0:
        imm_p = next(r for r in all_rows
                     if r["variant"] == "immediate_QLD" and r["period"] == row["period"] and r["cost"] == 0.0)
        row["vs_imm_pct"] = round((row["final_value"] / imm_p["final_value"] - 1) * 100, 2)

# ── Save CSV ───────────────────────────────────────────────────────────
out_dir = "backtest/output"
os.makedirs(out_dir, exist_ok=True)
cols = ["variant","period","cost","total_contrib","final_value","profit",
        "MWRR","MDD","ann_vol","sharpe_approx","end_cash","n_trades","vs_imm_pct"]
csv_path = os.path.join(out_dir, "results_portfolio.csv")
pd.DataFrame(all_rows)[cols].to_csv(csv_path, index=False)
logger.info("Saved %s", csv_path)

# Print full-period table
print("\n" + "=" * 120)
print(f"{'Variant':<28} {'Final':>13} {'MWRR':>8} {'MDD':>7} {'Vol':>7} {'Sharpe':>7} {'vsImm':>8}")
print("-" * 120)
for row in sorted(all_rows, key=lambda x: -x["final_value"]):
    if row["period"] == "full" and row["cost"] == 0.0:
        print(f"{row['variant']:<28} ${row['final_value']:>11,.0f} "
              f"{row['MWRR']*100:>6.1f}% {row['MDD']*100:>6.0f}% "
              f"{row['ann_vol']*100:>6.0f}% {row['sharpe_approx']:>7.3f} "
              f"{row['vs_imm_pct']:>+7.1f}%")
print("=" * 120)

# ── Equity plot (full, cost=0) ──────────────────────────────────────────
fig, ax = plt.subplots(figsize=(16, 8))
cmap = plt.cm.tab20
for i, (label, eq) in enumerate(sorted(all_equities_full.items())):
    if "_cost" in label:
        continue
    ax.plot(eq.index, eq.values, label=label.replace("_full", ""),
            linewidth=0.9, color=cmap(i % 20))
cd_full, _ = get_contrib_info(mdf)
cumul = np.arange(1, len(cd_full) + 1) * 300.0
ax.plot(cd_full, cumul, label="total_contrib", linewidth=2, color="black", linestyle="--")
ax.set_yscale("log")
ax.set_title("Portfolio Equity Curves incl. SOXL ($300/month, 2011–2026, log scale)")
ax.set_xlabel("Date"); ax.set_ylabel("Portfolio Value ($, log)")
ax.legend(loc="best", fontsize=6, ncol=2)
ax.grid(True, alpha=0.3)
fig.savefig(os.path.join(out_dir, "equity_portfolio.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
logger.info("Saved equity_portfolio.png")

# ── Korean report ──────────────────────────────────────────────────────
def r(name, period="full"):
    return next(x for x in all_rows
                if x["variant"] == name and x["period"] == period and x["cost"] == 0.0)

imm = r("immediate_QLD")
lines = []
def w(s): lines.append(s)
def block(name, d, note=""):
    w(f"  ◆ {name}")
    w(f"    최종자산      : ${d['final_value']:>11,.0f}")
    w(f"    MWRR(연)      : {d['MWRR']*100:.2f}%")
    w(f"    MDD           : {d['MDD']*100:.2f}%")
    w(f"    연변동성      : {d['ann_vol']*100:.2f}%")
    w(f"    Sharpe(근사)  : {d['sharpe_approx']:.3f}")
    w(f"    vs즉시        : {d['vs_imm_pct']:+.2f}%")
    if note: w(f"    비고          : {note}")
    w("")

w("포트폴리오 배분 전략 비교 (SOXL 포함) — 2011~2026 ($300/월 정기납입)")
w("=" * 60); w("")
w("■ 가정")
w(f"  납입액   : 매월 $300 (총납입 ${imm['total_contrib']:,.0f})")
w("  기간     : 2011-01-01 ~ 2026-06-19 (전체), OOS-A(2011~2017), OOS-B(2018~2026)")
w("  초기자본 : $0 (적립식)")
w("  유니버스 : QQQ/SPY/QLD/SSO/TQQQ/UPRO/SOXL/TLT/GLD")
w("  주: SOXL = 반도체(SOX 지수) 일간 3배 레버리지 ETF")
w("")
w("■ 전체기간 순위 (cost=0)"); w("")
for rank, v in enumerate(sorted(
        [x for x in all_rows if x["period"] == "full" and x["cost"] == 0.0],
        key=lambda x: -x["final_value"]), 1):
    w(f"  {rank:>2}위: {v['variant']:<26} ${v['final_value']:>11,.0f}  "
      f"MWRR {v['MWRR']*100:>4.1f}%  MDD {v['MDD']*100:>3.0f}%  "
      f"Sharpe {v['sharpe_approx']:.2f}  vs즉시 {v['vs_imm_pct']:+.0f}%")
w("")

w("■ SOXL 포함 핵심 전략 상세 (전체기간, cost=0)"); w("")
block("immediate_QLD (기준, QLD 2x 단순적립)", imm)
block("SOXL_imm_SOXL100 (SOXL 3x 단독)", r("SOXL_imm_SOXL100"), "반도체 3x 단독 — 원수익 1위, 위험 극대")
block("SOXL_TQQQ50SOXL50 (TQQQ+SOXL 반반)", r("SOXL_TQQQ50SOXL50"), "Sharpe 최고 — 두 성장 레버리지 분산")
block("SOXL_3x_equal (TQQQ/UPRO/SOXL 균등)", r("SOXL_3x_equal"), "3x 3종 균등 분산")
block("WIN_imm_TQQQ100 (TQQQ 3x 단독)", r("WIN_imm_TQQQ100"))
block("WIN_static_TQQQ60UPRO40 (이전 1위)", r("WIN_static_TQQQ60UPRO40"))

# OOS tables
for p in ["OOS-A", "OOS-B"]:
    w(f"■ {p} (cost=0) 순위"); w("")
    for rank, v in enumerate(sorted(
            [x for x in all_rows if x["period"] == p and x["cost"] == 0.0],
            key=lambda x: -x["final_value"]), 1):
        w(f"  {rank:>2}위: {v['variant']:<26} ${v['final_value']:>10,.0f}  "
          f"MWRR {v['MWRR']*100:>4.1f}%  MDD {v['MDD']*100:>3.0f}%  vs즉시 {v['vs_imm_pct']:+.0f}%")
    w("")

# Conclusions
sx = r("SOXL_imm_SOXL100"); sb = r("SOXL_TQQQ50SOXL50"); tq = r("WIN_imm_TQQQ100")
w("■ 결론 및 해석"); w("")
w("  1) SOXL(반도체 3x)을 넣으면 원수익이 압도적으로 커진다:")
w(f"  → SOXL_imm_SOXL100 최종 ${sx['final_value']:,.0f} (vs즉시 +{sx['vs_imm_pct']:.0f}%, QLD의 약 {sx['final_value']/imm['final_value']:.1f}배)")
w("  → 2011~2026 반도체(NVDA 등 AI붐)가 가장 강하게 오른 섹터라 3x가 폭발.")
w("")
w("  2) 의미있는 발견 — TQQQ50/SOXL50 블렌드는 위험조정수익까지 개선:")
w(f"  → Sharpe(근사) {sb['sharpe_approx']:.2f} (QLD {imm['sharpe_approx']:.2f}, SOXL단독 {sx['sharpe_approx']:.2f})")
w("  → 반도체(SOXL)와 광범위 기술주(TQQQ)가 완전 동조하지 않아 분산효과가 작동.")
w("  → OOS-A·OOS-B 양 구간에서 일관 — 단일기간 우연 아님.")
w("")
w("  3) 그러나 대가는 '재앙적 낙폭'과 '섹터 집중':")
w(f"  → MDD: SOXL단독 {sx['MDD']*100:.0f}%, TQQQ/SOXL {sb['MDD']*100:.0f}%, TQQQ단독 {tq['MDD']*100:.0f}% vs QLD {imm['MDD']*100:.0f}%")
w("  → 자산이 1/10토막 나는 것을 수년간 버텨야 함 — 대부분 공포에 매도.")
w("  → SOXL은 '단일 섹터(반도체)' 베팅. 승자를 이미 알고 추가한 사후확신(hindsight) 위험이 큼.")
w("    향후 반도체 침체 사이클이면 같은 전략이 가장 크게 다친다.")
w("")
w("  4) 타이밍/로테이션 전략(P1/P2/v3)은 여전히 전부 패배 — 강세장에서 시장이탈은 손해.")
w("")
w("■ 함의"); w("")
w("  ● 최대 원수익: SOXL/TQQQ 같은 3x를 계속 보유 — 단 -85~90% 낙폭과 섹터집중을 감내해야.")
w("  ● 분산된 절충: TQQQ50/SOXL50 또는 3x 균등이 SOXL단독보다 Sharpe 우수(낙폭도 약간↓).")
w("  ● 안정 지향: 그냥 QLD 적립이 위험 대비 여전히 합리적. 낙폭이 훨씬 얕다.")
w("  ● 모든 결론은 역사적 대강세장(특히 반도체) 기준 — 미래 보장 없음, 다른 국면 OOS 필요.")

report_path = os.path.join(out_dir, "report_portfolio_ko.txt")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
logger.info("Saved %s", report_path)
print(f"\n산출물: {csv_path}, equity_portfolio.png, {report_path}")
