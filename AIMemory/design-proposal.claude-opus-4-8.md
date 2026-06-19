# 설계 제안 (manager 자체안) — QLD 백테스트

**By**: claude-opus-4-8 (manager)
**날짜**: 2026-06-19

## 1. 전고점/전저점 판단 — confirmed swing pivot (권장)
- **방법**: lookback/lookforward 둘 다 두는 **확정 스윙 피벗(fractal pivot)**.
  - swing high = 어떤 봉의 고가가 좌우 각 `W`일보다 모두 높을 때 → 그 지점이 전고점 후보.
  - 확정은 lookforward 때문에 `W`일 **지연**되어 확정(미래참조 방지: 백테스트 t시점에선
    t-W 이전에 확정된 피벗만 사용).
- **파라미터 기본값**: `W = 20거래일`(약 1개월). 너무 잦은 갱신 방지 요구 충족.
- **"전고점(ATH)" 해석**: 규칙2의 ATH는 글로벌 ATH(확정 피벗 중 최대) 또는 단순 누적최고가.
  레버리지 ETF 특성상 **누적 최고 종가(running max)** 를 ATH로 쓰되, 분할매수 트리거 재무장은
  새 확정 스윙으로 갱신. 전저점은 **직전 확정 swing low**(running min 아님 — "전저점 대비 반등"
  의미).
- 대안: ZigZag(반전 임계 `θ=10%`). 단순하지만 임계 의존적. confirmed pivot을 1순위로.

## 2. 엔진 아키텍처 — 순수 pandas + 일자 이벤트 루프
- 의존성 최소: `pandas`, `numpy`, `yfinance`, `matplotlib`. backtrader/vectorbt 미사용
  (규칙이 경로의존적·상태기반이라 명시적 이벤트 루프가 검증·디버깅에 유리).
- 파일 구성:
  - `data.py` — yfinance 다운로드 + `AIMemory/tmp/` 캐시(parquet/csv), 조정종가.
  - `indicators.py` — 200MA, swing pivot(전고/전저), ATH running-max.
  - `strategy.py` — 신호전략 일자 루프(상태: 보유주수/현금/평단/트랜치 플래그/일상한 큐).
  - `baselines.py` — lump-sum, 1/100 DCA.
  - `metrics.py` — 총수익·CAGR·MDD·Sharpe·노출시간·거래수.
  - `run.py` — CLI(argparse): 파라미터·기간·자본·일상한·ablation 플래그. 하드코딩 0.
  - `config.yaml` 또는 CLI 기본값으로 n=5,m=50,a=10,b=15,c=20,d=40,e=10,f=20.
- 출력: `output/results.csv`(변형×지표), `output/equity_*.png`, `output/report.md`.

## 3. 자금·트랜치·일상한 규칙 (모호점 해소안)
- 자본 $10,000. 매수 트랜치 4개 각 목표 $1,000(=10%).
- **일상한 큐**: 어떤 날 트리거로 발생한 목표 매수액을 큐에 적재. 매일 `min(잔여목표, $1,000,
  보유현금)` 만큼 종가로 체결. 트리거 가격 조건이 깨지면(가격이 트리거 위로 회복) 잔여 큐 취소.
- **동시 트리거 우선순위**: 더 깊은 하락(=-b > -a, +f > +e 깊은가격) 먼저. 큐는 FIFO+우선순위.
- **트랜치 재무장**: 각 트랜치는 1회성 — 한 번 채우면 비활성. **익절로 전량 정리되거나 새 확정
  스윙(전고/전저 갱신)이 나오면 리셋**해 다음 사이클 재매수 허용. (리셋 규칙은 ablation 변수로도 가능)
- **익절**: 평단 +20% → 보유주수의 50% 매도(1차), +40% → 잔량 매도(2차). 매도 후 평단 유지.
- **하락장 축소**: 200MA 5일연속 하회 → 보유주수 50% 매도(중복발동 방지: 재무장은 200MA 회복 후).

## 4. Ablation 매트릭스
- V0 baseline-lump, V1 baseline-DCA100
- S-full(전체)
- S-no200(하락장축소 off)
- S-noATHbuy(규칙2 off)
- S-noPrevLowBuy(규칙3 off)
- S-noTakeProfit(규칙4 off)
- S-onlyATHbuy / S-onlyPrevLowBuy(단일규칙) — 기여도 확인
- (선택) 파라미터 민감도: n,a,b 격자 1~2개

## 5. 지표·검증
- 지표: TotalReturn, CAGR, MDD, Vol(연), Sharpe, Sortino, 시장노출%, 거래수, 평균현금%.
- sanity check: lump-sum CAGR이 QLD 실제 장기수익과 부합하는지, 미래참조 없는지(피벗 지연 확인),
  현금<0 없는지, 주수<0 없는지 단위테스트.
