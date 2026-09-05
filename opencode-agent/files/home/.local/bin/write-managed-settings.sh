#!/usr/bin/env bash
set -euo pipefail

# Write Claude Code managed-settings.json to /etc/claude-code (root). Highest-precedence
# settings the template does not overwrite at session start: statusLine + PreToolUse
# (run-config guard) + SessionStart (run-checks) hooks, so they are always configured.
#
# Referenced by setup.install in the opencode-agent and claude-zurich-agent kit specs.
# Bundled via files/home/.local/bin/, executed by setup.install as root. Must stay
# identical in both kits — edit one copy, then `cp` it to the other. Drift is caught by
# local-test-kits.py (--validate-only, INSTALL_SCRIPT_PAIRS).

mkdir -p /etc/claude-code
cat > /etc/claude-code/managed-settings.json <<'EOF'
{
  "statusLine": {
    "type": "command",
    "command": "bash ~/.claude/statusline.sh"
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__mcp-gateway__execute_run_configuration",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.config/sandbox-kit/intellij-run-config-guard.sh"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.config/sandbox-kit/run-checks-hook.sh"
          }
        ]
      }
    ]
  }
}
EOF
