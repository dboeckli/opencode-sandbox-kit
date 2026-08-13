# opencode-sandbox-kit

Sandbox Kit (mixin) for OpenCode / Mammouth Code / Claude Code with ctx7 and IntelliJ MCP.
Repo: https://github.com/dboeckli/opencode-sandbox-kit

## Environment (wichtig!)

Der Agent läuft in einer **Docker-Sandbox** (MicroVM). Das Kit ist aber ein **Windows-Setup** — der Host
(IntelliJ MCP via `host.docker.internal:64342`) läuft immer auf Windows:

- **Agent-Sandbox** (hier): Agent-Laufzeit — ich teste Linux-Tools (`ctx7`, `curl`, ...), Versions-Checks und Doku-Recherche. `sbx` ist hier **nicht** verfügbar (nicht im Sandbox-Image installiert).
- **Windows/PowerShell** (User, **Standard**): Alle Sandbox-Befehle (`sbx run`, `sbx exec`, `sbx template rm`, `sbx secret set`) führt der User in PowerShell aus — Docker Desktop läuft nativ auf Windows.
- **Ubuntu-WSL** (User, Alternative): Die Sandbox-Befehle laufen auch aus einem Ubuntu-WSL-Setup heraus (Laufzeitumgebung dort: **Ubuntu 26.04**) — inkl. `host.docker.internal`-Zugriff für IntelliJ MCP und der Secret-Injection. Der Host bleibt derselbe: IntelliJ auf Windows.
- Dokus (AGENTS.md/README) müssen **PowerShell-Syntax** verwenden.

## Git commits (Nachfragen-Pflicht)

Mache **niemals unaufgefordert Commits**: `git commit`, `git push`, PR-Erstellung und ähnliche Git-Operationen
nur mit expliziter Zustimmung des Users ausführen. Ansonsten Änderungen stehen lassen und am Ende den User fragen,
ob ein Commit erstellt werden soll.

## Commands

- `sbx kit validate .` — validate the kit; run it after every change and report the output as evidence before committing
- `sbx run opencode --name opencode-sandbox --kit .` — test the kit with an OpenCode sandbox (via PowerShell on Windows)
- `sbx run claude --name claude-sandbox --kit .` — test the kit with a Claude Code sandbox (via PowerShell on Windows)
- `sbx run mammouth --name mammouth-sandbox --kit ./mammouth-agent/` — run the dedicated Mammouth agent kit (kind: sandbox, entrypoint `mammouth`)
- `sbx run opencode --kit "git+https://github.com/dboeckli/opencode-sandbox-kit.git"` — run from remote Git repo
- `sbx run opencode --name spring-6-reactive --kit "git+https://github.com/dboeckli/opencode-sandbox-kit.git" "C:\development\projects\spring-6-reactive"` — use kit with another project
- `sbx kit add spring-6-reactive "git+https://github.com/dboeckli/opencode-sandbox-kit.git"` — apply kit to an existing sandbox (restarts sandbox, preserves VM state)
- `sbx settings set kit.allowedSources --% "[\"docker.io/\",\"github.com/dboeckli/\"]"` — allow GitHub as kit source (required once before remote Git)
- ctx7 installiert das Kit via `npm install -g ctx7` (spec.yaml `setup.install`); `npx ctx7 setup --opencode` konfiguriert nur ctx7 für OpenCode (nicht Teil des Kits)
- `npx ctx7 docs /docker/docs <query>` — sbx CLI / sandbox documentation (ctx7 library ID: `/docker/docs`)
- `python local-test/local-test-kits.py` — automate the 3 scenarios (OpenCode/Claude/Mammouth): validate kits, check secrets, create sandboxes, run startup checks, remove sandboxes (`--keep` to keep them)
- `python local-test/local-test-kits.py --ci` — CI mode (used by GitHub Actions `.github/workflows/e2e.yml`): fake API keys, no real mammouth API call (only proxy env wiring)
- `python local-test/local-test-kits.py --validate-only` — only `sbx kit validate` (both kits), no secrets check and no sandbox start (default is starting the sandboxes)
- GitHub Actions `.github/workflows/validate.yml` + `.github/workflows/e2e.yml` — install a **pinned sbx** (env `SBX_VERSION`, currently `v0.38.0`, mantained via Renovate customManager `docker/sbx-releases`); e2e logs into Docker Hub (variable `DOCKER_USERNAME` + secret `DOCKER_PAT`), registers fake sandbox secrets, runs `local-test-kits.py --ci`

