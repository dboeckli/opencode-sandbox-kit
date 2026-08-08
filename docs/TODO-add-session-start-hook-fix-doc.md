# Task: Create the missing `session-start-hook-fix.md`

## Problem

`session-start-hook-fix.md` is referenced by the docs but **not committed** —
dead link for every clone:

- `README.md:213` — „siehe `session-start-hook-fix.md`"
- `AGENTS.md:90` — Doku der Managed-Settings-Lösung

## What to do

Add the missing document (root level, alongside `AGENTS.md`), describing the
`/etc/claude-code/managed-settings.json` design:

1. **Context**: The `claude-code-docker` template overwrites
   `~/.claude/settings.json` at session start (incl. `apiKeyHelper`,
   `defaultMode: bypassPermissions`, model default Opus 5).
2. **Race condition**: A `setup.startup`-Hook merge (Python, `settings.kit.json`,
   `spec.yaml:191-214`) is not enough for hooks/statusLine.
3. **Solution**: hooks + statusLine go into `managed-settings.json` under
   `/etc/claude-code/` (highest precedence, template-safe, written at
   `setup.install`, `spec.yaml:156-190`).
4. **Consequences**:
   - `files/home/.claude/settings.json` + `settings.kit.json` intentionally carry
     **no** `hooks`/`statusLine`.
   - SessionStart-Hook: `~/.config/sandbox-kit/run-checks-hook.sh`
   - PreToolUse-Guard: `~/.config/sandbox-kit/intellij-run-config-guard.sh`
   - statusLine: `bash ~/.claude/statusline.sh`

Once added, update the reference in `README.md:213` to a local link
(`<session-start-hook-fix.md >` -> proper relative link `session-start-hook-fix.md`).

## Verify

- Link resolves in the repo file browser.
- `grep -rn "session-start-hook-fix.md"` only shows the new file + README link.
- Kit build still writes `managed-settings.json` (`sbx exec … ls /etc/claude-code/`).