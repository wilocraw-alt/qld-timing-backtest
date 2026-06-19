#!/usr/bin/env bash
# smoke.sh — isolated, headless smoke test for the aimux harness.
#
# Proves the CORE loop end to end WITHOUT any real agent CLI and WITHOUT
# touching a live aimux session:
#   pane registry (aimux name/panes/agents)
#     → queue (aimux enqueue/send-test/status)
#       → dispatcher delivery (aimux dispatch --once)
#         → injection (the prompt is actually pasted into the target pane)
#
# Isolation: a DEDICATED tmux socket plus a tmux shim on PATH, so even
# aimux's own bare `tmux` calls hit the throwaway server. Your real
# session (default socket) is never read or written.
#
# Usage:  bash .claude/skills/run-make-harness/smoke.sh
# Exit 0 + "SMOKE PASS" on success; non-zero + "SMOKE FAIL" otherwise.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
AIMUX="$REPO/AIMemory/bin/aimux"
REALTMUX="$(command -v tmux)"
SOCK="aimuxsmoke$$"
WORK="$REPO/AIMemory/tmp/run-smoke-$$"
mkdir -p "$WORK/shim"

# tmux shim → route ALL tmux calls (driver's + aimux's) to the throwaway socket.
cat > "$WORK/shim/tmux" <<SH
#!/usr/bin/env bash
exec "$REALTMUX" -L "$SOCK" "\$@"
SH
chmod +x "$WORK/shim/tmux"
export PATH="$WORK/shim:$PATH"

# Isolated aimux state + fast timings for a quick smoke.
export AIMUX_STATE="$WORK/state"
export AIMUX_SESSION="smoke"
export AIMUX_MIN_INFLIGHT_SECS=1
export AIMUX_IDLE_SAMPLE_SECS=0.6
export TMPDIR="$REPO/AIMemory/tmp"

cleanup(){ tmux kill-server 2>/dev/null || true; sleep 0.4; rm -f "${TMUX_TMPDIR:-/tmp/tmux-$(id -u)}/$SOCK" 2>/dev/null || true; rm -rf "$WORK"; }
trap cleanup EXIT
fail(){ echo "SMOKE FAIL: $*" >&2; exit 1; }

echo "== 1. throwaway tmux server ($SOCK) + 2 dummy bash panes =="
tmux kill-server 2>/dev/null || true
tmux new-session -d -s smoke -x 200 -y 50 bash || fail "new-session"
tmux split-window -t smoke -h bash || fail "split-window"
mapfile -t PANES < <(tmux list-panes -t smoke -F '#{pane_id}')
MGR="${PANES[0]}"; WRK="${PANES[1]}"
[ -n "$MGR" ] && [ -n "$WRK" ] || fail "could not create panes"
echo "manager=$MGR worker=$WRK"

echo "== 2. register pane names (the routing registry) =="
"$AIMUX" name manager --pane "$MGR" --kind claude-code || fail "name manager"
"$AIMUX" name worker  --pane "$WRK" --kind opencode    || fail "name worker"
sleep 2   # let the bash prompts render so idle-detection sees a stable screen

echo "== 3. roster + live board =="
"$AIMUX" panes  || fail "panes"
"$AIMUX" agents || fail "agents"

echo "== 4. enqueue a high-five (manager -> worker) =="
"$AIMUX" send-test --to worker --from "$MGR" || fail "send-test enqueue"
"$AIMUX" status || fail "status"

echo "== 5. run the dispatcher until the paste lands =="
delivered=0
for i in $(seq 1 10); do
  "$AIMUX" dispatch --once >/dev/null 2>&1 || true
  if tmux capture-pane -p -t "$WRK" | grep -q "high-five test received"; then delivered=1; break; fi
  sleep 1
done
echo "-- worker pane tail --"
tmux capture-pane -p -t "$WRK" | tail -12

[ "$delivered" = 1 ] || fail "high-five was never injected into the worker pane"
echo "SMOKE PASS: pane registry + queue + dispatcher delivery + injection all work"
