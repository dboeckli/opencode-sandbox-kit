#!/bin/sh
# Sandbox entrypoint for the claude-v3-agent kit.
#
# The kit config must be in place before Claude Code starts reading it: the
# base template resets ~/.claude/settings.json at session start and lifecycle
# startup hooks run after the entrypoint. Re-apply the kit defaults and the
# MCP gateway wiring first, then exec the CLI.
set -e
python3 /usr/local/bin/claude-config.py || true
exec claude "$@"
