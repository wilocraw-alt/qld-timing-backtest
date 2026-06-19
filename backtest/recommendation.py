#!/usr/bin/env python3
"""
전략 추천 — 패널 확률 × (강세장 백테스트 + 닷컴 위기) 기대값 분석.

- 확률: 세션 패널 토의(opencode/antigravity/manager) 종합 (12~24개월).
- 시나리오별 18개월 총수익(%): 우리 두 백테스트에 근거한 추정치.
    강세  = 2011~2026 MWRR을 18개월 복리환산 (QLD 33.5%/yr, TQQQ 42.8%/yr, 추세 ~25%/yr)
    폭락  = 닷컴 시나리오(1x -15% / 3x -97% / 추세 +147~339%)를 2x·보수적 매핑
    조정/스태그 = 두 사례 사이 + 레버리지 변동성 손실(decay) 반영
- 산출: 전략별 기대수익 + 최악(폭락) + 강세상단 → 추천.

주의: 시나리오 수익은 추정치이며 본 분석은 투자조언이 아님.
"""

# 패널 종합 확률
P = {"강세지속": 0.42, "의미있는조정": 0.38, "닷컴급폭락": 0.11, "스태그/침체": 0.09}

# 시나리오별 18개월 총수익 가정 (%)
S = {
    "QLD적립(2x보유)":     {"강세지속": +54, "의미있는조정": -10, "닷컴급폭락": -55, "스태그/침체": -15},
    "3x무방비보유":        {"강세지속": +71, "의미있는조정": -45, "닷컴급폭락": -88, "스태그/침체": -45},
    "3x+추세이탈(200MA)":  {"강세지속": +41, "의미있는조정":  -8, "닷컴급폭락":  +5, "스태그/침체": -22},
    "QLD+추세이탈(200MA)": {"강세지속": +38, "의미있는조정":  -4, "닷컴급폭락": +10, "스태그/침체": -12},
}
# 바벨: 60% QLD보유 + 40% (3x+추세이탈)
S["바벨(60%QLD+40%3x추세)"] = {
    k: round(0.6 * S["QLD적립(2x보유)"][k] + 0.4 * S["3x+추세이탈(200MA)"][k], 1) for k in P
}


def expected(sc):
    return sum(P[k] * sc[k] for k in P)


def ranked():
    rows = [(n, expected(sc), sc["닷컴급폭락"], sc["강세지속"]) for n, sc in S.items()]
    return sorted(rows, key=lambda x: -x[1])


def sensitivity(bull_p):
    """강세 확률을 bull_p로 올리고 나머지는 원비율 유지했을 때 재계산."""
    rest = 1 - bull_p
    base_rest = sum(v for k, v in P.items() if k != "강세지속")
    pp = {k: (bull_p if k == "강세지속" else P[k] / base_rest * rest) for k in P}
    rows = [(n, sum(pp[k] * sc[k] for k in P)) for n, sc in S.items()]
    return sorted(rows, key=lambda x: -x[1])


if __name__ == "__main__":
    print("패널 확률:", P)
    print(f"\n{'전략':26s} {'기대수익':>8s} {'최악(폭락)':>9s} {'강세상단':>8s}")
    for n, ev, worst, up in ranked():
        print(f"{n:26s} {ev:>+7.1f}% {worst:>+8.0f}% {up:>+7.0f}%")
    print("\n민감도 — 강세확률을 60%로 가정하면 1위:", sensitivity(0.60)[0])
    print("민감도 — 강세확률을 42%(패널) 1위:", sensitivity(0.42)[0])
