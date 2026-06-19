# v3 전략 제안: buy&hold를 이기는 능동매매 (PROPOSE)

**From**: opencode
**To**: manager
**Date**: 2026-06-19 11:50
**Type**: PROPOSE (REVIEW_RESPONSE)
**Priority**: HIGH
**Re**: handoff_propose-v3.claude-opus-4-8.md

## 핵심 인식

v1·v2가 모두 lumpsum에 진 근본 원인: **long/현금만으로는 최대 노출 = 100% = buy&hold 수준**인데,
15년 QLD는 압도적 우상향이라 현금 보유 기간이 그대로 손해였다.

이기려면 필요한 것:
1. **>100% 노출** (강세장에 레버리지 추가)
2. **하락장 수익** (숏/인버스로 수익원 확보)
3. **변동성 손실 회피** (QLD는 일간 2x → 변동성 큰 구간에서 decay 심화 — 이 구간을 피하면 QLD×2에 근접)

이 3가지를 결합한 **Regime-Dependent Leverage**가 가장 유망하다.

---

## 후보 1: QQQ Regime-Switching + TQQQ Leverage Stack ⭐ (최우선)

**메커니즘**
- 신호: QQQ(기초지수)의 200일 MA를 핵심 레짐 필터로 사용. QQQ는 QLD보다 노이즈가 적고 30년 이상 검증됨.
- 3개 레짐:
  - **strong_bull** (QQQ > 200MA, QQQ > 100MA, QQQ/200MA ratio > 1.15): TQQQ(3x) + QLD(2x) 혼합 → 유효 노출 250~300%
  - **bull** (QQQ > 200MA, ratio 1.0~1.15): QLD 100% (2x)
  - **bear** (QQQ < 200MA): 현금 또는 SHY
- TQQQ는 QQQ×3의 순수 레버리지라 QLD보다 decay가 심하지만, strong_bull에서만 쓰기 때문에 장기 우상향 구간만 추출 가능.

**왜 buy&hold를 이길 수 있는가**
- strong_bull 구간 250~300% 노출: QLD buy&hold가 100%일 때 2.5~3x 추격 → 수익 곡선이 급격히 상승
- bear 구간 회피: 2022년 40% 폭락 방어, 수익률 유지
- TQQQ strong_bull 전용 사용으로 decay는 QLD 보유보다 상대적으로 덜함 (원래 QQQ가 99x 상승한 15년, 그 구간의 subset에서 TQQQ는 폭발적)

**엔진 확장**
- QQQ 티커 데이터 로딩 필요 (현재는 QLD만 캐싱)
- TQQQ 티커 데이터 로딩 필요 (강세장에서 QQQ 대신 보유)
- 포트폴리오 상태: 복수 티커 보유 가능해야 함 (QLD + TQQQ + 현금)
- `BacktestResult` 확장: 다중 티커 트래킹

**오버피팅 위험**
- round-number 파라미터 (200MA, 1.15 threshold). threshold는 1.10~1.20에서 민감도 테스트
- QQQ 200MA는 20년 이상 학술적으로 검증된 전략 (Faber 2007, "Tactical Asset Allocation")
- 검증: 2000~2010(닷컴, 금융위기) 기간에도 QLD/QQQ 모두 검증 가능

**현실성**
- TQQQ daily rebalancing so tracking error minimal; long-only ETFs, 현실적
- 거래비용: 레짐 전환 = 월 1~2회, 무시 가능
- 마진/숏 없음, ETF만 사용 → 누구나 실행 가능

---

## 후보 2: Volatility-Targeting Dynamic Allocation

**메커니즘**
- 목표: 연간 변동성 30%로 고정 (QLD의 장기 평균 vol ≈ 40% → 이보다 낮춤)
- 매일 QQQ의 과거 20일 실현 변동성 계산
- 목표 변동성 / 실현 변동성 = 필요한 익스포저 비율
- 노출은 QLD, TQQQ, 현금으로 분배:
  - 필요 노출 < 100%: QLD + 현금
  - 필요 노출 100~200%: QLD + TQQQ 혼합 (QLD×2 + TQQQ×3 의 가중평균)
  - 필요 노출 > 200%: 전량 TQQQ
