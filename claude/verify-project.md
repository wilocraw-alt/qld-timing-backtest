# verify-project.md — Given-project verification flow

## 요약 (사용자용)

- **이미 존재하는** 프로젝트 폴더를 받아 **코드검증 → 설치검증 → 기능검증 → 적대적기능검증 → 종합**으로 검증하고 증거 보고서를 산출하는 스킬.
- `ideate`(사전 구체화)·`paper`(사후 논문화)와 대칭 — 이건 **주어진 프로젝트 검증**. 빌드가 아니라 검증(코드 미수정, 발견만 보고).
- 6단계: T0 정찰·표면감지 → T1 코드 → T2 설치 → T3 기능 → T4 적대적 → T5 종합. 각 단계 끝 사용자 게이트(G0~G4), 명확하면 fast-track.
- 표면(web/api/cli/lib/tui)을 자동 감지해 기능검증 드라이버를 전환 — `임의의 프로젝트`에 일반 적용.
- aimux 워커에 INSPECT/VERIFY/IMPLEMENT/TEST 위임, 없으면 매니저 단독.
- 안전 비협상: `.env` 미수정·비밀 미출력, 악성입력 데이터로만(미실행), heavy 상한, 대상 git 미변경.

---

**When to read**: 사용자가 **이미 만들어진** 프로젝트 폴더를 가리키며 동작·품질·안전성 검증을 요청할 때. 새 프로젝트를 만들 때가 아니다(그건 `ideate`/`intake`/`plan`/`implement`).

This guide is the **flow contract**. Operational detail lives in:
- `.claude/skills/verify-project/SKILL.md` — 진입점, 호출, 안전 계약, aimux vs solo 분기.
- `.claude/skills/verify-project/flow.md` — T0~T5 런북.
- `.claude/skills/verify-project/gate.md` — 게이트 G0~G4 템플릿.
- `.claude/skills/verify-project/surfaces/{web,api,cli,lib,tui}.md` — 표면별 기능검증 드라이버.
- `.claude/skills/verify-project/checklists/adversarial-catalog.md` — 경계·악성·heavy 케이스.
- `templates/verify-project/` — 단계별 보고서·케이스 블록 양식.

---

## 0. Principle — 증거 기반 누적 검증

검증은 **증거 우선**: 모든 판정은 재현 가능한 근거(명령·응답·스크린샷·로그·테스트)에 묶인다.
단계는 누적적 — T0가 표면·정상케이스를 정하고, T3·T4가 그것을 실행한다.
CRITICAL/HIGH 결함 후보는 **적대적 재검증**(독립 워커가 반증 시도)으로 과대평가를 거른다.

`ideate`의 diverge→converge가 *생성*을 위한 것이라면, 여기선 *반증→확정*이 핵심 루프다:
주장하지 말고 재현하라, 한 시각이 아니라 독립 시각으로 검증하라.

---

## 1. 단계 (상세는 flow.md)

- **T0 정찰·표면감지** — 구조·문서·실행법 파악, 표면 분류(web/api/cli/lib/tui), 정상케이스 도출, 검증계획. → `00_recon_plan.md`. 게이트 G0.
- **T1 코드검증** — 파일 단위 정적 점검 + 개념·일관성 + probe 테스트 + 결함 적대적 재검증. → `10_code_review.md`. 게이트 G1.
- **T2 설치검증** — 환경 재현·빌드·기동·헬스(매니저 독립확인) + 재기동 명령. `.env` 미수정. → `20_install_run.md`. 게이트 G2.
- **T3 기능검증** — 정상 케이스 Live Test(표면별 드라이버), 테스트별 pass/fail + 증거 + mermaid. → `30_functional.md`. 게이트 G3.
- **T4 적대적기능검증** — 경계·악성·heavy(안전 가드), 동일 포맷, 사후 무결성. → `40_adversarial.md`. 게이트 G4.
- **T5 종합** — T1~T4 통합 최종보고서(매니저 작성). → `FINAL_report.md`.

---

## 2. 표면 적응 (일반화의 핵심)

`임의의 프로젝트`에 적용하려면 기능검증이 표면에 적응해야 한다:
- `web` → Playwright headed(WSLg로 Windows 표시) + 스크린샷
- `api` → curl/httpx 요청·응답 캡처
- `cli` → subprocess 인자/stdin → 출력/exit
- `lib` → pytest / import-and-call(실행표면 없음 — 함수단위)
- `tui` → pexpect/tmux 화면 캡처

T0에서 신호로 자동 판정하되 `--surface`로 강제 가능. 복수 표면이면 각각 검증.

---

## 3. Roles (manager / worker)

- **Manager (claude)**: 대화·게이트·분해·라우팅·**검증/종합**·accept/re-route. 헬스·무결성은 직접 재현(워커 보고를 곧이곧대로 받지 않음).
- **Workers**: `INSPECT`(코드점검·인벤토리), `VERIFY`(결함 반증·정합), `IMPLEMENT`(환경구성·기동), `TEST`(라이브·적대적 실행). 능력 + **데이터 민감도**로 라우팅(`AIMemory/agents.md`).
- **No aimux session?** 매니저가 같은 단계·게이트를 단독 순차 수행. `SKILL.md` 분기가 모드를 정한다.
- aimux 운용 함정(매니저 패널 전달 차단·antigravity 스피너 오탐)은 그 세션의 `agents.md`/운용 메모를 따른다.

---

## 4. 산출물·git 규율

- 산출물은 **현재 작업 레포**의 `evaluation/<대상명>/`(기본). 대상 폴더(자체 git일 수 있음)는 **미변경**.
- probe 테스트를 대상 안에 둘 경우 격리 디렉토리 + 대상 레포 **자동 커밋 금지**.
- 외부 레포 push는 `gh` 인증 계정 기준(`CLAUDE.md` 0절) + 사용자 명시 요청 시.

---

## 5. 관계 — ideate / paper / 수정

- `ideate`: 사전(희망→PROJECT.md). `verify-project`: 검증(주어진 프로젝트→보고서). `paper`: 사후(완료 프로젝트→논문).
- 검증이 결함을 찾고 **수정**이 필요하면 별도 결정 — `plan.md`→`implement.md`→`verify.md`로 전환(이 스킬은 발견·보고까지).