## Testing (lokale Verifikation per IntelliJ Run-Configs)

> **Wichtig:** In der Sandbox-Laufzeit ist `sbx` **nicht** verfügbar (nicht im Sandbox-Image installiert — unabhängig
> von WSL). Validierung und Sandbox-Tests laufen daher auf dem Windows-Host via PowerShell (Docker Desktop nativ) —
> der Agent erreicht sie über den IntelliJ MCP (`idea_execute_run_configuration`) mit den Run-Configs in `.run/`.
> `idea_execute_run_configuration` mit der Config **ohne** `waitForExit=false` timeout't nach 15 min, obwohl der Test
> (~8 min) evtl. noch läuft — dann Prozessstatus via `idea_execute_terminal_command` + `Get-Process python` prüfen.

IntelliJ Run-Configs (`.run/*.run.xml`, alle rufen `local-test/local-test-kits.py` auf):

| Config | PARAMETERS | Zweck |
|--------|-----------|-------|
| `local-test-kits-full` | *(leer)* | Alle 3 Szenarien (OpenCode/Claude/Mammouth): validate + Secrets + Sandbox |
| `local-test-kits-validate-only` | `--validate-only` | Nur `sbx kit validate` (beide Kits), keine Sandbox |
| `local-test-kits-opencode` | `opencode` | Nur OpenCode-Szenario (Sandbox) |
| `local-test-kits-claude` | `claude` | Nur Claude-Szenario (Sandbox) |
| `local-test-kits-mammouth` | `mammouth` | Nur Mammouth-Szenario (Sandbox) |

Alle Configs nutzen dasselbe SDK (`~\AppData\Local\Microsoft\WindowsApps\python3.exe`), WORKING_DIRECTORY
`$PROJECT_DIR$/local-test`, `PYTHONUNBUFFERED=1`. Neue Config in `.run/` anlegen = nur eine XML-Datei mit passendem
`PARAMETERS`; IntelliJ erkennt sie (die `get_run_configurations`-Liste kann kurz veraltet sein — direkt per Namen starten
funktioniert trotzdem).

Äquivalente PowerShell-Befehle:

```powershell
python local-test\local-test-kits.py --validate-only   # nur Validierung
python local-test\local-test-kits.py opencode          # nur OpenCode-Sandbox
python local-test\local-test-kits.py claude            # nur Claude-Sandbox
python local-test\local-test-kits.py mammouth          # nur Mammouth-Sandbox
python local-test\local-test-kits.py                   # alle Szenarien
```

## IntelliJ MCP: Permission-Whitelist + Run-Config-Guard

Der Zugriff auf die IntelliJ-MCP-Tools (`idea_*`) ist für **OpenCode (Mixin-Kit), Claude Code und
Mammouth Code (Agent-Kit)** per **Whitelist** eingeschränkt — Deny-by-Default, nur lesende Operationen sind
erlaubt. Die Config liegt je Agent-Location vor:

- **OpenCode / Mammouth** (OpenCode-Fork, nutzt dieselben `permission`-Regeln und Plugin-Hooks):
  `permission`-Block in `files/home/.config/opencode/opencode.jsonc` und
  `mammouth-agent/files/home/.config/mammouth/opencode.jsonc`: breites `"idea_*": "deny"` zuerst, danach
  gezielte `allow`-Regeln. **Reihenfolge zählt** — opencode wertet die letzte passende Rule aus (`findLast`),
  deshalb Deny vor Allows.
