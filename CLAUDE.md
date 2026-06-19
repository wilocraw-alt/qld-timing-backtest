# CLAUDE.md

## 요약 (사용자용)

- 이 파일은 모델이 세션마다 항상 읽는 진입점. 본문은 토큰·추론 효율을 위해 영어로 작성됨.
- 사용자 응답은 **한국어**, 가로 표 금지, 세로 `key: value` 형식.
- 세션 시작 시 로딩 순서: `PROJECT.md` → (필요 시 `intake.md`) → `core.md` + `profiles/{profile}.md`.
- 표준 작업 흐름: 계획(`plan.md`) → 구현(`implement.md`) → 검증(`verify.md`).
- **"매니저로 진행"·"여러 에이전트로 병렬 진행" = aimux 오케스트레이션**(tmux 패널·`aimux enqueue` 위임). claude 내장 subagent를 다수 띄우는 게 아님. 미실행 상태면 `! AIMemory/bin/aimux-up` 안내. (§0 always-on 규칙 참조)
- 푸시·파괴적 명령은 **사용자가 명시 요청할 때만** 실행. (예외: 아래 신규 프로젝트 부트스트랩)
- GitHub은 **`gh` 인증 계정**을 사용(`gh api user --jq .login`) — 사용자명 하드코딩 금지(zip 배포 시 타인에게 잘못 적용·개인정보 노출). `gh` 미설치/미인증이면 멈추고 `gh auth login` 안내. **신규 프로젝트(리모트 없음)는 private 레포 생성+초기 commit·push가 기본** (민감데이터 프로젝트는 자동 push 금지·확인).

---

This file lists Claude's **always-on rules** and a guided index of stage files to load on demand.
- Project-specific info lives in `PROJECT.md`.
- Cross-cutting helper rules live in `claude/core.md`.
- Project-type rules live in `claude/profiles/{profile}.md`.
- Stage guides live in `claude/`.

**Load files only when needed** to conserve context.

---

## 0. Always-on rules

- **User-facing language: Korean.** For technical terms (table names, function names, library names) include a brief Korean gloss.
  - Example: `dataset_meta`(데이터셋 메타정보 테이블)
