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

### Veraltete CA-Zertifikate in bestehenden Sandboxes (Issue #202)

`sbx` v0.49.2 behebt die eMudhra-CA-Kompromittierung; die gepinnten Basis-Images
(`docker.io/sbx/shell-docker-image:latest` für alle Custom-Workload-Kits: OpenCode v3/Claude Code v3/Mammouth/Mistral Vibe/Pi) bringen den
aktualisierten Trust-Store mit. **Bestehende** Sandboxes behalten ihren alten Trust-Store —
ein CLI-Update allein genügt nicht. Zwei Wege:

```powershell
# a) laufende Sandbox aktualisieren, danach Apps/Agent in der Sandbox neu starten
sbx exec <sandbox-name> -- sudo apt-get update
sbx exec <sandbox-name> -- sudo apt-get install --only-upgrade -y ca-certificates
```

```powershell
# b) Sandbox mit frischem Image neu erstellen
sbx rm <sandbox-name> --force
sbx run <template> ... --pull always
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
- Z.AI direkt (`api.z.ai`, GLM-5.3-Flash/GLM-5.3): `429` → **Z.AI-Guthaben nicht aktiv/leer** oder Monats-/Rate-Limit
  (Guthaben: https://z.ai/manage-apikey/billing). Nach Aufladung kurz warten, bis das Guthaben aktiv ist.
- `blocked by network policy: domain …` → fehlende Domain in `mistral-vibe-agent/mistral-vibe-agent.yaml`
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
sbx run ./opencode-v3-agent/ `
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
  denselben Port. Aktuellen Port in der IDE ablesen (**Settings → Tools → MCP Server** → Client-Config „Copy Config")
  und die Registration anpassen (`sbx mcp rm idea`, dann `sbx mcp add idea --url http://localhost:<port>/stream
  --skip-ssrf-check`). Eine Sandbox-Allowlist-Anpassung ist **nicht** nötig (Issue #163). Symptom bei Port-Drift:
  `mcp-idea:FAIL` im Startup-Report/`mcp-check.sh`, Port ist auf dem Host aber belegt (Listener vorhanden).
- **Port ist dynamisch — Neustart von IDEA/Rechner verliert die Verbindung**: JetBrains bestätigt, dass der
  MCP-Server seinen Port **dynamisch wählt** (YouTrack IJPL-248682). Ein Neustart kann also einen neuen Port
  vergeben → nach jedem Neustart Port prüfen und Registration anpassen (s.o.). Dauerlösung steht aus:
  **IJPL-207839** („Configurable MCP Server Port") ist ein offener Feature-Request — **beobachten**.
  Vollständige Analyse + Issue-Referenzen: [`intellij-mcp-port.md`](intellij-mcp-port.md).

> **Wichtig (seit Issue #163):** Die Sandbox erreicht den IntelliJ-MCP **ausschließlich über den Gateway**.
> `host.docker.internal:64615`/`:64342` sind bewusst **nicht** allow-listed (Proxy → HTTP 403), damit kein
> Sandbox-Prozess die `mcp-gateway_*`-Whitelist und den Run-Config-Guard per `curl` umgehen kann. Der frühere
> direkte Health-Check (`intellij-mcp`) ist durch den Gateway-Check (`mcp-idea`) ersetzt.

**Manuelle Verifikation** (sbx CLI auf dem Host; prüft die volle Kette Sandbox → Gateway → IntelliJ):

```bash
sbx exec <sandbox-name> bash -c 'MCP_CHECK_DEEP=1 bash ~/.local/bin/mcp-check.sh'
```

Registration prüfen:

```bash
sbx mcp ls
```

Gateway laden (falls Sandbox ohne `--static-mcp` erzeugt wurde):

```bash
sbx mcp load idea --sandbox <sandbox-name>
```

Erwartet: (1) `mcp-idea:OK` aus `mcp-check.sh`, (2) `sbx mcp ls` zeigt `idea   remote   ✓ ready`.

Falls die Gateway-Verbindung fehlschlägt (Log: `connect to idea: … Method Not Allowed`): prüfen, dass der Endpoint
`/stream` (nicht `/sse`) registriert ist — `sbx mcp inspect idea` muss `URL: http://localhost:64615/stream` zeigen.
Der Gateway verbindet host-seitig über `localhost`; eine Windows-Firewall-Freigabe für Port 64615 ist für die
Sandbox **nicht** mehr nötig (Issue #163).

## Caveats

### Kit-Spec v3 und die sbx-Version

Alle Kits sind **v3-Workloads** (`schemaVersion: "3"`, `kind: workload`, Descriptor + Dockerfile) und
brauchen **sbx v0.45+** (Repo-Pin `v0.51.0`). v3-Kits sind nicht mit v1/v2-Kits kombinierbar
(`--template`/`--kit` entfallen). Validierung über den Kit-Builder:

```bash
sbx kit validate ./opencode-v3-agent
```

```bash
sbx kit validate ./claude-v3-agent
```

```bash
sbx kit validate ./mammouth-agent
```

```bash
sbx kit validate ./mistral-vibe-agent
```

```bash
sbx kit inspect ./opencode-v3-agent --json | jq '.warnings'
```

Erwartet: `[]` bzw. `null`. (Ohne Kit-Builder-Sandbox meldet `sbx kit validate` bei v3-Quellkits
`no kit builder configured` — der Buildx-Kit-Frontend-Build im Publish/e2e ist die Validierung.)

### Mammouth Code wird ausschließlich über das Agent-Kit betrieben

Mammouth Code wird über das **dedizierte Agent-Kit** (`mammouth-agent/`,
`sbx run --skills=off ./mammouth-agent/`) betrieben; das eigene Image `docker.io/domboeckli/sbx-mammouth`
backt Mammouth beim **Image-Build** (gepinnt auf **v1.18.31.2** via `ARG MAMMOUTH_VERSION` +
Symlink; Pin via Renovate).

### Mistral Vibe wird ausschließlich über das Agent-Kit betrieben

Mistral Vibe wird über das **dedizierte Agent-Kit** (`mistral-vibe-agent/`,
`sbx run --skills=off ./mistral-vibe-agent/`) betrieben. Das Kit nutzt ein eigenes, gepinntes Image
(`docker.io/domboeckli/sbx-mistral-vibe:<vibe-version>`), das Vibe beim Image-Build installiert — es gibt keinen
`setup.install`-Schritt für Vibe. Das Image muss vor dem ersten Start publiziert sein
(`build-and-publish-mistral-vibe-image.yml`, `workflow_dispatch`).

### OpenCode-Version im OpenCode-v3-Image

Das OpenCode-v3-Image basiert auf Dockers `docker.io/sbx/shell-docker-image:latest` (ohne Agent) und
installiert die OpenCode-CLI beim Image-Build per npm (`opencode-ai@OPENCODE_VERSION`, bewusst 1.x). Die
Version ist damit über `OPENCODE_VERSION` (Dockerfile + `local-test-kits.py` + Workflows) gepinnt — für ein
Update den Pin anheben und das Image neu bauen (`build-and-publish-opencode-v3-image.yml`), nicht in der
Sandbox `npm install -g` ausführen (das würde beim nächsten Start überschrieben/abweichen).

### Skills landen nicht bei `agent`

Falls Skills in der Sandbox nicht sichtbar sind (`ls ~/.agents/skills/` leer), liegt es meist daran,
dass der `skills add`-Befehl als `root` statt als `agent` lief. Im Kit ist `user: "1000"` gesetzt –
beim Test muss die Sandbox neu erstellt werden (`sbx template rm ...` + `sbx run ...`).
