#!/usr/bin/env bash
# Claude Code SessionStart hook - runs the startup checks once and injects
# the result as additionalContext so Claude sees it automatically.
report=$(bash ~/.config/sandbox-kit/run-checks.sh 2>&1)
escaped=$(printf '%s' "$report" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().strip()))' 2>/dev/null)
if [ -z "$escaped" ]; then
  escaped='"[startup-checks] FAILED to run checks"'
fi
printf '{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": %s}}\n' "$escaped"
