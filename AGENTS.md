# opencode-sandbox-kit

Sandbox Kit (mixin) for OpenCode / Mammouth Code / Claude Code with ctx7 and IntelliJ MCP.
Repo: https://github.com/dboeckli/opencode-sandbox-kit

## Environment (wichtig!)

Der Agent läuft in **WSL Ubuntu** (Linux). Das Kit ist aber ein **Windows-Setup**:

- **WSL Ubuntu** (hier): Ich kann Tools wie `ctx7`, `curl`, `sbx` testen — Library-IDs, Versions-Checks, Doku-Recherche.
- **Windows/PowerShell** (User): Alle Sandbox-Befehle (`sbx run`, `sbx exec`, `sbx template rm`, `sbx secret set`) führt der User in PowerShell aus — Docker Desktop läuft nativ auf Windows.
- Die Sandbox-Befehle aus WSL heraus sind **nicht möglich** (kein Zugriff auf den Windows-Docker-Daemon).
- Dokus (AGENTS.md/README) müssen **PowerShell-Syntax** verwenden.

## Commands

- `sbx kit validate .` — validate the kit (run before commit)
- `sbx run opencode --name opencode-sandbox --kit .` — test the kit with an OpenCode sandbox (via PowerShell on Windows)
- `sbx run claude --name claude-sandbox --kit .` — test the kit with a Claude Code sandbox (via PowerShell on Windows)
- `sbx run opencode --name mammouth-sandbox --kit .` — test the mixin kit with an OpenCode sandbox, then run `mammouth` manually in the terminal (Mammouth Code, OpenCode-Fork)
- `sbx run mammouth --name mammouth-sandbox --kit ./mammouth-agent/` — run the dedicated Mammouth agent kit (kind: sandbox, entrypoint `mammouth`)
- `sbx run opencode --kit "git+https://github.com/dboeckli/opencode-sandbox-kit.git"` — run from remote Git repo
- `sbx run opencode --name spring-6-reactive --kit "git+https://github.com/dboeckli/opencode-sandbox-kit.git" "C:\development\projects\spring-6-reactive"` — use kit with another project
- `sbx kit add spring-6-reactive "git+https://github.com/dboeckli/opencode-sandbox-kit.git"` — apply kit to an existing sandbox (restarts sandbox, preserves VM state)
- `sbx settings set kit.allowedSources --% "[\"docker.io/\",\"github.com/dboeckli/\"]"` — allow GitHub as kit source (required once before remote Git)
- The kit installs ctx7 via `npm install -g ctx7` (spec.yaml `commands.install`); `npx ctx7 setup --opencode` ist nur nötig, um ctx7 für OpenCode zu konfigurieren (nicht Teil des Kits)
- `npx ctx7 docs /docker/docs <query>` — sbx CLI / sandbox documentation (ctx7 library ID: `/docker/docs`)
- `python local-test/local-test-kits.py` — automate the 3 scenarios (OpenCode/Claude/Mammouth): validate kits, check secrets, create sandboxes, run startup checks, remove sandboxes (`--keep` to keep them)
- `python local-test/local-test-kits.py --ci` — CI mode (used by GitHub Actions `.github/workflows/e2e.yml`): fake API keys, no real mammouth API call (only proxy env wiring)
- GitHub Actions `.github/workflows/e2e.yml` — e2e on push + PR: installs sbx, logs into Docker Hub (variable `DOCKER_USERNAME` + secret `DOCKER_PAT`), registers fake sandbox secrets, runs `local-test-kits.py --ci`

## GitHub Authentication

Für `gh` CLI in der Sandbox ein persönliches GitHub-Token (Name: `opencode-sandbox-kit-github-token`) erstellen und als Secret speichern:

```powershell
sbx secret set -g github -t "<github-token>"
```

Das Token wird via Proxy automatisch injiziert – `gh auth status` sollte in der Sandbox funktionieren.

## Anthropic Authentication

Für Claude Code in der Sandbox wird der Anthropic API-Key als Secret gespeichert und vom Proxy verwaltet – der Key liegt nie im Sandbox-Filesystem:

```powershell
sbx secret set -g anthropic
```

Es wird davon ausgegangen, dass `ANTHROPIC_API_KEY` nicht als Env-Variable gesetzt ist – der Key wird interaktiv eingegeben. Falls bereits ein OAuth-Token existiert, wird nachgefragt – mit `-f` überschreiben:

```powershell
sbx secret set -g anthropic -f
```

In der Sandbox sollte `env | grep -i ANTHROPIC` leer sein, während API-Calls über den Proxy trotzdem funktionieren.

### Token-Scopes (aktuell konfiguriert)

| Scope | Beschreibung |
|-------|-------------|
| `read:org` | Organisationen lesen |
| `read:packages` | Packages lesen |
| `read:project` | Projects lesen |
| `read:user` | Benutzerdaten lesen |

> **Hinweis:** Für Private-Repo-Zugriff, Push oder PR/Issue-Erstellung wird zusätzlich das `repo`-Scope benötigt. Dies kann via `gh auth refresh -h github.com -s repo` nachgefordert werden.

## Layout

- `spec.yaml` — kit definition (schemaVersion, caps, commands, kind: mixin)
- `files/home/.config/opencode/opencode.jsonc` — OpenCode config with IntelliJ MCP via `host.docker.internal:64342/sse`
- `files/home/.config/opencode/AGENTS.md` — OpenCode rules (ctx7 + sandbox tools)
- `files/home/.claude/settings.json` — Claude Code config with IntelliJ MCP via `host.docker.internal:64342/sse`
- `files/home/.claude/CLAUDE.md` — Claude Code rules (ctx7 + sandbox tools)
- `files/home/.config/mammouth/opencode.jsonc` — Mammouth Code config (OpenCode-Fork) with IntelliJ MCP + `mammouth-recommended`
- `files/home/.config/mammouth/AGENTS.md` — Mammouth Code rules (ctx7 + sandbox tools)
- `mammouth-agent/spec.yaml` — dedicated Mammouth agent kit (kind: sandbox, name `mammouth`, entrypoint `mammouth`)
- `mammouth-agent/files/home/.config/mammouth/` — Mammouth config for the agent kit

## Dual agent support

Das Kit funktioniert mit **OpenCode, Claude Code und Mammouth Code** – der Agent wird nicht vom Kit bestimmt, sondern vom Template beim `sbx run`:

```powershell
sbx run opencode --name my-sandbox --kit .          # OpenCode (opencode-docker Template)
sbx run claude   --name my-sandbox --kit .          # Claude Code (claude-code-docker Template)
sbx run mammouth --name mammouth-sandbox --kit ./mammouth-agent/   # Mammouth Code (eigenes Agent-Kit, entrypoint mammouth)
```

Alle drei erhalten dieselben Tools (JDK, Maven, Docker CLI, Skills, ctx7) und den IntelliJ MCP via `host.docker.internal:64342`. Die jeweilige Config wird automatisch gelesen:
- OpenCode: `~/.config/opencode/opencode.jsonc` + `~/.config/opencode/AGENTS.md`
- Claude Code: `~/.claude/settings.json` + `~/.claude/CLAUDE.md`
- Mammouth Code: `~/.config/mammouth/opencode.jsonc` + `~/.config/mammouth/AGENTS.md`

> **Mammouth Code**: Installiert das Agent-Kit automatisch beim Build (`curl -fsSL https://code.mammouth.ai/install.sh | bash` als User 1000) + Symlink `/usr/local/bin/mammouth` für den Entrypoint. `~/.mammouth/bin` wird zusätzlich via `/etc/sandbox-persistent.sh` exportiert. API-Key als `MAMMOUTH_API_KEY` (Provider `mammouth-ai`, Base-URL `https://api.mammouth.ai/v1`), konfiguriert via `credentials[].apiKey` (`name`/`proxyManaged`/`inject`) im Kit.

## Tools installed by the kit