- **Claude Code**: `permissions`-Block in `files/home/.claude/settings.json`. Kein Deny-by-Default wie bei
  OpenCode, sondern eine explizite `allow`-Whitelist (nur-lesende MCP-Tools als `mcp__idea__<tool>`), eine
  `deny`-Blocklist für die schreibenden/ausführenden Tools. Nicht gelistete Tools fallen auf den
  Standard-Prompt zurück. Der Run-Config-Guard läuft als **PreToolUse-Hook** (siehe unten) statt als Plugin.
  Hooks + statusLine liegen **nicht** in der user-`settings.json`, sondern in der `managed-settings.json`
  unter `/etc/claude-code/` (via `setup.install`): höchste Precedence, wird vom Template nicht überschrieben —
  umgeht die Race Condition, bei der das Template die user-`settings.json` beim Start überschreibt (siehe
  `session-start-hook-fix.md`). Doppeltes Feuern wird vermieden, weil `files/home/.claude/settings.json` und
  `settings.kit.json` bewusst **keine** `hooks`/`statusLine` mehr enthalten.
- **Erlaubt (nur lesend)**: `idea_get_*`, `idea_list_*`, `idea_search_*`, `idea_read*`, `idea_generate_*`,
  `idea_xdebug_get_*`, `idea_xdebug_list_*` sowie einzeln `idea_analyze_calls`, `idea_git_status`,
  `idea_lint_files`, `idea_skill_search`, `idea_fetch_query_result`, `idea_preview_table_data`,
  `idea_test_database_connection`, `idea_introspect_schema`, `idea_run_inspection_kts`,
  `idea_validate_inspection_kts` (39 Tools).
- **`ask`**: `idea_execute_run_configuration` — braucht Bestätigung und wird zusätzlich durch den
  Run-Config-Guard auf `local-test-kits-validate-only` begrenzt.
- **Versteckt (deny)**: alle schreibenden/ausführenden Tools (`idea_apply_patch`, `idea_execute_terminal_command`,
  `idea_execute_tool`, `idea_open_file_in_editor`, `idea_reformat_file`, `idea_rename_refactoring`,
  `idea_build_project`, `idea_notebookEdit`, `idea_xdebug_set_*`, `idea_xdebug_run_to_line`,
  `idea_xdebug_control_session`, `idea_xdebug_start_debugger_session`, DB-Connection-Änderungen, ...) — via
  `visibleTools()` nicht einmal sichtbar.

**Run-Config-Guard**: Das Permission-System sieht bei
MCP-Tools nie die Tool-Inputs (immer `resource: "*"`), daher ist `configurationName` nur im Hook sichtbar.
- OpenCode/Mammouth (`files/home/.config/opencode/plugins/intellij-run-config-guard.js` und
  `mammouth-agent/files/home/.config/mammouth/plugins/intellij-run-config-guard.js`): Plugin-Hook
  `tool.execute.before`. Erlaubt dort ausschließlich die Run-Config `local-test-kits-validate-only` und blockt
  alle anderen mit einem Fehler.
- Claude Code (`files/home/.config/sandbox-kit/intellij-run-config-guard.sh`): PreToolUse-Hook gematcht auf
  `mcp__idea__execute_run_configuration`. Liest `tool_input.configurationName` aus dem Hook-Payload; erlaubt
  `local-test-kits-validate-only` (exit 0 = pass), blockt alles andere (`permissionDecision: deny`, exit 2).
  Andere MCP-Tools passieren den Hook unverändert.

> **Änderungen an `opencode.jsonc`/Plugins werden beim Start geladen (kein Hot-Reload)** — nach Anpassungen
> opencode/mammouth neu starten.

## GitHub Authentication

