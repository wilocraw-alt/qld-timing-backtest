# RESUME — 이어가기 가이드 (clear 후 콜드 세션용)

**작성**: claude-opus-4-8 (manager) · 2026-06-20 08:25
**용도**: 대화 context를 clear한 뒤에도 이 파일 + 메모리 + work.log만 읽고 작업을 이어가기 위한 단일 상태 문서.

## 0. 콜드 세션 부팅 순서 (이 순서로 읽어라)
1. `PROJECT.md` — 프로젝트 정체(qld-timing-backtest, research 프로파일).
2. 메모리 자동로드: `[[web-pwa-site]]`(라이브 사이트·구조·배포제약), `[[user-investment-research]]`.
3. 이 파일(`AIMemory/RESUME.claude-opus-4-8.md`) — 현재 상태·구조·이어가기.
4. `CHECKLIST.md` — 단계(W-A~W-J 완료) + 진행이력.
5. `AIMemory/work.log` 끝 ~80줄 — 최신 이벤트(매니저 판정·HANDOFF).
6. 매니저 규약: `AIMemory/briefs/manager.md` + `AIMemory/PROTOCOL.md` + `AIMemory/agents.md`.

## 1. 지금 상태 (2026-06-20 기준)
- **백테스트 연구**: 완료(`RESEARCH.md` 종합). 최종 전략 SOXL60(SOXX 120일선 ±3% buffer)+QLD40 월 $300.
- **웹사이트**: 완료·라이브. https://wilocraw-alt.github.io/qld-timing-backtest/ (HTTP 200).
  - GitHub Actions 매일 **08:30 KST**(`.github/workflows/daily.yml`, cron `30 23 * * *`) 자동 갱신 + workflow_dispatch.
  - 기능: 데일리 신호 배지(ON/OFF/NEUTRAL), SOXX 120MA ±3% **3개월 시계열 차트**(▲매수 초록/▼매도 빨강 마커), 목표배분, 최신가, 🔄 새로고침 + ⟳ Actions 수동트리거, **기기별 거래로그(localStorage `wath_journal_v1`)** 평단입력→수익률, PWA 오프라인.
- **git**: HEAD `8e8e6f8`, origin/main 동기(unpushed 0). repo **public**(사용자 승인).
- **워킹트리**: `AIMemory/work.log`만 상시 modified(오케스트레이션 로그 — 일부러 커밋 안 함, self-loop 방지).

## 2. 파일 구조 (웹)
- `web/build_site.py` — 빌더. `--out <dir> [--config backtest/live/advisor_config.yaml]`. yfinance로 SOXX/SOXL/QLD 받아 `data/latest.json`(신호 스냅샷)+`data/series.json`(3개월 차트, ~65pts) 산출, 템플릿을 out으로 복사하며 `sw.js`의 `__BUILD_ID__`를 updated_at 숫자로 치환(캐시 버전).
- `web/template_index.html` — 모바일 PWA 셸(인라인 바닐라 JS, 전부 상대경로 `./`). 차트·거래로그·새로고침.
- `web/template_sw.js` — 서비스워커. CACHE=`wath-__BUILD_ID__`(빌드별), `/data/`+네비게이션 network-first, 그외 cacheFirst, activate에서 옛 캐시 삭제+clients.claim.
- `web/template_manifest.webmanifest` — PWA manifest(standalone, start_url/scope=`./`).
- `web/validate_site.py` — stdlib 배포전 검증(필수파일/manifest/아이콘PNG/sw precache/PWA메타/절대경로/스키마 + README·RESEARCH 링크). `python3 web/validate_site.py <dir>`.
- `.github/workflows/daily.yml` — build(setup-python·pip install pandas numpy yfinance pyyaml matplotlib pillow·build_site --out _site·upload-pages-artifact)+deploy(deploy-pages).
- 데이터 원본 신호 로직: `backtest/live/daily_advisor.py`(`_NYSEHolidays`/`market_status`/120MA buffer).

## 3. 로컬 빌드·검증·배포 (재개 시 표준 절차)
```bash
python3 web/build_site.py --out AIMemory/tmp/site_preview      # 빌드(yfinance 필요)
python3 web/validate_site.py AIMemory/tmp/site_preview         # 8/8 PASS여야
# 배포: web/ 또는 .github/ 수정 후
git add web/ .github/ README.md RESEARCH.md CHECKLIST.md
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
- **work.log/run-summary의 `/home/` 경로**가 public repo에 이미 노출됨(과거 커밋부터). 정리하려면 .gitignore 제외 + 히스토리 정리 필요(사용자 승인 후).

## 6. 다음에 할 만한 것(미요청·아이디어)
- PC 가독성: 셸에 max-width 컨테이너(현재 풀폭). 
- 거래로그 내보내기/가져오기(JSON), 기기 간 수동 이전.
- series 기간 토글(3M/6M/1Y). 
- daily_advisor state.json 기반 실제 보유 연동(현재 웹은 무상태 신호 + 사용자 입력 로그).
