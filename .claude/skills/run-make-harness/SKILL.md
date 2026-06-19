---
name: run-make-harness
description: Build, launch, and drive the make_Harness aimux multi-agent harness. Use to run, start, smoke-test, or drive aimux — the tmux-based dispatcher/queue that delivers AICP handoffs between agent panes (manager + workers). Covers the headless smoke driver (proves pane-registry → queue → dispatch → injection without real agent CLIs) and the interactive launcher (aimux-up / aimux shell). Invoke for "run make_Harness", "test aimux", "launch a multi-agent session", "drive the dispatcher".
---

# Run make_Harness (aimux harness)

make_Harness is **not a web/GUI/server app** — it is a tmux-based multi-agent
orchestration harness. The "app" is the `aimux` CLI (`AIMemory/bin/aimux`, the
single-dispatcher queue) plus `aimux-up` (the interactive launcher that brings up
a tmux window of agent CLI panes + a dispatcher). There is **nothing to compile**:
pure bash, dependencies are **tmux + coreutils only**.

The agent-facing way to drive it headlessly is the **smoke driver**
`.claude/skills/run-make-harness/smoke.sh` — it spins up an isolated throwaway
tmux server, registers dummy panes, enqueues a high-five, runs the dispatcher,
and asserts the paste was injected. It exercises the full core loop
(**pane registry → queue → dispatcher delivery → injection**, and incidentally
the worker→manager return) without any real agent CLI and **without touching a
live session**.

Paths below are relative to the repo root (`<unit>` = the make_Harness checkout).

## Prerequisites
`tmux` (verified with 3.0a) and coreutils. Already present in this container; on a
bare box:
```bash
sudo apt-get update && sudo apt-get install -y tmux
```

## Build
None. Ensure the scripts are executable (they are in-repo):
```bash
chmod +x AIMemory/bin/aimux AIMemory/bin/aimux-up
```

## Run — agent path (headless, isolated) — START HERE
Drive the harness end to end with the committed smoke driver:
```bash
bash .claude/skills/run-make-harness/smoke.sh
```
Expected tail:
```
SMOKE PASS: pane registry + queue + dispatcher delivery + injection all work
```
It is self-isolating (dedicated `aimuxsmoke$$` tmux socket + a tmux shim on PATH,
so even aimux's internal bare-`tmux` calls hit the throwaway server) and
self-cleaning (kills the server + removes the socket + temp state on exit). Safe to
run while a real aimux session is attached — it never reads/writes the default
socket. Idempotent.

### Drive individual subcommands (what the driver wraps)
Against any aimux session (these are the verbs the smoke driver chains):
```bash
AIMemory/bin/aimux panes        # pane registry (name → kind → location)
AIMemory/bin/aimux agents       # live board: idle / busy / waiting + what each handles
AIMemory/bin/aimux status       # dispatcher state + pending/inflight/done/failed counts
AIMemory/bin/aimux send-test --to <name>      # enqueue a high-five (no AICP files)
AIMemory/bin/aimux dispatch --once            # run ONE delivery cycle (deterministic)
AIMemory/bin/aimux name <name> --pane <id> --kind <kind>   # register a pane
```

## Run — human path (full, interactive, needs a TTY)
Bring up the real multi-agent session (manager + worker panes running actual
agent CLIs + a dispatcher pane). **This is TTY-interactive and needs the real CLIs
(claude / agy / opencode) installed and authenticated — it is useless fully
headless** (the launcher prompts you to pick a manager + workers):
```bash
AIMemory/bin/aimux-up            # interactive launch; pick manager + workers
# or, one command for the whole lifecycle (up + attach + finalize on detach):
AIMemory/bin/aimux shell
```
Default roster (env-independent as of v0.3.1): manager **claude --model opus**,
workers **antigravity (agy) + opencode**. Override non-interactively with
`AWM_MANAGER=` / `AWM_WORKERS=` / `AWM_ROSTER=`.

## Gotchas (battle scars — verified this session)
- **aimux calls bare `tmux`.** To test against a throwaway server without
  disturbing a live session, you must route *aimux's own* tmux calls to a
  dedicated socket. The driver does this with a tiny `tmux` shim
  (`exec tmux -L aimuxsmoke$$ "$@"`) prepended to `PATH` — not just `-L` on the
  driver's own calls.
- **Duplicate pane names across sessions break routing.** `--to <name>`
  resolution requires the name be unique server-wide; if a live session already
  has a `worker`/`manager`, creating same-named panes in the *same* tmux server
  makes routing ambiguous (refused). Hence the **separate socket** for tests.
- **Delivery only into a settled, idle pane.** The dispatcher delivers only when
  the target is idle (screen hash stable across a sample), not `pane_waiting`, and
  has no in-flight lock. New dummy panes need a `sleep` so their bash prompt is
  rendered/stable before `dispatch`, or idle-detection sees churn and skips them.
- **`pane_waiting` matches the WHOLE visible screen** against `AIMUX_WAIT_PATTERN`
  ("Do you want to|Continue?|Proceed?|approve this|Press Enter…"). Any pane showing
  such text is treated as blocked-on-a-prompt and gets no delivery. The manager
  pane is exempt (v0.3.2); workers are not — a worker echoing those words can
  false-stall. Diagnose against a stuck pane with the same pattern aimux uses:
  ```bash
  PAT='Do you want to|allow this|\(y/n\)|Press Enter to|Esc to cancel|Continue\?|Proceed\?|approve this'
  tmux capture-pane -p -t <pane-id> | grep -niE "$PAT"   # any hit ⇒ false-waiting
  ```
- **High-five into a dummy bash pane runs the embedded return command.** The
  pasted prompt contains an `aimux enqueue --to manager --type response …` line;
  bash executes it, so the smoke incidentally exercises the worker→manager return
  path too (visible as `enqueued … to=manager, type=response`).

## Troubleshooting
- **`SMOKE FAIL: high-five was never injected`** — the target pane wasn't seen
  idle. Increase the post-`name` `sleep`, or check `aimux agents` shows the pane
  `idle` (not `busy`/`waiting`).
- **Leftover `aimuxsmoke*` socket in `/tmp/tmux-$UID/`** — `tmux kill-server` can
  re-leave a dead socket as the server exits (race); the driver sleeps then
  `rm -f`s it. A stale 0-byte socket with "no server running" is harmless; delete
  it manually if needed.
- **`no server running on …`** during cleanup — benign (server already gone).
