# 레버리지 ETF 적립·타이밍 전략 연구 — 종합 문서

> 본 문서는 이 저장소(`qld-timing-backtest`)에서 수행한 전체 연구 여정·발견·최종 전략·실행 도구를 한 곳에 정리한 마스터 문서입니다.
> **모든 수치는 과거 데이터 백테스트이며 투자 조언이 아닙니다. 거래비용·세금·슬리피지는 대부분 제외(실제 성과는 더 낮음).**

---

## 0. 한눈에 보기 (핵심 결론)

- **강세장(2011~2026)에서는** 타이밍·로테이션 전략이 단순 보유에 전부 패배했고, 더 번 것은 "레버리지를 계속 보유"한 경우뿐이었다. 단, 초과수익은 실력이 아니라 추가 위험의 대가(낙폭 확대)였다.
- **폭락장(2000 닷컴 시나리오)에서는 정반대** — 3배 레버리지 무방비 보유는 -97% 전멸(변동성 decay), 추세추종 타이밍은 +147~339%로 역전. **"시장 국면이 결론을 뒤집는다."**
- 따라서 **"강세에 올인"하지 말고 "틀려도 살아남게"** 설계하는 것이 핵심.
- 최종 추천: **SOXL 60%(120일선 ±3% 완충밴드 추세규칙) + QLD 40%, 매월 $300 소수점 적립·리밸런싱.** 무방비 3x 장기보유는 현재 확률 구조(붕괴·조정 우위)에서 기대값이 마이너스.

---

## 1. 목적과 데이터

- **목적**: 규칙 기반 투자시점/배분 전략을 백테스트로 검증하고, 강세·폭락 양 국면에서 buy&hold를 이길 수 있는지, 어떻게 위험을 관리할지 규명.
- **대상 자산**: QLD(나스닥100 2x), 확장으로 QQQ/SPY/SSO/TQQQ/UPRO/SOXL/TLT/GLD. 신호용 1x 지수 QQQ·SPY·SOXX.
- **데이터**: yfinance(adjusted close), parquet 캐시(`backtest/data/cache/`). 레버리지 ETF 상장 시점 제약 — TQQQ 2010-02, SOXL/SOXX 2010~. 기본 비교기간 2011-01~2026-06.
- **환경**: Python 3.8, pandas/numpy/yfinance/matplotlib/pyyaml. 멀티에이전트 오케스트레이션(aimux)으로 매니저(claude)가 워커(opencode·antigravity)에 분해 위임.

---

## 2. 연구 여정 (단계별)

### 2.1 v1 — 규칙 기반 타이밍 + Ablation
규칙: 200일선 n일 연속 하회 시 m% 매도 / ATH 대비 -a%·-b% 분할매수 / 전저점 대비 +e%·+f% 반등매수 / 평단 +c%·+d% 익절 / 일 매수상한. 전고·전저는 look-ahead 없는 확정 스윙피벗으로 판정.
- 비교군: 일괄매수(lumpsum), 1/100 분할(DCA). 항목별 on/off ablation.
- **결과**: 어떤 변형도 lumpsum을 못 이김. QLD가 2006~2026 약 100배 오른 장에서 현금 보유가 그대로 손해(현금 비중 81%). 일상한 제거·트랜치 스윕·익절 100/200% 등 실험도 결론 불변.
- 코드: `engine/indicators.py`, `engine/strategy.py`, `engine/baselines.py`, `ablation.py`, `main.py`, `experiments/`. 리포트: `output/report_ko.txt`, `experiments_ko.txt`.

### 2.2 v2 — 코어+위성 추세추종 (15년)
QQQ 레짐(이중MA·dd_exit·overheat) 기반 코어+위성 상태기계.
- **결과**: full v2 약 $305k(CAGR 25.6%, MDD 52% vs lumpsum 64%)였으나 여전히 lumpsum($806k/15yr) 미달. 2011~2026은 V자 반등이 잦아 추세추종이 불리.
- 코드: `engine/indicators_v2.py`, `engine/strategy_v2.py`, `ablation_v2.py`, `main_v2.py`. 리포트: `output/report_v2_ko.txt`.