| Tool | Source |
|------|--------|
| Liberica JDK 25.0.4 | GitHub Releases (bell-sw) |
| Apache Maven 3.9.16 | dlcdn.apache.org |
| Docker CLI 27.5.1 | download.docker.com (static binary) |
| kubectl (latest stable) | dl.k8s.io |
| ctx7 | npm |
| skills | npm (vercel-labs) |

## Mammouth Authentication

Für Mammouth Code wird der API-Key als Secret registriert und via Proxy als `MAMMOUTH_API_KEY` injiziert –
der Key liegt nie im Sandbox-Filesystem. Es gibt keinen eingebauten Provider wie bei `anthropic`/`github`,
daher den Kit-deklarierten Service `mammouth` nutzen:

```powershell
# Kit-deklarierter Service (wie sbx secret set -g anthropic)
sbx secret set -g mammouth
```

Der Key stammt aus https://mammouth.ai/app/account/settings/api.

> **Wichtig:** `MAMMOUTH_API_KEY` ist in der Sandbox auf den Platzhalter `proxy-managed` gesetzt (wie
> `ANTHROPIC_API_KEY` bei Claude). Das Agent-Kit setzt sie via `credentials[].apiKey.name` + `proxyManaged: true`
> (kit-spec v2). Der Proxy ersetzt den Platzhalter transparent bei Requests an `api.mammouth.ai`. `env | grep -i MAMMOUTH` in der
> Sandbox zeigt `MAMMOUTH_API_KEY=proxy-managed` (nie den echten Key).

Verifikation:

```powershell
sbx secret ls                                                    # Secret ist registriert
sbx exec mammouth-sandbox bash -c 'curl -s https://api.mammouth.ai/v1/models -H "Authorization: Bearer $MAMMOUTH_API_KEY" | head'
```

## Caveats

- **Docker Socket**: Jede Sandbox hat einen **isolierten Docker Daemon** im eigenen MicroVM (`docker info` zeigt den Sandbox-Namen als Servername) – kein Host-Socket-Mount nötig.
- **Pre-installed opencode**: Das Base-Image enthält eine eigene OpenCode CLI. `npm install -g` überschreibt sie, aber bei Abweichungen ist die Base-Image-Version die Ursache.
- **Skills in `~/.agents/skills/`**: Werden via `skills add -g --all` mit `user: "1000"` installiert, damit sie beim `agent`-User landen.
- **Mammouth Code**: Wird vom Agent-Kit (`mammouth-agent/`) automatisch installiert. Das Mixin-Kit installiert bewusst **nicht** automatisch – nur Config + PATH-Export; Installation manuell via `curl -fsSL https://code.mammouth.ai/install.sh | bash`. Ohne Installation meldet der Startup-Check `mammouth:FAIL`.
- **Kit-spec v1/v2**: Beide Kits (Mixin `spec.yaml` und `mammouth-agent/spec.yaml`) nutzen `schemaVersion: "1"` mit den v2-Feldnamen `caps.network.allow` + `credentials[].apiKey` — das validiert mit der aktuellen stabilen `sbx` **v0.37.1** ohne WARN. Die finale v2-Grammatik (`schemaVersion: "2"`, `permissions.network.allow`, `agentInstructions`, `setup`, flacher `entrypoint`) wird von v0.37.1 noch **nicht** unterstützt (`sbx kit validate` meldet "field ... not found"); eine Sandbox mit `schemaVersion: "2"` ließ sich zudem nicht starten. Erst **v0.38.0-rc1** (Pre-Release, 2026-07-31) bringt die strikte v2-Grammatik (bundles `sbx-kits-contrib` v0.12.0) — nach einem Upgrade das Kit per `go run scripts/migrate-v1-to-v2.go <kit-dir>` migrieren. Alte v1-Felder (`network.allowedDomains`, `credentials.sources`, `environment.proxyManaged`, `network.serviceAuth`/`serviceDomains`) erzeugen WARN-Meldungen. Offizielle v2-Referenz (nicht in Context7, `docker/docs` ist noch v1): https://github.com/docker/sbx-kits-contrib/blob/main/spec/SPEC-v2.md.
