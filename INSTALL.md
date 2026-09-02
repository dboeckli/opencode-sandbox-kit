# Installation

Setup für das opencode-sandbox-kit (OpenCode / Claude Code / Mammouth Code in Docker-Sandboxes).
Ausführliche Doku: [`README.md`](README.md) (Architektur, Kits, Auth-Details),
[`docs/prerequisites.md`](docs/prerequisites.md) (kompakte Gesamtübersicht), [`AGENTS.md`](AGENTS.md) (alle Befehle).

## 1. Voraussetzungen (Windows-Host)

| Voraussetzung | Beschreibung | Benötigt für |
|---------------|--------------|--------------|
| **Docker Desktop** (Windows) | Laufender Docker Daemon — nativ **oder** Ubuntu-WSL-Setup (Laufzeitumgebung: **Ubuntu 26.04**) | Sandbox-Ausführung |
| **`sbx` CLI** | Docker Sandbox CLI, `sbx` im PATH | Sandbox erstellen / verwalten |
| **KVM-Zugriff (WSL2)** | Zugriff auf `/dev/kvm` für die MicroVM (nerdbox) | Sandbox-VM starten |
| **IntelliJ IDEA** | MCP-Server-Plugin auf `127.0.0.1:64342/sse` + Firewall-Freigabe Port 64342 | IntelliJ MCP (optional) |
| **API-Keys / Secrets** | globale Secrets, vom Proxy verwaltet — liegen nie im Sandbox-Filesystem | je nach Agent (siehe Abschnitt 5) |

> **WSL als Alternative:** Standard ist Windows PowerShell + Docker Desktop. Das Kit läuft aber auch aus einem
> **Ubuntu-WSL-Setup** heraus (Laufzeitumgebung dort: **Ubuntu 26.04**). `sbx run` / `sbx exec`
> und der IntelliJ-MCP-Zugriff über `host.docker.internal:64342` funktionieren dort genauso — inkl.
> Secret-Injection (gh/ctx7) und Network-Allow-List.

## 2. Docker Desktop konfigurieren

> **Docker CLI in der Sandbox:** Das Kit installiert die Docker CLI (statisches Binary). Jede Sandbox hat einen
> **isolierten Docker Daemon** im eigenen MicroVM (nerdbox) — kein Host-Socket-Mount nötig, Docker-Befehle
> funktionieren direkt. Der Docker Socket kann nur beim **Erstellen** der Sandbox gemountet werden, nicht nachträglich.

1. **Daemon auf TCP freigeben** (optional, für Zugriff auf die **Host-Container** aus der Sandbox):
   Docker Desktop → **Settings → General → "Expose daemon on tcp://localhost:2375 without TLS"** aktivieren.
   - Ohne diese Einstellung hat die Sandbox nur ihren **isolierten Docker-Daemon** (eigene MicroVM) — Host-Container
     sind nicht sichtbar.
   - Mit aktiver Einstellung: In der Sandbox `export DOCKER_HOST=tcp://host.docker.internal:2375` setzen, um die
     Host-Container zu sehen/steuern (`host.docker.internal:2375` ist in der Network-Allowlist).
2. **Kubernetes** (optional): Docker Desktop → **Settings → Kubernetes → "Enable Kubernetes"** — für kubectl/helm
   mit dem integrierten Cluster. In der Sandbox per Host-kubeconfig (`"$env:USERPROFILE\.kube:ro"` mounten).

## 3. IntelliJ MCP Server aktivieren

Damit der Agent die IntelliJ-MCP-Tools (`idea_*`) nutzen kann, muss auf dem Windows-Host die IDE als
MCP-Server laufen:

1. **IntelliJ IDEA 2025.2 oder neuer** installieren — seit 2025.2 ist ein MCP-Server in der IDE integriert.
2. **MCP Server Plugin aktivieren**: Das Plugin ist gebündelt und standardmäßig aktiviert. Falls
   `idea_*`-Tools nicht verfügbar sind, den Plugin-Status unter **Settings → Plugins** prüfen
   (`MCP Server` muss aktiviert sein).
