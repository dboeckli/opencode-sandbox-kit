# Troubleshooting & Caveats

Häufige Probleme beim Betrieb der Sandboxes (KVM/WSL2, IntelliJ-MCP, Mistral-Rate-Limits) und
bekannte Einschränkungen (Kit-Spec v2, vorinstallierte Tools, Skills).

## Troubleshooting

> **Debugging, Analyzing & Logging** (Log-Dateien, `sbx exec`-Viewing, Kit-Validierung, Drift-Check,
> Blocked requests, IntelliJ MCP-Debug): [`debugging-analysis-logging.md`](debugging-analysis-logging.md)

### KVM Permission Denied (WSL2)

On WSL2, the sandbox VM (`nerdbox`) needs access to `/dev/kvm`. If you see:
```
failed to create VM: sailor: Hypervisor error: KVM error: Permission denied
```

User zu den Gruppen `kvm`/`sgx` hinzufügen und die `/dev/kvm`-Ownership korrigieren:

```console
sudo usermod -aG kvm $USER
sudo usermod -aG sgx $USER
sudo chgrp kvm /dev/kvm
```

Restart the sandbox daemon to pick up group changes:

```console
sbx daemon stop
```

```console
sbx daemon start --detach
```

### Remove a sandbox

```powershell
sbx rm <sandbox-name> --force
```

### Mistral Vibe: „Retrying…" / keine Antwort

Vibe-Log in der laufenden Sandbox ansehen (Retry-Grund, z. B. Rate-Limit/Quota):

```powershell
sbx exec <sandbox-name> bash -c 'tail -n 30 ~/.vibe/logs/vibe.log'
```

- `Retrying request category=rate_limited detail=HTTP 429` → **Mistral-Plan/Tier** prüfen, **nicht** das Guthaben:
  die RPS/TPM-Limits hängen am Plan. **Free mode** (Default neuer Accounts) hat sehr niedrige Limits → 429 auch
  bei vorhandenem Guthaben. Limits: https://admin.mistral.ai/plateforme/limits · Plan: https://admin.mistral.ai/subscription
- `403 … tier_not_allowed` (Mistral, Third-Party-Modell wie `zai-glm-5-3`) → Third-Party-Modelle erfordern einen
  **bezahlten Mistral-Plan** (Free mode sperrt sie); das API-Guthaben ($10 Free-Credit) ändert das nicht.
