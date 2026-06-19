# flow.md — verify-project runbook (T0→T5)

This is the **operational runbook**. The flow contract / rationale lives in `claude/verify-project.md`;
the entry point and invocation in `SKILL.md`. Read the safety contract in `SKILL.md` before any stage —
it is non-negotiable and applies throughout.

표면별 드라이버: `surfaces/{web,api,cli,lib,tui}.md`. 케이스 카탈로그: `checklists/adversarial-catalog.md`.
보고서 양식: `templates/verify-project/`. 사용자 게이트: `gate.md`.

---

## 0. Principle

검증은 **증거 우선**이다. 모든 판정은 재현 가능한 근거(명령·응답·스크린샷·로그·테스트 결과)에 묶인다.
발견 결함은 *주장*이 아니라 **재현 절차 + 심각도**로 기록한다. CRITICAL/HIGH 후보는 **적대적 재검증**
(독립 워커가 반증 시도)을 거쳐 과대평가를 거른다 — STEP1에서 2건의 CRITICAL을 근거에 따라 하향한 사례가 본보기.

단계는 **누적적**: T0가 표면·케이스를 정하면 T3·T4가 그것을 실행한다. 명확하면 게이트는 fast-track.

---

## T0 — Recon & surface detection (매니저 주도, 게이트 G0)

- **Do**:
  1. 대상 폴더 구조·문서(README/docs/ARCHITECTURE)·빌드정의(pyproject/package.json/Makefile/Dockerfile/compose)·`.env(.example)`를 읽어 **진입점·실행법·의존성**을 파악.
  2. **표면 분류** — 프로젝트가 노출하는 인터페이스를 판정(복수 가능):
     - `web` — 브라우저 UI(HTTP server + HTML/SPA). → Playwright headed Live Test.
     - `api` — HTTP/gRPC API(UI 없음). → curl/httpx 요청·응답 캡처.
     - `cli` — 명령행 도구/엔트리포인트. → subprocess 호출·출력 캡처.
     - `lib` — import해서 쓰는 라이브러리/패키지(실행표면 없음). → pytest/import-and-call.
     - `tui` — 터미널 UI. → pexpect/tmux 캡처(없으면 lib처럼 함수단위).
     감지 신호는 `surfaces/*.md` 상단 "Detect" 절 참조. `--surface`로 강제 가능.
  3. **정상 동작 케이스 목록**을 문서·코드에서 도출(happy path) — T3 입력.
  4. **검증계획** 작성: 어떤 컴포넌트를 T1에서 점검, 어떻게 T2에서 띄움, T3에서 어떤 케이스를 어떤 표면 드라이버로, T4에서 어떤 적대적/heavy 케이스(카탈로그에서 선별).
- **Output**: `00_recon_plan.md`(`templates/verify-project/00_recon_plan.md`).
- **aimux**: 대형 코드베이스면 인벤토리/열거를 antigravity에, 구조 파악을 opencode에 `INSPECT`로 위임; 매니저가 표면·계획 종합.
- **Gate G0 (범위·표면 확인)**: 표면분류 + 정상케이스 + 단계범위를 사용자가 확인.

---

## T1 — 코드검증 (CODE; INSPECT+VERIFY, 게이트 G1)

- **Do**:
  1. **파일 단위 정적 점검** — 주요 컴포넌트(모듈/서비스)별로 책임·경계·오류처리·자원수명·동시성·입력검증을 읽는다.
  2. **개념·일관성 점검** — 문서 ↔ 코드 ↔ 스키마 ↔ 설정의 정합(예: 문서가 말하는 테이블 수 vs 실제). 불일치는 결함 후보.
  3. **probe 테스트 작성** — 주요 컴포넌트마다 오류 가능성을 찌르는 테스트 코드(경로검증·경계·동시성·예외경로). 대상 안에 둘 경우 격리 디렉토리(`tests/_verify_probes/`), 대상 레포에 자동 커밋 금지. 실행 가능하면 실행하고 결과 기록.
  4. **적대적 재검증** — CRITICAL/HIGH 후보는 독립 워커에게 "반증하라" `VERIFY`. 실제 보호장치(예: read_only+cap_drop)나 언어보장(예: GIL atomic)으로 무력화되면 **하향**. 라이브 차단(HTTP 404)과 함수단위 결함은 **구분 기록**.
- **Output**: `10_code_review.md`(컴포넌트별 소견 + 심각도표 + probe 결과) + `probes/`.
- **aimux**: 컴포넌트별 `INSPECT`를 opencode에 fan-out, 열거·카운트 정합은 antigravity, 결함 재검증은 별도 `VERIFY` 워커.
- **Gate G1 (코드검증 수용)**: 결함목록·심각도·probe 결과 확인.

---

## T2 — 설치검증 (INSTALL; IMPLEMENT+VERIFY, 게이트 G2)