> **`sbx secret` (v0.38+):** Seit v0.38 ist das `-g`-Flag bei `sbx secret set` entfernt — Service-Secrets sind
> standardmäßig **global**, der Service ist ein Positionsargument (`sbx secret set github` statt
> `sbx secret set -g github`). Mit `--sandbox <name>` wird ein Secret auf eine Sandbox gescoped.
> Kit-deklarierte Services (context7, deepseek, openrouter, mammouth) funktionieren identisch zu den Built-ins.
> **Neu:** Third-Party-v2-Kits benötigen pro Service ein **Credential-Binding** (`credentials.yaml`,
> Windows: `%APPDATA%\sbx\credentials.yaml`) — beim ersten Lauf interaktiv abgefragt, in CI vorab anlegen.

Für `gh` CLI in der Sandbox ein persönliches GitHub-Token (Name: `opencode-sandbox-kit-github-token`) erstellen und als Secret speichern:

```powershell
sbx secret set github -t "<github-token>"
```

Das Token wird via Proxy automatisch injiziert – `gh auth status` sollte in der Sandbox funktionieren.

## Anthropic Authentication

Für Claude Code in der Sandbox wird der Anthropic API-Key als Secret gespeichert und vom Proxy verwaltet – der Key liegt nie im Sandbox-Filesystem:

```powershell
sbx secret set anthropic
```

Es wird davon ausgegangen, dass `ANTHROPIC_API_KEY` nicht als Env-Variable gesetzt ist – der Key wird interaktiv eingegeben. Falls bereits ein OAuth-Token existiert, wird nachgefragt – mit `-f` überschreiben:

```powershell
sbx secret set anthropic -f
```

In der Sandbox sollte `env | grep -i ANTHROPIC` leer sein, während API-Calls über den Proxy trotzdem funktionieren.

## Context7 Authentication

Für höheres Rate-Limit kann ein Context7 API-Key (https://context7.com/dashboard) verwendet werden.
Das Kit deklariert den Service `context7` (`credentials[].apiKey` mit `name: CONTEXT7_API_KEY`,
`proxyManaged: true`). Den Key als Secret registrieren – der Key liegt nie im Sandbox-Filesystem:

```powershell
sbx secret set context7
```

In der Sandbox ist `CONTEXT7_API_KEY=proxy-managed` gesetzt (Platzhalter); die ctx7-CLI sendet
`Authorization: Bearer proxy-managed`, der Proxy ersetzt den Platzhalter transparent bei Requests
an `context7.com`. `echo $CONTEXT7_API_KEY` zeigt nie den echten Key.

## OpenRouter Authentication

OpenRouter ist als zusätzlicher Provider im OpenCode-Setup konfiguriert (`provider.openrouter` in
`files/home/.config/opencode/opencode.jsonc`, DeepSeek bleibt Default-Modell). `openrouter` ist ein
**Built-in-Service des `opencode`-Templates** — das Kit deklariert ihn **bewusst nicht** in `spec.yaml`
(Doppel-Deklaration → `credential ... defined in both "opencode" and ...`). Den Key als Secret
registrieren; das Template setzt `OPENROUTER_API_KEY=proxy-managed`, der Proxy injiziert den echten
Key bei Requests an `openrouter.ai` – der Key liegt nie im Sandbox-Filesystem:

```powershell
sbx secret set openrouter
```

In der Sandbox ist `OPENROUTER_API_KEY=proxy-managed` gesetzt (Platzhalter); OpenCode sendet
`Authorization: Bearer proxy-managed`, der Proxy ersetzt den Platzhalter transparent bei Requests
an `openrouter.ai`. `echo $OPENROUTER_API_KEY` zeigt nie den echten Key.

## Google Authentication

Google Gemini ist als zusätzlicher Provider im OpenCode-Setup konfiguriert (`provider.google` in
`files/home/.config/opencode/opencode.jsonc`, DeepSeek bleibt Default-Modell). `google` ist ein
**Built-in-Service des `opencode`-Templates** (wie `openrouter`) — das Kit deklariert ihn **bewusst nicht**
in `spec.yaml` (Doppel-Deklaration → `credential ... defined in both "opencode" and ...`). Den Key als
Secret registrieren; das Template setzt den Platzhalter `GOOGLE_GENERATIVE_AI_API_KEY=proxy-managed`,
der Proxy injiziert den echten Key bei Requests an `generativelanguage.googleapis.com` – der Key liegt nie im Sandbox-Filesystem:

```powershell
# 1. API-Key erstellen: https://aistudio.google.com/apikey
# 2. Secret registrieren (Built-in-Service)
sbx secret set google
```

In der Sandbox ist `GOOGLE_GENERATIVE_AI_API_KEY=proxy-managed` gesetzt (Platzhalter); OpenCode sendet
den Platzhalter als Key, der Proxy ersetzt ihn transparent bei Requests
an `generativelanguage.googleapis.com`. `echo $GOOGLE_GENERATIVE_AI_API_KEY` zeigt nie den echten Key.

### Token-Scopes (aktuell konfiguriert)

| Scope | Beschreibung |
|-------|-------------|
| `read:org` | Organisationen lesen |
| `read:packages` | Packages lesen |
| `read:project` | Projects lesen |
| `read:user` | Benutzerdaten lesen |

> **Hinweis:** Für Private-Repo-Zugriff, Push oder PR/Issue-Erstellung wird zusätzlich das `repo`-Scope benötigt. Dies kann via `gh auth refresh -h github.com -s repo` nachgefordert werden.

## Stack Overflow Authentication

Stack Overflow ist eine **optionale Fallback-Quelle** (`api.stackexchange.com`) bei konkreten
Fehlermeldungen (Exception-Stacktraces, Build-Fehler, Plugin-Konflikte), wenn Context7 **keine
Ergebnisse** liefert. Den API-Key anlegen unter https://stackapps.com/applications (Application
registrieren, dann `key` kopieren). Das Kit deklariert den Service `stackoverflow`
(`credentials[].apiKey` mit `name: STACKOVERFLOW_API_KEY`, `proxyManaged: true`). Den Key als
Secret registrieren – der Key liegt nie im Sandbox-Filesystem:

