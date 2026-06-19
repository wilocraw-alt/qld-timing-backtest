# FINAL 설계 + 인터페이스 계약 + 분해 — QLD 백테스트

**By**: claude-opus-4-8 (manager) — opencode/antigravity/자체 제안 수렴
**날짜**: 2026-06-19
**근거**: requirements.claude-opus-4-8.md + design-proposal.{opencode,antigravity,claude-opus-4-8}.md

## A. 확정 설계 (수렴 결과)

### A1. 전고점/전저점
- **전고점(ATH)** = 시점 t까지 **누적 최고 종가(running max of adj close)**. repaint·미래참조 없음.
  -a/-b 매수 트리거: `Close_t <= ATH_t*(1-a/100)` / `*(1-b/100)`.
- **전저점** = **확정 스윙로우(confirmed swing low)**: 좌우 각 `L`일(기본 L=10, 총 윈도우 2L=20)에서
  중앙봉이 최저 종가이면 그 날을 저점으로 확정. **확정은 lookforward L일 지연** → 일자 루프 t시점에는
  `t-L` 이전에 확정된 저점만 사용(미래참조 차단). **min_move=5%** 필터(직전 확정저점 대비 5% 미만 변동
  무시)로 잡음 억제. +e/+f 매수 트리거: `Close_t >= ConfirmedLow*(1+e/100)` / `*(1+f/100)`.

### A2. 엔진
- 순수 **pandas + numpy** 커스텀 엔진. 지표는 **벡터화로 사전계산**(200MA, ATH, confirmed-low,
  트리거 불리언 칼럼), 자금/트랜치/이월 등 경로의존 로직은 **일자별 순차 루프**.
- 데이터: yfinance 조정종가, `backtest/data/cache/QLD.parquet` 로컬 캐시(없으면 다운로드).
- 파라미터: `config.yaml` + CLI override(argparse). 하드코딩 0.

### A3. 자금·트랜치·일상한 (모호점 확정)
- 자본 $10,000. 매수 트랜치 4개: T1(ATH-10%), T2(ATH-15%), T3(Low+10%), T4(Low+20%), 각 목표 $1,000.
- **트랜치 상태**: Inactive→(체결)→Active. Active면 매수신호 무시(중복매수 방지).
- **재무장(re-arm)**: (1) **전량청산(shares→0)** 시 전 트랜치 Inactive 리셋. (2) **새 ATH 경신** 시
  T1/T2 재무장, **새 확정저점 형성** 시 T3/T4 재무장 → 17년 다회 사이클 보장. (config: `rearm_on_new_pivot`)
- **일상한 큐(FIFO)**: 신호 발생 시 트랜치 주문($1,000)을 큐 삽입(동일일 다중신호는 T1→T2→T3→T4 순).
  매 거래일 `min(잔여, $1,000, 현금)` 종가 체결. 체결 직전 **가격조건 재검증**(조건 이탈 시 주문 폐기).
  `pending_expiry_days=5` 경과 시 만료.
- **매도**: 익절 평단+c%→보유주수 50% 매도(1차), +d%→잔량 매도(2차). 하락장: 200MA를 n일 연속 하회→
  보유주수 m% 매도(재발동 방지: 200MA 회복 후 재무장).
- **같은 날 순서**: ①하락장축소 매도 ②익절 매도 ③매수 큐 체결(현금 갱신 후).

### A4. Ablation 변형 (11개)
full / no-200ma / no-ath-buy / no-prevlow-buy / no-takeprofit /
only-200ma / only-ath / only-prevlow / buy-only-no-sell /
baseline-lumpsum / baseline-dca100.

### A5. 지표·검증
- 지표: TotalReturn, CAGR, MDD, AnnVol, Sharpe(rf=0), Sortino, MarketExposure%, AvgCash%, TradeCount, FinalValue.
- sanity: 자산보존(Cash+Shares*Close 일별 일관), 일매수≤$1,000 전수, 미래참조 없음(피벗 지연 확인),
  Cash≥0·Shares≥0, baseline-lumpsum 교차검증.

## B. 인터페이스 계약 (모듈 간 합의 — 병렬 구현 가능하도록)

