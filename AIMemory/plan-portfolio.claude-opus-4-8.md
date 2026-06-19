# plan — 장-성격 적응형 다자산 포트폴리오(4~10종목) vs 기존 5전략

**By**: claude-opus-4-8 (manager) / 2026-06-19
**Re**: 사용자 — QLD 단일 대신 4~10개 ETF를 장 성격에 따라 섞어 더 높은 수익 추구, 위 방법들과 비교

## 핵심 설계 (매니저 확정, 이전 수렴 제안 기반)
- 단일 76x 강세장(QLD)을 **원수익**으로 이기긴 어렵다. 그래서 (a)강세장엔 3x 슬리브(TQQQ/UPRO)로 노출↑, (b)약세장엔 현금이 아니라 방어자산(TLT/GLD)으로 수익·복리기반 보존 → 원수익+위험조정 모두 노린다.
- 엔진 재사용: `run_contrib`는 이미 멀티에셋(decide_fn이 dict{ticker:signed_dollars}). 단, **리밸런싱 정확성 위해 엔진을 '매도 먼저, 매수 나중' 2패스로 보정**(현재는 컬럼순 처리라 매수가 현금부족으로 과소체결될 수 있음). 하위호환(단일자산·immediate/daily/rule_v1 영향 없음).

## 유니버스 (8 ETF, 전부 2011~2026 공통구간 확보)
QQQ, SPY, QLD(2x), SSO(2x), TQQQ(3x), UPRO(3x), TLT(장기국채), GLD(금)

## 비교 기간/조건
- 2011-01 ~ 2026-06, 매월 $300 적립(기존과 동일 스케줄·동일 인덱스).
- 비용 0% / 0.05% 2세트. **OOS 분할: 2011-2018 / 2018-2026** 각각도 산출(과적합 점검).
- 지표: final_value, MWRR(연), MDD, ann_vol, **Sharpe근사=MWRR/ann_vol**, end_cash, n_trades, vs_immediate_pct.

## 신규 포트폴리오 전략 (decide_fn, 월 리밸런싱, factory-closure로 last_month 상태 보유 — 전역 reset 불필요)
- **P1 regime_basket** ⭐: 위험-ON(QQQ>200MA AND SPY>200MA) → 레버리지주식 바스켓 {TQQQ,UPRO,QLD,SSO} 역변동성 가중. 위험-OFF → 방어 {TLT,GLD} 역변동성. (현금 최소화)
- **P2 xsec_momentum**: 매월 8자산 블렌드 모멘텀(3·6·12개월 평균수익률) 상위 top_n=3 보유(역변동성 가중), 모멘텀>0인 것만, 부족분 현금.
- **P3 static_lev**: 고정 {TQQQ:0.40, UPRO:0.30, TLT:0.15, GLD:0.15} 월 리밸런싱(타이밍 無 분산 베이스라인).
- 공통 헬퍼: `_inv_vol_weights(ctx,tickers,win=60)`(1/실현변동성 정규화, NaN/데이터부족 스킵), `_rebalance_orders(ctx,target_w)`(order=w*equity - 보유평가; 유니버스 전체에 대해 0포함 → 비목표 청산).
- 모두 ctx.prices i까지만 사용(미래참조 금지), 데이터부족 초기엔 안전(현금/스킵).

## 인터페이스 계약 (신규 파일만, v1/v2 수정 금지)
- `backtest/data/loader_multi.py` (antigravity): `load_many(tickers, start=None,end=None,cache_dir="backtest/data/cache")->dict[str,Series]`(기존 load_prices 재사용, close만) + `align(prices)->DataFrame`(inner-join, 컬럼=티커, dropna, 오름차순).
- `backtest/portfolio_alloc.py` (opencode): 위 3 decide_fn 팩토리(`make_regime_basket(params=None)`, `make_xsec_momentum(params=None)`, `make_static_lev(params=None)`) + 헬퍼. 합성 멀티에셋 fixture 자체검증.
- `backtest/contrib.py` run_contrib **2패스(매도→매수) 보정** (opencode).
- `backtest/portfolio_run.py` (opencode Wave2): 8티커 align→2011~2026, 3 포트폴리오 + 기존 5전략 동일조건 재실행 + OOS분할 + 비용2세트 → `output/results_portfolio.csv`, `output/equity_portfolio.png`, `output/report_portfolio_ko.txt`(한국어, 세로 key:value, 가로표 금지).

## Wave
- W1 병렬: antigravity=loader_multi.py(8티커 load+align, 공통구간 검증) / opencode=portfolio_alloc.py(3전략+헬퍼) + contrib.py 2패스보정 (둘 다 자체 RUN 검증).
- W2: opencode=portfolio_run.py 풀런+OOS+리포트.
- 매니저: 독립검증(미래참조·cash≥0·리밸런싱 정확·OOS 일관성·immediate 교차확인). 강세장 원수익 한계/과적합 솔직 명시.