### 2.3 정기납입($300/월) 4전략 비교
가정 변경: 일괄 $10k → **매월 $300**(2011~2026, 총납입 $55,800). 즉시 B&H / 일분할 / v1규칙 / v3추천(레짐·듀얼모멘텀).
- **결과(최종액)**: 즉시 QLD $1,097,738(MWRR 33.5%, MDD 63%) = 1위. 일분할 -0.8%, v1규칙 -13%, v3레짐 -52%, v3듀얼모멘텀 -54%. **로테이션·타이밍 전부 패배.** QLD 2011 $1.28 → 2026 $97.91(76배)라 시장이탈이 곧 손해.
- 코드: `contrib.py`(정기납입 엔진), `contrib_v3_alloc.py`, `contrib_run.py`. 리포트: `output/report_contrib_ko.txt`.

### 2.4 다자산 포트폴리오(8 ETF, 장-성격 적응)
P1 레짐바스켓 / P2 횡단모멘텀 / P3 정적분산 + 정적 레버리지 블렌드. OOS 분할(2011-18/18-26) + 거래비용 민감도.
- **결과**: 로테이션(P1/P2/v3) 전부 패배. 적립 QLD를 이긴 건 "레버리지 계속보유"뿐 — TQQQ100 $2.55M(+132%), TQQQ60/UPRO40 $1.70M(+55%), OOS 양 구간 일관. **단 초과수익은 순수 추가위험**(MDD 74~82% vs 63%, Sharpe 동률). 채권혼합(TLT)은 2022 금리인상기 비robust.
- 코드: `data/loader_multi.py`, `portfolio_alloc.py`, `portfolio_run.py`. 리포트: `output/report_portfolio_ko.txt`.

### 2.5 SOXL(반도체 3x) 포함
- **결과**: SOXL 단독 $7.998M(+629%, MDD 90%) 원수익 1위. **TQQQ50/SOXL50 $6.24M, Sharpe 0.67로 QLD(0.64) 초과** — 반도체·광범위기술주 분산효과. OOS 양 구간 1~3위(robust). 단 MDD 85~90% + 반도체 단일섹터 사후확신(hindsight) 위험.
- 리포트: `output/report_portfolio_ko.txt`(SOXL 반영), `report_easy_ko.md`(일반인용).

### 2.6 닷컴 위기 시나리오(2000)
포 호스맨(MSFT/INTC/CSCO/ORCL) 등가중 지수 1x vs 합성 3x. 고점 2000-03-10 기준 1년 전~3년 후. 초기 $10k.
- **결과**: B&H 1x -15% / **B&H 3x -97%(전멸, decay)** / DCA 3x -78%(완충) / **추세추종(200MA) 1x +147%·3x +339%(역전)**. 강세장 결론을 정반대로 뒤집음.
- 코드: `dotcom_scenario.py`. 리포트: `output/report_dotcom_ko.txt`.

### 2.7 패널 토의 — "AI 강세 지속 vs 닷컴 붕괴?"
멀티에이전트(opencode·antigravity·매니저) 개별 견해 → 종합.
- **종합확률(12~24개월)**: 강세지속 ~42% / 의미있는조정 ~38% / 닷컴급폭락 ~11% / 기타 ~9%. (비강세 58% > 강세 42%)
- 공통: 닷컴식 '전멸'은 낮음(이익·현금흐름 실재) but **사상 최고 시장집중도**가 최대 취약점. 트리거 = CapEx 회수 의문 / 금리 재상승 / 규제·전력병목.
- 리포트: `output/report_panel_ko.md`.

