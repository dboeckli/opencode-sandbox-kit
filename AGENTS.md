# opencode-sandbox-kit

Sandbox Kit (mixin) for OpenCode / Mammouth Code / Claude Code / Mistral Vibe with ctx7 and IntelliJ MCP.
Repo: https://github.com/dboeckli/opencode-sandbox-kit

## Environment (wichtig!)

Der Agent läuft in einer **Docker-Sandbox** (MicroVM). Das Kit ist aber ein **Windows-Setup** — der Host
(IntelliJ MCP via `host.docker.internal:64615`; Port 64615 seit IDEA 2026.2.2, Legacy 64342) läuft immer auf Windows:

- **Agent-Sandbox** (hier): Agent-Laufzeit — ich teste Linux-Tools (`ctx7`, `curl`, ...), Versions-Checks und Doku-Recherche. `sbx` ist hier **nicht** verfügbar (nicht im Sandbox-Image installiert).
- **Windows/PowerShell** (User, **Standard**): Alle Sandbox-Befehle (`sbx run`, `sbx exec`, `sbx template rm`, `sbx secret set`) führt der User in PowerShell aus — Docker Desktop läuft nativ auf Windows.
- **Ubuntu-WSL** (User, Alternative): Die Sandbox-Befehle laufen auch aus einem Ubuntu-WSL-Setup heraus (Laufzeitumgebung dort: **Ubuntu 26.04**) — inkl. `host.docker.internal`-Zugriff für IntelliJ MCP und der Secret-Injection. Der Host bleibt derselbe: IntelliJ auf Windows.
- Dokus (AGENTS.md/README) müssen **PowerShell-Syntax** verwenden.

## Git commits (Nachfragen-Pflicht)

Mache **niemals unaufgefordert Commits**: `git commit`, `git push`, PR-Erstellung und ähnliche Git-Operationen
nur mit expliziter Zustimmung des Users ausführen. Ansonsten Änderungen stehen lassen und am Ende den User fragen,
ob ein Commit erstellt werden soll.

## Feature Branches (Pflicht)

Bei **jeder Änderung** an diesem Repository immer **zuerst einen Feature Branch anlegen** (falls noch nicht
vorhanden), dessen Name mit `feature/` beginnt (z. B. `feature/mein-feature`). Direktes Committen auf `master`
ist nicht erlaubt. Nach Änderungen den Feature Branch committen/pushen und den User fragen, ob ein PR erstellt
werden soll.

### Feature Branch mit GitHub-Issue (Zusatzregel)

Gehört zu einem Feature Branch ein GitHub-Issue, gilt zusätzlich:

- **Namenskonvention:** `feature/<issue-nummer>-<kurzer-text>` — Issue-Nummer direkt nach `feature/`, danach ein
  Dash, danach ein kurzer Text mit **maximal 4 Wörtern** (z. B. `feature/66-github-packages-maven`).