- **Do**:
  1. 문서·빌드정의대로 **환경 재현**(venv/node_modules/docker), 의존성 설치. 대상 `.env` 있으면 그대로 사용(**수정·비밀출력 금지**); 없으면 `.env.example`로 필요한 키를 식별해 사용자에게 값 요청.
  2. **빌드·기동** — 엔트리포인트/Makefile/compose로 띄우고, 외부 의존(DB·LLM·MCP 등)은 문서·`.env` 기준으로 연결.
  3. **헬스 확인** — `/health`·포트 listen·로그 무오류 등으로 가동 검증. 매니저가 **독립 재현**(워커 보고를 곧이곧대로 받지 않음).
  4. **재기동 명령** 문서화(죽었을 때 되살리는 절차) — 후속 단계·재개용.
- **Output**: `20_install_run.md`(설치 절차 + 가동 표[포트/PID/로그경로] + 재기동 명령 + 환경 갭).
- **설명 가능한 환경 갭**(미설치 SDK·미가동 레거시 서비스 등)은 **플랫폼 버그와 구분**해 기록.
- **aimux**: `IMPLEMENT`(opencode)로 기동 시도, 매니저가 헬스 독립확인.
- **Gate G2 (가동 확인)**: 플랫폼이 떴고 헬스 통과함을 확인.

---

## T3 — 기능검증 (FUNCTION; TEST, 게이트 G3)

- **Do**:
  1. T0의 **정상 케이스**를 표면별 드라이버로 Live Test:
     - `web` → Playwright **headed**(WSLg `DISPLAY=:0`로 Windows에 보이게) + 단계 스크린샷.
     - `api` → 요청/응답 본문·상태코드 캡처.
     - `cli` → 인자·stdin → stdout/stderr/exit code 캡처.
     - `lib` → pytest 또는 import-and-call로 입출력 단언.
     - `tui` → pexpect/tmux 캡처.
     자세한 드라이버 레시피는 `surfaces/<표면>.md`.
  2. **테스트별 보고**: 케이스명·입력·기대·실측·**pass/fail**·증거(web=스크린샷 경로, api/cli=응답 블록)·**mermaid flow**(그 테스트의 흐름) — `templates/verify-project/_case_block.md` 사용.
- **Output**: `30_functional.md` + `screenshots/`(web).
- **aimux**: `TEST`(opencode)로 실행, 매니저가 핵심 케이스 1~2건 직접 재현.
- **Gate G3 (정상 기능 확인)**: pass/fail 요약 확인.

---

## T4 — 적대적기능검증 (ADVERSARIAL; TEST, 게이트 G4)

- **Do**:
  1. `checklists/adversarial-catalog.md`에서 대상·표면에 맞는 **경계(boundary)·악성(malicious)·타입오류(type)·heavy** 케이스를 선별/구체화.
  2. **안전 가드** 하에 실행: 악성 페이로드는 **데이터로만** 주입(미실행), heavy는 상한(동시성·반복·페이로드 크기) 명시, 파괴적 부작용 금지.
  3. T3과 **동일 포맷**으로 측정(케이스 블록 + mermaid). 시스템이 안전 처리했는지(거부/검증/격리) vs 취약한지 판정.
  4. **사후 무결성 확인** — 컴포넌트 헬스 + 데이터(예: DB 행수·DROP 피해 없음) + orphan 자원 없음을 매니저가 직접 확인.
- **Output**: `40_adversarial.md`(케이스별 + 무결성 결과 + 관찰된 약점).
- **무음 상한 금지**: 케이스/부하를 잘랐다면(top-N·미반복·샘플링) 보고서에 명시.
- **Gate G4 (적대적 검증 수용)**: 안전처리율 + 취약점 확인.

---

## T5 — 종합 (FINAL; 매니저 작성)

- **Do**: T1~T4를 통합한 최종 보고서 — 요약 판정, 단계별 핵심, **결함 종합표(심각도·재현·수정권고)**, 환경 갭, 산출물 인덱스, (요청 시) 다음 작업 후보.
- **Output**: `FINAL_report.md`(`templates/verify-project/FINAL_report.md`).
- 매니저가 직접 작성(워커 산출 종합) — 검증의 최종 판정은 매니저 책임.

---

## Termination & loop control

- **완료**: 요청한 단계 전부 게이트 통과 + `FINAL_report.md`.
- **차단**: T2에서 기동 불가(외부 의존·비밀 부재 등) → 갭을 명시하고 가능한 범위(T1 + 정적 T3)로 축소, 사용자에게 보고.
- **표면 없음/불명**: T0에서 실행표면이 없으면(순수 lib) T3는 함수단위로 수행하고 그렇게 명시.
- **결함만 보고, 수정 안 함**: 수정은 별도 요청 시 `plan.md`→`implement.md`로 전환.
