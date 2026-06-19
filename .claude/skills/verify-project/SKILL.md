---
name: verify-project
description: Run a 4-stage verification pipeline (code review → install/run → functional live-test → adversarial/heavy) against an arbitrary project folder, producing per-stage evidence reports and a final summary. Use when handed an existing/third-party project to vet — not to build one. Auto-detects the project's surface (web UI / HTTP API / CLI / library / TUI) and adapts the functional drivers. Runs the manager that drives aimux workers (or works solo if no aimux session). Invoke as /verify-project <project-folder> [--surface auto|web|api|cli|lib|tui] [--stages 1-5] [--out <dir>].
---

# SKILL: verify-project — Given-project verification harness

주어진(서드파티 포함) 프로젝트 폴더를 **코드검증 → 설치검증 → 기능검증 → 적대적기능검증 → 종합**의
4(+1)단계로 검증하고, 단계별 **증거 보고서**와 **최종 종합보고서**를 산출하는 스킬.

`ideate`(프로젝트 **사전** 구체화), `paper`(프로젝트 **사후** 논문화)와 대칭을 이루는 세 번째 축 —
**이미 존재하는 프로젝트를 검증**한다. 빌드가 아니라 **검증**이 목적이다(코드를 고치지 않는다; 발견만 보고).
이 스킬은 **매니저 역할**로 동작하며, aimux 워커에게 INSPECT/VERIFY/TEST/IMPLEMENT를 위임하거나
(세션 있을 때) 단독으로 수행한다(없을 때).

## When to use

- 사용자가 **이미 만들어진 프로젝트 폴더**를 가리키며 "동작·품질·안전성을 검증해 달라"고 할 때.
- 새 프로젝트를 **만들** 때가 아니다 → 그건 `ideate`/`intake`/`plan`/`implement`.
- 검증 대상은 보통 **별도 git 레포**일 수 있다. 이 스킬은 대상 폴더를 **수정하지 않고**(probe 테스트는 격리 위치), 산출물은 **현재 작업 레포**에 쓴다.

## Invocation

- `/verify-project <project-folder>` — 필수: 검증할 대상 폴더 경로.
- 옵션:
  - `--surface auto|web|api|cli|lib|tui` (기본 `auto` — T0에서 자동감지)
  - `--stages 1-5` (기본 전체 — 예: `--stages 1-2`만 코드·설치까지)
  - `--out <dir>` (기본 `./evaluation/<대상폴더명>/`)

## Inputs / Outputs

- **Input**: 검증할 프로젝트 폴더(경로). 그 안의 문서(README/docs)·빌드정의(pyproject/package.json/Makefile)·`.env(.example)`.
- **Output**(기본 `./evaluation/<대상명>/`, 대상 폴더는 미수정):
  - `00_recon_plan.md` — 표면분류 + 검증계획 + 정상 케이스 목록
  - `10_code_review.md` — 정적 점검·일관성·probe 결과 (+ 분리된 probe 테스트)
  - `20_install_run.md` — 환경재현·기동·헬스 + 재기동 명령
  - `30_functional.md` — 정상 케이스 Live Test (표면별 증거 + 테스트별 mermaid)
  - `40_adversarial.md` — 경계·악성·heavy 케이스 (동일 포맷 + 사후 무결성)
  - `FINAL_report.md` — T1~T4 종합
  - `screenshots/`(web 표면), `worker_reports/`(aimux 위임 산출), `probes/`(probe 테스트 코드)

## Mode branch — aimux vs solo (decide first)

시작 시 1회 확인:

```bash
AIMemory/bin/aimux agents 2>/dev/null
```

- **aimux mode** — 명령이 동작하고 idle 워커가 보이면 당신은 **매니저**. 단계별 작업을
  `INSPECT`(코드점검)·`VERIFY`(검증/재검증)·`IMPLEMENT`(환경구성)·`TEST`(라이브/적대적 실행)로 위임하고,
  당신은 분해·라우팅·검증·종합만 한다. 라우팅은 능력 + **데이터 민감도**로(`AIMemory/agents.md`).
  매니저 패널 전달 함정 → out-of-band 운영(워커 산출 파일 직접검증 + `aimux resolve <req-id>`).
- **solo mode** — aimux 세션이 없으면 **같은 단계·게이트를 매니저 단독**으로 순차 수행.

흐름 계약은 두 모드에서 동일 — *누가 실행하느냐*만 다르다.

## Procedure

`flow.md`(런북)의 6단계 T0→T5와 `gate.md`(사용자 게이트 G0→G4)를 따른다.
표면별 기능검증 드라이버는 `surfaces/{web,api,cli,lib,tui}.md`,
경계·악성·heavy 케이스 카탈로그는 `checklists/adversarial-catalog.md`,
보고서 양식은 `templates/verify-project/`.

## Safety contract (항상 적용 — 비협상)

- 대상 `.env`는 **읽기만**(수정 금지). 비밀값은 **출력·로그·보고서에 금지** — 키 이름만(`.env.example` 수준).
- 적대적/악성 입력(rm -rf, DROP TABLE, XSS, 경로순회 등)은 **데이터로만** 주입 — 호스트에서 **실행 금지**.
- heavy/부하 케이스는 **상한**을 두고(동시성·반복·크기), 대상·호스트를 손상시키지 않게 한다.
- 대상 폴더 트리·자체 git을 **변경/커밋하지 않는다**(사용자가 명시 요청할 때만).
- probe 테스트는 대상 안에 둘 경우에도 별도 디렉토리(`tests/_verify_probes/` 등)에 격리하고 대상 레포에 자동 커밋하지 않는다.

## Done criteria

- 요청한 `--stages` 전부 게이트 통과 + 보고서 산출, `FINAL_report.md`까지 작성.
- 발견 결함은 **심각도·재현근거**와 함께 기록(수정은 별도 요청 시에만).
- 산출물 인덱스가 `FINAL_report.md` 말미에 정리됨.

## Detail

- Flow runbook → `flow.md`
- Gate templates → `gate.md`
- Surface drivers → `surfaces/` (web·api·cli·lib·tui)
- Adversarial/heavy catalog → `checklists/adversarial-catalog.md`
- Report templates → `templates/verify-project/`
- Contract / rationale → `claude/verify-project.md`
