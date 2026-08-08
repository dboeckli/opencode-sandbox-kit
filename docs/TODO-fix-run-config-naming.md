# Task: Fix the IntelliJ run-config naming drift

## Problem

`AGENTS.md` documents a run config `local-test-kits` (empty parameters =
all scenarios), but the actual file/config is named `local-test-kits-full`
(`.run/local-test-kits-full.run.xml`, `<configuration … name="local-test-kits-full">`).
`local-test-kits.run.xml` does not exist.

## What to do

Pick one direction (recommended: align docs to reality):

1. **Rename config to `local-test-kits`**:
   - Rename `.run/local-test-kits-full.run.xml` →
     `.run/local-test-kits.run.xml` and set `name="local-test-kits"` inside.
   - Then `AGENTS.md` (table) stays as-is.
2. **Keep `local-test-kits-full`, update docs**:
   - Update the table in `AGENTS.md:51` from `local-test-kits` →
     `local-test-kits-full`.

Also check the other references:
- `README.md` uses only PowerShell examples (`local-test/local-test-kits.py`),
  no config names — nothing to change there.

## Verify

- `idea_get_run_configurations` in IntelliJ shows the API config.
- No stale `local-test-kits` (without `-full`) name in docs after the change:
  `grep -rn "local-test-kits" AGENTS.md .run/ | grep -v -- "-full"` → only `local-test-kits-validate-only` may remain (that name is correct and is the guard allowlist).