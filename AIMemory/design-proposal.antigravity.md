# ANSWER: QLD 백테스트 설계안 제안

**From**: antigravity (worker)
**To**: claude-opus-4-8 (manager)
**Date**: 2026-06-19 08:38
**Type**: REVIEW_RESPONSE
**Priority**: NORMAL
**Re**: AIMemory/handoff_propose-design.claude-opus-4-8.md

## Summary
QLD 규칙기반 투자시점 전략 백테스트 설계안을 제안합니다.
전고점은 All-Time High(ATH), 전저점은 Confirmed Swing Low(20일 윈도우) 방식을 적용해 일별 가격 노이즈와 미래 편향을 배제했습니다.
Pandas+Numpy 기반 커스텀 시뮬레이터로 구현하며, 자본금 상태 기계 및 일일 매수 한도($1,000) 이월 큐를 구동합니다.
실험군으로 8종의 Ablation 매트릭스와 2종의 baselines를 비교 분석합니다.

## Content

### 1. 전고점/전저점 판단법 (Peak & Low Detection)

매일의 미세한 주가 변동(노이즈)에 휩쓸리지 않으면서도 Look-ahead bias(미래참조 편향)가 없는 강건한 전고점/전저점 기준을 제안합니다.

#### A. 전고점 (ATH: All-Time High) 기준
- **판단법**: 백테스트 시점 $t$까지의 역사적 최고 종가(Cumulative Maximum Close)를 사용합니다.
  $$ATH_t = \max_{1 \le i \le t} (Close_i)$$
- **장점**: 미래 편향이 전혀 없으며, 역사적 최고가가 경신될 때만 기준이 자연스럽게 상승하므로 잔출렁임에 반응하지 않습니다.
- **파라미터**:
  - $a = 10\%$ 하락 시 1차 매수 ($Close_t \le ATH_t \times 0.90$)
  - $b = 15\%$ 하락 시 2차 매수 ($Close_t \le ATH_t \times 0.85$)

#### B. 전저점 (Confirmed Swing Low) 기준
- **판단법**: 최근 $2L$ 영업일(예: $20$일) 동안의 극값 중, 중간에 위치한 날짜의 종가가 해당 구간의 최저점일 때 이를 로컬 저점으로 확정하는 **Confirmed Swing Low (Lookback $L$일)** 기법을 사용합니다.
  - 시점 $t$에서, $Close_{t-L}$이 구간 $[t-2L, t]$의 최저점인 경우:
    $$ConfirmedLow_t = Close_{t-L}$$
  - $t$ 시점에서는 확정된 $ConfirmedLow_t$ 가격을 기준으로 매수 신호를 판단합니다.
- **노이즈 억제 원리**:
  - 저점이 형성된 후 최소 $L$일 동안 주가가 그 저점을 깨지 않고 버텨주어야만 저점으로 인정(지연 확정)됩니다.
  - 매일 저점이 새로 갱신되며 출렁이는 현상을 완전히 배제합니다.
- **파라미터 기본값**:
  - 저점 확정 윈도우: $L = 10$ 영업일 (총 판단 윈도우 $2L = 20$일)
  - 3차 매수: 확정 저점 대비 $+e = 10\%$ 반등 ($Close_t \ge ConfirmedLow_t \times 1.10$)
  - 4차 매수: 확정 저점 대비 $+f = 20\%$ 반등 ($Close_t \ge ConfirmedLow_t \times 1.20$)

---

### 2. 백테스트 엔진 아키텍처 (Engine Architecture)

의존성을 최소화하고 전략의 독특한 주문 제한/이월 규칙을 완벽하게 재현하기 위해 **Pandas + numpy 기반의 커스텀 이벤트-드리븐 백테스트 엔진**을 구축합니다.

#### A. 파일 구성
```
timing_wATH/
├── config.yaml                          # 백테스트 파라미터 설정 파일
├── run_backtest.py                      # CLI 실행 스크립트 (인자 처리 및 실행)
└── engine/
    ├── __init__.py
    ├── data.py                          # yfinance 데이터 로드, 정합성 검증, 로컬 캐시 관리
    ├── simulator.py                     # 일자별 루프 구동 및 주문 체결 엔진
    └── metrics.py                       # 성과 지표 계산 및 결과 리포팅
```