- **Verdrahtung:** Der Branch wird im Issue verlinkt (Feld „Development"/Linked Branches). Am saubersten legt man
  den Branch **direkt über die GitHub-GraphQL-Mutation `createLinkedBranch`** an (`issueId` + `oid` = Base-SHA +
  `name`) — sie erstellt und verlinkt den Branch in einem Schritt. Alternativ `gh issue develop <nummer> --name <branch>`.
  **Nicht** vorher per REST/Git anlegen: `createLinkedBranch` verknüpft nur frisch angelegte Branches, sonst
  schlägt die Verknüpfung fehl (`linkedBranch: null`).

## GitHub Actions: `action_required` — Build manuell freigeben (Pflicht)

Endet ein CI-Lauf nach Push/PR mit **`action_required`** (typisch: kein Job gestartet, PR-Status
„Expected — Waiting" bzw. `BLOCKED`), liegt das in der Regel an der **manuellen Freigabepflicht für
geänderte Pipelines** (`.github/workflows/*.yml` wurde im Branch/PR geändert). Den **Entwickler
darauf hinweisen, den Build im GitHub-UI manuell freizugeben** (Actions-Tab → Run → „Review" /
Approve) und die Freigabe abwarten. **Keine Workarounds** zur Umgehung der Freigabe: kein
Close/Reopen des PRs, kein Rerun über die API, kein Force-Push/Empty-Commit.

## Commands

- `sbx kit validate ./opencode-agent` — validate the kit; run it after every change and report the output as evidence before committing
- `sbx mcp add idea --url http://localhost:64615/stream --skip-ssrf-check` — einmalig (IntelliJ MCP auf dem Host registrieren; Voraussetzung für `--static-mcp idea`, siehe Abschnitt "IntelliJ MCP")
- Test the kit with an OpenCode sandbox (via PowerShell on Windows); Template-Version **gepinnt** auf `0.5.0`:
  ```powershell
  sbx run opencode `
      --kit ./opencode-agent/ `
      --template docker/sandbox-templates:opencode-docker-0.5.0 `
      --skills=off `
      --static-mcp idea
  ```
- Test the kit with a Claude Code sandbox (via PowerShell on Windows); Template-Pin `0.5.0` (Home, `api.anthropic.com`):
  ```powershell
  sbx run claude `
      --kit ./opencode-agent/ `
      --template docker/sandbox-templates:claude-code-docker-0.5.0 `
      --skills=off `
      --static-mcp idea
  ```
- Run the dedicated Mammouth agent kit (kind: sandbox, entrypoint `mammouth`); Template-Pin `0.5.0` steckt im spec-Image (kein `--template` nötig):
  ```powershell
  sbx run ./mammouth-agent/ `
      --skills=off `
      --static-mcp idea
  ```
- Run the dedicated Mistral Vibe agent kit (kind: sandbox; eigenes gepinntes Image `domboeckli/sbx-mistral-vibe:<vibe-version>`, Pin im Dockerfile + spec-Image — kein `--template` nötig). Image muss vorher publiziert sein: CI via `publish-mistral-vibe-image.yml` (`workflow_dispatch`/Push auf `master`), lokal per `docker buildx build ... -t domboeckli/sbx-mistral-vibe:<version> -t domboeckli/sbx-mistral-vibe:local --push ./mistral-vibe-agent` (lokaler Bootstrap setzt zusätzlich den beweglichen Tag `:local`):
  ```powershell
  sbx run ./mistral-vibe-agent/ `
      --skills=off `
      --static-mcp idea
  ```
- Run from remote Git repo:
  ```powershell
  sbx run opencode `
      --kit "git+https://github.com/dboeckli/opencode-sandbox-kit.git#dir=opencode-agent" `
      --skills=off `
      --static-mcp idea
  ```
- Use kit with another project:
  ```powershell
  sbx run opencode `
      --kit "git+https://github.com/dboeckli/opencode-sandbox-kit.git#dir=opencode-agent" `
      --skills=off `
      --static-mcp idea `
      "C:\development\projects\spring-6-reactive"
  ```
- Kubernetes-Support + Maven-Host-Cache: Host-kubeconfig und Host-Maven-Repo (read-only) mounten (kubectl/helm im Sandbox-Cluster; Maven nutzt den lokalen Cache, Issue #87):
  ```powershell
  sbx run opencode `
      --kit ./opencode-agent/ `
      --skills=off `
      --static-mcp idea `
      . `
      "$env:USERPROFILE\.kube:ro" `
      "C:\development\maven-repo:ro"
  ```
- Kubernetes-Support (Claude Code):
  ```powershell
  sbx run claude `
      --kit ./opencode-agent/ `
      --skills=off `
      --static-mcp idea `
      . `
      "$env:USERPROFILE\.kube:ro" `
      "C:\development\maven-repo:ro"
  ```
- Kubernetes-Support (Mammouth Code):
  ```powershell
  sbx run ./mammouth-agent/ `
      --skills=off `
      --static-mcp idea `
      . `
      "$env:USERPROFILE\.kube:ro" `
      "C:\development\maven-repo:ro"
  ```
- Kubernetes-Support (Mistral Vibe):
  ```powershell
  sbx run ./mistral-vibe-agent/ `
      --skills=off `
      --static-mcp idea `
      . `
      "$env:USERPROFILE\.kube:ro" `
      "C:\development\maven-repo:ro"
  ```
- Apply kit to an existing sandbox (restarts sandbox, preserves VM state):
  ```powershell
  sbx kit add <sandbox-name> `
      "git+https://github.com/dboeckli/opencode-sandbox-kit.git#dir=opencode-agent"
  ```
- `sbx settings set kit.allowedSources --% "[\"docker.io/\",\"github.com/dboeckli/\"]"` — allow GitHub as kit source (required once before remote Git)
- `--skills=off` gehört in **jedes** `sbx run`/`sbx create`: der Host-Shared-Skills-Store wird nicht gemountet (Trust Boundary); die Kit-Skills kommen aus `dboeckli/ai-agent-skills`, nicht vom Host. Nur bei Sandbox-Erstellung wirksam — bestehende Sandbox neu erstellen. Doku: https://docs.docker.com/ai/sandboxes/workflows/agent-skills/
- ctx7 installiert das Kit via `npm install -g ctx7` (opencode-agent/spec.yaml `setup.install`); `npx ctx7 setup --opencode` konfiguriert nur ctx7 für OpenCode (nicht Teil des Kits)
- `npx ctx7 docs /docker/docs <query>` — sbx CLI / sandbox documentation (ctx7 library ID: `/docker/docs`; die CLI selbst ist NICHT in Context7 — Offline-Referenz: `~/sbx-cli.md`)
- `python local-test/local-test-kits.py` — automate the 4 scenarios (OpenCode/Claude/Mammouth/Mistral Vibe): validate kits, check secrets, create sandboxes, run startup checks, remove sandboxes (`--keep` to keep them)
- `python local-test/local-test-kits.py --ci` — CI mode (used by GitHub Actions `.github/workflows/e2e.yml`): fake API keys, no real mammouth/mistral API call (only proxy env wiring)
- `python local-test/local-test-kits.py --validate-only` — only `sbx kit validate` (all kits), no secrets check and no sandbox start (default is starting the sandboxes); includes the Stack Exchange + sbx CLI offline-doc update checks, the install-script sync check, the **Sandbox-Template-Version check** (explizite `TEMPLATE_VERSION`-Konstante in `local-test-kits.py` gegen `validate.yml`/`e2e.yml` + Mammouth-spec-Image-Drift + Docker-Hub-Tags, alle Kits), den **Mammouth-CLI-Versions-Check** (Pin vs. latest GitHub-Release `mammouth-ai/code`) und den **Mistral-Vibe-Versions-Check** (Dockerfile-Pin + spec-Image-Tag + shell-Basis-Template vs. latest PyPI `mistral-vibe`)
- `python local-test/regenerate-sbx-doc.py [<version>]` — regenerate `opencode-agent/files/home/sbx-cli.md` (all `--help` outputs) from the pinned `docker/sbx-releases` release binary and sync both kit copies (default: `SBX_VERSION` from `.github/workflows/validate.yml`; pass an explicit version like `v0.39.0` to override). `local-test-kits.py --validate-only` fails when the documented version diverges from the (Renovate-managed) pin and tells you to run this script
- GitHub Actions `.github/workflows/validate.yml` + `.github/workflows/e2e.yml` + `.github/workflows/publish-mistral-vibe-image.yml` — install a **pinned sbx** (env `SBX_VERSION`, currently `v0.43.0`, mantained via Renovate customManager `docker/sbx-releases`); **gepinnte Sandbox-Template-Version** (env `TEMPLATE_VERSION` in beiden Workflows + explizite Konstante in `local-test-kits.py`, aktuell `0.5.0`, Renovate customManager `docker/sandbox-templates`); e2e logs into Docker Hub (variable `DOCKER_USERNAME` + secret `DOCKER_PAT`), registers fake sandbox secrets, runs `local-test-kits.py --ci`. `publish-mistral-vibe-image.yml` baut/pusht das Vibe-Image (linux/amd64, provenance/SBOM) — reusable (`workflow_call`), wird vom e2e vor der Matrix aufgerufen; zusätzlich manuell via `workflow_dispatch`. Tags: master `<pin>`, Feature-Branch `<pin>-<branch-slug>.<timestamp>` (semver) + `<branch-slug>`; das e2e übergibt den Tag per `--kit-arg imageTag=…` (`mistral-vibe-agent/spec.yaml` `args.imageTag`)

## Testing (lokale Verifikation per IntelliJ Run-Configs)

> **Wichtig:** In der Sandbox-Laufzeit ist `sbx` **nicht** verfügbar (nicht im Sandbox-Image installiert — unabhängig
> von WSL). Validierung und Sandbox-Tests laufen daher auf dem Windows-Host via PowerShell (Docker Desktop nativ) —
> der Agent erreicht sie über den IntelliJ MCP (`mcp-gateway_execute_run_configuration` bzw.
> `mcp__mcp-gateway__execute_run_configuration`) mit den Run-Configs in `.run/`.
> `idea_execute_run_configuration` (Legacy-Name der Direkt-Config) ist dabei nicht mehr relevant.
> Der Aufruf mit der Config **ohne** `waitForExit=false` timeout't nach 15 min, obwohl der Test
> (~8 min) evtl. noch läuft — dann Prozessstatus via `idea_execute_terminal_command` + `Get-Process python` prüfen.

IntelliJ Run-Configs (`.run/*.run.xml`, alle rufen `local-test/local-test-kits.py` auf):

| Config | PARAMETERS | Zweck |
|--------|-----------|-------|
| `local-test-kits-full` | *(leer)* | Alle 4 Szenarien (OpenCode/Claude/Mammouth/Mistral Vibe): validate + Secrets + Sandbox |
| `local-test-kits-validate-only` | `--validate-only` | Nur `sbx kit validate` (alle Kits), keine Sandbox |
| `local-test-kits-opencode` | `opencode` | Nur OpenCode-Szenario (Sandbox) |
| `local-test-kits-claude` | `claude` | Nur Claude-Szenario Home (Sandbox) |
| `local-test-kits-mammouth` | `mammouth` | Nur Mammouth-Szenario (Sandbox) |
| `local-test-kits-mistral-vibe` | `mistral-vibe` | Nur Mistral-Vibe-Szenario (Sandbox) |

Alle Configs nutzen dasselbe SDK (`~\AppData\Local\Microsoft\WindowsApps\python3.exe`), WORKING_DIRECTORY
`$PROJECT_DIR$/local-test`, `PYTHONUNBUFFERED=1`. Neue Config in `.run/` anlegen = nur eine XML-Datei mit passendem
`PARAMETERS`; IntelliJ erkennt sie (die `get_run_configurations`-Liste kann kurz veraltet sein — direkt per Namen starten
funktioniert trotzdem).

Äquivalente PowerShell-Befehle:

```powershell
python local-test\local-test-kits.py --validate-only   # nur Validierung
python local-test\local-test-kits.py opencode          # nur OpenCode-Sandbox
python local-test\local-test-kits.py claude            # nur Claude-Sandbox (Home)
python local-test\local-test-kits.py mammouth          # nur Mammouth-Sandbox
python local-test\local-test-kits.py mistral-vibe      # nur Mistral-Vibe-Sandbox
python local-test\local-test-kits.py                   # alle Szenarien
```

## IntelliJ MCP: Permission-Whitelist + Run-Config-Guard

Der IntelliJ-MCP-Server läuft auf dem Windows-Host und wird über den **sbx MCP Gateway** in die Sandbox geliefert
(dokumentierter Weg, Issue #57): einmalig `sbx mcp add idea --url http://localhost:64615/stream --skip-ssrf-check`
registrieren (SSRF-Guard blockt Loopback; `/stream` = Streamable HTTP, nicht `/sse`), dann beim Erzeugen
`--static-mcp idea` setzen (oder `sbx mcp load idea --sandbox` in laufende Sandbox). Die Agent-Configs enthalten
**keine** direkte `mcp.idea`-Konfiguration mehr — die Gateway-Verbindung legt das Template automatisch als
`mcp-gateway` (OpenCode/Mammouth) bzw. in `~/.claude.json` unter `mcp-gateway` (Claude Code) an. Tool-Präfixe:
`mcp-gateway_<tool>` (OpenCode/Mammouth) bzw. `mcp__mcp-gateway__<tool>` (Claude Code) — der frühere direkte
`idea_`/`mcp__idea__`-Prefix existiert nicht mehr.

Der Zugriff auf die IntelliJ-MCP-Tools ist für **OpenCode (Mixin-Kit), Claude Code,
Mammouth Code und Mistral Vibe (Agent-Kits)** per **Whitelist** eingeschränkt — Deny-by-Default, nur lesende Operationen sind
erlaubt. Die Config liegt je Agent-Location vor:

- **OpenCode / Mammouth** (OpenCode-Fork, nutzt dieselben `permission`-Regeln und Plugin-Hooks):
  `permission`-Block in `opencode-agent/files/home/.config/opencode/opencode.jsonc` und
  `mammouth-agent/files/home/.config/mammouth/opencode.jsonc`: breites `"mcp-gateway_*": "deny"` zuerst, danach
  gezielte `allow`-Regeln. **Reihenfolge zählt** — opencode wertet die letzte passende Rule aus (`findLast`),
  deshalb Deny vor Allows.
- **Claude Code**: `permissions`-Block in `opencode-agent/files/home/.claude/settings.json`. Kein Deny-by-Default wie bei
  OpenCode, sondern eine explizite `allow`-Whitelist (nur-lesende MCP-Tools als `mcp__mcp-gateway__<tool>`), eine
  `deny`-Blocklist für die schreibenden/ausführenden Tools. Nicht gelistete Tools fallen auf den
  Standard-Prompt zurück. Der Run-Config-Guard läuft als **PreToolUse-Hook** (siehe unten) statt als Plugin.
  Hooks + statusLine liegen **nicht** in der user-`settings.json`, sondern in der `managed-settings.json`
  unter `/etc/claude-code/` (via `setup.install`): höchste Precedence, wird vom Template nicht überschrieben —
  umgeht die Race Condition, bei der das Template die user-`settings.json` beim Start überschreibt (siehe
  `session-start-hook-fix.md`). Doppeltes Feuern wird vermieden, weil `opencode-agent/files/home/.claude/settings.json` und
  `settings.kit.json` bewusst **keine** `hooks`/`statusLine` mehr enthalten.
- **Mistral Vibe**: `~/.vibe/config.toml` verdrahtet den Gateway (`[[mcp_servers]]`, `transport = "streamable-http"`,
  `url = "http://mcp-gateway.docker.internal/mcp"`, static auth `Authorization: Bearer proxy-managed`) — Vibe ist
  kein unterstützter Template-Agent, das Kit bringt die Config selbst mit. Die Whitelist läuft als
  `pre_tool`-Hook (`~/.vibe/hooks.toml` → `~/.config/sandbox-kit/vibe-mcp-guard.py`), weil das Image Vibe mit
  `--agent auto-approve` startet (approvt alle Tool-Calls, umgeht das Permission-System). Der Hook matcht
  `mcp-gateway_*` und erlaubt dieselbe Read-only-Liste; `strict = true` (fail closed).
- **Erlaubt (nur lesend, OpenCode/Mammouth/Vibe-Pattern)**: `mcp-gateway_get_*`, `mcp-gateway_list_*`,
  `mcp-gateway_search_*`, `mcp-gateway_read*`, `mcp-gateway_generate_*`, `mcp-gateway_xdebug_get_*`,
  `mcp-gateway_xdebug_list_*` sowie einzeln `mcp-gateway_analyze_calls`, `mcp-gateway_git_status`,
  `mcp-gateway_lint_files`, `mcp-gateway_fetch_query_result`, `mcp-gateway_preview_table_data`,
  `mcp-gateway_test_database_connection`, `mcp-gateway_introspect_schema`, `mcp-gateway_run_inspection_kts`,
  `mcp-gateway_validate_inspection_kts`, `mcp-gateway_build_project` (kompiliert das Projekt im IntelliJ —
  bewusst erlaubt, ohne ask), `mcp-gateway_open_file_in_editor` (öffnet Dateien im IntelliJ-Editor —
  bewusst erlaubt, ohne ask). Claude listet die erlaubten Tools einzeln als
  `mcp__mcp-gateway__<tool>` in `permissions.allow`.
- **`ask`**: `mcp-gateway_execute_run_configuration` (Claude: `mcp__mcp-gateway__execute_run_configuration`) —
  braucht Bestätigung und wird zusätzlich durch den Run-Config-Guard auf `local-test-kits-validate-only` begrenzt.
- **Versteckt (deny)**: alle schreibenden/ausführenden Tools (`apply_patch`, `execute_terminal_command`,
  `execute_tool`, `reformat_file`, `rename_refactoring`,
  Notebook-Schreibzugriffe, `xdebug_set_*`, `xdebug_run_to_line`,
  `xdebug_control_session`, `xdebug_start_debugger_session`, DB-Connection-Änderungen, ...) sowie die
  Gateway-Meta-Tools (`code-mode`, `mcp-exec`, `mcp-find`, `mcp-add`, `mcp-config-set`) — via `visibleTools()`
  nicht einmal sichtbar (OpenCode) bzw. in `permissions.deny` (Claude).

**Run-Config-Guard**: Das Permission-System sieht bei
MCP-Tools nie die Tool-Inputs (immer `resource: "*"`), daher ist `configurationName` nur im Hook sichtbar.
- OpenCode/Mammouth (`opencode-agent/files/home/.config/opencode/plugins/intellij-run-config-guard.js` und
  `mammouth-agent/files/home/.config/mammouth/plugins/intellij-run-config-guard.js`): Plugin-Hook
  `tool.execute.before` auf Tool `mcp-gateway_execute_run_configuration`. Erlaubt dort ausschließlich die
  Run-Config `local-test-kits-validate-only` und blockt alle anderen mit einem Fehler.
- Claude Code (`opencode-agent/files/home/.config/sandbox-kit/intellij-run-config-guard.sh`): PreToolUse-Hook gematcht auf
  `mcp__mcp-gateway__execute_run_configuration`. Liest `tool_input.configurationName` aus dem Hook-Payload; erlaubt
  `local-test-kits-validate-only` (exit 0 = pass), blockt alles andere (`permissionDecision: deny`, exit 2).
  Andere MCP-Tools passieren den Hook unverändert.
- Mistral Vibe (`mistral-vibe-agent/files/home/.config/sandbox-kit/vibe-mcp-guard.py`, verdrahtet über
  `~/.vibe/hooks.toml`): `pre_tool`-Hook gematcht auf `mcp-gateway_*`. Kombiniert Read-only-Whitelist und
  Run-Config-Guard: erlaubt die Read-only-Tools, `mcp-gateway_execute_run_configuration` nur für
  `local-test-kits-validate-only`, blockt alles andere.

> **Voraussetzung (Option A, self-contained-Bruch):** Ohne Host-Registrierung (`sbx mcp add idea …`) und ohne
> `--static-mcp idea`/`sbx mcp load` sind keine IntelliJ-MCP-Tools verfügbar. Das ist der dokumentierte
> Docker-Sandboxes-Weg (zentrale MCP-Registry am Host) und der Grund, warum das Kit keine direkte `mcp.idea`-
> Konfiguration mehr mitbringt. Details/Verifikation: Issue #57.

> **Änderungen an `opencode.jsonc`/Plugins werden beim Start geladen (kein Hot-Reload)** — nach Anpassungen
> opencode/mammouth neu starten.

## GitHub Authentication

> **`sbx secret` (v0.38+):** Seit v0.38 ist das `-g`-Flag bei `sbx secret set` entfernt — Service-Secrets sind
> standardmäßig **global**, der Service ist ein Positionsargument (`sbx secret set github` statt
> `sbx secret set -g github`). Mit `--sandbox <name>` wird ein Secret auf eine Sandbox gescoped.
> Kit-deklarierte Services (context7, deepseek, openrouter, mammouth, github-maven) funktionieren identisch zu den Built-ins.
> **Neu:** Third-Party-v2-Kits benötigen pro Service ein **Credential-Binding** (`credentials.yaml`,
> Windows: `%APPDATA%\sbx\credentials.yaml`) — beim ersten Lauf interaktiv abgefragt, in CI vorab anlegen.

Für `gh` CLI in der Sandbox ein persönliches GitHub-Token (Name: `opencode-sandbox-kit-github-token`) erstellen und als Secret speichern:

```powershell
sbx secret set github -t "<github-token>"
```

Das Token wird via Proxy automatisch injiziert – `gh auth status` sollte in der Sandbox funktionieren.

### GitHub Packages Maven (`github-maven`)

Maven-Builds, die ein Artifact aus **GitHub Packages** (`maven.pkg.github.com`) auflösen, brauchen ein
**separates** klassisches PAT (nur Scope `read:packages`) — GitHub Packages akzeptiert kein OAuth-Token
(`gho_…`) und das `github`-Secret bleibt unverändert für `gh`/`git push`:

```powershell
# 1. Klassisches PAT mit Scope read:packages anlegen: https://github.com/settings/tokens
# 2. Secret registrieren
sbx secret set github-maven -t "<classic-pat-read-packages>"
```

In der Sandbox wirkt das Kit so (Startup-Hooks, `opencode-agent/spec.yaml`):
- `~/.m2/settings.xml` wird geschrieben mit einem `<proxies>`-Block (`gateway.docker.internal:3128` — Maven muss
  **durch den Sandbox-Proxy routen**, damit die Credential-Injection greifen kann) und dem Server `github`
  (`<password>${env.GITHUB_MAVEN_TOKEN}</password>`).
- Die Proxy-CA wird in die JDK-`cacerts` importiert (Java/Maven müssen das TLS-Intercept des Proxys vertrauen).
- Der Proxy injiziert den echten `ghp_…`-Token als `Authorization: Bearer <pat>` bei Requests an
  `maven.pkg.github.com` (GitHub Packages akzeptiert den klassischen PAT als Bearer; die `scheme: basic`-Injection
  des Proxys funktioniert nicht und wird nicht verwendet). Der Token liegt nie im Sandbox-Filesystem.
`gh auth status` zeigt weiterhin den vollen OAuth-Token des `github`-Secrets.

> **Wichtig:** Nur echte Maven-Builds (`./mvnw validate` etc.) sind repräsentativ — `mvn dependency:get` ignoriert
> settings-`<proxies>` und läuft an der Injection vorbei (401 ist dort ein Fehlalarm).


### Maven Host-Cache wiederverwenden (optional)

Jede Sandbox lädt Dependencies neu. Um den **lokal gefüllten** Maven-Cache des Hosts zu nutzen, den Host
`~/.m2/repository` **read-only** mounten (keine Credentials, nur Artefakte):

```powershell
sbx run opencode `
    --kit ./opencode-agent/ `
    --skills=off `
    --static-mcp idea `
    . `
    "C:\development\maven-repo:ro"
```

Der settings.xml-Startup-Hook erkennt den Mount (`/c/Users/<user>/.m2/repository`, `/c/*/maven-repo` oder `/c/*/m2-repository`) und ergänzt ein aktives Profil mit
`<repository id="host-cache" url="file://…">` (snapshots disabled). Maven prüft dann: Sandbox-lokal → Host-Cache
(`file://`, kopiert lokal statt Netz) → echte Remotes (Central/GitHub Packages). Ohne Mount bleibt settings.xml
unverändert. Neu geladene Artefakte landen nur im Sandbox-lokalen Repo; der Host-Cache bleibt read-only.

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
`opencode-agent/files/home/.config/opencode/opencode.jsonc`, DeepSeek bleibt Default-Modell). `openrouter` ist ein
**Built-in-Service des `opencode`-Templates** — das Kit deklariert ihn **bewusst nicht** in `opencode-agent/spec.yaml`
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
`opencode-agent/files/home/.config/opencode/opencode.jsonc`, DeepSeek bleibt Default-Modell). `google` ist ein
**Built-in-Service des `opencode`-Templates** (wie `openrouter`) — das Kit deklariert ihn **bewusst nicht**
in `opencode-agent/spec.yaml` (Doppel-Deklaration → `credential ... defined in both "opencode" and ...`). Den Key als
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

Die API-Doku liegt **offline im Kit**: `opencode-agent/files/home/stackexchange-api.md` → `~/stackexchange-api.md`
(kompakte Endpoint-Tabelle, generische Parameter, API-Version `api_revision`); Detail-Doku mit allen
Parametern je Methode in `~/stackexchange-api-detail.md` (nur bei Bedarf lesen). Das spart Kontext —
die Website https://api.stackexchange.com/docs wird nur noch bei Unklarheiten abgerufen. Die
API-Version (`api_revision`) kann per `GET /2.3/info?site=stackoverflow` verifiziert werden.
Der **Update-Check** läuft im Validate-Script (`local-test/local-test-kits.py --validate-only`,
IntelliJ-Config `local-test-kits-validate-only`): er vergleicht die dokumentierte Version in den
Doku-Dateien mit dem offiziellen Change-Log (`https://api.stackexchange.com/docs/change-log`) und
**schlägt fehl**, wenn eine neuere Version existiert (Doku-Dateien + `api_revision` aktualisieren).
Beide Kits führen identische Kopien (`opencode-agent/files/home/`, `mammouth-agent/files/home/`),
weil jeder Agent sein eigenes
`files/home/`-Mapping hat.

Nutzungsregeln (siehe `opencode-agent/files/home/.config/opencode/AGENTS.md` bzw. `.claude/CLAUDE.md`):
- **Letzte Quelle** in der Abfragehierarchie (nach Context7/anderen Quellen, nur bei leeren Ergebnissen).
- **Vor jedem API-Call** fragt die KI den Benutzer explizit um Erlaubnis.
- **Nie** über `websearch`/`webfetch`, nur als direkter API-Call gegen `api.stackexchange.com`.

## Cloudsmith Authentication

Cloudsmith ist eine Artifact-Hosting-Plattform (Maven/NuGet/Npm/PyPI/Docker/etc.). Doku ist via
Context7 verfügbar (`npx ctx7 docs /websites/cloudsmith <query>` bzw.
`/cloudsmith-io/cloudsmith-api` für die API-Bindings, z. B. Uploads über FilesApi).
Den API-Key anlegen unter
https://cloudsmith.io/user/settings/api-keys/. Das Kit deklariert den Service `cloudsmith`
(`credentials[].apiKey` mit `name: CLOUDSMITH_API_KEY`, `proxyManaged: true`). Den Key als
Secret registrieren – der Key liegt nie im Sandbox-Filesystem:

```powershell
sbx secret set cloudsmith
```

In der Sandbox ist `CLOUDSMITH_API_KEY=proxy-managed` gesetzt (Platzhalter); der Agent sendet
`X-Api-Key: proxy-managed`, der Proxy ersetzt den Platzhalter transparent bei Requests an
`api.cloudsmith.io` (REST-API) und `upload.cloudsmith.io` (Package-Upload).
`echo $CLOUDSMITH_API_KEY` zeigt nie den echten Key.

> **Helm-OCI-Pull aus Cloudsmith:** `docker.cloudsmith.io` + `dl.cloudsmith.io` sind in der
> Netzwerk-Allowlist (`permissions.network.allow`) enthalten — Helm-Pull von
> `oci://docker.cloudsmith.io/…` (z. B. rest-mvc-Subcharts) funktioniert in der Sandbox
> (Blob-Download via `dl.cloudsmith.io`). Ein `helm registry login`
> für `docker.cloudsmith.io` ist in der Sandbox nicht möglich (Credential-Injection
> nur für die API-Domains); für lokale Helm-Pull-Tests den `CLOUDSMITH_API_KEY` direkt verwenden.

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
Clone läuft über `opencode-agent/files/home/.local/bin/install-tooling-user.sh` (alle Kit-Kopien, Drift-Check
greift automatisch) — `github.com` ist bereits in der Network-Allowlist, keine spec.yaml-Änderung
nötig.

## Layout

- `opencode-agent/spec.yaml` — kit definition (schemaVersion, caps, commands, kind: mixin)
- `opencode-agent/files/home/.config/opencode/opencode.jsonc` — OpenCode config (Permission-Whitelist für IntelliJ-MCP-Tools via sbx MCP Gateway `mcp-gateway_*`; keine direkte `mcp.idea`-Konfiguration, siehe Abschnitt "IntelliJ MCP: Permission-Whitelist + Run-Config-Guard")
- `opencode-agent/files/home/.config/opencode/plugins/intellij-run-config-guard.js` — OpenCode-Plugin: erlaubt `mcp-gateway_execute_run_configuration` nur für `local-test-kits-validate-only`
- `opencode-agent/files/home/.config/opencode/AGENTS.md` — OpenCode rules (ctx7 + sandbox tools)
- `opencode-agent/files/home/.claude/settings.json` — Claude Code config (Permission-Whitelist `mcp__mcp-gateway__*`; keine `mcpServers.idea`-Konfiguration, siehe Abschnitt "IntelliJ MCP: Permission-Whitelist + Run-Config-Guard")
- `opencode-agent/files/home/.config/sandbox-kit/intellij-run-config-guard.sh` — Claude Code PreToolUse-Hook: erlaubt `mcp__mcp-gateway__execute_run_configuration` nur für `local-test-kits-validate-only`
- `opencode-agent/files/home/.claude/CLAUDE.md` — Claude Code rules (ctx7 + sandbox tools)
- `mammouth-agent/spec.yaml` — dedicated Mammouth agent kit (kind: sandbox, name `mammouth`, entrypoint `mammouth`)
- `mammouth-agent/files/home/.config/mammouth/` — Mammouth config for the agent kit
- `mistral-vibe-agent/spec.yaml` — dedicated Mistral Vibe agent kit (kind: sandbox, name `mistral-vibe`, eigenes Image `domboeckli/sbx-mistral-vibe:<vibe-version>`)
- `mistral-vibe-agent/Dockerfile` — pinned Vibe image (shell-docker-0.5.0 + `uv tool install mistral-vibe==<pin>`); Build/Publish via `.github/workflows/publish-mistral-vibe-image.yml`
- `mistral-vibe-agent/files/home/.vibe/config.toml` — MCP-Gateway-Verdrahtung (`[[mcp_servers]]` → `mcp-gateway.docker.internal/mcp`, `Bearer proxy-managed`)
- `mistral-vibe-agent/files/home/.vibe/hooks.toml` + `files/home/.config/sandbox-kit/vibe-mcp-guard.py` — pre_tool-Read-only-Guard für die IntelliJ-MCP-Tools (auto-approve umgeht das Permission-System)
- `docs/prerequisites.md` — kompakte Übersicht aller Voraussetzungen (Host + Sandbox + Secrets + Netzwerk)

## Dual agent support

Das Kit funktioniert mit **OpenCode, Claude Code, Mammouth Code und Mistral Vibe** – der Agent wird nicht vom Kit bestimmt, sondern vom Template bzw. dem Kit-Image beim `sbx run`. Die **Template-Version ist gepinnt** auf `0.5.0` (2026-08-26) für alle Kits: OpenCode/Mammouth `opencode-docker-0.5.0`, Claude (Home) `claude-code-docker-0.5.0`, Mistral Vibe `shell-docker-0.5.0` (Basis des eigenen Images) — zentrale Source of Truth: `TEMPLATE_VERSION` in `.github/workflows/validate.yml`/`e2e.yml` (Renovate); Mixin-Kits pinnen via `--template` im Command, die Agent-Kits (`kind: sandbox`) via spec-Image bzw. Dockerfile. `local-test-kits.py --validate-only` **warnt** (gelb), sobald ein neuerer Template-Tag auf Docker Hub existiert.

```powershell
sbx mcp add idea --url http://localhost:64615/stream --skip-ssrf-check

sbx run opencode `
    --kit ./opencode-agent/ `
    --template docker/sandbox-templates:opencode-docker-0.5.0 `
    --skills=off `
    --static-mcp idea
sbx run claude `
    --kit ./opencode-agent/ `
    --template docker/sandbox-templates:claude-code-docker-0.5.0 `
    --skills=off `
    --static-mcp idea
sbx run ./mammouth-agent/ `
    --skills=off `
    --static-mcp idea
sbx run ./mistral-vibe-agent/ `
    --skills=off `
    --static-mcp idea
```

Alle vier erhalten dieselben Tools (JDK, Maven, Docker CLI, Helm, Apache Kafka CLI, Skills, ctx7) und den IntelliJ MCP via **sbx MCP Gateway**
(Voraussetzung: einmalig `sbx mcp add idea --url http://localhost:64615/stream --skip-ssrf-check`, Sandbox mit
`--static-mcp idea` erzeugen oder `sbx mcp load idea --sandbox`). Die jeweilige Config wird automatisch gelesen:
- OpenCode: `~/.config/opencode/opencode.jsonc` + `~/.config/opencode/AGENTS.md` — Modell `deepseek/deepseek-v4-flash`
- Claude Code: `~/.claude/settings.json` + `~/.claude/CLAUDE.md` — Modell `claude-sonnet-4-6`, zusätzlich per `ANTHROPIC_DEFAULT_SONNET_MODEL`/`ANTHROPIC_MODEL`-Env (via Kit-`environment.variables`) abgesichert. `opencode-agent/files/home/.claude/settings.json` enthält bereits alle nötigen Felder (Kit-Settings + bekannte Template-Keys wie `apiKeyHelper`), damit Claude Code die korrekten Settings liest — auch bei einer Race Condition zwischen Template-Startup und dem `setup.startup`-Hook. Das Template überschreibt die settings.json beim Start — ein `setup.startup`-Hook (Python-Merge, schneller als jq, korrekte Array-Behandlung) stellt danach alle Kit-Felder aus `opencode-agent/files/home/.claude/settings.kit.json` sicher. **Hooks + statusLine werden NICHT über diesen Merge gesetzt**, sondern liegen in `managed-settings.json` unter `/etc/claude-code/` (höchste Precedence, Template-sicher, via `setup.install`). Referenz bei Änderungen an `opencode-agent/files/home/.claude/settings.json` synchron halten (Kit-Felder in `settings.kit.json`, Template-Felder nur in `settings.json`).
- Mammouth Code: `~/.config/mammouth/opencode.jsonc` + `~/.config/mammouth/AGENTS.md` (nur Agent-Kit)
- Mistral Vibe: `~/.vibe/config.toml` (MCP-Gateway) + `~/.vibe/hooks.toml` (Read-only-Guard) + `~/.vibe/AGENTS.md` (nur Agent-Kit)

> **Mammouth Code**: Installiert das Agent-Kit automatisch beim Build — **gepinnt auf v1.18.31.1**
> (`curl -fsSL https://code.mammouth.ai/install.sh | VERSION=1.18.31.1 bash` als User 1000, Renovate
> `mammouth-ai/code`; `--validate-only` warnt bei neuerem Release) + Symlink `/usr/local/bin/mammouth` für den Entrypoint. API-Key als `MAMMOUTH_API_KEY` (Provider `mammouth-ai`, Base-URL `https://api.mammouth.ai/v1`), konfiguriert via `credentials[].apiKey` (`name`/`proxyManaged`/`inject`) im Kit.

> **Mistral Vibe**: Installiert das Agent-Kit als eigenes gepinntes Image (`mistral-vibe-agent/Dockerfile`: shell-docker-0.5.0 + `uv tool install mistral-vibe==<pin>`, Renovate `mistral-vibe` PyPI). API-Key via Built-in-Service `mistral` (`MISTRAL_API_KEY`, `api.mistral.ai`, Sentinel `proxy-managed`). Image muss vor dem ersten Start publiziert sein (`publish-mistral-vibe-image.yml`, workflow_dispatch).

## Tools installed by the kit

> Die Tooling-Installation ist in allen Kit-Specs dedupliziert: `setup.install` nutzt für die
> **schweren Tools** `bash /home/agent/.local/bin/install-tooling.sh <tool>` — **einen Command pro Tool**
> (`shfmt|jdk|maven|docker|compose|kubectl|helm|helm4|kafka`, Default `all`), damit die `sbx run`-Konsole
> jedes Tool als eigene Zeile (Spinner → ✓) zeigt. npm/apt-Pakete sind als Inline-Commands direkt in
> den Specs (`npm_config_bin_links=true npm install -g ctx7` usw., `apt-get update && …`). Die Skripte
> liegen als identische Kopien in den `files/home/.local/bin/`-Bundles der Kits (kein separates
> Kanonik-Verzeichnis). **Versionsänderungen**
> (JDK, Maven, Docker, Compose, Helm, Kafka, shfmt) in einer Kit-Kopie machen, dann die anderen identisch halten
> (`opencode-agent/files/home/.local/bin/`, `mammouth-agent/files/home/.local/bin/`, `mistral-vibe-agent/files/home/.local/bin/`) → der Validate-only-Lauf
> (`local-test-kits-validate-only`) schlägt bei Drift fehl.

| Tool | Source |
|------|--------|
| Liberica JDK 25.0.4 | GitHub Releases (bell-sw) |
| Apache Maven 3.9.16 | dlcdn.apache.org |
| Docker CLI 27.5.1 | download.docker.com (static binary) |
| Docker Compose 5.4.0 (Plugin) | GitHub Releases (docker/compose) |
| kubectl (latest stable) | dl.k8s.io |
| Helm 3.22.0 (v3, Default) + 4.3.0 (v4) | get.helm.sh |
| Apache Kafka CLI 4.3.1 (Scala 2.13) | dlcdn.apache.org (`/opt/kafka` + `kafka-*.sh`-Wrapper in `/usr/local/bin`) |
| ctx7 | npm |
| skills | npm (vercel-labs) |
| prettier | npm |
| renovate | npm |

> **`npm_config_bin_links`:** Die npm-Install-Kommandos laufen mit explizitem Prefix
> `npm_config_bin_links=true` (`install-tooling.sh`), damit die globalen CLIs als Symlinks nach
> `/usr/local/share/npm-global/bin` landen. Zur Laufzeit setzt das Kit dagegen
> `environment.variables.npm_config_bin_links: "false"` (`opencode-agent/spec.yaml`), damit npm-Aufrufe des Agents keine
> bin-link-Seiteneffekte erzeugen. **Die Variable ist damit bereits global gesetzt — kein
> `export npm_config_bin_links=...` vor npm- oder Build-Kommandos nötig (redundant).**
> Siehe dazu auch `README.md` → "npm bin-links: Install vs. Laufzeit".

> **Helm v3 vs. v4 — beide installiert:** **v3 ist der Default auf dem PATH** (`/usr/local/bin/helm`, gepinnt auf 3.22.0); **v4 liegt parallel** als `/usr/local/bin/helm4` (4.3.0) und kann explizit aufgerufen werden. Renovate trackt beide Versionen getrennt (`HELM_VER` → v3, `HELM4_VER` → v4).

> **Apache Kafka CLI:** Die Kafka-Distribution liegt unter `/opt/kafka`; `install-tooling.sh` legt für jedes
> `bin/*.sh` einen Wrapper in `/usr/local/bin` an, der das Skript per absolutem Pfad ausführt (die Skripte
> lösen ihr `base_dir` über `$(dirname $0)/..` auf — ein Symlink würde das brechen). `dlcdn.apache.org`
> ist in der Network-Allowlist. Renovate trackt `KAFKA_VER` gegen `org.apache.kafka:kafka_2.13` (Maven).

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

## Mistral Authentication

Für Mistral Vibe wird der API-Key als Secret registriert und via Proxy als `MISTRAL_API_KEY` injiziert –
der Key liegt nie im Sandbox-Filesystem. `mistral` ist ein **Built-in-Service** von `sbx` (mappt auf
`MISTRAL_API_KEY` + `api.mistral.ai`); das Kit deklariert `credentials[].service: mistral`:

```powershell
# Built-in-Service (wie sbx secret set anthropic)
sbx secret set mistral
```

Der Key stammt aus https://console.mistral.ai/.

> **Wichtig:** `MISTRAL_API_KEY` ist in der Sandbox auf den Platzhalter `proxy-managed` gesetzt (wie
> `ANTHROPIC_API_KEY` bei Claude). Der Proxy ersetzt den Platzhalter transparent bei Requests an
> `api.mistral.ai`. `env | grep -i MISTRAL` in der Sandbox zeigt `MISTRAL_API_KEY=proxy-managed`
> (nie den echten Key).

Verifikation:

```powershell
sbx secret ls                                                    # Secret ist registriert
sbx exec mistral-vibe-sandbox bash -c 'curl -s https://api.mistral.ai/v1/models -H "Authorization: Bearer $MISTRAL_API_KEY" | head'
```

## Netzwerk-Policy (Deny-by-Default)

- **Quelle**: `permissions.network.allow` in `opencode-agent/spec.yaml` (bzw. `mammouth-agent/spec.yaml`/`mistral-vibe-agent/spec.yaml`). Nur gelistete
  Domains sind erreichbar, alles andere → HTTP 403.
- **Enforcement**: Nicht das Kit, sondern die Sandbox selbst erzwingt die Liste — über den **Sandbox-Proxy**
  (`mcp-gateway`, `mcp-gateway.docker.internal`). Er ist der einzige Netzwerk-Ausgang; die Template
  (`docker/sandbox-templates:opencode-docker`) trägt ihn automatisch als `mcp-gateway`-MCP-Server in die
  Agent-Config ein (daher „mcp-gateway Connected“ in OpenCode — kein Fehler). Derselbe Proxy macht die
  **Credential-Injection** (`proxy-managed`-Platzhalter → echter Key, siehe Auth-Abschnitte oben).
- **`files/home/.../network-policy.md` ist rein informativ**: Nur Doku der Allow-Liste in den Agent-Instructions
  (damit der Agent geblockte Calls vermeidet). Erzwingt nichts. Bei Änderungen an `permissions.network.allow`
  synchron aktualisieren (4 Dateien: OpenCode, Claude, Mammouth, Mistral Vibe).

## Docker Sandbox / sbx Dokumentation

Offizielle Docker-Doku für Sandbox-Kits, Templates und Custom Agents:

- **`~/sbx-cli.md`** — **Offline-Referenz der sbx CLI** (alle `--help`-Outputs, generiert aus der
  v0.43.0-Release-Binary; identische Kopien in allen Kit-Bundles)
- [Templates](https://docs.docker.com/ai/sandboxes/customize/templates/) — Custom Template-Images bauen (Base-Images, Dockerfile, `sbx template save`/`load`)
- [Kits](https://docs.docker.com/ai/sandboxes/customize/kits/) — Kit-Übersicht (`kind: mixin` vs. `kind: sandbox`)
- [Kit Reference](https://docs.docker.com/ai/sandboxes/customize/kit-reference/) — spec.yaml-Felder (`sandbox`, `network`, `credentials`, `commands`, `agentContext`)
- [Kit Examples](https://docs.docker.com/ai/sandboxes/customize/kit-examples/) — Beispiel-Kits
- [Build an Agent](https://docs.docker.com/ai/sandboxes/customize/build-an-agent/) — eigenes Agent-Kit bauen (Amp-Tutorial)

## Caveats

- **Docker Socket**: Jede Sandbox hat einen **isolierten Docker Daemon** im eigenen MicroVM (`docker info` zeigt den Sandbox-Namen als Servername) – kein Host-Socket-Mount nötig. Optional Zugriff auf den **Windows-Host-Daemon** (Container des Hosts sehen/steuern): Docker Desktop → Settings → General → **"Expose daemon on tcp://localhost:2375 without TLS"** aktivieren und in der Sandbox `export DOCKER_HOST=tcp://host.docker.internal:2375` setzen (`host.docker.internal:2375` ist in der Network-Allowlist, siehe `permissions.network.allow`).
- **Pre-installed opencode**: Das Base-Image enthält eine eigene OpenCode CLI. `npm install -g` überschreibt sie, aber bei Abweichungen ist die Base-Image-Version die Ursache.
- **Skills in `~/.agents/skills/`**: Werden via `skills add -g --all` mit `user: "1000"` installiert, damit sie beim `agent`-User landen.
- **Mammouth Code**: Wird vom Agent-Kit (`mammouth-agent/`) automatisch installiert. Das `opencode-agent/`-Kit ist bewusst auf OpenCode/Claude Code fokussiert — Mammouth wird ausschließlich über das Agent-Kit betrieben (`sbx run --skills=off ./mammouth-agent/`).
- **Mistral Vibe**: Wird über das Agent-Kit (`mistral-vibe-agent/`) mit eigenem gepinntem Image betrieben (`sbx run --skills=off ./mistral-vibe-agent/`). Kein `setup.install` für Vibe — die Version steckt im Image (`ARG VIBE_VERSION` im Dockerfile). Image-Bootstrap vor dem ersten Start: `publish-mistral-vibe-image.yml` (workflow_dispatch).
- **Kit-spec v2**: Alle Kits (`opencode-agent/spec.yaml` (Mixin), `mammouth-agent/spec.yaml`, `mistral-vibe-agent/spec.yaml`) nutzen die **stabilen** v2-Felder `schemaVersion: "2"` + `permissions.network.allow` + `setup` + `agentInstructions` (flacher `entrypoint`) — benötigt **sbx v0.38+** (strikte v2-Grammatik; ein v1-Feld in einer `"2"`-Spec ist ein harter Decode-Fehler). Validieren mit `sbx kit validate ./opencode-agent` (bzw. `./mammouth-agent`/`./mistral-vibe-agent`) und `sbx kit inspect ... --json | jq '.warnings'` (erwartet `[]`). Migration aufs offizielle Skript: `git clone --depth 1 https://github.com/docker/sbx-kits-contrib.git && go run scripts/migrate-v1-to-v2.go <kit-dir>`. Alte v1-Felder (`network.allowedDomains`, `credentials.sources`, `environment.proxyManaged`, `network.serviceAuth`/`serviceDomains`) erzeugen WARN-Meldungen. Offizielle v2-Referenz (nicht in Context7, `docker/docs` ist noch v1): https://github.com/docker/sbx-kits-contrib/blob/main/spec/SPEC-v2.md.