- **Output format: vertical `key: value` blocks.** **Do not use horizontal markdown tables** (`| col | col |`) in user-facing output. (Tables inside guide files like this one are fine — they're not user output.)
- **Reasoning language: English internally, Korean for the final user response.** (Performance optimization — English-dominant training distribution.)
- **No hardcoding.** Dates, paths, URLs, parameters must come from input files or CLI arguments — never embedded as literals.
- **Secrets stay in `.env`.** Read from `.env`, maintain `.env.example` alongside. Never inline credentials.
- **No guessing.** If you don't know, verify or ask the user (1–3 condensed questions).
- **"Manager" role = aimux orchestration, NOT Claude's built-in subagents.** When the user asks you to act as the **manager**, to **orchestrate / delegate / split the work across agents in parallel**, or to "여러 에이전트로 진행" — that means the **aimux** multi-CLI workflow (persistent tmux panes of possibly-different CLIs, work delegated via `AIMemory/bin/aimux enqueue`), governed by `AIMemory/briefs/manager.md` + `AIMemory/PROTOCOL.md`. It does **NOT** mean spawning Claude's built-in `Agent`/Task subagents to do the work.
  - **Already inside an aimux manager pane** (your onboarding/brief message named you the manager): follow `AIMemory/briefs/manager.md` — delegate every substantive unit via `aimux enqueue`, never via built-in subagents.
  - **Plain session, no aimux running**: do **not** silently fan out Claude subagents as a substitute. The aimux launcher (`AIMemory/bin/aimux-up`) is TTY-interactive (it prompts to pick a manager + workers), so guide the user to run it themselves (e.g. `! AIMemory/bin/aimux-up`), then orchestrate per the manager brief.
  - Claude's built-in `Agent` subagents are for **your own read-only exploration/search only** (e.g. `subagent_type=Explore` in `plan.md §1.2`) — never as the work-delegation mechanism for a multi-agent build/test/verify task.
- **Destructive commands** (`git push`, `reset --hard`, `clean -f`, file deletion, etc.): execute **only when the user explicitly requests them** — *except* the new-project GitHub bootstrap below, which is a standing default.
- **GitHub via `gh` (account-agnostic).** The remote account is always **whoever `gh` is authenticated as** (`gh api user --jq .login`) — never hardcode a username. This harness ships as a `dist/` zip to other people, so a baked-in account would be both wrong for them and a personal-info leak. If `gh` is missing or not authenticated, **stop and guide the user** (`gh auth login`) instead of guessing a remote.
  - **New-project default = private repo + push.** When the project is brand-new (no git repo, or a repo with no `origin` remote), the default is to make the initial commit and create a **private** repo under the gh account, then push: `gh repo create <name> --private --source=. --remote=origin --push`. Announce the resulting `owner/name`; the user can rename or make it public later. See `claude/intake.md §3.8`.
  - **Sensitive-data guard.** If the project handles personal / sensitive / confidential data, do **not** auto-push — confirm with the user first (pushing ships it to an external service).
  - Existing repos (already have a remote — e.g. make_Harness itself) keep the normal rule: push only on explicit request.
- **Long-running batch / subagent work**: before starting, also write a standalone status-check script (`status.sh` or `check_status.py`) the user can run from a terminal outside Claude's session.

---

## 1. Files to load at session start

In this order:

1. **`PROJECT.md`** — project name, purpose, profile, tech stack, domain notes.
   - If any required field (`이름`·`목적`·`입력`·`출력`) is empty → **시작 시점에 사용자에게 진입 경로를 물어본다**:
     - 요청이 **모호한 희망**(구체적 스펙 아님)이면 → `claude/ideate.md`(`/ideate` 스킬)로 발산→수렴 구체화 후, 산출된 PROJECT.md로 intake 진입.
     - 이미 **구체적 스펙**이거나 사용자가 직접 진행을 택하면 → 바로 **`claude/intake.md` 실행**.
   - If `profile` is empty → intake §3.3 recommends and confirms one.
2. **`claude/core.md`** — cross-cutting helper rules (memory, diagrams, general outputs, batch scripts).
3. **`claude/profiles/{profile}.md`** — exactly one file, chosen by PROJECT.md's `profile` value.

After intake completes, transition to the normal workflow (§3).

---

## 2. Stage-specific references (load only when needed)

| Situation | File | When to load |
| --- | --- | --- |
| Cross-cutting rules | `claude/core.md` | Once at session start (§1) |
| Manager / multi-agent orchestration (aimux) | `AIMemory/briefs/manager.md` + `AIMemory/PROTOCOL.md` | When asked to act as manager / orchestrate / run agents in parallel — see §0 "Manager role" rule (aimux, not built-in subagents) |
| Profile-specific rules | `claude/profiles/{profile}.md` | Once at session start (§1) |
| Vague wish / new idea (no concrete spec) | `claude/ideate.md` | Before intake — when PROJECT.md fields are empty and the request is only a fuzzy wish (ask the user at the start which path to take) |
| Verify a GIVEN (third-party) project | `claude/verify-project.md` (skill `/verify-project`) | When handed an existing project folder to vet (동작·품질·안전성) — NOT to build one. 4단계 코드→설치→기능→적대적 검증. aimux 매니저로 동작(없으면 단독). |
| New project intake | `claude/intake.md` | When PROJECT.md is incomplete |
| Planning | `claude/plan.md` | Just before a non-trivial task |
| Implementation | `claude/implement.md` | During code changes |
| Verification | `claude/verify.md` | After changes, before reporting done |
| Large files / data | `claude/token-efficiency.md` | Before reading or editing big files |
| Reasoning-heavy work | `claude/llm-performance.md` | Design, debugging, deep analysis |
| Model selection / switching | `claude/model-routing.md` | Once at session start + on trial-and-error |

> Loading discipline: read one file just before entering its stage, then swap to the next. Don't read them all up front.

---

## 3. Workflow skeleton

```
Load PROJECT.md → check profile
   ↓
If incomplete (name / purpose / input / output / profile missing)
   → ask at start: 모호한 희망 vs 구체적 스펙?
       ├ 모호한 희망 → claude/ideate.md (/ideate): S0→S4 발산→수렴 → 채워진 PROJECT.md → intake
       └ 구체적 스펙 / 직접 진행 → claude/intake.md (request memo → profile recommendation → fill fields)
   ↓
Load claude/core.md + claude/profiles/{profile}.md
   ↓
[PLAN]    claude/plan.md
          → step checklist + verification criteria
          → save CHECKLIST.md → get user agreement
   ↓
[BUILD]   claude/implement.md (+ token-efficiency.md, profile output rules as needed)
          After each step:
            1) Update CHECKLIST.md (tick the box, append history line)
            2) Print progress (N / total, next step) to user
            3) Decide on context compaction (/compact conditions)
   ↓
[VERIFY]  claude/verify.md (against CHECKLIST.md criteria)
          → mark CHECKLIST.md fully complete
   ↓
On failure or stalling → claude/model-routing.md (rollback, replan with Opus)
   ↓
Update docs / memory → commit & push (with user approval)
```
