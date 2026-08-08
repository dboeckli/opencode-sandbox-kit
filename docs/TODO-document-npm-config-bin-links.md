# Task: Document the `npm_config_bin_links` env split

## Problem

Undocumented subtlety: the kit sets a global env
`environment.variables.npm_config_bin_links: "false"`
(`spec.yaml:221`), while individual `setup.install` commands explicitly prefix
`npm_config_bin_links=true` (e.g. `spec.yaml:98-101`).

This is intentional — during install, npm should create bin links for the
global CLIs (ctx7, skills, rename, on PATH at `/usr/local/share/npm-global/bin`);
at runtime the flag avoids bin-link side effects. But nothing explains this,
which is easy to break or to confuse with the `template` behavior.

## What to do

1. Add a short subsection to `README.md` (near "Installierte Tools", e.g. after
   the install table at `README.md:417`) explaining:
   - install commands run with `npm_config_bin_links=true`
     (explicit per-command prefix),
   - runtime environment has `npm_config_bin_links=false`
     (kit `environment.variables`, `spec.yaml:221`),
   - why the two differ.
2. Optional: add the same note to `AGENTS.md` (Layout / Tools sections).
3. Do NOT change behavior — documentation only.

## Verify

- In a running sandbox: `npm config get bin-links` → `false`.
- During kit `setup.install`, the ctx7/skills binaries land in
  `/usr/local/share/npm-global/bin` (bin links created).