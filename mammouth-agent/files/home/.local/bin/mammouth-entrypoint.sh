#!/bin/sh
# Sandbox entrypoint for the mammouth-agent kit (spec: sandbox.entrypoint).
#
# The model-picker favorites must exist on disk BEFORE mammouth starts: sbx runs
# the `setup.startup` hooks concurrently with (in practice after) the entrypoint,
# so a seed there loses the race — the TUI reads model.json at startup and later
# overwrites it with its in-memory (empty) favorites. Seeding here is idempotent:
# existing favorites keep their order, missing seed models are appended.
set -e
python3 /usr/local/bin/seed-mammouth-model-favorites.py || true
exec mammouth "$@"