3. **IDE laufen lassen** und das Projekt öffnen — der MCP-Server lauscht auf `127.0.0.1:64342/sse`.
4. **Port 64342 in der Windows-Firewall freigeben** (nötig für den Zugriff aus der Sandbox über
   `host.docker.internal:64342`).

> Optional (z. B. für weitere MCP-Server im Kit): unter **Settings → Tools → MCP Server** die SSE-URL
> `http://127.0.0.1:64342/sse` als Server registrieren. Für die Kit-Nutzung ist das nicht nötig — die
> Konfiguration liegt bereits in `opencode.jsonc` / `settings.json`.

### IntelliJ MCP Zugriff einschränken (Whitelist + Run-Config-Guard)

Für **OpenCode (Mixin-Kit), Claude Code und Mammouth Code (Agent-Kit)** ist der Zugriff auf die `idea_*`-Tools
per **Whitelist** geregelt (Deny-by-Default, nur lesende Operationen erlaubt). Die Config liegt je
Agent-Location vor:

**OpenCode / Mammouth** (Mammouth ist ein OpenCode-Fork und nutzt dieselben `permission`-Regeln und
Plugin-Hooks) — unter `~/.config/opencode/opencode.jsonc` und `~/.config/mammouth/opencode.jsonc`
(nur Agent-Kit):

- `"idea_*": "deny"` zuerst, danach gezielte `allow`-Regeln. **Reihenfolge zählt**: opencode wertet die letzte
  passende Rule aus (`findLast`), deshalb Deny vor Allows.
- **Erlaubt (nur lesend)**: `idea_get_*`, `idea_list_*`, `idea_search_*`, `idea_read*`, `idea_generate_*`,
  `idea_xdebug_get_*`, `idea_xdebug_list_*` sowie einzeln `idea_analyze_calls`, `idea_git_status`,
  `idea_lint_files`, `idea_skill_search`, `idea_fetch_query_result`, `idea_preview_table_data`,
  `idea_test_database_connection`, `idea_introspect_schema`, `idea_run_inspection_kts`,
  `idea_validate_inspection_kts`.
- **`ask`**: `idea_execute_run_configuration` — nur mit Bestätigung und nur für die im Run-Config-Guard
  erlaubte Config.
- **Versteckt (deny)**: alle schreibenden/ausführenden Tools (`idea_apply_patch`, `idea_execute_terminal_command`,
  `idea_execute_tool`, `idea_open_file_in_editor`, `idea_reformat_file`, `idea_rename_refactoring`,
  `idea_build_project`, `idea_notebookEdit`, `idea_xdebug_set_*`, `idea_xdebug_run_to_line`,
  `idea_xdebug_control_session`, `idea_xdebug_start_debugger_session`, DB-Connection-Änderungen, ...) — sie
  tauchen gar nicht erst in der Tool-Liste auf.

**Claude Code** — `~/.claude/settings.json` (`permissions`-Block): kein Deny-by-Default-Wildcard wie bei
OpenCode (Claude wertet `deny` vor `allow` aus, ein breites `mcp__idea__*`-Deny würde alle Allows
überdecken). Stattdessen eine explizite **`allow`-Whitelist** der nur-lesenden MCP-Tools als
`mcp__idea__<tool>` (analog zur OpenCode-Allowlist), eine **`deny`-Blocklist** für die
schreibenden/ausführenden Tools. Nicht gelistete MCP-Tools fallen auf den Standard-Prompt zurück.
`idea_execute_run_configuration` ist nicht in `allow` — der PreToolUse-Guard trifft die Entscheidung.

**Run-Config-Guard**: MCP-Tools reporten dem Permission-System immer
`resource: "*"` (nie die Tool-Inputs), deshalb kann `idea_execute_run_configuration` nicht per reiner
`permission`-Config auf einzelne Run-Configs begrenzt werden.
- OpenCode/Mammouth (`~/.config/opencode/plugins/intellij-run-config-guard.js` und
  `~/.config/mammouth/plugins/intellij-run-config-guard.js` im Agent-Kit): Plugin-Hook `tool.execute.before`
  liest `configurationName` und erlaubt ausschließlich `local-test-kits-validate-only` — jede andere Config
  wirft einen Fehler.