### B1. 디렉토리/파일
```
backtest/
├── config.yaml          # 파라미터 (아래 스키마)
├── main.py              # CLI: --config --ablation <name|all> --start --end --force-dl
├── data/loader.py       # load_prices(ticker, start, end, cache_dir, force_dl) -> DataFrame
├── engine/indicators.py # annotate_signals(df, params) -> DataFrame(+신호칼럼)
├── engine/portfolio.py  # PortfolioState dataclass + 체결 헬퍼
├── engine/strategy.py   # run_strategy(df_annotated, params, ablation) -> BacktestResult
├── engine/baselines.py  # run_lumpsum(df, cap) / run_dca(df, cap, n_slices) -> BacktestResult
├── analyze/metrics.py   # compute_metrics(result) -> dict
├── analyze/plot.py      # plot_equity(results, out), plot_drawdown(results, out)
├── ablation.py          # ABLATIONS dict + run_all(config) -> results.csv
├── requirements.txt
└── output/              # results.csv, equity.png, drawdown.png, report.txt
```

### B2. 데이터 계약 — `load_prices()` 반환 DataFrame
- index: `DatetimeIndex`(거래일, 오름차순, tz-naive). 컬럼: `close`(조정종가 float). (필요시 open/high/low/volume)
- 결측 없음, 중복일 없음.

### B3. 신호 계약 — `annotate_signals(df, params)` 추가 컬럼
- `ma200`(float), `below_ma200_streak`(int 연속 하회일수),
- `ath`(float running-max close), `confirmed_low`(float, t시점 가용한 최신 확정저점; 없으면 NaN),
- `trig_t1`,`trig_t2`(bool, ATH -a/-b 도달), `trig_t3`,`trig_t4`(bool, Low +e/+f 도달),
- `new_ath`(bool 신고가 경신), `new_low`(bool 새 확정저점 형성).
- 모든 컬럼은 **t시점 정보만** 사용(미래참조 금지). confirmed_low는 L일 지연 확정.

### B4. 파라미터 스키마 — `params`(dict, config.yaml에서 로드)
```yaml
ticker: QLD
initial_capital: 10000
daily_buy_limit: 1000
tranche_size: 1000
pending_expiry_days: 5
rearm_on_new_pivot: true
pivot_lookback: 10        # L (총 윈도우 2L=20)
pivot_min_move: 0.05
strategy:
  n: 5    # 200MA 연속하회일
  m: 50   # 하락장 매도 비율(%)
  a: 10   # ATH -a% T1
  b: 15   # ATH -b% T2
  c: 20   # 평단 +c% 익절1(50%)
  d: 40   # 평단 +d% 익절2(잔량)
  e: 10   # Low +e% T3
  f: 20   # Low +f% T4
```

### B5. 결과 계약 — `BacktestResult`(dataclass)
- `equity: pd.Series`(일별 총자산, index=거래일), `cash: pd.Series`, `shares: pd.Series`,
- `trades: pd.DataFrame`(date, side[buy/sell], reason[t1/t2/t3/t4/tp1/tp2/ma200], shares, price, cash_after),
- `name: str`(변형명).
- `compute_metrics(result)` → `{total_return, cagr, mdd, ann_vol, sharpe, sortino, exposure, avg_cash, trades, final_value}`.

### B6. Ablation 계약 — `ABLATIONS: dict[str, dict]`
각 변형명 → params override(예: `{"disable_ma200_sell": True}`, `{"disable_ath_buy": True}` 등).
`strategy.run_strategy`는 override 플래그를 해석해 해당 규칙을 끈다.

## C. 분해 & 디스패치 (의존성 기준)
- **Wave 1 (병렬, 서로 다른 파일 → 충돌 없음)**:
  - **U-DATA+SIGNALS → antigravity**: `data/loader.py` + `engine/indicators.py`(+ B2/B3 계약 충족,
    합성 fixture로 자체 sanity). 가장 입력측, 독립.
  - **U-ENGINE → opencode**(최고 신뢰 워커, 최난도/최결합): `engine/portfolio.py`+`engine/strategy.py`
    (B3 신호 칼럼 계약을 입력으로 가정, 합성 fixture DataFrame으로 단위테스트).
- **Wave 2 (Wave1 반환 후 병렬)**: U-BASELINES+METRICS / U-ABLATION+CLI+config.
- **Wave 3**: 실제 QLD 풀런 + plot + 한국어 report.
- **Wave 4 (delegated VERIFY)**: sanity 전수 + baseline 교차검증 + 미래참조 점검.
