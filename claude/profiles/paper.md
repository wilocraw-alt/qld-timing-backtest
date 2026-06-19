# profile: paper — Write a paper FROM a completed aimux multi-agent run

## 요약 (사용자용)

- **별도 프로젝트**에서 실행하지만 **이 하네스로** 수행: 이미 끝난 프로젝트의 `AIMemory/`를 입력으로 읽어 논문화. 논문 주제는 그 프로젝트의 **문제/실험(도메인)**; aimux는 산출 방법일 뿐 보통 논문의 주제가 아님.
- **관련연구 필수**: 선행연구를 조사해 본 연구와의 **유사점·차이점**을 명시(기본 포함).
- **내부 파일명 인용 금지**: `run-summary.json`·`per_agent`·`compare_⟨task⟩.md`·`work.log`·`handoff_*` 등 하네스 내부 산출물은 **인용 대상이 아니며 논문 본문에 등장하면 안 됨**. 그 데이터는 "측정 결과"로 제시하고, 인용은 실제 외부 문헌만.
- **비전문가도 이해 가능하게**: 풀려는 문제, 선택한 예제의 특성, 필요한 용어의 간단한 정의를 앞에서 짚고 들어감.
- **주제 무관 내용 제외**: 구현·실험 중 시행착오라도 논문 주제와 무관한 방향이면 과감히 뺌.
- 정량 주장은 신뢰 가능한 기계 기록에서(저자 검증용), 산출물은 **PDF + Word(.docx) + 발표자료(.pptx)** 셋 다.
- **버전 관리로 반복**: 피드백 반영 전 `make snapshot` 후 증분 수정. 통째로 갈아엎지 말 것.

---

**When to use**: PROJECT.md `profile: paper`. Produce a research paper on the
completed project's **topic / experiment (its domain)**, in a NEW session that
takes the finished project's `AIMemory/` as input evidence. The harness/aimux is
the *method by which the work was produced* — it is process, not the paper's
subject; only make aimux itself the subject if the user explicitly asks for an
"aimux paper". Pairs with the `research` profile (literature/citation
discipline) — load both.

---

## 1. Inputs (read first, in this order)

From the completed project (path given by the user):
1. `AIMemory/run-summary.json` — machine-authored metrics (schema
   `aimux-run-summary/1`): `totals`, `per_agent` (requests/completed/failed),
   `release_reasons`, `durations_seconds`, `handoffs[]`. **Source of truth for
   numbers.** This file mirrors the **latest** versioned snapshot.
   - **Versioning**: every checkpoint/shutdown saves a snapshot under
     `AIMemory/run-summary/vNNN-<ts>[-label].json` (kept for history). By
     default (no version named) write from the latest (`run-summary.json`). If
     the user asks, target a specific `vNNN` or **compare across versions**
     (e.g., milestone-1 vs final) — diff `totals`/`per_agent`/durations and
     discuss the trend.
   - If stale/absent, refresh from that project:
     `AIMemory/bin/aimux report --write` (or `checkpoint --label <m>`).
2. `AIMemory/work.log` — event narrative (HANDOFF / RECEIVED / CLOSED / NOTE /
   judgments / auto-notices). Use for the *story* and qualitative findings;
   treat its timestamps/prose as LLM-authored (less reliable than run-summary).
3. `AIMemory/handoff_*.md` — the actual plans (PROPOSE drafts, final plan) and
   worker reports.
4. `DESIGN.md`, `AIMemory/tmux-handoff.md`, `AIMemory/agents.md` — the method
   and the agent-capability context.

> These are **author-side inputs** for your own accuracy. Their file names and
> field names (run-summary.json, per_agent, compare_*.md, work.log, handoff_*…)
> must NOT appear in the paper — present their data as measured results. See §3.

## 2. Procedure (the "skill")

1. **Scope the paper** with the user: topic/angle, target reader/venue, length.
   Confirm before drafting (follow the diverge–then–converge habit: ask the
   angle first).
2. **Extract evidence** into a small author-side `data/metrics.md` mapping each
   intended claim → its source field/line. No number enters the paper without
   such a mapping. (This file is for you, not part of the paper.)
3. **Survey related work**: gather the relevant prior research for the paper's
   domain and note, for each, the **similarities and differences** vs. this
   work (what's the same, what's new/better/different). Use the `research`
   profile's citation discipline; cite real external literature only.
4. **Set the stage for a non-expert reader** (Introduction/Background): state
   the problem being solved and why it matters, describe the chosen example and
   its relevant characteristics, and briefly define any key terms/jargon before
   using them.
5. **Copy the scaffold**: `cp -r <harness>/templates/paper ./paper` (or start
   from it). Fill `sections/*.tex`:
   - Background/Related work ← step 3 (prior research, similarities/differences).
   - Method ← the experiment design (and, briefly, how it was produced).
   - Results ← the measured data + concrete episodes, presented as results.
   - Discussion ← interpretation, threats to validity, limits.
