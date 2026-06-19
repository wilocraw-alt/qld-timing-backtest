---
name: ideate
description: Turn a vague wish into a concrete PROJECT.md via two-level diverge→converge ideation. Use BEFORE a project starts when the user has only a fuzzy idea (not a concrete spec) and PROJECT.md is empty. Runs the manager that drives aimux workers (or works solo if no aimux session). Invoke as /ideate or /ideate <memo-file>.
---

# SKILL: ideate — Pre-project ideation harness

모호한 희망사항을 **발산→수렴**으로 구체화해 `PROJECT.md`를 산출하는 사전 단계 스킬.
`paper`(사후 논문화)의 대칭. 이 스킬은 **매니저 역할**로 동작하며, aimux 워커에게 PROPOSE/VERIFY를
위임하거나(세션 있을 때) 단독으로 수행한다(없을 때).

## When to use

- The user arrives with a **vague wish**, not a concrete spec, and no filled `PROJECT.md` yet.
- For an already-concrete request, skip this and use `claude/intake.md` directly.

## Invocation

- `/ideate` — elicit the wish conversationally.
- `/ideate <memo-file>` — start from a free-text idea memo, supplement by conversation.

## Inputs / Outputs

- **Input**: a vague wish (conversation and/or memo file).
- **Output**: a filled `PROJECT.md` at the target project root (+ an ideation record under `AIMemory/`).

## Mode branch — aimux vs solo (decide first)

Run this check at start:

```bash
AIMemory/bin/aimux agents 2>/dev/null
```

- **aimux mode** — if the command works and lists idle workers, you are the **manager**. Delegate
  divergence (`PROPOSE`) and valuation (`VERIFY`) to workers in parallel; you converge. Route by
  capability and **data sensitivity** (sensitive/personal wishes → qwen only; `AIMemory/agents.md`).
- **solo mode** — if there is no aimux session, run the **same stages and gates yourself**,
  sequentially: you generate candidate methods, candidate ideas, and valuations in-session.

The flow contract is identical in both modes — only *who executes* the diverge units changes.

## Procedure

Follow `flow.md` (the runbook) for the five stages S0→S4 and `gate.md` for the user gates G0→G3.
The methodology library is in `methods/`; selection uses `methods/selection.md` (two-level
diverge→converge, max 2–3 methods, each bound to one concrete unknown). Fill the output with
`templates/ideate/` (draft template + valuation rubric + gate checklist).

## Done criteria

- All gates passed; `PROJECT.md` filled (이름·목적·profile·입력·출력·제약·스택·경로) with a recommended
  downstream profile; original wish preserved as the request memo.
- Control then passes to `claude/intake.md` → `claude/plan.md`.

## Detail

- Flow runbook → `flow.md`
- Gate templates → `gate.md`
- Methods → `methods/` (+ `methods/selection.md`)
- Contract / rationale → `claude/ideate.md`