- Z.AI direkt (`api.z.ai`, GLM-5.3-Flash): `429` → **Z.AI-Guthaben nicht aktiv/leer** oder Monats-/Rate-Limit
  (Guthaben: https://z.ai/manage-apikey/billing). Nach Aufladung kurz warten, bis das Guthaben aktiv ist.
- `blocked by network policy: domain …` → fehlende Domain in `mistral-vibe-agent/spec.yaml`
  (`permissions.network.allow`, siehe auch `~/.vibe/network-policy.md`). Hinweis: Wildcards wie `*.mistral.ai`
  matchen **keine** mehrstufigen Subdomains (`api.eu.mistral.ai`) → explizit listen.

### IntelliJ MCP connection failed (WSL2 / Docker)

Seit Issue #57 läuft der IntelliJ MCP über den **sbx MCP Gateway** (dokumentierter Weg). Der Gateway verbindet sich
vom Windows-Host aus mit dem IntelliJ-MCP-Server (`127.0.0.1:64615`, Endpoint `/stream`; Port 64615 seit
IDEA 2026.2.2, Legacy 64342). Voraussetzungen:

Einmalig registrieren:

```powershell
sbx mcp add idea --url http://localhost:64615/stream --skip-ssrf-check
```

Sandbox mit dem MCP-Gateway erzeugen:

```powershell
sbx run opencode `
    --kit ./opencode-agent/ `
    --template docker.io/domboeckli/sbx-opencode-tooling:local `
    --skills=off `
    --static-mcp idea
```

- **Registration nötig**: Ohne `sbx mcp add idea …` und ohne `--static-mcp idea` (oder `sbx mcp load idea --sandbox`)
  sind keine IntelliJ-MCP-Tools verfügbar — der Gateway lädt nur registrierte Server.
- **Endpoint `/stream`**: Der JetBrains-Server (2026.2.1) bietet Streamable HTTP unter `/stream`
  (nicht `/sse`); `/sse` ist klassisches SSE und vom Gateway nicht nutzbar (POST `initialize` → 405).
- **`--skip-ssrf-check`**: Die SSRF-Guard blockt Loopback-Hosts; `localhost` ist hier sicher (eigener IntelliJ).
- **Registration lebt auf dem Host**: Der Gateway erreicht IntelliJ über `localhost` (Host-Seite), nicht über
  `host.docker.internal` aus der Sandbox.
- **Port ändert sich nach IDE-Update (2026.2.2 → 64615)**: Der JetBrains-MCP-Server bindet nicht zwingend dauerhaft
  denselben Port. Aktuellen Port in der IDE ablesen (**Settings → Tools → MCP Server** → Client-Config „Copy Config"),
  die Registration anpassen (`sbx mcp rm idea`, dann `sbx mcp add idea --url http://localhost:<port>/stream
  --skip-ssrf-check`) und die Sandbox mit aktualisierter Kit-Allowlist neu erzeugen (sonst blockt der Proxy den neuen
  Port mit HTTP 403). Symptom bei Port-Drift: Health-Check meldet `intellij-mcp:FAIL`, Port ist auf dem Host aber
  belegt (Listener vorhanden).
- **Port ist dynamisch — Neustart von IDEA/Rechner verliert die Verbindung**: JetBrains bestätigt, dass der
  MCP-Server seinen Port **dynamisch wählt** (YouTrack IJPL-248682). Ein Neustart kann also einen neuen Port
  vergeben → nach jedem Neustart Port prüfen und Registration/Allowlist anpassen (s.o.). Dauerlösung steht aus:
  **IJPL-207839** („Configurable MCP Server Port") ist ein offener Feature-Request — **beobachten**.
  Vollständige Analyse + Issue-Referenzen: [`intellij-mcp-port.md`](intellij-mcp-port.md).

> **Wichtig (Legacy, vor Issue #57):** Bei der alten Direkt-Config war die MCP-URL auf `host.docker.internal:64342/sse`
> konfiguriert und die Sandbox verband sich direkt mit dem Host. Dieser Weg ist entfernt. Für Health-Checks
> (`[startup-checks] intellij-mcp:OK`) wird die Erreichbarkeit weiterhin aus der Sandbox über
> `host.docker.internal:64615/sse` geprüft (Port 64615 seit IDEA 2026.2.2, Legacy 64342) — das bestätigt nur,
> dass IntelliJ auf dem Host läuft (Voraussetzung für den Gateway), nicht dass der Gateway verbunden ist.

**Manuelle Verifikation vom Host** (PowerShell oder WSL):

IntelliJ-Server läuft? (Host-Seite; Health-Check-Pfad wie im Sandbox-Startup-Check):

```bash
sbx exec <sandbox-name> bash -c 'curl -s -o /dev/null -w "HTTP %{http_code}\n" -m 3 http://host.docker.internal:64615/sse'
```

Registration prüfen:

```bash
sbx mcp ls
```

Gateway laden (falls Sandbox ohne `--static-mcp` erzeugt wurde):

```bash
sbx mcp load idea --sandbox <sandbox-name>
```

Erwartet (1): `HTTP 200` (das SSE-Endpoint hält die Verbindung offen — `-m 3` beendet curl nach 3s;
nur der HTTP-Code zählt, ein `FEHLER`-Exit ist dabei normal). (2) `sbx mcp ls` zeigt `idea   remote   ✓ ready`.

Falls die Gateway-Verbindung fehlschlägt (Log: `connect to idea: … Method Not Allowed`): prüfen, dass der Endpoint
`/stream` (nicht `/sse`) registriert ist — `sbx mcp inspect idea` muss `URL: http://localhost:64615/stream` zeigen.
Stelle zudem sicher, dass Port 64615 in der Windows-Firewall freigegeben ist.

## Caveats

### Kit-Spec v2 und die sbx-Version

Alle Kits (`opencode-agent/`, `mammouth-agent/`, `mistral-vibe-agent/`) sind auf die
**v2-Kit-Grammatik** migriert:
`schemaVersion: "2"`, `permissions.network.allow`, `credentials[].apiKey` (`apiKey.name` + `inject`),
`setup.install` und `setup.startup`, Top-Level `environment.variables`, `agentInstructions` sowie flacher
`sandbox.entrypoint`. Die Migration verlangt **sbx v0.38+** (strikte v2-Grammatik mit hartem
Decode-Fehler für v1-Felder in einer `"2"`-Spec). Validierung:

```bash
sbx kit validate ./opencode-agent
```

```bash
sbx kit validate ./mammouth-agent
```

```bash
sbx kit validate ./mistral-vibe-agent
```

```bash
sbx kit inspect ./opencode-agent --json | jq '.warnings'
```

Erwartet: `[]` bzw. `null`.

Migration auf das offizielle Skript aus `docker/sbx-kits-contrib`:

```bash
git clone --depth 1 https://github.com/docker/sbx-kits-contrib.git
go run scripts/migrate-v1-to-v2.go <kit-dir>
```

Offizielle v2-Referenz: https://github.com/docker/sbx-kits-contrib/blob/main/spec/SPEC-v2.md
(enthalten im `sbx-kits-contrib`-Repo; nicht in Context7, `docker/docs` dokumentiert noch v1).

### Mammouth Code wird ausschließlich über das Agent-Kit betrieben

Mammouth Code wird über das **dedizierte Agent-Kit** (`mammouth-agent/`,
`sbx run --skills=off ./mammouth-agent/`) betrieben; das eigene Image `docker.io/domboeckli/sbx-mammouth`
backt Mammouth beim **Image-Build** (gepinnt auf **v1.18.31.2** via `ARG MAMMOUTH_VERSION` +
Symlink; Pin via Renovate). Das
`opencode-agent/`-Kit (`sbx run --skills=off opencode/claude --kit ./opencode-agent/`) ist bewusst auf OpenCode und
Claude Code fokussiert und enthält keine Mammouth-Konfiguration.

### Mistral Vibe wird ausschließlich über das Agent-Kit betrieben

Mistral Vibe wird über das **dedizierte Agent-Kit** (`mistral-vibe-agent/`,
`sbx run --skills=off ./mistral-vibe-agent/`) betrieben. Das Kit nutzt ein eigenes, gepinntes Image
(`docker.io/domboeckli/sbx-mistral-vibe:<vibe-version>`), das Vibe beim Image-Build installiert — es gibt keinen
`setup.install`-Schritt für Vibe. Das Image muss vor dem ersten Start publiziert sein
(`build-and-publish-mistral-vibe-image.yml`, `workflow_dispatch`).

### Pre-installed Tools im Base Image

Das Sandbox Base-Image (`docker/sandbox-templates:opencode-docker-0.x.0`; für OpenCode gebacken in `docker.io/domboeckli/sbx-opencode-tooling:0.x.0`) enthält eine eigene OpenCode CLI
(aktuell `1.17.11` in der Sandbox). Das Kit überschreibt diese Version **nicht**. OpenCode ist inzwischen
bei `1.18.11` – falls nach dem Kit-Build eine ältere Version angezeigt wird, liegt das an der
vorinstallierten Version im Base-Image. Zum Aktualisieren in der Sandbox:

```
npm install -g @opencode-ai/cli
```

### Skills landen nicht bei `agent`

Falls Skills in der Sandbox nicht sichtbar sind (`ls ~/.agents/skills/` leer), liegt es meist daran,
dass der `skills add`-Befehl als `root` statt als `agent` lief. Im Kit ist `user: "1000"` gesetzt –
beim Test muss die Sandbox neu erstellt werden (`sbx template rm ...` + `sbx run ...`).