```powershell
sbx secret set stackoverflow
```

In der Sandbox ist `STACKOVERFLOW_API_KEY=proxy-managed` gesetzt (Platzhalter); der Agent sendet
`Authorization: Bearer proxy-managed`, der Proxy ersetzt den Platzhalter transparent bei Requests
an `api.stackexchange.com`. `echo $STACKOVERFLOW_API_KEY` zeigt nie den echten Key.

Die API-Doku liegt **offline im Kit**: `files/home/stackexchange-api.md` → `~/stackexchange-api.md`
(kompakte Endpoint-Tabelle, generische Parameter, API-Version `api_revision`); Detail-Doku mit allen
Parametern je Methode in `~/stackexchange-api-detail.md` (nur bei Bedarf lesen). Das spart Kontext —
die Website https://api.stackexchange.com/docs wird nur noch bei Unklarheiten abgerufen. Die
API-Version (`api_revision`) kann per `GET /2.3/info?site=stackoverflow` verifiziert werden.
Der **Update-Check** läuft im Validate-Script (`local-test/local-test-kits.py --validate-only`,
IntelliJ-Config `local-test-kits-validate-only`): er vergleicht die dokumentierte Version in den
Doku-Dateien mit dem offiziellen Change-Log (`https://api.stackexchange.com/docs/change-log`) und
**schlägt fehl**, wenn eine neuere Version existiert (Doku-Dateien + `api_revision` aktualisieren).
Beide Kits führen identische Kopien (`mammouth-agent/files/home/`), weil jeder Agent sein eigenes
`files/home/`-Mapping hat.

Nutzungsregeln (siehe `files/home/.config/opencode/AGENTS.md` bzw. `.claude/CLAUDE.md`):
- **Letzte Quelle** in der Abfragehierarchie (nach Context7/anderen Quellen, nur bei leeren Ergebnissen).
- **Vor jedem API-Call** fragt die KI den Benutzer explizit um Erlaubnis.
- **Nie** über `websearch`/`webfetch`, nur als direkter API-Call gegen `api.stackexchange.com`.

## Offline Dokumentation (Repsy)