- Claude Code (`~/.config/sandbox-kit/intellij-run-config-guard.sh`): PreToolUse-Hook gematcht auf
  `mcp__idea__execute_run_configuration`. Liest `tool_input.configurationName`; erlaubt
  `local-test-kits-validate-only` (exit 0), blockt alles andere (`permissionDecision: deny`, exit 2). Andere
  MCP-Tools passieren den Hook unverändert.

> Config und Plugins werden beim Start geladen (kein Hot-Reload) — nach Änderungen opencode/mammouth/claude neu starten.

## 4. Kit-Quellen freigeben (Remote-Git-Kits)

Einmalig nötig, bevor Kits direkt aus GitHub bezogen werden
(`--kit "git+https://github.com/dboeckli/opencode-sandbox-kit.git#dir=opencode-agent"`):

```powershell
sbx settings set kit.allowedSources --% "[\"docker.io/\",\"github.com/dboeckli/\"]"
```

## 5. Secrets registrieren

> **`sbx secret` (v0.38+):** Das `-g`-Flag bei `sbx secret set` ist entfernt — Service-Secrets sind standardmäßig
> **global**, der Service ist ein Positionsargument (`sbx secret set github`). Mit `--sandbox <name>` scopen.
> Kit-deklarierte Services (context7/deepseek/openrouter/mammouth) funktionieren identisch. Third-Party-v2-Kits brauchen
> zusätzlich pro Service ein **Credential-Binding** (`%APPDATA%\sbx\credentials.yaml`; beim ersten Lauf interaktiv).

| Service | Secret | Befehl | Benötigt für |
|---------|--------|--------|--------------|
| GitHub | persönliches Token (`opencode-sandbox-kit-github-token`) | `sbx secret set github -t "<token>"` | `gh` CLI |
| Anthropic | Anthropic API-Key | `sbx secret set anthropic` | Claude Code (Home) |
| Zurich | Zurich LiteLLM API-Key | `sbx secret set zurich` | Claude Code (Zurich-Proxy, `claude-zurich-agent/`) |
| Mammouth | Mammouth API-Key | `sbx secret set mammouth` | Mammouth Code |
| DeepSeek | DeepSeek API-Key | `sbx secret set deepseek` | OpenCode + Mammouth (Default-Modell `deepseek/…`) |
| OpenRouter | OpenRouter API-Key | `sbx secret set openrouter` | OpenCode (optional, Modell `openrouter/…`) |
| Google | Google AI Studio API-Key | `sbx secret set google` | OpenCode (optional, Modell `google/…`) |
| Context7 | Context7 API-Key (optional) | `sbx secret set context7` | ctx7 (höheres Rate-Limit) |
| Stack Overflow | Stack Overflow API-Key (optional) | `sbx secret set stackoverflow` | Fallback-Quelle bei Fehlermeldungen |
| Cloudsmith | Cloudsmith API-Key (optional) | `sbx secret set cloudsmith` | Artifact-Hosting API |

Für den e2e-Test in GitHub Actions werden zusätzlich `DOCKER_USERNAME` (Repo-Variable) und
`DOCKER_PAT` (Secret) benötigt.

### API-Keys & Billing: Konsolen-URLs

| Service | API-Key ansehen/erstellen | Abrechnung / Billing |
|---------|---------------------------|----------------------|
| OpenCode Zen | https://opencode.ai/auth | https://opencode.ai/auth (Guthaben) |
| Google Gemini | https://aistudio.google.com/apikey | https://console.cloud.google.com/billing |
| Anthropic | https://console.anthropic.com/settings/keys | https://console.anthropic.com/settings/billing |
| OpenRouter | https://openrouter.ai/settings/keys | https://openrouter.ai/settings/credits |
| DeepSeek | https://platform.deepseek.com/api_keys | https://platform.deepseek.com/top_up |
| GitHub | https://github.com/settings/tokens | — |
| Context7 | https://context7.com/dashboard | https://context7.com/dashboard |
| Stack Overflow | https://stackapps.com/applications | — |
| Cloudsmith | https://cloudsmith.io/user/settings/api-keys/ | https://cloudsmith.io/user/settings/billing/ |

