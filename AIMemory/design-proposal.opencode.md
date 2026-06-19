# QLD 백테스트 설계 제안 — opencode

**From**: opencode (worker)
**To**: manager
**Date**: 2026-06-19
**Type**: PROPOSE → ANSWER
**Ref**: 20260619-083716-10272-4807

---

## 1. 전고점/전저점 판단법

**권장: Confirmed Pivot (확정 고점/저점)**

| 항목 | 선택 | 근거 |
|------|------|------|
| 기법 | Confirmed Pivot (좌우 L일 lookback/lookforward) | ZigZag은 미래 종가에 따라 과거 pivot이 바뀜(repainting). Rolling swing은 단순 극값으로 잡음에 취약. Confirmed pivot은 고점 기준 좌우 L일 중 자신이 최대이면 확정 — 과거값이 미래에 바뀌지 않고, 매일 출렁임에 갱신되지 않음 |
| 윈도우 L | **20 거래일** (약 1개월) | QLD 변동성 2x 고려. 10↓ 너무 잦음, 40↑ 반응느림. 일단 20으로 시작 |
| 반전 임계값 | **5%** (고점→저점 또는 저점→고점 간 최소 변동) | ZigZag 계열 repaint 방지용 필터. Confirmed pivot + 최소 5% 변동 없으면 무시 |
| 최신 pivot 처리 | 미확정 구간은 `pending` 플래그로 관리 | 마지막 봉은 미래 좌우 확인 불가 → 백테스트 당일 기준 마지막 확정 pivot까지만 사용. 일자 루프에서 t일 시점에 t+L까지만 보고 확정된 pivot만 인정 |

**"매일 갱신 방지" 구현**: Confirmed pivot은 정의상 좌우 L일을 다 채워야 확정되므로, t일의 고점이 t+L일이 되어야 최종 확정됨. 따라서 일자별로 과거 pivot이 갑자기 바뀌는 repaint 현상이 없음. 또한 최소 변동 5%로 잡음 추가 차단.

```python
# 의사코드
def find_confirmed_pivots(close: pd.Series, L=20, min_move=0.05):
    # 좌우 L일 window 내 최대/최소 확인
    # 고점: t가 [t-L, t+L]에서 최대고, 이전 pivot 대비 min_move 이상 하락 후
    # 저점: t가 [t-L, t+L]에서 최소고, 이전 pivot 대비 min_move 이상 상승 후
```

---

## 2. 백테스트 엔진 아키텍처

### 파일 구성

```
backtest/
├── config.yaml              # 전략 파라미터 (n,m,a,b,c,d,e,f, 초기자본, 일상한)
├── data/
│   ├── loader.py            # yfinance 다운로드 + parquet 캐시
│   └── qld_cache.parquet    # 로컬 캐시 (재다운로드 방지)
├── engine/
│   ├── backtest.py          # 메인 루프 (일자별 state machine)
│   ├── portfolio.py         # Position, Cash, Trade 추적
│   ├── signals.py           # 신호 생성 (200MA, pivot, ATH, 익절)
│   └── ablation.py          # 변형별 config override + 일괄 실행
├── output/
│   └── results/             # CSV + 플롯 저장 위치
├── analyze/
│   ├── metrics.py           # CAGR, MDD, Sharpe 등 계산
│   └── plot.py              # 자산곡선 + 거래 마커
├── main.py                  # CLI 진입점 (argparse)
└── requirements.txt         # 의존성
```

### 데이터 로딩

```python
# loader.py
import yfinance as yf
import pandas as pd

def load_qld(cache_path="data/qld_cache.parquet", force_dl=False):
    if not force_dl and Path(cache_path).exists():
        return pd.read_parquet(cache_path)
    df = yf.download("QLD", auto_adjust=True)
    df.to_parquet(cache_path)
    return df
```

- parquet 캐시로 재현성 + 인터넷 불가시에도 실행 가능
- force_dl=True 주면 갱신

### 엔진: 일자 루프 (state machine)