Die Repsy-Doku (Maven/Helm/NuGet/Npm/PyPI/Cargo/Docker auf `repo.repsy.io`) ist
**nicht in Context7** verfügbar. Das Kit checked den Hugo-Markdown-Source beim `setup.install`
(als User 1000) offline nach `~/docs/repsy-docs/` aus — Shallow-Clone (ohne Theme-Submodule,
nur `content/`), idempotent (`git pull --ff-only` bei erneutem Install):

```bash
git clone --depth 1 --single-branch https://github.com/repsyio/repsy-docs.git ~/docs/repsy-docs
```

Der Agent liest bei Bedarf **direkt den Markdown-Source** (token-effizienter als HTML-Parsing
der gerenderten Site) und kann per `git -C ~/docs/repsy-docs pull --ff-only` aktualisieren. Der
Clone läuft über `files/home/.local/bin/install-tooling-user.sh` (beide Kit-Kopien, Drift-Check
greift automatisch) — `github.com` ist bereits in der Network-Allowlist, keine spec.yaml-Änderung
nötig.

## Layout

- `spec.yaml` — kit definition (schemaVersion, caps, commands, kind: mixin)
- `files/home/.config/opencode/opencode.jsonc` — OpenCode config with IntelliJ MCP via `host.docker.internal:64342/sse` + IntelliJ-MCP-Permission-Whitelist (siehe Abschnitt "IntelliJ MCP: Permission-Whitelist + Run-Config-Guard")
- `files/home/.config/opencode/plugins/intellij-run-config-guard.js` — OpenCode-Plugin: erlaubt `idea_execute_run_configuration` nur für `local-test-kits-validate-only`
- `files/home/.config/opencode/AGENTS.md` — OpenCode rules (ctx7 + sandbox tools)
- `files/home/.claude/settings.json` — Claude Code config with IntelliJ MCP via `host.docker.internal:64342/sse` + IntelliJ-MCP-Permission-Whitelist (siehe Abschnitt "IntelliJ MCP: Permission-Whitelist + Run-Config-Guard")
- `files/home/.config/sandbox-kit/intellij-run-config-guard.sh` — Claude Code PreToolUse-Hook: erlaubt `idea_execute_run_configuration` nur für `local-test-kits-validate-only`
- `files/home/.claude/CLAUDE.md` — Claude Code rules (ctx7 + sandbox tools)
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
- OpenCode: `~/.config/opencode/opencode.jsonc` + `~/.config/opencode/AGENTS.md` — Modell `opencode/deepseek-v4-flash-free`
- Claude Code: `~/.claude/settings.json` + `~/.claude/CLAUDE.md` — Modell `claude-sonnet-4-6`, zusätzlich per `ANTHROPIC_DEFAULT_SONNET_MODEL`/`ANTHROPIC_MODEL`-Env (via Kit-`environment.variables`) abgesichert. `files/home/.claude/settings.json` enthält bereits alle nötigen Felder (Kit-Settings + bekannte Template-Keys wie `apiKeyHelper`), damit Claude Code die korrekten Settings liest — auch bei einer Race Condition zwischen Template-Startup und dem `setup.startup`-Hook. Das Template überschreibt die settings.json beim Start — ein `setup.startup`-Hook (Python-Merge, schneller als jq, korrekte Array-Behandlung) stellt danach alle Kit-Felder aus `files/home/.claude/settings.kit.json` sicher. **Hooks + statusLine werden NICHT über diesen Merge gesetzt**, sondern liegen in `managed-settings.json` unter `/etc/claude-code/` (höchste Precedence, Template-sicher, via `setup.install`). Referenz bei Änderungen an `files/home/.claude/settings.json` synchron halten (Kit-Felder in `settings.kit.json`, Template-Felder nur in `settings.json`).
- Mammouth Code: `~/.config/mammouth/opencode.jsonc` + `~/.config/mammouth/AGENTS.md` (nur Agent-Kit)