### 2.8 확률가중 전략 추천
패널 확률 × (강세 백테스트 + 닷컴 위기) 기대값.
- **EV**: QLD+추세이탈 +14.5% > 3x+추세이탈 +12.8% > 바벨 +12.0% > QLD보유 +11.5% > **무방비3x -1.0%(꼴찌)**.
- 무방비 3x는 **강세확률 75%+** 일 때만 1위 → 패널 42%와 거리 큼.
- 코드: `recommendation.py`. 리포트: `output/report_recommendation_ko.txt`.

### 2.9 120일선 + 휩쏘 완화 + 최종 전략
기준선 200→120일, 휩쏘(잦은 매매) 완화 변형 비교.
- **발견**: plain(매일 판정)은 166회 전환 = 휩쏘 참사(수익 반토막). **buffer±3%·monthly**가 휩쏘를 죽이고 무규칙보다 수익↑·낙폭↓.
- ⚠️ **매니저 독립검증이 함정 적발**: 두 패널이 추천한 'monthly+buffer 결합'은 과도필터로 최악(SOXL $2.2M/2022 -54%). **휩쏘필터는 하나만 사용**.
- 최종 결합 포트(SOXL60/QLD40) 실측: 4안 모두 '둘다 무규칙'(MDD 86%)보다 위험조정 우수(MDD 61~66%).
- 코드: `ma_whipsaw.py`, `final_strategy.py`. 리포트: `output/report_final_strategy_ko.md`(개별안+최종안).

### 2.10 소수점 리밸런싱 검증
- 소수점 + 매월/신호전환시 60:40 목표비중 리밸런싱이 정수주①보다 우수: **강세 $5.58M·MDD 56%**(vs $5.54M/61%), 2022 -2%(vs -8%), COVID +123%(vs +114%).

### 2.11 데일리 어드바이저 + cron + NYSE 휴장
최종 전략을 매일 실행해 "오늘 살 주식·수량"을 알려주는 실행 도구.
- `backtest/live/daily_advisor.py` + `advisor_config.yaml`: 전일 종가로 SOXX 120일선 ±3% 신호 판정 → 소수점 목표비중 리밸런싱 주문 출력. 상태 `state.json` 영속(주문 실행 가정), 실행 타임스탬프, **NYSE 휴장 캘린더(규칙기반)** 반영(휴장일 매매 보류).
- cron: `0 15 * * *`(매일 15:00 KST, 미국장 개장 전).

---

## 3. 최종 추천 전략 (검증 완료)

### 기본안 — SOXL 60% + QLD 40%, 매월 $300 소수점 적립
- **코어 60% SOXL(반도체 3x)**: 신호 SOXX **120일선 ±3% 완충밴드**. SOXX 종가가 120MA×1.03 위 → 보유, ×0.97 아래 → 현금, 사이 → 직전상태 유지(휩쏘 차단).
- **위성 40% QLD(나스닥 2x)**: 무규칙 항상 보유(V자 반등 완충).
- **집행**: 매월 첫 개장일 $300 유입, 매월·신호전환 시 60:40 소수점 리밸런싱(SOXL OFF면 코어→현금). 휴장일 보류.
- **성과(2011~2026 백테스트)**: 강세 $5.58M·MWRR 51.7%·MDD 56% / 2022 폭락 -2% / COVID +123%.

### 성향별 틸트
- **공격(강세 확신)**: SOXL monthly + QLD 무규칙 — 강세 $6.88M, 전환 최소. 단 2022 -25%.
- **방어(폭락 대비)**: SOXL·QLD 둘 다 buffer±3% — 2022 -2%, MDD 46%.

### 반드시 인지할 한계
- SOXX/SOXL은 2010~ 시작 → 2000 닷컴·2008 금융위기 OOS 미검증.
- 반도체 단일섹터 집중 + 사후확신 위험(AI 사이클 종료 시 가장 큰 타격).
- buffer 3%·120일은 라운드넘버(데이터 최적값 아님) → 민감도 점검 권장.
- MDD 56%는 여전히 큼. 규칙 미준수 시 무방비 3x로 전락.

---

## 4. 파일 가이드

