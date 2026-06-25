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

## 후속: 데일리 어드바이저 웹사이트 (PWA + GitHub Actions 일일 갱신)

- [x] **W-A. README 프로젝트화** (antigravity): make_Harness 스캐폴드 설명 → qld-timing-backtest README 재작성. 매니저 수락.
- [x] **W-B. 사이트 빌더 + PWA 프론트** (opencode): web/build_site.py + index/manifest/sw 템플릿 + 아이콘. FIX-B 갱신버튼(새로고침 재fetch + Actions 트리거 링크). 매니저 재빌드 수락.
- [x] **W-C. GitHub Actions 워크플로** (antigravity/opencode): .github/workflows/daily.yml, FIX-C cron 08:30 KST(30 23 * * *)+workflow_dispatch, Pages 배포 잡.
- [x] **W-D. 통합·푸시·Pages 활성·배포검증** (opencode): commit+push(workflow scope 인증)+Pages(Actions소스)+workflow run success. 라이브 URL 실측 200 + 최신 데이터.
- [x] **W-E. 배포전 정적검증 하니스** (antigravity): web/validate_site.py(stdlib) — PWA 설치적합성+문서링크. 진짜결함 1건(SW 등록 누락) 적발.
- [x] **W-G. SW 등록 FIX + 재배포** (opencode): serviceWorker.register('./sw.js') 추가 → 재배포 → 라이브 반영 확인. 검증기도 6번 오탐 정교화(8/8 PASS).
- [x] **W-H. 신호 시계열 차트** (opencode): build_site가 series.json(188pts,~18mo) 산출 + 바닐라 canvas 차트(SOXX선+120MA선+±3% 밴드 음영+현재점 ratio라벨). 사용자 피드백 반영. 라이브 검증.

- [x] **W-I. 차트 3개월 + 매수/매도 마커 + 기기별 거래로그·수익률** (opencode): series 3개월(65pts), localStorage(wath_journal_v1) 거래로그+수익률+평가손익, SOXX선 ▲매수/▼매도 색상 마커(±3% 밴드 타이밍 확인). 사용자 피드백 반영. 라이브 검증.

- [x] **W-J. SW 캐시 정체 FIX** (opencode): CACHE 빌드별 버전화(__BUILD_ID__←updated_at) + /data·네비게이션 network-first + clients.claim. PC가 옛 셸(거래로그 미포함)을 캐시하던 문제 해소. 라이브 검증.

- [x] **W-K. 웹 개선 5종 + cron 07:30 KST** (opencode): 차트 기간토글 2W/3M/6M/1Y(일 기반 슬라이스, series 전기간 ~500pts) + 수집날짜 KST 제목하단 표시 + 거래로그 JSON 내보내기/가져오기(로컬 전용) + 빌드 cron 08:30→07:30 KST. 매니저 라이브검증(2W/3M/6M/1Y·8/8 PASS). commit a34ad7b·20d7d7e.

배포 URL: https://wilocraw-alt.github.io/qld-timing-backtest/ (public, 사용자 승인)
참고: repo public 전환(무료 Pages 제약, 사용자 승인). 푸시 시 workflow scope 필요. 민감 런타임(state.json/advisor.log/.env)은 .gitignore 미추적. SW 캐시는 빌드별 버전화되어 배포 시 자동 갱신(예전엔 wath-signal-v1 고정이라 정체).

## 웹 v2 추가요구 (2026-06-25) — 티커 select / 거래목록 UX / 현재배분·리밸런싱

- [x] **V0. 요구확정 + PROPOSE→수렴**: 사용자 4결정(전체리밸런싱·신호반영·거래기록수량합산·SOXL/QLD) + NEUTRAL=보유상태기반동적. opencode·antigravity PROPOSE 수렴 → plan_web-v2-final.
- [x] **V-IMPL (opencode)**: template_index.html에 Req1(티커 select)+Req2(종목요약강화·목록20제한더보기·폼접이식·삭제confirm)+Req3(현재배분%·리밸런싱 매수/매도$·주수, 신호ON/OFF/NEUTRAL분기) 구현 + window.__computeRebalance 순수함수 노출. 커밋 953e283.
- [x] **V-TESTGEN (antigravity)**: web/test_rebalance.mjs Node 단위테스트(vm 추출, 8시나리오/31assertion). ※범위초과로 validate_site.py도 편집(검사9~11) — 결과 클린.
- [x] **V-VERIFY (opencode)**: build_site 성공 + validate_site 11/11 + node test_rebalance.mjs 31/31. FIX불요. validate_site 정적검사 추가.
- [x] **V-RENDER (opencode)**: playwright 헤드리스 렌더 스모크 18/18 PASS(select·폼토글·20제한더보기·보유수량·평단·리밸런싱 현재/목표/매수매도·삭제confirm·페이지에러0). 초기 [object Object] 에러는 테스트하니스 버그(JSON.stringify 누락)로 확정·수정 — 앱 무결. 템플릿 클린(디버그 잔여無).
- [x] **V-SHIP**: 커밋 953e283 push(wilocraw-alt/qld-timing-backtest main). web/ + CHECKLIST/PROJECT/TESTING-web-v2.md만. 테스트가이드 TESTING-web-v2.md.

## 진행 이력

- 2026-06-19 — 0단계 완료: 요구사항 확정(트랜치 균등10%/일상한$1k/전체기간/$10k, 비교군 2종), 설계 PROPOSE 병렬→수렴(plan-final)
- 2026-06-20 — 웹사이트 후속: README 프로젝트화 + 데일리 신호 PWA(web/) + GH Actions 일일배포(.github/workflows/daily.yml, 08:30 KST) + 정적검증 하니스. 라이브 https://wilocraw-alt.github.io/qld-timing-backtest/ . SW 등록 FIX 재배포 진행 중.
- 2026-06-23 — 웹 개선 5종 배포: 차트 2W/3M/6M/1Y 토글·수집날짜 KST 표시·거래로그 JSON export/import·cron 07:30 KST. 라이브 검증 통과(20d7d7e).