- 저변동성 구간에 과감히 레버리지, 고변동성 구간에 방어

**왜 buy&hold를 이길 수 있는가**
- 저변동성(보통 상승장)에 200~300% 노출 → 수익 폭증
- 고변동성(보통 하락장)에 0~100% 노출 → decay 방어 + 자본 보존
- vol-targeting은 학술적으로 Sharpe ratio를 높이는 검증된 기법

**엔진 확장**
- QQQ 데이터 로딩 (QQQ가 없으면 QLD의 vol로 대체 가능하나 QQQ가 더 안정적)
- TQQQ 데이터 로딩
- 매일의 vol 계산 로직
- 복수 티커 보유

**오버피팅 위험**
- 20일 window와 목표 vol 결정에서 약간의 자유도 존재
- 목표 vol 25%~35% 사이 민감도 테스트 필요
- vol targeting은 파라미터에 덜 민감한 특성 있음

**현실성**
- 연간 250회 리밸런싱 → 거래비용 고려해야
- TQQQ의 daily decay는 vol-targeting 하에서도 영향 있음
- 검증: QQQ의 30년 데이터로 out-of-sample 테스트 가능

---

## 후보 3: Dual Momentum (QQQ/QLD/TQQQ + Cash)

**메커니즘**
- 매월 말, 최근 12개월 수익률이 가장 높은 자산으로 전환
- 후보: QQQ, QLD, TQQQ, 현금(1-month T-bill 수익률)
- 단순히 1위에 100% 할당
- 원조: Gary Antonacci "Dual Momentum" (2014)

**왜 buy&hold를 이길 수 있는가**
- 대세 상승기: TQQQ나 QLD 선택 → 2~3x 수익으로 lumpsum 압도
- QQQ 약세/조정기: 현금 선택 → 하락 방어
- 12개월 모멘텀은 추세를 잘 포착하며, QQQ 강세장이 12개월 이상 지속되는 특성에 잘 맞음

**엔진 확장**
- QQQ, TQQQ 데이터 로딩
- 월별 리밸런싱 로직 (매달 말일 체크)
- 멀티 티커 BacktestResult

**오버피팅 위험**
- 거의 없음: 단일 파라미터(12개월 lookback)는 원조 그대로
- 6개월/9개월/12개월 lookback 민감도 테스트 가능

**현실성**
- 월 1회 거래 → 거래비용 무시 가능
- 매우 직관적, 누구나 실행 가능
- 15년 QLD 역사로는 충분히 검증 가능 (360개월)

---

## 후보 4: Core-Satellite with QQQ Put Selling

**메커니즘**
- Core: QLD 70% 장기 보유 (lumpsum에 준하는 베타 노출 유지)
- Satellite: QQQ cash-secured put 매도 (현금의 30%로 운용)
  - QQQ가 강세장이면: put 프리미엄 수익 + QQQ 하락 시 행사 → QQQ 매수 (QLD 보유와 시너지)
  - QQQ가 약세장이면: 행사될 위험 있으나, 어차피 QLD가 하락 중이라 QQQ 매수는 오히려 좋은 매수 기회
- 추가: 강세 확신 구간에만 put 매도, 약세장에는 put 매도 중단
- 이 전략은 엄밀히 옵션이 필요하지만, 동일 현금흐름을 아래 근사로 백테스트 가능:
  - 매도한 현금의 30%로 1개월 만기 ATM put 근사 → 매달 행가 95% 수준에서 프리미엄 2% 가정
  - 행사 시: QQQ 편입, 다음 달 만기시 평가

**왜 buy&hold를 이길 수 있는가**
- Core 70%만으로 lumpsum의 70% 수익 확보
- Put 프리미엄 연 10~15% 추가 수익 (QQQ의 일반적인 put premium)
- 대부분의 달은 행사되지 않고 프리미엄만 수취 → 초과수익
- QQQ 강세장에서 QLD 수익 + put 프리미엄 수익 = >QLD 단순 보유

**엔진 확장**
- QQQ 데이터 로딩
- 옵션 모의: 매달 ATM put 프리미엄 추정 필요 (실제 데이터 또는 Black-Scholes 근사)
- 이건 "백테스트 가능성" 측면에서 가장 복잡함

