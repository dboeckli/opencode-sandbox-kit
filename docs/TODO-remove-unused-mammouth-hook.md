# Task: Remove unused Claude hook from the mammouth kit

## Problem

`mammouth-agent/files/home/.config/sandbox-kit/run-checks-hook.sh` is a
**Claude Code** `SessionStart` hook. The mammouth kit is OpenCode-based
(entrypoint `mammouth`, startup via `startup-checks.js` plugin); it registers
**no** Claude hooks and has no `managed-settings.json`. The file is dead
weight — and its output schema (`systemMessage`) diverges from the mixin
variant (`additionalContext`, `files/home/.config/sandbox-kit/run-checks-hook.sh`)
which Claude actually uses.

## What to do

Decision first:

1. **Remove** `mammouth-agent/files/home/.config/sandbox-kit/run-checks-hook.sh`.
   `run-checks.sh` stays (used by the OpenCode plugin + `local-test-kits.py`).
2. Alternative: if you intend `sbx run claude --kit ./mammouth-agent/` to
   work, then actually **register** the hook (add a `managed-settings.json`
   write + `run-checks-hook.sh` referenced in the mammouth `setup.install`)
   and align the output schema with the mixin variant.

## Verify

- If removed: `git grep -l "run-checks-hook" mammouth-agent/` returns nothing.
- `local-test-kits.py` mammouth scenario still passes
  (`python local-test/local-test-kits.py mammouth`):
  `run_checks` only shells `~/.config/sandbox-kit/run-checks.sh`, not the hook.