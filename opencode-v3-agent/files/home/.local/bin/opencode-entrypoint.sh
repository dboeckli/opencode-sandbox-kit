#!/bin/sh
# Sandbox entrypoint for the opencode-v3-agent kit.
#
# Model-picker favorites must exist before the TUI starts: lifecycle startup
# hooks run after the entrypoint, so a seed there loses the race (OpenCode reads
# model.json at startup and later writes its in-memory state back).
set -e
python3 /usr/local/bin/seed-opencode-model-favorites.py || true
exec opencode "$@"
