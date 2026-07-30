# opencode-sandbox-kit

Sandbox Kit (mixin) for OpenCode with ctx7 and IntelliJ MCP.
Repo: https://github.com/dboeckli/opencode-sandbox-kit

## Commands

- `sbx kit validate .` — validate the kit (run before commit)
- `sbx run opencode --name opencode-sandbox --kit .` — test the kit with a sandbox (via PowerShell on Windows)
- `sbx run opencode --kit "git+https://github.com/dboeckli/opencode-sandbox-kit.git"` — run from remote Git repo
- `sbx settings set kit.allowedSources '["docker.io/","github.com/dboeckli/"]'` — allow GitHub as kit source (required once before remote Git)
- The kit installs via `npx ctx7 setup --opencode` (spec.yaml `commands.install`)
- `npx ctx7 docs /docker/docs <query>` — sbx CLI / sandbox documentation (ctx7 library ID: `/docker/docs`)

## Layout

- `spec.yaml` — kit definition (schemaVersion, caps, commands, kind: mixin)
- `files/home/.config/opencode/opencode.jsonc` — OpenCode config with IntelliJ MCP via `host.docker.internal:64342/sse`

## Tools installed by the kit

| Tool | Source |
|------|--------|
| Liberica JDK 25.0.4 | GitHub Releases (bell-sw) |
| Apache Maven 3.9.16 | dlcdn.apache.org |
| Docker CLI 27.5.1 | download.docker.com (static binary) |
| kubectl (latest stable) | dl.k8s.io |
| ctx7 | npm |

## Caveats

- **Docker Socket**: Wird von Docker Desktop automatisch in die Sandbox gemountet – kein manuelles Mount nötig.
- **Pre-installed opencode**: Das Base-Image enthält eine eigene OpenCode CLI. `npm install -g` überschreibt sie, aber bei Abweichungen ist die Base-Image-Version die Ursache.
- No commits yet (fresh repo)
- Kit uses kit-spec v2 (`caps.network.allow`, not deprecated `network.allowedDomains`)
