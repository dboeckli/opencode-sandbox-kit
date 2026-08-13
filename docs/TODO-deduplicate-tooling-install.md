# DONE: Deduplicate tooling installation

Implemented (2026-08-12). Both kit specs now reference shared install scripts instead
of duplicating the full `setup.install` tooling block.

## Approach

**Shared build script** — the tooling-install commands were extracted into two
scripts that are bundled as identical copies in both kits' `files/home/.local/bin/`
(no separate canonical `scripts/` directory):

| Script (files/home/.local/bin/) | User | Contents |
|--------|------|----------|
| `install-tooling.sh` | root | npm-CLIs (ctx7/skills/prettier/renovate), apt (jq/python3/pip/yaml), shfmt, Liberica JDK, Maven, Docker CLI, Compose, kubectl, Helm |
| `install-tooling-user.sh` | uid 1000 | skills (`~/.agents/skills`) + Claude statusline |

Both specs keep only:

```yaml
setup:
  install:
    - command: "bash /home/agent/.local/bin/install-tooling.sh"
    - command: "bash /home/agent/.local/bin/install-tooling-user.sh"
      user: "1000"
```

The scripts reach the sandbox via the `files/home/.local/bin/` bundles of both kits.
This works because **`files/home/` is injected before `setup.install`** and install
commands may consume bundled `files/home/` files (official Docker docs,
`kit-reference.md` → "Execution order"). The `user: "1000"` distinction is preserved
via the separate user script.

The scripts are bundled into both kits' `files/home/.local/bin/` (identical copies);
`local-test-kits.py --validate-only` fails if the two kit copies drift. Keep them in sync
manually (`cp` one to the other) or via Renovate, which bumps versions in both together.

## Differences kept minimal

- mixin only: `deepseek` + `anthropic` credentials, `setup.startup` merge,
  `/etc/claude-code/managed-settings.json` step, `npm_config_bin_links` env.
- mammouth only: mammouth install + symlink steps.
- The apt line now uniformly installs `python3 python3-pip` in both kits (was
  mammouth-only) so a single shared root script stays identical.

## Renovate

`customManager` regexes for the tool versions now target both copies of
`files/home/.local/bin/install-tooling.sh`; a shfmt manager was added.

## Verify

- `sbx kit validate .` and `sbx kit validate ./mammouth-agent` (via
  `local-test-kits-validate-only`)
- `shfmt` on the scripts (shellcheck not available in the sandbox)
- drift guard `check_install_scripts_sync()` in `local-test-kits.py --validate-only`