**오버피팅 위험**
- 옵션 가격을 가정해야 하므로 근사 오차 있음
- VIX 변동에 따른 put premium 변동 반영하기 어려움

**현실성**
- 옵션 거래 경험 필요, 개인투자자도 가능하나 진입장벽 높음
- 실제 put 매도는 마진콜 위험 존재 (cash-secured이면 괜찮음)
- 백테스트 근사의 신뢰도가 다른 전략보다 낮음

---

## 후보 5: QQQ Short-Term Mean Reversion Swing

**메커니즘**
- QQQ의 2~5일 단기 낙폭과도매도 → QLD 매수, 반등 시 청산
- 신호: QQQ가 3거래일 연속 하락 + 합계 -3% 이상 + RSI(5) < 30
  - 이틀에 걸쳐 QLD 분할 매수 (각각 현금의 50%)
- 청산: QQQ가 2거래일 연속 상승 또는 RSI(5) > 70
  - 분할 청산 (각각 50%)
- Core: QLD 40% 고정보유
- Signal: 현금 60%로 swing trading (연간 30~50회)
- V자 반등을 포착하는 것이 목적 (v2의 dd_exit가 실패한 부분)

**왜 buy&hold를 이길 수 있는가**
- QLD buy&hold가 가장 취약한 급락 → V자 반등 구간에서 수익
- 예: 2020년 3월 COVID 폭락(QQQ -28%) → 3일 연속 하락 트리거로 진입 → 2개월 후 40% 상승 → 청산
- 핵심: V자 반등 바닥에서 60% 현금으로 QLD 매수 → lumpsum보다 훨씬 높은 수익률
- 문제점: rectangle 패턴(횡보)에서는 손실 발생

**엔진 확장**
- QQQ 데이터 로딩
- 다중 매수/매도 주문 로직 (동일 티커에 여러 진입가)
- 현재 엔진은 단일 avg_cost 기반 → 확장 필요

**오버피팅 위험**
- 높음: RSI 기간, 하락률, 연속일 등 여러 파라미터
- 검증: 2000~2011 out-of-sample, 2012~2026 in-sample으로 분할 필요
- round number 사용 (3%, 2거래일 등)으로 최소화

**현실성**
- 연 30~50회 거래 → 거래비용 고려해야 (현대 증권사 수수료 무시 가능)
- 단기 스윙은 감정적 부담 있음

---

## 종합 추천

| # | 전략 | BUY&HOLD 승산 | 구현 난이도 | 오버핏 위험 | 실현가능성 |
|---|---|---|---|---|---|
| 1 | QQQ Regime + TQQQ Stack | ★★★★★ | ★★☆☆☆ | ★★☆☆☆ | ★★★★★ |
| 2 | Vol-Targeting | ★★★★☆ | ★★★☆☆ | ★★★☆☆ | ★★★★☆ |
| 3 | Dual Momentum | ★★★★☆ | ★☆☆☆☆ | ★☆☆☆☆ | ★★★★★ |
| 4 | Put Selling | ★★★☆☆ | ★★★★☆ | ★★★☆☆ | ★★☆☆☆ |
| 5 | Mean Reversion Swing | ★★☆☆☆ | ★★★☆☆ | ★★★★☆ | ★★★☆☆ |

**1순위 추천: QQQ Regime-Switching + TQQQ Leverage Stack**
- QQQ 200MA 레짐 필터는 Faber TAA로 20년 검증됨
- Strong_bull에서 TQQQ로 250~300% 노출이 핵심 edge
- QQQ만 추가 로딩하면 기존 인프라로 구현 가능 (loader.py 수정 없음 — 이미 yfinance 기반)
- 개인 투자자가 실제 실행 가능
- 15년 QLD 강세장에 가장 적합

**제안 순서: 1 → 3 → 2 → 5 → 4** (효용 대비 구현 비용)

- 1이 안 되면 3(Dual Momentum — 가장 단순)
- 3이 안 되면 2(Vol-Targeting — 학술적 근거 탄탄)
- 그 다음 5, 마지막 4
