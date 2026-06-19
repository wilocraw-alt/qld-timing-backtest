# CHECKLIST.md  <!-- 이 프로젝트의 단계별 체크리스트 -->

<!--
plan 단계(claude/plan.md)가 이 파일을 채운다. 사용자 합의 후 구현을 시작하고,
각 단계 완료 시 체크박스를 갱신하며 아래 "진행 이력"에 한 줄씩 누적한다.
스캐폴드(make_Harness) 자체의 개발 이력은 여기가 아니라 HARNESS-CHANGELOG.md에 적는다.
-->

생성일  : 2026-06-19
목표    : QLD 규칙기반 투자시점 전략 백테스트 + 규칙별 ablation 효과 및 2개 비교군 대비 성과 검증
진행    : 8/8 (완료)

---

## 수행 단계

- [x] **0. 요구사항 확정 + 설계 PROPOSE→수렴**
  - 출력: requirements / plan-final / design-proposal{,.opencode,.antigravity} (AIMemory/)
- [x] **1. U-DATA+SIGNALS (antigravity)**: data/loader.py + engine/indicators.py — 매니저 검증·수락(지연확정/미래참조無/계약OK). 환경블로커(py3.8 multitasking) 해결.
- [x] **2. U-ENGINE (opencode)**: engine/portfolio.py + engine/strategy.py + ma200/tp latch FIX — 매니저 재검증·수락
- [x] **3+5. U-FINAL (opencode 재배정)**: baselines.py + metrics.py + plot.py + 풀런 + 한국어 report — 수락
  - 주: antigravity가 metrics/baselines를 못 만들고 환경 thrash → opencode로 재배정
- [x] **4. U-ABLATION+CLI (opencode)**: ablation.py + main.py + config.yaml — 17년 실데이터 풀파이프라인 에러0 완주, 수락
- [x] **6. VERIFY**: opencode sanity(전 변형 PASS) + 매니저 독립검증(일매수≤$1,000 전수, lumpsum 교차 $995,646.89, 미래참조無)
- [x] **7. 최종 리포트 + 추가실험(트랜치/익절/일한도) + git private push (wilocraw-alt/qld-timing-backtest)**

---

## 진행 이력

- 2026-06-19 — 0단계 완료: 요구사항 확정(트랜치 균등10%/일상한$1k/전체기간/$10k, 비교군 2종), 설계 PROPOSE 병렬→수렴(plan-final)
