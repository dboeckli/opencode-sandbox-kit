# Task: Update startup-checks documentation (missing helm check)

## Problem

`run-checks.sh` performs **8** checks (incl. `helm`, `run-checks.sh:66-71`),
but two docs list only 7 and omit `helm:OK`:

- `README.md:387` — example report line
- `files/home/.config/opencode/AGENTS.md` (Startup checks section, injected
  system prompt) — enumerates „Context7, IntelliJ MCP, gh, Java/Maven, Docker,
  kubectl, skills"

Reference doc `files/home/.config/sandbox-kit/startup-checks.md` is already
correct (8 checks + `helm:OK`).

## What to do

1. `README.md:387`: add `helm:OK` to the example line.
2. `files/home/.config/opencode/AGENTS.md` Startup checks section: add `helm`
   to the enumeration.
3. `files/home/.claude/CLAUDE.md` (Claude variant of the same text): check and
   update the corresponding Startup-checks paragraph for `helm` — the Claude
   and OpenCode AGENTS.md files are kept in sync.
4. `mammouth-agent/files/home/.config/mammouth/AGENTS.md` (Startup checks
   section): lists `…, kubectl, skills, mammouth)` — also verify helm there;
   mammouth run-checks.sh has 9 checks (8 + mammouth).

## Verify

- `grep -rn "kubectl:OK" README.md files/ mammouth-agent/` shows `helm:OK` in
  all report examples.
- Grep the enumeration sections for `helm`.