**권장: 순수 pandas 일자 루프** (backtrader/vectorbt 비권장)

| 라이브러리 | 판단 |
|-----------|------|
| backtrader | 복잡한 전략에 유연하나, 간단한 규칙 기반에는 오버헤드. 의존성 무거움 |
| vectorbt | 벡터화 빠르나, 상태(트랜치 보유/리셋/이월) 표현이 어려움. 디버깅 어려움 |
| **순수 pandas + numpy** | 의존성 최소, 재현성 최고, 디버깅 쉬움. 17년 일자 루프는 QLD 단일종목에 충분히 빠름 |

포트폴리오 상태는 NamedTuple + dict로 관리:

```python
# portfolio.py
@dataclass
class PortfolioState:
    cash: float          # 현금 잔고
    shares: int          # 보유 주식 수
    avg_cost: float      # 평균 매수 단가
    pending_buys: list   # 이월된 매수 요청
    tranches: list       # 각 트랜치의 매수일·수량·단가
```

### 파라미터 전달 (하드코딩 금지)

```
python main.py --config config.yaml --ablation full
python main.py --config config.yaml --ablation no-200ma
python main.py --config config.yaml --ablation no-ath-buy
```

config.yaml:
```yaml
initial_capital: 10000
daily_buy_limit: 1000
tranche_size: 1000
params:
  n: 5
  m: 0.5
  a: 10
  b: 15
  c: 20
  d: 40
  e: 10
  f: 20
pivot_window: 20
pivot_min_move: 0.05
```

main.py는 argparse로 config 경로 + ablation 변형명 + 기간(시작/종료)을 받음.

---

## 3. 자금·트랜치·일상한 상호작용 규칙

### 핵심 자료구조

- **트랜치 = $1,000 (고정)**. 총 4개 트랜치 (max 40% 노출)
- 각 트랜치는 `매수됨/매도됨/미매수` 상태를 가짐
- 트랜치가 매도된 후에는 재매수 가능? → **익절/하락장축소로 매도된 트랜치는 리셋되어 재매수 가능**
- 단, 동일 트랜치가 같은 날 재매수되지 않도록: 매수는 장 종료 시점에 처리, 매도도 장 종료 시점에 처리

### 우선순위 규칙 (같은 날 여러 신호 발생 시)

1. **하락장 축소** (200MA n일 하회 → 50% 매도)가 가장 우선: 매도 후 현금 확보
2. 매도 후 남은 현금으로 **매수 신호 처리**: ATH 매수 → 전저점 매수 순으로
3. **익절 매도**: 보유 트랜치 중 평단 대비 조건 달성 시 매도. 하락장 축소와 같은 날이라면 하락장이 우선
4. **같은 날 매수와 매도가 모두 발생**: 매도 먼저 실행 → 현금 증가 → 매수 실행

### 일상한 이월 규칙

- 당일 목표 매수액 = 조건 달성한 미매수 트랜치 수 × $1,000
- 이 금액이 $1,000 초과 시 → 나머지는 `pending_buys` 큐에 저장
- 이후 거래일마다 $1,000 한도 내에서 pending → 실행 (가격 조건이 여전히 유효한지 재확인)
- pending이 5일 이상 지속되면 해당 트랜치는 만료(시장 상황 변동 반영)

### 트랜치 리셋 시점

- 익절 매도된 트랜치: 즉시 미매수 상태로 리셋, 다음 신호에서 재매수 가능
- 하락장 축소로 매도된 주식: m% 비율 매도이므로 특정 트랜치 단위가 아님. 잔여 트랜치는 그대로 유지
- 대형 하락장 종료 판단(200MA 재돌파) 시 → 축소된 비중을 다시 매수할지는 설계 이슈 (일단은 별도 규칙 없이 자연스럽게 매수 신호 따라감)

---

## 4. Ablation 매트릭스

### 최소 변형 (A–H)