#### B. 데이터 로딩 및 캐싱
- 인터넷 단절 또는 yfinance API 속도 지연을 극복하기 위해 `AIMemory/cache/` 내에 원본 데이터를 CSV 포맷으로 캐싱합니다.
- 로컬 캐시 파일(`QLD_raw.csv`)이 존재하면 이를 우선 사용하고, 없으면 yfinance에서 다운로드하여 저장합니다.

#### C. 계산 방식: 벡터화 지표 + 일자별 루프 체결
- **지표 계산 (벡터화)**: 이동평균선(200MA), ATH, Confirmed Low 및 각 매수/매도 트리거 조건은 성능 극대화를 위해 pandas 벡터화 연산으로 사전에 일자별 시그널 칼럼으로 계산해 둡니다.
- **시뮬레이션 (일자별 루프)**: 자금 배분, 트랜치 상태 리셋, 매수 이월 큐 관리, 당일 체결 한도($1,000) 집행 등 시점 간 상호작용이 복잡한 영역은 일자별 순차 루프(`for row in df.itertuples()`)로 구현하여 미래 참조 오류를 완전히 차단합니다.

#### D. 파라미터 주입 및 재현성
- `config.yaml`에 모든 파라미터를 정의하고, `run_backtest.py`에서 CLI 인자(`--config`, `--n`, `--m` 등)로 이를 덮어쓸 수 있도록 구현하여 코드 수정 없는 실험을 보장합니다.

---

### 3. 자금·트랜치·일상한 상호작용 규칙 (Tranche & Cash Rules)

규칙의 모호성을 제거하기 위해 상태 머신(State Machine)과 이월 큐(Queue) 구조를 명확히 정의합니다.

#### A. 트랜치 상태 및 재매수 방지
- **트랜치 관리**: `T1(ATH -10%)`, `T2(ATH -15%)`, `T3(Low +10%)`, `T4(Low +20%)` 총 4개의 트랜치 상태를 가집니다.
- **상태 정의**: 각 트랜치는 `Inactive` (매수 대기), `Active` (매수 완료 후 보유 중) 상태를 가집니다.
- **재매수 방지**: 특정 트랜치가 체결되어 `Active`가 되면, 포지션이 리셋되기 전까지 해당 트랜치의 매수 시그널은 무시됩니다.

#### B. 트랜치 리셋 규칙
- **리셋 조건**: 익절(+c%, +d%) 혹은 대형 하락장 매도(200MA 하회 m%)로 인해 **보유 주식 수량이 0(완전 청산)이 되는 날의 장 마감 후**, 모든 트랜치 상태를 `Inactive`로 일괄 리셋합니다.
- 이에 따라 다음 날부터 새로운 1~4차 분할매수가 다시 시작될 수 있습니다.

#### C. 일 매수 상한 및 이월 큐 관리
- **매수 대기 큐 (Buy Queue)**: 매수 신호가 감지되면 해당 트랜치 주문(금액 $1,000)을 `Buy Queue`에 삽입합니다.
- **일일 체결 제한**: 매 거래일마다 `Buy Queue`에서 가장 오래된 주문부터 꺼내어 **하루 최대 $1,000**까지 체결합니다. 남은 주문은 다음 날로 이월됩니다.
- **이월 주문 체결 조건 검증**: 이월된 주문이 다음 날 체결될 때, **해당 거래일의 종가 기준 가격 조건이 유효한지 재검증**합니다.
  - 예: T1 주문이 이월되어 $t+1$일에 실행되려 할 때, $t+1$일 종가가 여전히 $ATH_{t+1} \times 0.90$ 이하인 경우에만 체결합니다. 만약 가격이 반등하여 조건을 벗어났다면 큐에서 해당 주문을 취소하고 폐기합니다.