> **Hinweis:** OpenCode Zen und Direkt-Provider (Google, Anthropic, ...) sind **getrennte Abrechnung**.
> Die Kosten-Anzeige in OpenCode (`$ x.xx spent`) ist eine **lokale Schätzung** aus
> `Token-Verbrauch × Modellpreis` — keine echte Abbuchung. Abgerechnet wird beim jeweiligen Provider
> über dessen Key/Guthaben.

### GitHub Authentication

Für `gh` CLI in der Sandbox ein persönliches GitHub-Token (Name: `opencode-sandbox-kit-github-token`) mit den
Scopes `read:org`, `read:packages`, `read:project`, `read:user` erstellen und als Secret speichern:

```powershell
sbx secret set github -t "<github-token>"
```

Das Token wird via Proxy automatisch injiziert – `gh auth status` funktioniert ohne weitere Konfiguration.

> **Hinweis:** Für Private-Repo-Zugriff, Push oder PR/Issue-Erstellung wird zusätzlich das `repo`-Scope
> benötigt. Dies kann via `gh auth refresh -h github.com -s repo` nachgefordert werden.

### Anthropic Authentication

Für Claude Code in der Sandbox wird der Anthropic API-Key als Secret gespeichert und vom Proxy verwaltet – der Key liegt nie im Sandbox-Filesystem:

```powershell
sbx secret set anthropic
```

Es wird davon ausgegangen, dass `ANTHROPIC_API_KEY` nicht als Env-Variable gesetzt ist – der Key wird interaktiv eingegeben. Falls bereits ein OAuth-Token existiert, wird nachgefragt – mit `-f` überschreiben:

```powershell
sbx secret set anthropic -f
```

Verifikation:

```powershell
sbx secret ls   # sollte "anthropic (stored)" zeigen
```

In der Sandbox sollte `env | grep -i ANTHROPIC` leer sein, während API-Calls über den Proxy trotzdem funktionieren.

### Zurich LiteLLM (separates Kit `claude-zurich-agent/`)

Das `opencode-agent/`-Kit ist der **Home-Standard** (Claude Code gegen `api.anthropic.com`, Modell `claude-sonnet-4-6`).
Für Claude Code über den Zurich-LiteLLM-Proxy (`genai-lounge-nx-litellm-uat-emea.zurich.com`, nur im
Firmennetz erreichbar) das separate Kit `claude-zurich-agent/` verwenden:

```powershell
sbx run claude --name claude-zurich --kit ./claude-zurich-agent/ -t docker/sandbox-templates:claude-code-docker-0.5.0
sbx secret set zurich
```

Es setzt `ANTHROPIC_BASE_URL`, die `eu.anthropic.*`-Modell-Aliasse (`ANTHROPIC_MODEL`/`ANTHROPIC_DEFAULT_SONNET_MODEL`
= `eu.anthropic.claude-sonnet-4-6`, `ANTHROPIC_DEFAULT_OPUS_MODEL` = `eu.anthropic.claude-opus-4-8`,
`ANTHROPIC_DEFAULT_HAIKU_MODEL`/`CLAUDE_CODE_SUBAGENT_MODEL` = `eu.anthropic.claude-haiku-4-5-20251001-v1:0`,
sonst 403 `key not allowed to access model`) und den Service `zurich` (`proxyManaged: true`, Header
`Authorization: Bearer` + `x-api-key`). Details: `claude-zurich-agent/README.md`.

### Mammouth Authentication

**Auth** — API-Key wird als Env-Variable `MAMMOUTH_API_KEY` erwartet (Provider `mammouth-ai` mit Base-URL
`https://api.mammouth.ai/v1`). Der Key stammt aus https://mammouth.ai/app/account/settings/api.

**Secret setzen** — es gibt keinen eingebauten Provider wie bei `anthropic`/`github`. Das Agent-Kit deklariert
den Service `mammouth` (`credentials[].apiKey` mit `name: MAMMOUTH_API_KEY`). Den Key als Secret registrieren,
damit der Proxy ihn für Requests an `api.mammouth.ai` als `MAMMOUTH_API_KEY` injiziert — der Key liegt nie im
Sandbox-Filesystem:

```powershell
# Kit-deklarierter Service (wie sbx secret set anthropic)
sbx secret set mammouth
```