| ID | 변형명 | 규칙 on/off | 의미 |
|----|--------|------------|------|
| A | `full` | 전부 on | 기준 전략 |
| B | `no-200ma` | 하락장 축소 off | 200MA 보호 없음 |
| C | `no-ath-buy` | ATH 분할매수 off | 전고점 매수 없음 |
| D | `no-prevlow-buy` | 전저점 매수 off | 전저점 매수 없음 |
| E | `no-takeprofit` | 익절 off | 익절 없음 (팔지 않음) |
| F | `only-200ma` | 하락장 축소만 on | 단일 규칙 효과 |
| G | `only-ath` | ATH 매수만 on | 단일 규칙 효과 |
| H | `only-prevlow` | 전저점 매수만 on | 단일 규칙 효과 |

### 비교군 (I–J)

| ID | 변형명 | 내용 |
|----|--------|------|
| I | `buy-hold` | 1일차 $10,000 전액 QLD 매수 |
| J | `dca-100` | $10,000 → 100분할 $100, 전체기간 균등분할 매수 |

Ablation 실행: `ablation.py`가 config를 읽어 각 변형별로 override dict를 생성 → engine 호출

```python
ablations = {
    "full": {},
    "no-200ma": {"disable_200ma_sell": True},
    "no-ath-buy": {"disable_ath_buy": True},
    ...
}
```

---

## 5. 지표·결과물·검증

### 성과 지표

| 지표 | 계산법 | 용도 |
|------|--------|------|
| 총수익률 | (최종자산 - 초기자본) / 초기자본 | 절대 성과 |
| CAGR | (최종자산/초기자본)^(1/년수) - 1 | 연환산 수익률 |
| MDD | 일별 피크대비 낙폭 최대값 | 최대 손실 위험 |
| Sharpe | (일별수익률 평균 - 0) / 일별수익률 표준편차 × sqrt(252) | 무위험 0% 가정 위험조정수익 |
| 연 변동성 | 일별수익률 표준편차 × sqrt(252) | 리스크 크기 |
| 시장노출시간% | 보유일수 / 전체거래일수 | 현금비중 실현 |
| 최종평가액 | 마지막 날 현금 + 주식×종가 | 절대 결과 |
| 거래횟수 | 매수+매도 총 횟수 | 전략 활동성 |
| 평균 현금비중 | 일별 현금비중 평균 | 보수성 측정 |

### 산출물

1. **CSV**: `results/{ablation_name}_metrics.csv` — 모든 변형 × 모든 지표 (열: 변형명, 행: 지표)
2. **CSV**: `results/{ablation_name}_trades.csv` — 각 변형의 개별 거래 내역
3. **플롯**: `results/equity_curve.png` — 모든 변형+비교군 자산곡선 중첩
4. **플롯**: `results/drawdown.png` — MDD 시각화
5. **한국어 요약 리포트**: stdout으로 출력 (세로 key:value, 가로표 금지)

### 검증 (sanity check)

| 검증 항목 | 방법 |
|-----------|------|
| 현금 불일치 | 초기자본 - 총매수액 + 총매도액 = 최종현금 (정합성) |
| MDD ≥ 0 | MDD가 음수면 버그 |
| CAGR 부호 일관성 | 총수익률과 CAGR 부호 일치 |
| 거래일 정렬 | 모든 거래가 거래일 범위 내, 역정렬 없음 |
| 트랜치 중복 | 같은 날 동일 트랜치 중복 매수 없음 |
| buy-hold 비교 | buy-hold의 최종 주식 수 = 초기자본/1일차종가 × 1일차종가 등 (단순 검증) |

---

## 요약 (key:value)

```
권장 pivot 기법: Confirmed pivot (L=20, min_move=5%)
엔진: 순수 pandas 일자 루프 (state machine)
의존성: pandas, numpy, yfinance, matplotlib, pyyaml
하드코딩 금지: config.yaml + argparse
트랜치: 4개 × $1,000, 매도 시 리셋 가능
일상한 초과분: pending 큐 → 이후 일자로 이월 (5일 만료)
Ablation: 10개 변형 (A-J), ablation.py로 일괄 실행
검증: 6개 sanity check 포함
```
