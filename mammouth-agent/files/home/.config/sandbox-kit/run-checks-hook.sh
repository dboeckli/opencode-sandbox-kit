#!/usr/bin/env bash
# Claude Code SessionStart hook - runs the startup checks once and reports
# the result as a systemMessage so Claude sees it automatically.
report=$(bash ~/.config/sandbox-kit/run-checks.sh 2>&1)
escaped=$(printf '%s' "$report" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().strip()))' 2>/dev/null)
if [ -z "$escaped" ]; then
  escaped='"[startup-checks] FAILED to run checks"'
fi
printf '{"continue": true, "suppressOutput": false, "systemMessage": %s}\n' "$escaped"
