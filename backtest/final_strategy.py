#!/usr/bin/env python3
"""
최종 추천 전략 검증 — SOXL60/QLD40 결합 포트폴리오, 120일선 + 휩쏘완화 변형.
ma_whipsaw.py의 신호/체결 함수를 재사용해 결합 포트폴리오를 백테스트.
신호: SOXL←SOXX 120일선, QLD←QQQ 120일선 (전일 판정, 미래참조 없음).

핵심 검증 결과(요약, 본문 report_final_strategy_ko.md):
- 'monthly+buffer 결합'은 과도필터 → 실패(SOXL 단독 강세 $2.2M / 2022 -54%). 휩쏘필터는 '하나만'.
- 결합 포트(SOXL60/QLD40) 4안 모두 '둘다 무규칙'(MDD 86%)보다 위험조정 우수(MDD 61~66%).
"""
import pandas as pd
import importlib.util
import os

_spec = importlib.util.spec_from_file_location(
    "mw", os.path.join(os.path.dirname(__file__), "ma_whipsaw.py"))
mw = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(mw)
DF, inv, dca, lump, mdd, irr = mw.DF, mw.invested_series, mw.dca, mw.lump, mw.mdd, mw.irr

BULL = ("2011-01-01", "2026-06-19")
CRASH22 = ("2022-01-03", "2023-12-29")
COVID = ("2020-02-03", "2020-12-31")
HOLD = pd.Series(True, index=DF.index)

# 신호 (120일선)
SOXL_BUF = inv(DF["SOXX"], 120, "buffer", buffer=0.03)   # daily buffer ±3%
SOXL_MON = inv(DF["SOXX"], 120, "plain", monthly=True)    # monthly
QLD_BUF = inv(DF["QQQ"], 120, "buffer", buffer=0.03)

W_SOXL = 0.60  # 코어 SOXL 60% / 위성 QLD 40%

CANDIDATES = [
    ("①SOXL buf3% + QLD무규칙 (최종추천)", SOXL_BUF, HOLD),
    ("②SOXL buf3% + QLD buf3% (최대방어)", SOXL_BUF, QLD_BUF),
    ("③SOXL monthly + QLD무규칙 (공격틸트)", SOXL_MON, HOLD),
    ("④SOXL monthly + QLD buf3%", SOXL_MON, QLD_BUF),
    ("참고: 둘다 무규칙", HOLD, HOLD),
]


def combo_dca(si, qi, w=W_SOXL):
    a, c, fa = dca("SOXL", si, BULL); b, _, fb = dca("QLD", qi, BULL)
    eq = w * a + (1 - w) * b; fv = float(eq.iloc[-1])
    return fv, irr(c + [fv]), mdd(eq), fa + fb


def combo_lump(si, qi, win, w=W_SOXL):
    a, _ = lump("SOXL", si, win); b, _ = lump("QLD", qi, win)
    eq = w * a + (1 - w) * b
    return float(eq.iloc[-1]), mdd(eq)


if __name__ == "__main__":
    print("=== 강세장 2011~2026 (월$300, SOXL60/QLD40) ===")
    for nm, si, qi in CANDIDATES:
        fv, m, dd, fl = combo_dca(si, qi)
        print(f"  {nm:34s} 최종 ${fv:>11,.0f}  MWRR {m*100:>5.1f}%  MDD {dd*100:>3.0f}%  전환 {fl}")
    for lb, win in [("2022 반도체 폭락", CRASH22), ("COVID 2020", COVID)]:
        print(f"\n=== {lb} (일괄 $10k) ===")
        for nm, si, qi in CANDIDATES:
            fv, dd = combo_lump(si, qi, win)
            print(f"  {nm:34s} 최종 ${fv:>9,.0f}  총수익 {fv/1e4-1:>+5.0%}  MDD {dd*100:>3.0f}%")
