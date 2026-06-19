# v3 FINAL — buy&hold를 이기는 능동매매 (멀티에셋 레버리지) + OOS 검증

**By**: claude-opus-4-8 (manager) / 2026-06-19 / 3제안 수렴

## A. 확정 — 구현할 전략 3종 (저오버핏·구조적 근거)
레버리지는 **마진 아님**: 실제 ETF로 노출 확보 — QLD(QQQ×2), TQQQ(QQQ×3), 현금. (필요시 SQQQ 제외)
1. **DM (Dual Momentum)**: 매월 말, {QQQ, QLD, TQQQ, CASH} 중 **최근 12개월 수익률 1위** 100% 보유.
   1위가 CASH(=0%)보다 낮으면 CASH. (단일 파라미터 lookback=12mo, 학술: Antonacci)
2. **REG (QQQ 레짐 + TQQQ 스택)**: 일/주 단위. QQQ>200MA & QQQ/200MA>1.15 → TQQQ(노출~300%);
   QQQ>200MA → QLD(200%); else CASH. (Faber TAA. 파라미터: 200MA, 1.15)
3. **VT (변동성 타겟팅)**: 목표연변동성 T(기본 0.30)/QQQ20일실현변동성 = 노출배수(상한 3.0).
   배수를 QLD(2x)/TQQQ(3x)/현금 블렌드로 매핑. 일 리밸런스.

## B. 비교/검증 (오버핏 방지 — 필수)
- 기본 기간: **2010-02-11~2026-06-19**(TQQQ 상장 이후; 2006~2010은 TQQQ 부재로 제외, 정직히 명시).
- **OOS 분할**: 설계 직관 점검용 2010-2018 / 검증 2018-2026 — 두 구간 각각 buy&hold 대비.
- **다른 자산군 전이**: 동일 로직을 SPY신호→SSO(2x)/UPRO(3x)에 적용(SSO 2006, UPRO 2009 → 2010~ 사용).
- 비교군: QLD lumpsum, QLD dca100(동일 기간). 성공정의 = **여러 기간·자산에서 일관 초과**(단일 승리=불채택, 보고에 명시).
- 거래비용 민감도: 0%/0.05% 두 케이스. 지표: 기존 metrics + excess_vs_lumpsum.

## C. 인터페이스 계약 (멀티에셋, v1/v2 파일 수정 금지·신규만)
### C1. 신규 파일
- `backtest/data/loader_multi.py` — `load_many(tickers, start, end, cache_dir) -> dict[str,pd.Series]`(close),
  + `align(prices) -> pd.DataFrame`(공통일 inner-join, 컬럼=티커). yfinance 캐시 재사용.
- `backtest/engine/strategy_v3.py` — 멀티에셋 엔진 + 3 allocator:
  - `run_allocation(prices_df, weight_fn, params, rebalance='M'|'D', cost=0.0) -> BacktestResult`
    (각 리밸런스일 weight_fn이 목표가중 dict 반환 → 체결, 현금=1-Σw, equity 추적). BacktestResult 재사용.
  - `w_dual_momentum(prices_df, t, params)`, `w_regime_stack(...)`, `w_vol_target(...)` — 각 t시점 목표가중(미래참조 금지).
- `backtest/ablation_v3.py` + `backtest/main_v3.py` — 전략×기간×자산 매트릭스 실행 → output/results_v3.csv.
- 기존 loader/metrics/baselines/plot 재사용.

### C2. weight_fn 계약
`weight_fn(prices_df, i, params) -> dict{ticker: weight}` (weight≥0, Σ≤1; 나머지 현금). i시점까지 데이터만 사용.
DM은 월말에만 갱신(그 외 유지), REG/VT는 매일.

### C3. 엔진 규칙
- 자본 $10,000. 리밸런스일에 목표가중으로 정수주 근사 체결(잔여 현금). cost>0이면 |turnover|×cost 차감.
- equity=Σ(shares_t*price_t)+cash. 음수 없음. 미래참조 없음(weight_fn은 i까지만).

## D. 분해 (Wave 1 병렬, 신규 파일 → 충돌 없음)
- **U-V3-DATA → antigravity** (clean, env-free): `loader_multi.py`(load_many+align) + 신호헬퍼
  (12mo momentum, 200MA ratio, 20d realized vol) — 순수 데이터/지표. 합성·실데이터 자체검증.
- **U-V3-ENGINE → opencode**: `strategy_v3.py`(run_allocation + 3 weight_fn). 합성 멀티에셋 fixture로
  자산보존·미래참조·레버리지(TQQQ)·리밸런스 검증.
- **Wave 2 (수렴 후, opencode)**: ablation_v3 + main_v3 + 전 매트릭스 풀런(기간×OOS×자산×비용) +
  results_v3.csv + 플롯 + 한국어 리포트(어느 전략이 어느 조건에서 robust하게 buy&hold 초과하는지, 오버핏 경고 포함).
