# RESUME — 이어가기 가이드 (clear 후 콜드 세션용)

**작성**: claude-opus-4-8 (manager) · 2026-06-23 08:45 · **갱신 2026-07-01(리밸런싱 개편·보유현황 동시입력)**
**용도**: 대화 context를 clear한 뒤에도 이 파일 + 메모리 + work.log만 읽고 작업을 이어가기 위한 단일 상태 문서.

## 0. 콜드 세션 부팅 순서 (이 순서로 읽어라)
1. `PROJECT.md` — 프로젝트 정체(qld-timing-backtest, research 프로파일).
2. 메모리 자동로드: `[[web-pwa-site]]`(라이브 사이트·구조·배포제약), `[[user-investment-research]]`.
3. 이 파일(`AIMemory/RESUME.claude-opus-4-8.md`) — 현재 상태·구조·이어가기.
4. \`CHECKLIST.md\` — 단계(W-A~W-K 완료 + 웹 v2 V-IMPL/TESTGEN/VERIFY/RENDER/SHIP 완료 + 리밸런싱 개편 RB-0~SHIP·RB-4 완료) + 진행이력.
5. `AIMemory/work.log` 끝 ~80줄 — 최신 이벤트(매니저 판정·HANDOFF).
6. 매니저 규약: `AIMemory/briefs/manager.md` + `AIMemory/PROTOCOL.md` + `AIMemory/agents.md`.

## 1. 지금 상태 (2026-07-01 기준 · 웹 v2 + 리밸런싱 개편 배포)
- **백테스트 연구**: 완료(`RESEARCH.md` 종합). 최종 전략 SOXL60(SOXX 120일선 ±3% buffer)+QLD40 월 $300.
- **웹사이트**: 완료·라이브. https://wilocraw-alt.github.io/qld-timing-backtest/ (HTTP 200).
  - GitHub Actions 매일 **07:30 KST**(`.github/workflows/daily.yml`, cron `30 22 * * *`) 자동 갱신 + workflow_dispatch.
  - 기능(v1): 데일리 신호 배지(ON/OFF/NEUTRAL), SOXX 120MA ±3% **전기간(~500pts) 시계열 차트(2W/3M/6M/1Y 토글)**(▲매수 초록/▼매도 빨강 마커), 수집날짜 KST 제목하단, 목표배분, 최신가, 🔄 새로고침 + ⟳ Actions 수동트리거, **기기별 거래로그(localStorage `wath_journal_v1`)** 평단입력→수익률·JSON 내보내기/가져오기, PWA 오프라인.
  - **기능(v2, 2026-06-25 추가)**: ① 거래폼 티커 **SOXL/QLD select**(자유입력→드롭다운) ② 거래목록 UX(종목별 요약 강화: 보유수량·평단·평가손익 / 목록 **최신 20개 제한 + 더보기·접기** / 입력폼 **접이식 "+ 거래 추가"** / 삭제 **confirm**) ③ 목표배분 카드에 **현재 배분% + 리밸런싱 지시**(현재가 기준 종목별 매수/매도 $·주수). **신호 반영**: ON=60/40, OFF=SOXL 0%·현금60%, **NEUTRAL=보유상태 기반 동적**(SOXL 보유>$1면 60/40, 미보유면 OFF목표). 계산은 순수함수 `window.__computeRebalance(journal, prices, signalState)`로 분리(테스트 대상).
- **2026-07-01 개편**: 리밸런싱 입력을 현재보유 덮어쓰기(누적X)로 교체 + 추가 구매 $ 전체재분배(매도허용) + 매수/매도·보유 주수 소수점 4자리(fmtShares). 계산 순수함수 `__computeRebalance(journal,prices,signalState,additionalCash)`.
- **2026-07-01(2차)**: 보유현황 입력 select 제거 → SOXL·QLD 동시입력·__saveHoldings 일괄 덮어쓰기(프리필). validate #10=4입력 검사.
- **git**: HEAD \`f387ca7\`(보유현황 동시입력), origin/main 동기(unpushed 0). repo **public**(사용자 승인).
- **워킹트리**: `AIMemory/` 오케스트레이션 산출물만 uncommitted(work.log·run-summary·agents.md·plan/requirements). 일부러 커밋 안 함(self-loop·HOME경로 방지). `handoff_*.md`/`.aimux/`/`tmp/`는 .gitignore. 배포 코드(web/)는 전부 커밋됨.

## 2. 파일 구조 (웹)
- `web/build_site.py` — 빌더. `--out <dir> [--config backtest/live/advisor_config.yaml]`. yfinance로 SOXX/SOXL/QLD 받아 `data/latest.json`(신호 스냅샷)+`data/series.json`(전기간 ~500pts, 약 2년) 산출, 템플릿을 out으로 복사하며 `sw.js`의 `__BUILD_ID__`를 updated_at 숫자로 치환(캐시 버전).
- \`web/template_index.html\` — 모바일 PWA 셸(인라인 바닐라 JS, 전부 상대경로 \`./\`). 차트(2W/3M/6M/1Y)·수집날짜 KST·거래로그(JSON export/import)·새로고침 + **v2: 티커 select·접이식폼·목록20제한더보기·종목요약강화·삭제confirm·리밸런싱 카드·\`window.__computeRebalance\` 순수함수**.
  + 2026-07-01: 보유현황 **SOXL·QLD 동시입력폼**(select 제거, \`__saveHoldings\` 일괄 덮어쓰기, 폼 프리필), 리밸런싱 \`__computeRebalance(journal,prices,signalState,additionalCash)\`(추가현금 전체재분배·매도허용), 매수/매도·보유 주수 **소수점4자리 \`fmtShares\`**.
- `web/test_rebalance.mjs` — **v2 리밸런싱 단위테스트**(Node stdlib `vm`로 template에서 `__computeRebalance` 추출→10시나리오/40 assertion, 현재 \`node web/test_rebalance.mjs\` 40/40). 실행 `node web/test_rebalance.mjs`(무설치). localStorage 주입은 반드시 `JSON.stringify` (하니스 함정).
- `web/template_sw.js` — 서비스워커. CACHE=`wath-__BUILD_ID__`(빌드별), `/data/`+네비게이션 network-first, 그외 cacheFirst, activate에서 옛 캐시 삭제+clients.claim.
- `web/template_manifest.webmanifest` — PWA manifest(standalone, start_url/scope=`./`).
- \`web/validate_site.py\` — stdlib 배포전 검증(**11개 체크**: 필수파일/manifest/아이콘PNG/sw precache/PWA메타/절대경로/스키마/문서링크 + **v2: 9.리밸런싱 단위테스트 실행 10.보유현황 SOXL/QLD 동시입력란(jPrice/jQty SOXL·QLD 4입력) 검사 11.리밸런싱 카드 문자열**). `python3 web/validate_site.py <dir>`.
- `.github/workflows/daily.yml` — build(setup-python·pip install pandas numpy yfinance pyyaml matplotlib pillow·build_site --out _site·upload-pages-artifact)+deploy(deploy-pages).
- 데이터 원본 신호 로직: `backtest/live/daily_advisor.py`(`_NYSEHolidays`/`market_status`/120MA buffer).

## 3. 로컬 빌드·검증·배포 (재개 시 표준 절차)
```bash
python3 web/build_site.py --out AIMemory/tmp/site_preview      # 빌드(yfinance 필요)
python3 web/validate_site.py AIMemory/tmp/site_preview         # 11/11 PASS여야(내부에서 node test 실행)
node web/test_rebalance.mjs                                    # 40/40 PASS(리밸런싱 계산, 무설치)
# 배포: web/ 또는 .github/ 수정 후 (AIMemory 로그·_site/는 stage 금지)
git add web/ .github/ README.md RESEARCH.md CHECKLIST.md PROJECT.md TESTING-web-v2.md
git commit -m "..."; git push origin main
gh workflow run daily.yml && gh run watch "$(gh run list --workflow=daily.yml -L1 --json databaseId --jq '.[0].databaseId')" --exit-status
curl -sS -o /dev/null -w "%{http_code}\n" https://wilocraw-alt.github.io/qld-timing-backtest/
```

## 4. 멀티에이전트 운영 (이어서 매니저로 할 때)
- aimux 가동 중이면 워커에 위임: `AIMemory/bin/aimux enqueue --to <opencode|antigravity> --handoff <file> --roles <R> --from manager`. 상태: `AIMemory/bin/aimux agents` / `status`.
- 가동 안 되어 있으면(콜드): `! AIMemory/bin/aimux-up` (TTY 대화형 — 사용자가 실행) 후 매니저로 진행.
- **검증은 매니저가 직접**(라이브 curl·재빌드) — 워커 자기보고만 믿지 말 것.
- 라우팅: **opencode=신뢰**(멀티파일·git/gh·env OK). **antigravity=순수 docs/YAML만**(env 건드리면 pip rabbit-hole; 권한 프롬프트 빈발 → 저위험이면 `tmux send-keys -t <pane> '1' Enter`로 승인).

## 5. 핵심 함정 (재발 방지)
- **push에 workflow scope 필요**: `.github/workflows/*` 푸시는 gh 토큰 `workflow` 스코프 필수. 없으면 거부 → `gh auth refresh -h github.com -s workflow`(사용자 브라우저 device flow). 워커에 맡기면 코드 반복재발급으로 정체 → **사용자 직접 인증이 안정적**.
- **무료 Pages = public repo**: 비공개로 되돌리면 Pages 죽음(Pro 필요).
- **SW 캐시**: CACHE는 반드시 빌드별 버전(고정이면 셸 정체로 갱신 안 됨 — 과거 `wath-signal-v1` 고정이 PC에서 거래로그 미표시 유발). 데이터/HTML은 network-first 유지.
- **개인 보유데이터**: 거래로그는 localStorage만(서버·repo 미전송) — 절대 커밋·서버전송 금지.
- **헤드리스 렌더테스트 함정(v2)**: playwright로 localStorage 주입 시 배열을 그대로 `setItem`하면 `[object Object]`로 저장돼 `getJournal()` JSON.parse가 깨지고 가짜 'fetch 에러'처럼 보임 → 반드시 `JSON.stringify`. 데이터는 `page.route`로 모킹 + 스레디드 HTTPServer로 서빙. 렌더테스트는 ~12분 걸리니 계산검증(node vm, 빠름)과 분리해 비차단으로 돌릴 것.
- **work.log/run-summary의 `/home/` 경로**가 public repo에 이미 노출됨(과거 커밋부터). 정리하려면 .gitignore 제외 + 히스토리 정리 필요(사용자 승인 후).

- **보유 모델(2026-07-01~)**: journal은 종목당 1엔트리 덮어쓰기(누적 아님). __saveHoldings가 SOXL/QLD를 함께 저장. 계산은 __computeRebalance 4번째 인자 additionalCash로 추가현금 재분배. 표시 주수는 fmtShares(4자리).

## 6. 다음에 할 만한 것(미요청·아이디어)
- PC 가독성: 셸에 max-width 컨테이너(현재 풀폭). 
- daily_advisor state.json 기반 실제 보유 연동(현재 웹은 무상태 신호 + 사용자 입력 로그).
- 리밸런싱: 매수전용 모드/현금 추가투입액 입력 옵션(현재는 전체 리밸런싱=매도포함).
- (완료) 차트 기간 토글 2W/3M/6M/1Y + 거래로그 JSON 내보내기/가져오기 + 수집날짜 KST 표시.
- (완료, v2) 티커 select·거래목록 UX(요약강화/20제한더보기/접이식폼/삭제confirm)·현재배분%+리밸런싱(신호반영). 테스트: `TESTING-web-v2.md`.