> **Wichtig:** `MAMMOUTH_API_KEY` ist in der Sandbox auf den Platzhalter `proxy-managed` gesetzt — genau wie
> bei Claude Code. Das Agent-Kit setzt sie via `credentials[].apiKey.name` + `proxyManaged: true`; der
> Proxy ersetzt den Platzhalter transparent bei Outbound-Requests an `api.mammouth.ai`. Das ist gewollt,
> kein Fehler. `env | grep MAMMOUTH` zeigt `MAMMOUTH_API_KEY=proxy-managed` (nie den echten Key).

**Verifikation:**

```powershell
# 1. Secret ist registriert
sbx secret ls

# 2. Test-Call aus der Sandbox (Key wird vom Proxy injiziert)
sbx exec mammouth-sandbox bash -c 'curl -s https://api.mammouth.ai/v1/models -H "Authorization: Bearer $MAMMOUTH_API_KEY" | head'
```

#### Context7 API-Key (optional)

Für höheres Rate-Limit kann ein Context7 API-Key verwendet werden (https://context7.com/dashboard).
Das Kit deklariert den Service `context7` (`credentials[].apiKey` mit `name: CONTEXT7_API_KEY`,
`proxyManaged: true`). Den Key als Secret registrieren, damit der Proxy ihn für Requests an
`context7.com` als `Authorization: Bearer` injiziert — der Key liegt nie im Sandbox-Filesystem:

```powershell
# Kit-deklarierter Service (wie sbx secret set mammouth)
sbx secret set context7
```

> **Wichtig:** `CONTEXT7_API_KEY` ist in der Sandbox auf den Platzhalter `proxy-managed` gesetzt.
> Die ctx7-CLI liest die Variable und sendet `Authorization: Bearer proxy-managed`; der Proxy
> ersetzt den Platzhalter transparent bei Outbound-Requests an `context7.com`. Das ist gewollt,
> kein Fehler. `echo $CONTEXT7_API_KEY` zeigt `proxy-managed` (nie den echten Key).

Verifikation (identisch zur Prüfung im automatisierten Test `local-test-kits.py` — ohne Live-API-Call):

```powershell
# 1. Secret ist registriert
sbx secret ls

# 2. In der Sandbox: Platzhalter sichtbar (nie der echte Key) — das ist die Verifikation
sbx exec opencode-sandbox bash -c 'echo $CONTEXT7_API_KEY'   # → proxy-managed
```

Der automatisierte Test prüft bewusst nur den Platzhalter (`echo $CONTEXT7_API_KEY` → `proxy-managed`),
keinen echten Request an `context7.com` — damit läuft er auch im CI mit Fake-Keys.
Ein manueller Live-Call (Key wird dann vom Proxy injiziert) ist optional möglich:

```powershell
sbx exec opencode-sandbox bash -c 'npx ctx7 docs /vercel/next.js "app router"'
```

#### OpenRouter API-Key (optional)

OpenRouter bietet Zugriff auf viele Modelle (Anthropic, OpenAI, Google, DeepSeek, ...) über einen
einheitlichen Endpoint mit Failover — in OpenCode als zusätzlicher Provider konfiguriert
(`opencode-agent/files/home/.config/opencode/opencode.jsonc` → `provider.openrouter`, DeepSeek bleibt Default-Modell).
Doku: https://openrouter.ai/docs/cookbook/coding-agents/opencode-integration

`openrouter` ist ein **Built-in-Service des `opencode`-Templates** (`docker/sandbox-templates:opencode-docker`)
— das Kit deklariert ihn **bewusst nicht** in `opencode-agent/spec.yaml` (eine zweite Deklaration führt zu
`credential for service "openrouter" defined in both "opencode" and ...`). Es reicht, den Key als
Secret zu registrieren; das Template setzt `OPENROUTER_API_KEY` auf den Platzhalter `proxy-managed`
und der Proxy injiziert den echten Key bei Requests an `openrouter.ai` — der Key liegt nie im
Sandbox-Filesystem:

```powershell
# Built-in-Service (wie sbx secret set anthropic / github)
sbx secret set openrouter
```

> **Wichtig:** `OPENROUTER_API_KEY` ist in der Sandbox auf den Platzhalter `proxy-managed` gesetzt.
> OpenCode liest die Variable als `apiKey` für den OpenRouter-Provider; der Proxy ersetzt den
> Platzhalter transparent bei Outbound-Requests an `openrouter.ai`. Das ist gewollt, kein Fehler.
> `echo $OPENROUTER_API_KEY` zeigt `proxy-managed` (nie den echten Key).

Verifikation (identisch zur Prüfung im automatisierten Test `local-test-kits.py` — ohne Live-API-Call):

```powershell
# 1. Secret ist registriert
sbx secret ls

# 2. In der Sandbox: Platzhalter sichtbar (nie der echte Key)
sbx exec opencode-sandbox bash -c 'echo $OPENROUTER_API_KEY'   # → proxy-managed
```

Modellwechsel in OpenCode via `/models` (z. B. `openrouter/~anthropic/claude-sonnet-latest`).

#### Google AI Studio API-Key (optional)

Google Gemini bietet einen generösen Free-Tier (Flash-Modelle) und einen günstigen Pro-Tier — in OpenCode als
zusätzlicher Provider konfiguriert (`opencode-agent/files/home/.config/opencode/opencode.jsonc` → `provider.google`,
DeepSeek bleibt Default-Modell). Doku: https://aistudio.google.com/apikey

`google` ist ein **Built-in-Service des `opencode`-Templates** (`docker/sandbox-templates:opencode-docker`)
— das Kit deklariert ihn **bewusst nicht** in `opencode-agent/spec.yaml` (wie `openrouter`, gleiche Double-Deklarations-Problematik).
Es reicht, den Key als Secret zu registrieren; das Template setzt den Platzhalter `proxy-managed` unter
`GOOGLE_GENERATIVE_AI_API_KEY` (der Env-Name, den OpenCodes Google-Provider standardmäßig liest) und der
Proxy injiziert den echten Key bei Requests an
`generativelanguage.googleapis.com` — der Key liegt nie im Sandbox-Filesystem:

```powershell
# 1. Google AI Studio API-Key erstellen
#    https://aistudio.google.com/apikey

# 2. Built-in-Service (wie sbx secret set anthropic / github)
sbx secret set google
```

> **Wichtig:** Der Google-Platzhalter liegt in der Sandbox unter `GOOGLE_GENERATIVE_AI_API_KEY` auf
> `proxy-managed`. OpenCode liest die Variable als `apiKey` für den Google-Provider; der Proxy ersetzt
> den Platzhalter transparent bei Outbound-Requests an `generativelanguage.googleapis.com`.
> Das ist gewollt, kein Fehler. `echo $GOOGLE_GENERATIVE_AI_API_KEY` zeigt `proxy-managed`
> (nie den echten Key).

Verifikation (identisch zur Prüfung im automatisierten Test `local-test-kits.py` — ohne Live-API-Call):

```powershell
# 1. Secret ist registriert
sbx secret ls

# 2. In der Sandbox: Platzhalter sichtbar (nie der echte Key)
sbx exec opencode-sandbox bash -c 'echo "${GOOGLE_GENERATIVE_AI_API_KEY:-<unset>}"'   # → proxy-managed
```

Modellwechsel in OpenCode via `/models` (z. B. `google/gemini-3.5-flash`).

#### Stack Overflow API-Key (optional)

Stack Overflow (`api.stackexchange.com`) ist eine **optionale Fallback-Quelle** bei konkreten
Fehlermeldungen (Exception-Stacktraces, Build-Fehler, Plugin-Konflikte), wenn Context7 keine
Ergebnisse liefert. Den API-Key anlegen unter **https://stackapps.com/applications** (Application
registrieren, dann `key` kopieren). Das Kit deklariert den Service `stackoverflow` (`credentials[].apiKey` mit
`name: STACKOVERFLOW_API_KEY`, `proxyManaged: true`) — wie `context7` ein Kit-deklarierter
Service. Den Key als Secret registrieren, damit der Proxy ihn für Requests an
`api.stackexchange.com` als `Authorization: Bearer` injiziert — der Key liegt nie im Sandbox-Filesystem:

```powershell
# Kit-deklarierter Service (wie sbx secret set context7)
sbx secret set stackoverflow
```

> **Wichtig:** `STACKOVERFLOW_API_KEY` ist in der Sandbox auf den Platzhalter `proxy-managed` gesetzt.
> Der Agent sendet `Authorization: Bearer proxy-managed`; der Proxy ersetzt den Platzhalter
> transparent bei Outbound-Requests an `api.stackexchange.com`. Das ist gewollt, kein Fehler.
> `echo $STACKOVERFLOW_API_KEY` zeigt `proxy-managed` (nie den echten Key).

Die API-Doku liegt **offline im Kit**: `opencode-agent/files/home/stackexchange-api.md` → `~/stackexchange-api.md`
(kompakte Endpoint-Tabelle, generische Parameter, API-Version `api_revision`); Detail-Doku mit allen
Parametern je Methode in `~/stackexchange-api-detail.md` (nur bei Bedarf lesen). Das spart Kontext —
die Website https://api.stackexchange.com/docs wird nur noch bei Unklarheiten abgerufen. Die
API-Version (`api_revision`) kann per `GET /2.3/info?site=stackoverflow` verifiziert werden.
Der **Update-Check** läuft im Validate-Script (`local-test/local-test-kits.py --validate-only`,
IntelliJ-Config `local-test-kits-validate-only`): er vergleicht die dokumentierte Version in den
Doku-Dateien mit dem offiziellen Change-Log (`https://api.stackexchange.com/docs/change-log`) und
**schlägt fehl**, wenn eine neuere Version existiert (Doku-Dateien + `api_revision` aktualisieren).
Alle Kits führen identische Kopien (`opencode-agent/files/home/`, `mammouth-agent/files/home/`,
`claude-zurich-agent/files/home/`), weil jeder Agent sein eigenes
`files/home/`-Mapping hat.

