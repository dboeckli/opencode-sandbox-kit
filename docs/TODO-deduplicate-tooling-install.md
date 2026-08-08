# TODO: Deduplicate tooling installation

## Problem

The complete `setup.install` list is duplicated across the two kit specs
(~50 lines): `spec.yaml:96-214` and `mammouth-agent/spec.yaml:111-177`.
Every tool/version change must be made twice — high drift risk for human
edits (Renovate keeps versions in sync, but humans don't).

## What to do

Pick one approach:

1. **Shared build script (recommended)** — extract all tool-install commands
   into `scripts/install-tooling.sh` in the repo, then keep only
   `command: bash /path/to/install-tooling.sh` (copied into the sandbox first)
   in both specs. Must keep the `user: "1000"` distinction for the skills /
   statusline steps (root vs. agent user).
2. **Shared kit** — since the tooling is identical, let the `mammouth-agent`
   kit reuse the mixin payload via a single `include` / templated generation
   step (e.g. generate both `spec.yaml` files from one template in CI).

Keep the differences minimal:
- mixin only: `deepseek` + `anthropic` credentials, `setup.startup`
  (settings.kit.json merge), `/etc/claude-code/managed-settings.json`,
  `environment.variables.npm_config_bin_links`, `JAVA_HOME`.
- mammouth only: `python3`/`python3-pip`, mammouth install + symlink.

## Verify

- `sbx kit validate .` and `sbx kit validate ./mammouth-agent`
- `shfmt` / `shellcheck` on the extracted script
- local test `python local-test/local-test-kits.py`