### 실행 도구 (라이브)
- `backtest/live/daily_advisor.py` — 데일리 매매 어드바이저(cron 15:00).
- `backtest/live/advisor_config.yaml` — 예산·비중·MA·buffer·티커(하드코딩 금지).
- (런타임 `state.json`/`advisor.log`/`today_action.txt`는 .gitignore — 개인 상태)

### 엔진·전략
- `backtest/contrib.py` — 정기납입 백테스트 엔진(run_contrib, 매도→매수 2패스) + 전략1·2·3.
- `backtest/contrib_v3_alloc.py` — v3 레짐/듀얼모멘텀 배분.
- `backtest/portfolio_alloc.py` — P1 레짐바스켓/P2 횡단모멘텀/P3 정적 + 역변동성·리밸런싱 헬퍼.
- `backtest/data/loader_multi.py` — 다자산 로드·정렬. `data/loader.py` — 단일 로드·캐시.
- `backtest/engine/` — v1/v2 엔진(indicators, strategy, baselines, portfolio).

### 실행·분석 스크립트
- `backtest/contrib_run.py` — 정기납입 5전략 풀런.
- `backtest/portfolio_run.py` — 14전략×3기간×2비용(SOXL 포함).
- `backtest/dotcom_scenario.py` — 닷컴 위기 시나리오.
- `backtest/recommendation.py` — 확률가중 기대값 추천 + 민감도.
- `backtest/ma_whipsaw.py` — 120 vs 200일선 × 휩쏘완화 변형.
- `backtest/final_strategy.py` — SOXL60/QLD40 결합 4안 검증.

### 리포트 (`backtest/output/`)
- `report_final_strategy_ko.md` — **최종 정리 + 개별안 + 최종안**(읽기 시작점).
- `report_recommendation_ko.txt` — 확률가중 전략 추천.
- `report_panel_ko.md` — AI 강세 vs 닷컴 패널 토의.
- `report_dotcom_ko.txt` — 닷컴 위기 시나리오.
- `report_portfolio_ko.txt` — 다자산 포트폴리오(SOXL 포함).
- `report_contrib_ko.txt` — 정기납입 4전략.
- `report_easy_ko.md` — 일반인(대학생)용 쉬운 설명.
- `report_ko.txt`, `report_v2_ko.txt`, `experiments_ko.txt` — v1/v2/실험.
- `results_*.csv`, `equity_*.png` — 수치·그림.

---

## 5. 재현 방법

```bash
# 패키지: pandas/numpy/yfinance/matplotlib/pyyaml (Python 3.8)
python3 backtest/contrib_run.py          # 정기납입 5전략
python3 backtest/portfolio_run.py        # 다자산 14전략 + OOS
python3 backtest/dotcom_scenario.py      # 닷컴 위기 시나리오
python3 backtest/recommendation.py       # 확률가중 추천
python3 backtest/ma_whipsaw.py           # 120/200 + 휩쏘완화
python3 backtest/final_strategy.py       # 최종 결합전략
python3 backtest/live/daily_advisor.py --dry-run   # 오늘 매매(미리보기)
```

cron(매일 15:00 KST):
```
0 15 * * * cd <repo> && /usr/bin/python3 backtest/live/daily_advisor.py >> backtest/live/advisor.log 2>&1
```

---

## 6. 면책
본 저장소의 모든 분석은 과거 데이터 기반 연구이며 **투자 조언이 아닙니다**. 레버리지 ETF는 변동성 손실(decay)로 장기 약세·횡보장에서 가치가 크게 훼손될 수 있고, 백테스트 성과는 미래를 보장하지 않습니다. 실제 투자 판단과 책임은 전적으로 본인에게 있습니다.

> 참고: 이 저장소는 make_Harness 스캐폴드에서 생성되었습니다. 스캐폴드/멀티에이전트(aimux) 구조 설명은 `DESIGN.md`·`README.md`를, 작업 이력은 `AIMemory/work.log`를 참고하세요.
