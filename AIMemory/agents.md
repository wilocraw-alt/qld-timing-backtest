# Agent capability & know-how ledger

How the manager picks agents and gets the most out of each. **Read this before
assigning work; append to "Learnings" after every notable success or failure.**
Keep entries short and concrete. Pair it with the live state board:

```
AIMemory/bin/aimux agents   # NAME · KIND · idle/busy/waiting · what it's HANDLING now
```

`waiting` = the worker is BLOCKED on a user prompt (held by the dispatcher, being
unblocked) — it is NOT idle and NOT a failure. Never reassign or re-route a
`waiting` worker; answer its prompt (low-risk) or let the human handle it
(high-risk). Only `idle` means free-to-assign.

## Operating rules (manager)

0. **Diverge-then-converge planning first (non-trivial work).** Confirm
   requirements with the user; then have EVERYONE independently draft their own
   plan in parallel — `PROPOSE` to each worker (they propose, don't build) and
   draft your own; analyze the pros/cons across all proposals and synthesize the
   best parts into the final plan before decomposing. (See tmux-handoff.md
   "Phase 0".)
1. **Profile by KIND, not just name.** Match the task to the agent's strengths
   below; give the hardest/most-tool-heavy unit to the most reliable agent.
2. **Idle is not success.** A worker going idle ≠ it did the work (the
   dispatcher sends a `notice` when a request is freed without a response).
   Always verify the actual output. (A worker *blocked on a user prompt* is a
   third state — the dispatcher HOLDS it, never reassigns it, and routes by
   risk: a **LOW-RISK** prompt becomes a `notice` to YOU saying "act as the
   human" — read its excerpt, decide, and answer it directly in that pane with
   `tmux send-keys -t <pane> '<answer>' Enter` (the one allowed direct paste —
   answering a prompt is not a handoff); pick whatever keeps the assigned work
   moving. A **HIGH-RISK** prompt — judged by the ACTION behind it (destructive /
   irreversible / external / touches credentials), NOT by whether it offers an
   "always allow / don't ask again" option — is escalated to the real human only;
   don't answer it. A routine permission request is LOW-RISK: just approve it to
   keep work moving. If you read a low-risk notice and judge it actually risky,
   escalate instead of answering. If a CLI's prompt isn't recognized, add its
   marker to `AIMUX_WAIT_PATTERN`; tune what counts as dangerous via
   `AIMUX_WAIT_RISK_PATTERN`.)
3. **Failure → diagnose, adapt, retry ONCE, then re-route.** Don't permanently
   abandon an agent on first failure:
   - Read *why* it failed (its pane + `work.log` + any BLOCKER it returned).
   - Re-issue adapted to its known constraints (smaller scope, single step,
     "apply the edits now", explicit "actually run the command").
   - If it still fails, re-route the unit to an **idle, capable** agent
     (`aimux agents` → pick `state=idle` with the right KIND).
   - Record the cause and what worked in **Learnings** below.
4. **Delegate ALL substantive work — implementation, integration, test, verify.**
   Producing/editing/running anything is *work*, not judgment. Even testing or
   assembling the finished build is a delegated unit (roles `IMPLEMENT` / `TEST`
   / `VERIFY`): hand an idle worker "write AND RUN a test/harness for <criteria>,
   report pass/fail + evidence" or "integrate A+B and confirm it builds." Do NOT
   write code, verify behavior, or hand-assemble while workers can do it. Reserve
   for yourself only decomposition, routing, and the accept/re-route decision
   from the returned evidence.
   - **Manager does work directly ONLY after 2+ failures + user approval.** If a
     unit has failed delegation **twice or more** (diagnosed, adapted, retried,
     re-routed to another capable worker — not merely "no idle worker now"),
     surface it to the user and take it over yourself ONLY with their explicit
     approval. Default is always: keep it on a worker. (Acting as the human to
     answer a low-risk prompt is orchestration, not "doing the work" — no
     approval needed.)
5. **Route by data sensitivity, then by capability.**
    - **Sensitive / personal / confidential data stays local → qwen ONLY.**
      `claude`, `opencode`, `antigravity` are cloud models — sending them private data
      ships it to an external provider. Never paste personal/sensitive content
      (PII, secrets, internal/confidential material) into a cloud agent; route
      that unit to **qwen** (fully local), accepting its weakness as the cost of
      privacy.
    - **qwen is a weak local model (gemma4:e4b)** — for non-sensitive work, give
      it ONLY low-stakes, self-contained units: research / info-gathering,
      simple shell scripts, small mechanical edits. Not main logic.
    - **Main / complex / quality-critical work → a capable worker** (e.g.
      opencode or antigravity), never qwen. The manager does NOT self-serve when
      workers are merely busy — queue or wait. (Direct manager work only via the
      2-failure + user-approval gate; see rule 4.)

## Agents (seed — refine from Learnings)

### claude-code
- Strong reasoning, reliable, applies edits autonomously. Can run as **manager**
  OR **worker** — the role is chosen at launch (see the roster `[manager]` /
  `[worker]` pools) and set by its session brief + onboarding, not by being
  claude. As MANAGER: orchestrates, does not do the work itself — takes a unit
  directly ONLY after it has failed delegation 2+ times AND the user explicitly
  approves (Operating rule 4); "workers are busy right now" is not a reason. As
  WORKER: a strong, reliable implementer.

### opencode
- **Most reliable worker** observed. Handles multi-file implementation well and
  applies edits without prompting. Good default for important/complex units and
  as the re-route target when another worker fails.

### antigravity
- Claude-Code-style CLI (command `agy`). Supports `--dangerously-skip-permissions`
  (auto-approve) and resumes via `--continue` (most recent conversation, so the
  nested-project bleed caveat applies — keep projects in separate git roots).
- Loads `AGENTS.md` for its project brief (shared with opencode).
- Uses `.antigravity/` for project-local config data.

### qwen (qwen-code; small **fully-local** model, e.g. gemma4:e4b)
- **Weak** and slow: tends to **narrate tool calls instead of running them**
  ("[완료]" without acting) — needs an explicit "actually RUN the command, do
  not just describe it." May also plan edits without applying them; instruct explicitly to "APPLY/WRITE the files now."
- **Use it for, and basically only for:**
  - **Privacy-sensitive units** — because it runs entirely on-machine, it is
    the ONLY agent allowed to touch personal/sensitive/confidential data
    (never send such data to opencode/antigravity/claude).
  - **Low-stakes simple work** — research / information gathering, simple shell
    scripts, small self-contained mechanical tasks.
- **Do NOT give qwen the main/complex implementation** — route that to opencode
  or antigravity. Keep qwen's units small, explicit, and single-step.

## Learnings (append-only; newest at the bottom)

- 2026-05-30 | qwen | created the result file but only *described* the return
  `aimux enqueue` command; ran it only after an explicit "actually execute, do
  not describe."
- 2026-06-15 | opencode | handled full release finalization (version bump + changelog + git add -u + commit + push) reliably. Diagnosed that the pre-push dist-scan hook REJECTS work.log's session-specific absolute HOME paths, and excluded work.log from the release commit. Lesson: for release/commit units, tell the worker the dist-scan hook rejects absolute home paths → stage harness files explicitly and keep work.log / run-summary OUT of release commits.
- 2026-06-15 | antigravity | confirmed live (post-auth smoke): `agy models` lists models; `agy -p` does real inference; agy auto-loads AGENTS.md (so initfile_of=AGENTS.md is correct); resumes via --continue; no project-local config dir (HOME-based at ~/.gemini/antigravity-cli). Honors --dangerously-skip-permissions.
- 2026-06-15 | dispatcher | `pane_waiting` matches `AIMUX_WAIT_PATTERN` against the WHOLE visible screen, not just a live prompt box — so any pane whose last rendered text contains pattern words ("Do you want to|Continue?|Proceed?|approve this|Press Enter…") is mislabeled `waiting` and gets no delivery. Hit the MANAGER hardest (it continuously renders handoff/PROTOCOL/quoted-prompt text) AND any worker whose last message quoted such words (e.g. opencode after returning a diagnosis ABOUT the pattern — a self-referential deadlock that blocked a release delivery). Fix (v0.3.2): exempt the manager pane from `pane_waiting` at the deliver guard, `process_inflight` waiting-block, and the `agents` board; workers keep wait-detection. Lesson: a worker can be FALSE-`waiting` purely from leftover on-screen text → if a delivery to an idle pane stalls, check whether its visible screen false-matches the wait pattern (`tmux capture-pane -p -t <pane> | grep -iE "$AIMUX_WAIT_PATTERN"`); the running dispatcher only picks up an aimux fix on the NEXT session relaunch.
- 2026-06-15 | manager(claude) | when the delivery channel itself is deadlocked (the pane_waiting bug above blocked ALL delivery to a false-`waiting` worker), delegation is impossible — got explicit user approval and did the fix + releases directly. Lesson: a broken delegation CHANNEL (not a worker failing) is a valid trigger to surface to the user and take a unit over with approval; don't keep re-enqueueing into a dead channel.
- 2026-06-15 | dispatcher | `deliver()` was missing `-p` on `tmux paste-buffer`, so multi-line handoff prompts were sent without bracketed-paste wrapping. On CLIs that support bracketed paste (antigravity = Gemini CLI), each newline was replayed as Enter, causing the first line to be submitted immediately and the rest to queue as separate messages. Fix: add `-p` flag so tmux wraps the paste in `ESC[200~…ESC[201~` and the entire handoff body arrives as one paste. Takes effect on next `aimux-up` relaunch.

- 2026-06-15 | antigravity/dispatcher | antigravity (Gemini CLI) enables bracketed-paste, so the dispatcher's pre-fix `paste-buffer` (no `-p`) split multi-line handoffs: first line submits, rest queue as separate messages → misbehavior. Until a relaunch loads the `-p` fix (Unit F), antigravity is UNUSABLE for live delivery; route everything to opencode. After relaunch, antigravity is fine again. Lesson: a known-buggy delivery channel (not a worker-capability failure) is grounds to pull that worker from the routing pool for the session and serialize on a reliable one.

- 2026-06-15 | manager(claude) | v0.4.0 build (GitHub install/update + `aimux-up make` mode) ran cleanly as a full delegated session with `-p` fix in place: decomposed by DEPENDENCY into UNIT1 install/update subsystem (opencode, heaviest+most-coupled → most reliable worker), UNIT2 make-mode + UNIT3 release script (antigravity), then Wave-2 docs + E2E verify in parallel. Manager review (not the worker's self-report) caught 3 real defects and re-routed focused FIX units: (a) manifest omitted the update tooling itself from `managed` → updater couldn't self-update; (b) `harness-release.sh --dry-run` still ran bump-version + make-dist for real (mutated VERSION/dist); (c) verify-as-work paid off — delegated E2E proved managed-overwrite + project/seed preservation. Lesson: trust worker EVIDENCE, but still independently grep the actual files before accepting — every defect here was invisible in the (passing) self-reports.
- 2026-06-15 | antigravity | permission-prompt friction is high without auto-approve: every DISTINCT command word triggers a fresh "Do you want to proceed?" prompt (its "always allow" options 2/3 are scoped to that exact command string, so they don't generalize). A delegated build stalls repeatedly waiting on the manager. The prompt shows the command after `Requesting permission for:` (NOT `Full command:`), so parse both. Lesson: launch with `AWM_AUTO_APPROVE=1` for antigravity-heavy delegation, OR have the manager auto-answer a SAFE whitelist (read-only/local-build/repo-internal: bash -n, cat, grep, mkdir, chmod, git archive/add/status, ./make-dist.sh, bin/harness-*, smoke.sh, …) and escalate only destructive/external/credential commands (git push, reset --hard, gh release create, rm -rf outside tmp, sudo).
- 2026-06-15 | opencode+antigravity | when documenting an identifier-SCRUBBING feature, workers wrote the literal example tokens (the maintainer's GitHub account/username) INTO shipped docs (DESIGN.md, HARNESS-CHANGELOG.md) — i.e. describing the scan-by-example leaked the very tokens make-dist scans for, which would have blocked the release build. Lesson: in any handoff that touches docs about the scrub/identifier feature, instruct the worker to use GENERIC placeholders ("maintainer account/username"), never the literal account strings, in files that ship (everything not `export-ignore`d). Always re-run the dist identifier scan on the STAGED tree before committing.

- 2026-06-19 | antigravity | given a simple self-contained unit (write metrics.py + baselines.py), it ignored the handoff's explicit "env is already fixed, do not run pip" and burned ~15min thrashing the environment (`pip install -U yfinance`, `yfinance==999.999`, `yfinance==0.2.66` version-probing) while producing ZERO deliverable files, repeatedly blocking on per-command permission prompts. Lesson: antigravity is high-friction for units that touch (or merely mention) the environment — it latches onto env-debugging rabbit holes and stalls. For such units route to opencode, or strip ALL env mentions from its handoff and pre-install deps so it never reaches for pip. `pip install -U <pkg>` from a worker can also silently re-break a pinned shared env — deny those prompts.
