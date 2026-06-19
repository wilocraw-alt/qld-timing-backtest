# Multi-Agent Collaboration Protocol (Lite)

The minimum protocol for multiple AI agents to share state and hand off
work without losing context. Two artifacts, five rules.

## Files

```
AIMemory/
├── PROTOCOL.md                          ← this file
├── work.log                             ← append-only event log
└── handoff_<topic>.<model-id>.md        ← agent-to-agent message
```

No INDEX, no tiering, no Obsidian. When `work.log` gets unwieldy, the
user trims it manually.

**Optional tmux transport.** When agents run in tmux panes and you want
handoffs *delivered* (pasted) into another pane instead of picked up
passively, load `tmux-handoff.md`. Agents enqueue with `bin/aimux enqueue`
and a single `bin/aimux dispatch` rings each pane's doorbell only when it is
idle — so parallel handoffs never collide. AICP (this file) stays the source
of truth; tmux is just transport.

## Rules

### 1. work.log is append-only

Every agent writes events to the same file. Never edit in place. To
correct an earlier entry, append a `CORRECTION` event referencing the
original timestamp.

Event format:

```
### YYYY-MM-DD HH:MM | <model-id> | <EVENT>
<free-form body>
```

**Get the timestamp from the system, never guess it.** Use the real wall clock
— run `date '+%Y-%m-%d %H:%M'` and paste its output. An estimated time desyncs
the log (entries land out of order, breaking "newest at the bottom").

Required events:

| Event | When |
|---|---|
| `SESSION_START` | First turn of a new agent session. Body: model-id only. |
| `PROMPT` | User's message verbatim, in a `> ` blockquote. |
| `WORK_START` | When you begin acting. Body: one-line task summary. |
| `WORK_END` | When you finish. Body: `complete` / `blocked` / `partial`. |
| `FILES_CREATED` / `FILES_MODIFIED` / `FILES_DELETED` | Absolute paths, one per line. |
| `NOTE` | Assumptions, open questions, anything for the next agent. |
| `HANDOFF` / `HANDOFF_RECEIVED` / `HANDOFF_CLOSED` | See rule 5. |
| `CORRECTION` | Fix an earlier event. Body: `Re: <original timestamp>`. |

Skip events for trivial single-turn requests. Use judgment.

### 2. Read work.log before acting

Every new session, read the tail (last ~50 lines).

If you find a `WORK_START` without a matching `WORK_END`, ASK the user:
"Previous task `<summary>` looks unfinished. Resume or start fresh?"
Do not silently start something else.

### 3. Atomic append

Append each event in **one** write (heredoc to `>>`). Never split an
event across multiple writes. Never use a read-modify-write file edit
tool on `work.log` — concurrent agents lose data.

```bash
cat >> AIMemory/work.log <<'EOF'

### 2026-05-28 14:30 | claude-opus-4-7 | NOTE
<body here>
EOF
```

Keep each event under ~3 KB. If longer, put the bulk in a separate
file and link to it from the event body.

### 4. Model name in every file you author

Files you create go in `AIMemory/<slug>.<your-model-id>.md`. The
model-id prevents collisions when two agents work on the same topic.

The **originator's** model-id stays in the filename. Later editors note
their contribution in `work.log`, not in the filename.

### 5. Handoffs between agents

When agent A needs agent B to do something specific, create a handoff
file:

```
AIMemory/handoff_<topic-slug>.<A-model-id>.md
```

Required header:

```markdown
# <Short title>

**From**: <A-model-id>
**To**: <B-model-id | "any">
**Date**: YYYY-MM-DD HH:MM
**Type**: REVIEW_REQUEST | REVIEW_RESPONSE | QUESTION | ANSWER | STATUS_REPORT | BLOCKER
**Priority**: BLOCKING | HIGH | NORMAL | LOW
**Re**: <prior handoff file | work.log timestamp | "new topic">

## Summary
<2–4 sentences, plain language>

## Content
<the actual payload>

## Action items
- [ ] B: <imperative, specific>
```

Then log it:

```
### HH:MM | <A-model> | FILES_CREATED
- AIMemory/handoff_<topic>.<A-model>.md

### HH:MM | <A-model> | HANDOFF
→ <B-model>: <one-line purpose>. See handoff_<topic>.<A-model>.md.
Priority: NORMAL.
```

Receiving agent on pickup:

```
### HH:MM | <B-model> | HANDOFF_RECEIVED
← <A-model>: handoff_<topic>.<A-model>.md. Acting on action items.
```

When done:

```
### HH:MM | <B-model> | HANDOFF_CLOSED
← <A-model>: handoff_<topic>.<A-model>.md.
Completed: <short status>. See <deliverable files>.
```

For replies (REVIEW_RESPONSE / ANSWER), create a new handoff file
`handoff_<topic>-reply.<B-model>.md` with `Re:` pointing at the original.

---

That's the whole protocol. See `handoff_example.md` for a worked example.