> **Mammouth Code**: Installiert das Agent-Kit automatisch beim Build (`curl -fsSL https://code.mammouth.ai/install.sh | bash` als User 1000) + Symlink `/usr/local/bin/mammouth` für den Entrypoint. API-Key als `MAMMOUTH_API_KEY` (Provider `mammouth-ai`, Base-URL `https://api.mammouth.ai/v1`), konfiguriert via `credentials[].apiKey` (`name`/`proxyManaged`/`inject`) im Kit.

## Tools installed by the kit

> Die Tooling-Installation ist in beiden Kit-Specs dedupliziert: `setup.install` führt nur noch
> `bash /home/agent/.local/bin/install-tooling*.sh` aus. Die Skripte liegen als identische Kopien in
> den `files/home/.local/bin/`-Bundles beider Kits (kein separates Kanonik-Verzeichnis). **Versionsänderungen**
> (JDK, Maven, Docker, Compose, Helm, shfmt) in einer Kit-Kopie machen, dann die zweite identisch halten
> (`mammouth-agent/files/home/.local/bin/`) → der Validate-only-Lauf (`local-test-kits-validate-only`)
> schlägt bei Drift fehl.

| Tool | Source |
|------|--------|
| Liberica JDK 25.0.4 | GitHub Releases (bell-sw) |
| Apache Maven 3.9.16 | dlcdn.apache.org |
| Docker CLI 27.5.1 | download.docker.com (static binary) |
| Docker Compose 5.4.0 (Plugin) | GitHub Releases (docker/compose) |
| kubectl (latest stable) | dl.k8s.io |
| Helm 3.21.3 (v3) | get.helm.sh |
| ctx7 | npm |
| skills | npm (vercel-labs) |
| prettier | npm |
| renovate | npm |

> **`npm_config_bin_links`:** Die npm-Install-Kommandos laufen mit explizitem Prefix
> `npm_config_bin_links=true` (`install-tooling.sh`), damit die globalen CLIs als Symlinks nach
> `/usr/local/share/npm-global/bin` landen. Zur Laufzeit setzt das Kit dagegen
> `environment.variables.npm_config_bin_links: "false"` (`spec.yaml`), damit npm-Aufrufe des Agents keine
> bin-link-Seiteneffekte erzeugen. Siehe dazu auch `README.md` → "npm bin-links: Install vs. Laufzeit".