6. **Add visual aids** (intuition first):
   - An **experiment-structure diagram of the paper's own experiment** (not the
     aimux internals) — edit `figures/experiment-structure.svg`.
   - **Numerical comparisons as BOTH a `booktabs` table and a chart** — edit
     `figures/results-bar.fig.tex` (pgfplots) or add more `*.svg`/`*.fig.tex`.
   - Include figures as `\includegraphics{figures/<name>}` (no extension) so
     they render in both PDF and Word.
7. **References**: cite real external literature in `references.bib` (the
   related-work sources). Do NOT cite or name internal harness artifacts.
8. **Build ALL formats**: `make` → `main.pdf` + `main.docx` + `main.pptx`. Report TODOs.
    - **Prerequisites** (deck only; pdf+docx unaffected if missing): Node.js + npm
      (pptxgenjs installed via `cd slides && npm install`), LibreOffice (`soffice`),
      poppler (`pdftoppm`), `pip install "markitdown[pptx]"`. If Node is absent,
      `make pptx` prints a warning and skips gracefully.
    - **Author the deck**: read `.claude/skills/pptx/SKILL.md` and
      `slides/README.md`. Create a ~12-slide academic talk (title, problem,
      related work, method, experiment, results, discussion, limitations,
      conclusion, thanks) by editing the CONTENT section at the top of
      `slides/build_pptx.js`. Drive content from the paper's `sections/*.tex`
      (primary) or `main.docx` via markitdown (fallback). Reuse already-built
      `figures/*.png` — no extra figure generation. Follow the pptx skill's
      design guidance (palette, motif, no boring slides).
    - **Build**: `make pptx` (or `node slides/build_pptx.js` from the paper root).
    - **QA loop (REQUIRED)**: `make pptx-qa` — content check via
      `python3 -m markitdown main.pptx`, then render to `slide-NN.jpg` images.
      Perform a **visual subagent inspection** per the pptx skill's QA prompt.
      Fix issues in `slides/build_pptx.js`, rebuild, re-verify. Complete at least
      one fix-and-verify cycle before declaring success.

### Iterating on feedback — VERSION, don't clobber
When the user reviews a draft and asks for changes:
- FIRST snapshot the current draft: `make snapshot LABEL=<what-it-is>`
  (→ `versions/vNNN-<date>-<label>/`, sources + built PDF/DOCX/PPTX + `slides/`
  scaffold preserved).
- Then revise **incrementally** — edit only the sections the feedback targets.
  **Never regenerate the whole paper from scratch** (that wholesale-replaces
  approved content). For the deck, edit the CONTENT section of
  `slides/build_pptx.js` — never regenerate the script from scratch. Earlier
  versions stay in `versions/` for comparison/rollback.

## 3. Rules

- **Related work is mandatory.** Include a section surveying prior research in
  the paper's domain and stating, explicitly, the similarities and differences
  vs. this work.
- **Never name internal harness artifacts in the paper or deck.** `run-summary.json`,
  `per_agent`, `compare_⟨task⟩.md`, `work.log`, `handoff_*`, `.aimux`, the word
  "aimux"/"dispatcher", etc. are NOT citable sources and must not appear in the
  paper text, captions, references, slide titles, slide bullets, figure captions
  OR speaker notes. Present their data as measured results only ("we observed…",
  "the success rate was…"). Citations = external literature only.
- **Write for a non-expert.** Assume little domain/dev background: motivate the
  problem, describe the chosen example and its relevant properties, and define
  key terms briefly before using them.
- **Stay on theme.** Implementation/experiment detours and trial-and-error that
  don't serve the paper's thesis may be omitted; include a setback only when it
  supports the message (e.g. a genuine finding).
- **Evidence only / don't fabricate.** Every quantitative claim traces (in your
  author-side notes) to a real measurement; mark inference as
  "estimate"/"hypothesis"; if a number isn't available, say so.
- Diagrams: see `claude/core.md`. Reuse `research` profile conventions for
  external citations.

## 4. run-summary.json schema (`aimux-run-summary/1`)

```
session, project_dir
totals: { requests, responses, notices, highfives, redispatches }
release_reasons: { response-seen, idle-stable, unacked, timeout, pane-gone }
durations_seconds: { session_span, turnaround_min, turnaround_avg, turnaround_max }
per_agent: { <name>: { requests, completed, failed } }
handoffs: [ { type, to, handoff, delivered, released, release_reason } ]
```
- `redispatches` = requests beyond the first per work-topic (retry + reroute).
- `completed` = requests that returned a response (`response-seen`); `failed` =
  the rest (no return / unacked / timeout).
- `notices` = dispatcher "worker freed without a response" events (a reliable
  reassignment-trigger proxy).