Nutzungsregeln (SO-1…SO-4):
- **Letzte Quelle** in der Abfragehierarchie (nach Context7/anderen Quellen, nur bei leeren Ergebnissen).
- Die KI fragt den Benutzer **vor jedem API-Call explizit um Erlaubnis**.
- **Nie** über `websearch`/`webfetch`, nur als direkter API-Call gegen `api.stackexchange.com`.
- Calls ohne registriertes Secret oder ohne Zustimmung werden nicht ausgeführt (Netzwerk-Policy blockt).

#### Cloudsmith Authentication

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

## 6. Sandbox starten

```powershell
# Template-Version gepinnt auf 0.5.0 (alle drei Kits, gleiche Version; Mammouth via spec-Image, kein -t nötig)

# OpenCode (Home-Standard)
sbx run opencode --name opencode-sandbox --kit ./opencode-agent/ -t docker/sandbox-templates:opencode-docker-0.5.0

# Claude Code (Home, gegen api.anthropic.com)
sbx run claude --name claude-sandbox --kit ./opencode-agent/ -t docker/sandbox-templates:claude-code-docker-0.5.0

# Claude Code gegen den Zurich-LiteLLM-Proxy (Büro)
sbx run claude --name claude-zurich --kit ./claude-zurich-agent/ -t docker/sandbox-templates:claude-code-docker-0.5.0

# Mammouth Code (eigenes Agent-Kit; Pin im spec-Image)
sbx run mammouth --name mammouth-sandbox --kit ./mammouth-agent/
```

Projekt einbinden + Kubernetes-Support:

```powershell
sbx run opencode --name opencode-sandbox --kit ./opencode-agent/ -t docker/sandbox-templates:opencode-docker-0.5.0 "C:\development\projects\dein-projekt" "$env:USERPROFILE\.kube:ro"
```

Weitere Varianten (Remote-Git-Kit, `sbx kit add`, Ubuntu-WSL-Pfade): [`AGENTS.md`](AGENTS.md#commands) und
[`README.md`](README.md#quickstart).

## 7. Verifikation

```powershell
python local-test\local-test-kits.py --validate-only   # Kit-Validierung (3 Kits) + Drift-Checks
python local-test\local-test-kits.py                   # Volltest (OpenCode/Claude/Claude-Zurich/Mammouth)
```

IntelliJ Run-Configs (alternativ): `local-test-kits-validate-only`, `local-test-kits-full` (siehe `.run/`).
