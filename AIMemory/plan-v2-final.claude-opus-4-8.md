# v2 FINAL 설계 + 계약 + 분해 (코어+위성 추세추종)

**By**: claude-opus-4-8 (manager) — opencode/antigravity/자체 제안 수렴 / 2026-06-19
**근거**: requirements-v2 + v2-proposal.{opencode,antigravity,claude-opus-4-8}

## A. 확정 설계
### A1. 구조: 코어(Core) + 위성(Satellite)
- 자본 $10,000. **코어 = core_ratio**(기본 0.30) 비중은 **1일차 매수 후 절대 안 팖** → 모든 반등 초기 자동 포착.
- 위성 = 나머지. 추세 레짐에 따라 시간기반 분할 인/아웃.

### A2. 레짐(국면) 판정 — 비대칭(느린 청산·빠른 재진입)
- ma_fast=50, ma_slow=200.
- **하락(bear) 진입(느림·강건)**: `close<ma_slow AND ma_fast<ma_slow`(데드크로스 확증).
- **(선택) 빠른 선행 청산**: `dd_from_high(252d) > dd_threshold`(기본 0.20) — 레버리지 급락 조기 회피. ablation 토글.
- **회복(재진입, 빠름)**: `close>ma_fast` 가 recovery_days(기본 3) 연속.
- 미래참조 금지(전 지표 rolling, t시점 가용 데이터만).

### A3. 분할 인/아웃 (정밀타이밍 지양)
- 하락 전환 시 위성을 **sell_days(기본 3)일 균등 청산**. instant_sell(=1) ablation.
- 회복 전환 시 위성을 **buy_days(기본 3)일 균등 재매수**(현금/buy_days/일, 목표=위성목표 도달/현금소진). slow_reentry(=10) ablation.
- 청산 도중 회복 신호 오면 잔여 청산 중단→재매수 전환(상태 전이).

### A4. (선택) 과열 현금화 — ablation
- `close/ma_slow > overheat_ratio`(기본 1.4) → 위성 절반 현금화. `close/ma_slow < cool_ratio`(1.2)면 재매수.

### A5. 목표·비교·검증
- 기간 **2011-06-19~2026-06-19(15년)**, 자본 $10,000.
- 비교군(동일 15년): **lumpsum**(목표: 이기기), dca100, 참고로 v1-full.
- 지표: total_return, cagr, mdd, ann_vol, sharpe, sortino, exposure, avg_cash, trades, final_value + **excess_vs_lumpsum**(초과수익, O/X).
- 과적합 경계: 파라미터 라운드넘버, best 1개 단정 금지(강건 구간 제시).

## B. 인터페이스 계약 (v1 인프라 재사용, v1 파일은 수정 금지)
### B1. 신규 파일
- `backtest/engine/indicators_v2.py` — `annotate_v2(df, params) -> df(+컬럼)`
- `backtest/engine/strategy_v2.py` — `run_strategy_v2(df, params, ablation_overrides=None) -> BacktestResult`
  - `BacktestResult`는 `from backtest.engine.strategy import BacktestResult` 재사용(중복정의 금지).
- `backtest/ablation_v2.py` — ABLATIONS_V2 + run_all_v2(15yr 풀런 → output/results_v2.csv)
- `backtest/main_v2.py` — CLI(argparse): --config --ablation --start --end + 파라미터 override.
- 기존 loader.py/metrics.py/baselines.py/plot.py/strategy.py(v1)/indicators.py(v1)는 **재사용만, 수정 금지**.

### B2. 신호 계약 — annotate_v2가 추가하는 컬럼
`ma_fast, ma_slow, dead_cross(bool), golden_cross(bool), high_252(float), dd_from_high(float 0~1),
regime_bear(bool: close<ma_slow & ma_fast<ma_slow), dd_exit(bool: dd_from_high>dd_threshold),
recovery(bool: close>ma_fast recovery_days연속), overheat(bool: close/ma_slow>overheat_ratio),
cooled(bool: close/ma_slow<cool_ratio)`. 전부 t시점 정보만.

### B3. 파라미터 스키마 — config_v2.yaml (또는 기존 config에 v2 섹션)
```yaml
ticker: QLD
initial_capital: 10000
start: 2011-06-19
end: 2026-06-19
v2:
  ma_fast: 50
  ma_slow: 200
  recovery_days: 3
  core_ratio: 0.30
  sell_days: 3
  buy_days: 3
  dd_threshold: 0.20
  overheat_ratio: 1.40
  cool_ratio: 1.20
```

### B4. 엔진 상태/규칙 (strategy_v2)
- 상태: cash, shares, core_shares(불변), satellite 목표/진행, 분할 진행 카운터, 레짐(on/off), 과열 플래그.
- 1일차: 코어 매수(core_ratio*capital) + 위성 스케일인 개시(risk-on 가정, close≥ma_slow면).
- 매일: 레짐 전이 판정 → 분할 청산/매수 진행. 과열(enabled)면 위성 절반 현금화→cooled시 복귀.
- ablation_overrides 플래그: `disable_core(core_ratio=0), disable_overheat, disable_dd_exit,
  instant_sell(sell_days=1), slow_reentry(buy_days=10), lump_cashout(core_ratio=0 & 청산 시 위성 전량 즉시)`.

### B5. ABLATIONS_V2
v2-full / no-core / core-50 / no-overheat / no-dd-exit / instant-sell / slow-reentry / lump-cashout
+ 비교군: lumpsum, dca100, (참고) v1-full. 전부 동일 15년.

## C. 분해 (Wave 1 병렬, 서로 다른 신규 파일 → 충돌 없음)
- **U-V2-IND → antigravity**: `indicators_v2.py`(B2 계약). 합성 fixture로 미래참조無·지표정확 자체 검증.
  (clean 핸드오프: 환경 언급 0, "pip 금지 python3만", 정확 스펙 제공.)
- **U-V2-ENGINE → opencode**: `strategy_v2.py`(B4, 최난도 상태머신). 합성 fixture(레짐 전이·코어불변·분할)로 자체검증.
- **Wave 2(수렴 후)**: ablation_v2 + main_v2 + 15yr 풀런 + lumpsum 대비 리포트(opencode).
