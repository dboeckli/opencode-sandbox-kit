#!/bin/sh
# Sandbox entrypoint for the claude-v3-agent kit.
#
# The kit config must be in place before Claude Code starts reading it: re-apply the
# kit defaults and the MCP gateway wiring first (idempotent), then exec the CLI.
set -e
python3 /usr/local/bin/claude-config.py || true
exec claude "$@"
