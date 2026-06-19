# flow.md — ideate runbook (operational)

## 요약 (사용자용)

- `SKILL.md`가 가리키는 실행 런북. S0~S4 각 단계에서 **무엇을·어떤 aimux 명령으로·어떻게 회수**하는지.
- aimux 모드(워커 위임)와 solo 모드(매니저 단독) 양쪽 절차를 함께 기술.
- 게이트 질문은 `gate.md`, 방법론은 `methods/`, 산출 채움은 `templates/ideate/`.

---

**When to read**: while executing the ideate skill. This is the step-by-step procedure; `claude/ideate.md` is the contract/why behind it.

Below, "aimux:" lines are run only in aimux mode; in solo mode the manager performs the same unit itself.

---

## S0 — Capture & frame

1. If a memo file was given, read it. Otherwise ask the user for the wish in their own words.
2. Restate in 2–3 sentences: "~하시려는 거죠?".
3. Ambiguity triage → Vague / Fuzzy / Clear (`claude/ideate.md §1`). Record it.
4. **Gate G0** (`gate.md`). On pass, continue; on fail, re-frame.

Write the framing + level to the ideation record:
```bash
cat >> AIMemory/work.log <<'EOF'

### <date> | <model> | NOTE
ideate S0: wish=<one line>, ambiguity=<Vague|Fuzzy|Clear>.
EOF
```

## S1 — Methodology selection (meta diverge→converge)

1. From `methods/selection.md`, take the candidate set suggested for the ambiguity level.
2. **Diverge**:
   - aimux: send `PROPOSE` to 1–2 idle workers — "이 희망 `<요약>`에 적합한 발굴 방법론 2~3개와 이유, 각 방법이 답할 미지수." Draft your own candidate set in parallel.
   - solo: list candidate methods yourself with rationale.
   ```bash
   # aimux example
   AIMemory/bin/aimux enqueue --to opencode --handoff <handoff> --roles PROPOSE --from %0
   ```
3. **Converge**: synthesize → pick **2–3** methods, each bound to **one concrete unknown** (drop any method with no unknown). Anti-theater rule (`methods/selection.md`).
4. **Gate G1** (`gate.md`). Clear wishes may auto-pass.

## S2 — Idea divergence

1. For each chosen method, prepare a worker prompt from that method's file (`methods/<m>.md` → "Worker prompt").
2. **Diverge** (parallel):
   - aimux: fan out one `PROPOSE` unit per method/angle to idle workers (`aimux agents` to find them). **Sensitive wish → qwen only.**
   - solo: work each method in turn yourself.
3. Collect framed options. **Manager dedups/cleans** before showing anything to the user.

## S3 — Convergence & valuation

1. Score candidates with `templates/ideate/valuation-rubric.md` (실현성·임팩트·적합·노력).
   - aimux: delegate as `VERIFY` units — "이 아이디어의 강점·위험·필요 리소스를 평가하고 증거를 보고하라" (one per candidate, parallel). Run a `pre-mortem` (`methods/pre-mortem.md`) on the front-runner.
   - solo: score and pre-mortem yourself.
2. **Converge**: synthesize the evidence into a recommended idea + rationale.
3. **Gate G2** (`gate.md`). On fail, re-converge from another candidate or loop to S2 (respect the 3-round cap in `claude/ideate.md §3`).

## S4 — Concretize to PROJECT.md

1. Fill `templates/ideate/project-draft.md` → the target project's `PROJECT.md` (이름·목적·profile·입력·출력·주요 제약·기술 스택·경로). Preserve the original wish as the request memo.
2. Recommend the **downstream profile** (dev/research/docs/data/paper) with one-line reason.
   - aimux (optional): a `VERIFY` unit checks PROJECT.md completeness against the template.
3. **Gate G3** (`gate.md`). On approval, the PROJECT.md is final.

## Exit

Hand the approved PROJECT.md to `claude/intake.md` (fields filled → light confirm → `claude/plan.md`).
Log a closing `NOTE` summarizing chosen methods, the converged idea, and the recommended profile.