> **Warum Helm v3 und nicht v4?** `kokuwaio/helm-maven-plugin` (io.kokuwa.maven, derzeit 6.17.0) ist **nicht mit Helm v4 kompatibel** (offenes Issue [#427](https://github.com/kokuwaio/helm-maven-plugin/issues/427)): Das `registry-login`-Goal übergibt die volle Registry-URL an `helm registry login` — v3 gab dafür nur eine Warnung, **v4 bricht mit `invalid reference: invalid registry` ab**. Das betrifft den `helm push`/Upload (z. B. im spring-6-reactive-Build). Ein Fix-Release existiert noch nicht (nur 6.17.1-SNAPSHOT auf master). Daher pinnt das Kit Helm auf 3.21.3. Ohne Pin würde das Plugin selbst das "latest" Release ziehen (aktuell v4) — bei `useLocalHelmBinary=true` greift die Sandbox-Helm-Version.

## Mammouth Authentication

Für Mammouth Code wird der API-Key als Secret registriert und via Proxy als `MAMMOUTH_API_KEY` injiziert –
der Key liegt nie im Sandbox-Filesystem. Es gibt keinen eingebauten Provider wie bei `anthropic`/`github`,
daher den Kit-deklarierten Service `mammouth` nutzen:

```powershell
# Kit-deklarierter Service (wie sbx secret set anthropic)
sbx secret set mammouth
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

## Netzwerk-Policy (Deny-by-Default)

- **Quelle**: `permissions.network.allow` in `spec.yaml` (bzw. `mammouth-agent/spec.yaml`). Nur gelistete
  Domains sind erreichbar, alles andere → HTTP 403.
- **Enforcement**: Nicht das Kit, sondern die Sandbox selbst erzwingt die Liste — über den **Sandbox-Proxy**
  (`mcp-gateway`, `mcp-gateway.docker.internal`). Er ist der einzige Netzwerk-Ausgang; die Template
  (`docker/sandbox-templates:opencode-docker`) trägt ihn automatisch als `mcp-gateway`-MCP-Server in die
  Agent-Config ein (daher „mcp-gateway Connected“ in OpenCode — kein Fehler). Derselbe Proxy macht die
  **Credential-Injection** (`proxy-managed`-Platzhalter → echter Key, siehe Auth-Abschnitte oben).
- **`files/home/.../network-policy.md` ist rein informativ**: Nur Doku der Allow-Liste in den Agent-Instructions
  (damit der Agent geblockte Calls vermeidet). Erzwingt nichts. Bei Änderungen an `permissions.network.allow`
  synchron aktualisieren (3 Dateien: OpenCode, Claude, Mammouth).

## Docker Sandbox / sbx Dokumentation

Offizielle Docker-Doku für Sandbox-Kits, Templates und Custom Agents:

- [Templates](https://docs.docker.com/ai/sandboxes/customize/templates/) — Custom Template-Images bauen (Base-Images, Dockerfile, `sbx template save`/`load`)
- [Kits](https://docs.docker.com/ai/sandboxes/customize/kits/) — Kit-Übersicht (`kind: mixin` vs. `kind: sandbox`)
- [Kit Reference](https://docs.docker.com/ai/sandboxes/customize/kit-reference/) — spec.yaml-Felder (`sandbox`, `network`, `credentials`, `commands`, `agentContext`)
- [Kit Examples](https://docs.docker.com/ai/sandboxes/customize/kit-examples/) — Beispiel-Kits
- [Build an Agent](https://docs.docker.com/ai/sandboxes/customize/build-an-agent/) — eigenes Agent-Kit bauen (Amp-Tutorial)

## Caveats

- **Docker Socket**: Jede Sandbox hat einen **isolierten Docker Daemon** im eigenen MicroVM (`docker info` zeigt den Sandbox-Namen als Servername) – kein Host-Socket-Mount nötig.
- **Pre-installed opencode**: Das Base-Image enthält eine eigene OpenCode CLI. `npm install -g` überschreibt sie, aber bei Abweichungen ist die Base-Image-Version die Ursache.
- **Skills in `~/.agents/skills/`**: Werden via `skills add -g --all` mit `user: "1000"` installiert, damit sie beim `agent`-User landen.
- **Mammouth Code**: Wird vom Agent-Kit (`mammouth-agent/`) automatisch installiert. Das Mixin-Kit ist bewusst auf OpenCode/Claude Code fokussiert — Mammouth wird ausschließlich über das Agent-Kit betrieben (`sbx run mammouth`).
- **Kit-spec v2**: Beide Kits (Mixin `spec.yaml` und `mammouth-agent/spec.yaml`) nutzen die **stabilen** v2-Felder `schemaVersion: "2"` + `permissions.network.allow` + `setup` + `agentInstructions` (flacher `entrypoint`) — benötigt **sbx v0.38+** (strikte v2-Grammatik; ein v1-Feld in einer `"2"`-Spec ist ein harter Decode-Fehler). Validieren mit `sbx kit validate .` (bzw. `./mammouth-agent`) und `sbx kit inspect ... --output json | jq '.warnings'` (erwartet `[]`). Migration aufs offizielle Skript: `git clone --depth 1 https://github.com/docker/sbx-kits-contrib.git && go run scripts/migrate-v1-to-v2.go <kit-dir>`. Alte v1-Felder (`network.allowedDomains`, `credentials.sources`, `environment.proxyManaged`, `network.serviceAuth`/`serviceDomains`) erzeugen WARN-Meldungen. Offizielle v2-Referenz (nicht in Context7, `docker/docs` ist noch v1): https://github.com/docker/sbx-kits-contrib/blob/main/spec/SPEC-v2.md.
