# plan — 매달 $300 적립(정기 납입) 4전략 비교

**By**: claude-opus-4-8 (manager) / 2026-06-19
**Re**: 사용자 요청 — 일괄 $10k 가정을 버리고 "매달 $300 예산"으로 바꿔 4가지 비교

## 가정 변경(핵심)
- 자본이 t0에 한 번에 들어오지 않고 **매달 $300**씩 유입.
- 비교 기간: **2011-01 ~ 2026-06**(15년, v3 레짐이 TQQQ 2010-02 상장 이후만 가능 → 통일).
- 총 납입금은 4전략 **동일**($300 × 월수). 차이는 "들어온 돈을 언제/어떻게 굴리나"뿐.
- 공정성: 4전략 모두 매달 $300 전액을 결국 투입(daily도 $300 전부를 그 달 거래일에 분산). 성과지표 = **최종 평가액**(동일 납입 스케줄이므로 직접 비교 가능) + MWRR/IRR + MDD.

## 비교 대상 4
1. **즉시 B&H**: 매달 $300 들어오면 그 즉시 QLD 매수, 영구 보유.
2. **일 분할(하루 ~$10)**: 그 달 $300을 그 달 거래일에 **균등 분산** 매수(literal $10/day는 월 ~$210로 과소투입이라 비교 불공정 → 전액 균등분산으로 통일하고 사용자에게 명시).
3. **앞 전략(v1 규칙 타이밍)**: 들어온 현금을 모았다가 규칙(ATH 분할매수·전저점 반등매수·200MA 하락 매도·익절)대로 집행.
4. **v3 추천(레짐 스택)**: QQQ 200MA 레짐으로 TQQQ(3x)/QLD(2x)/현금 배분 + 보조로 듀얼모멘텀.

## 인터페이스 계약 (신규 파일만 — 기존 v1/v2 수정 금지)
### 엔진 (opencode 소유): `backtest/contrib.py`
- `make_contributions(index, monthly=300.0) -> pd.Series` : 매월 첫 거래일에 $300, 그 외 0.
- `run_contrib(prices_df, decide_fn, monthly=300.0, name="", cost=0.0) -> BacktestResult`
  - prices_df: index=거래일, 컬럼=티커 close(단일자산이면 "QLD" 컬럼).
  - 매일: 당일 납입금을 cash에 더함 → `decide_fn(ctx)` 호출 → 주문 집행 → equity 기록.
  - `ctx`(decide_fn 인자): `.i`(int) `.date` `.cash`(float) `.shares`(dict t->int) `.price`(dict t->float, 당일) `.contrib_today`(float) `.equity`(float) `.prices`(전체 df, **i까지만 사용 — 미래참조 금지**).
  - `decide_fn(ctx) -> dict{ticker: signed_dollars}` (+매수/−매도). 엔진이 매수는 가용현금, 매도는 보유주로 클램프, 정수주, cash≥0.
- 동봉 전략: `decide_immediate`, `decide_daily`(그 달 잔여거래일 균등분산), `decide_rule_v1`(기존 indicators.annotate_signals 재사용해 QLD 신호 → 모은 현금으로 트랜치 매수/규칙 매도).
- BacktestResult는 `from backtest.engine.strategy import BacktestResult` 재사용.

### v3 배분 (antigravity 소유): `backtest/contrib_v3_alloc.py`
- 위 `ctx` 계약을 따르는 `decide_v3_regime(ctx)` + `decide_dual_momentum(ctx)`.
- prices_df는 QQQ/QLD/TQQQ 3컬럼 가정. QQQ로 200MA·ratio·12mo모멘텀 산출(i까지만). 모은 현금+보유분을 목표 자산으로 이동(레짐: ratio>1.15→TQQQ, >1.0→QLD, else 현금 / DM: 12mo 1위).

### Wave2 (opencode): `backtest/contrib_run.py`
- 캐시에서 QLD/QQQ/TQQQ 로드 → 2011~2026 정렬. 4전략 monthly=$300 실행.
- 지표(최종액·총납입·MWRR/IRR·MDD·연변동성) → `output/results_contrib.csv`, equity 플롯, `output/report_contrib_ko.txt`(한국어, 가로표 금지).

## Wave
- W1 병렬: opencode=contrib.py(엔진+전략1·2·3, 합성 fixture 자체검증) / antigravity=contrib_v3_alloc.py(전략4, ctx 스텁으로 자체검증).
- W2: opencode=contrib_run.py 통합 실행+리포트.
- 매니저: 워커 산출물 독립검증(납입 스케줄 동일·미래참조 없음·cash≥0·최종액 교차확인).