- **동시 발생 시 우선순위**:
  1. 먼저 큐에 진입한 주문 (FIFO)
  2. 동일 거래일에 신호가 여러 개 떴을 경우: `T1 (ATH -10%)` -> `T2 (ATH -15%)` -> `T3 (Low +10%)` -> `T4 (Low +20%)` 순으로 큐에 삽입되어 순차 체결됩니다.

---

### 4. Ablation 매트릭스 (Ablation Matrix)

전략의 핵심 규칙 4가지의 독립적 기여도를 평가하기 위한 실험 매트릭스입니다.

| Case ID | Case Name | 1. 200MA 매도 | 2. ATH 매수 (T1, T2) | 3. 전저점 매수 (T3, T4) | 4. 익절 (c%, d%) | 비고 |
|:---:|---|:---:|:---:|:---:|:---:|---|
| **0** | **Full Strategy** | **ON** | **ON** | **ON** | **ON** | 전체 규칙 활성화 (기준점) |
| **1** | **No-200MA-Reduction** | OFF | ON | ON | ON | 하락장 200MA 하회 시 50% 축소 제거 |
| **2** | **No-ATH-Buy** | ON | OFF | ON | ON | ATH 대비 하락 매수(T1, T2) 비활성화 |
| **3** | **No-PrevLow-Buy** | ON | ON | OFF | ON | 전저점 대비 반등 매수(T3, T4) 비활성화 |
| **4** | **No-Take-Profit** | ON | ON | ON | OFF | 평단 대비 익절 분할매도 비활성화 (보유 지속) |
| **5** | **ATH-Buy-Only** | OFF | ON | OFF | OFF | ATH 매수만 수행, 그 외 모든 규칙 OFF |
| **6** | **PrevLow-Buy-Only** | OFF | OFF | ON | OFF | 전저점 매수만 수행, 그 외 모든 규칙 OFF |
| **7** | **Buy-Only-No-Sell** | OFF | ON | ON | OFF | 매수 규칙(T1~T4)만 적용하고 일체 매도 안 함 |

---

### 5. 지표·결과물·검증 (Metrics & Sanity Checks)

#### A. 성과 지표 (Key Performance Indicators)
- **총수익률 (Total Return %)** & **연평균복리수익률 (CAGR %)**
- **최대 낙폭 (MDD %)**: 자산 고점 대비 최대 하락폭
- **샤프 지수 (Sharpe Ratio)**: 연율화 수익률 / 연율화 변동성 (무위험수익률 = 0% 가정)
- **소르티노 지수 (Sortino Ratio)**: 하방 변동성(Downside Volatility) 기준 위험조정성과
- **시장 노출도 (Market Exposure %)**: 주식을 보유하고 있었던 일수 비율
- **평균 현금 비중 (Average Cash Ratio %)**: 전체 기간 일별 (현금/총자산)의 평균
- **거래 횟수 (Total Trade Count)**: 총 매수 및 매도 체결 건수

#### B. 결과 산출물
1. `results_ablation.csv`: Ablation 매트릭스 8종 및 Baselines 2종의 성과 요약 비교표
2. `portfolio_value.png`: 주요 케이스별 포트폴리오 누적 가치 추이 시각화 차트
3. `summary_report.txt`: 최종 요약 리포트 (한국어, Key-Value 세로형식)

#### C. 검증 기법 (Sanity Checks)
- **자산 보존의 법칙 검증**: 매일 `Total_Asset(t) = Cash(t) + Holdings_Shares(t) * Close(t)` 공식이 성립하는지 확인하여 자금 유실 버그 검증.
- **거래 정합성**: 매수/매도 발생 시 `Cash`의 변동이 `Shares * Price` 및 수수료/슬리피지(설정 시)와 정확히 일치하는지 확인.
- **Baseline A 일치 확인**: 초기 자금을 100% 매수하고 익절 및 MA 매도를 비활성화했을 때, 결과가 Baseline A(초기 일괄투자)의 성과와 일치하는지 체크.
- **일상한 검증**: 임의의 날짜에 집행된 총 매수 금액이 설정값(기본 $1,000)을 초과한 이력이 존재하지 않는지 전수 검증.

## Action items
- [x] antigravity: 설계 권장안 작성 완료
