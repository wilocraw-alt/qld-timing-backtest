# gate.md — ideate user gates

## 요약 (사용자용)

- 발굴 흐름 각 단계 끝의 **사용자 게이트** 질문 템플릿 + 통과/실패 기준.
- 원칙: **단일 확인/선택**으로 최소화(서술 강요 금지). 모호도가 낮으면 일부 게이트는 자동 통과.
- 실행 중 채우는 체크리스트는 `templates/ideate/gate-checklist.md`.

---

**When to read**: at the end of each stage in `flow.md`. Keep gates lightweight — one confirm or one pick. The point is to let the user steer and signal satisfaction, not to interrogate.

User-facing output is Korean, vertical `key: value`, no horizontal tables.

---

## G0 — 의도 확인 (after S0)

- **Ask**: "요청하신 걸 이렇게 이해했습니다: `<2~3문장 요약>`. 이 방향이 맞나요? 빠진 게 있나요?"
- **Pass**: user confirms the framing.
- **Fail**: re-frame from the correction; re-ask. Do not proceed to S1 without G0 pass.

## G1 — 방법 승인 (after S1)

- **Ask** (present 2–3 chosen methods, each with the unknown it answers):
  ```
  이 희망엔 다음 방법으로 발굴해 보려 합니다:
    - <방법1> → 풀 미지수: <unknown1>
    - <방법2> → 풀 미지수: <unknown2>
  이대로 진행할까요? 빼거나 바꿀 방법 있나요?
  ```
- **Pass**: user approves (or **auto-pass** when ambiguity=Clear — note it and proceed).
- **Fail**: re-pick methods per `methods/selection.md` and re-ask.

## G2 — 컨셉 확정 (after S3)

- **Ask** (present the recommended idea + 1–2 runners-up with rubric scores):
  ```
  발굴 결과 추천 아이디어:
    추천 : <idea> — <한 줄 근거> (점수 요약)
    대안 : <idea2>
  이 컨셉으로 추진할까요? 보정하거나 다른 후보로 갈까요?
  ```
- **Pass**: user picks/refines a concept.
- **Fail**: re-converge from another candidate, or loop back to S2 (3-round cap, `claude/ideate.md §3`).
- **No viable idea**: say so plainly and stop — do not manufacture a project.

## G3 — 설계도 승인 (after S4)

- **Ask**: present the filled PROJECT.md (fields + recommended profile). "이 PROJECT.md로 확정할까요? 수정할 항목 있나요?"
- **Pass**: PROJECT.md is final → hand to `claude/intake.md`.
- **Fail**: edit the specified fields and re-show.

---

## Fast-track (ambiguity = Clear)

- G1 may auto-pass (record the chosen methods anyway).
- S2 divergence may be skipped; go light valuation → S4.
- G0, G2, G3 still require an explicit user signal — never skip the framing and final-approval gates.
