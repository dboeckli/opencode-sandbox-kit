# Kubernetes-MCP-Server auf dem Windows-Host (PowerShell)

Issue: [#40](https://codeberg.org/dboeckli/opencode-sandbox-kit/issues/40) — Kubernetes-Zugriff
aus der Sandbox **ohne Credentials in der Sandbox**.

**Entscheid:** Der Kubernetes-Zugriff läuft über einen **Host-seitigen MCP-Server**
([`containers/kubernetes-mcp-server`](https://github.com/containers/kubernetes-mcp-server),
Go, aktive Pflege) im **Streamable-HTTP**-Modus. Die Sandbox spricht ausschließlich über den
**sbx MCP-Gateway** mit dem Server; die Host-`kubeconfig` (Client-Zertifikat/-Key) verlässt den
Host-Prozess nie. Read-only wird zentral im MCP-Server erzwungen.

```
Sandbox ── MCP ──▶ sbx MCP-Gateway (Host) ── HTTP :8080/mcp ──▶ kubernetes-mcp-server (Host)
                                                                      │ kubeconfig (Host)
                                                                      ▼
                                                          kube-apiserver (Docker Desktop)
```

> Alle Befehle laufen in **PowerShell auf dem Windows-Host** (nicht in der Sandbox).

## Voraussetzungen

- Docker Desktop mit aktiviertem **Kubernetes**; kubeconfig unter `%USERPROFILE%\.kube\config`.
- `sbx` CLI auf dem Host verfügbar (Sandbox-Kit).
- Der Kubernetes-Context wird aus der Host-kubeconfig gelesen (Docker Desktop nutzt Client-Cert-Auth).

## 1. Server installieren (native Windows-Binary)

```powershell
# Zielverzeichnis
$dir = "$env:USERPROFILE\.local\bin"
New-Item -ItemType Directory -Force -Path $dir | Out-Null

# Aktuelle Release-Version ermitteln (oder fest pinnen, z. B. "v0.0.67")
$ver = (Invoke-RestMethod "https://api.github.com/repos/containers/kubernetes-mcp-server/releases/latest").tag_name

$url = "https://github.com/containers/kubernetes-mcp-server/releases/download/$ver/kubernetes-mcp-server-windows-amd64.exe"
Invoke-WebRequest -Uri $url -OutFile "$dir\kubernetes-mcp-server.exe"

# Herkunfts-Markierung (SmartScreen) entfernen, falls gesetzt
Unblock-File "$dir\kubernetes-mcp-server.exe"

# Version prüfen
& "$dir\kubernetes-mcp-server.exe" --version
```

Optional dauerhaft in den PATH aufnehmen (neue Shells):

```powershell
[Environment]::SetEnvironmentVariable(
  "Path",
  "$dir;" + [Environment]::GetEnvironmentVariable("Path", "User"),
  "User")
```

## 2. Konfiguration anlegen (`config.toml`)

```powershell
$cfgDir = "$env:USERPROFILE\.config\kubernetes-mcp-server"
New-Item -ItemType Directory -Force -Path $cfgDir | Out-Null

# Windows-Pfad mit Forward-Slashes (Go akzeptiert das)
$kubeconfig = (Resolve-Path "$env:USERPROFILE\.kube\config").Path -replace '\\', '/'

$toml = @"
# --- HTTP (Streamable) nur lokal ---
port = "8080"
bind_address = "127.0.0.1"
metrics_port = "9090"          # /healthz für den Health-Check

# --- Sicherheit: nur lesende Tools ---
read_only = true

# --- Toolsets (core = Pods/Events/Resources, config = kubeconfig, helm = Releases) ---
toolsets = ["core", "config", "helm"]

# --- Cluster-Zugriff aus der Host-kubeconfig ---
kubeconfig = "$kubeconfig"
cluster_provider_strategy = "kubeconfig"

# Sensible Ressourcen aussperren (z. B. Secrets)
[[denied_resources]]
group = ""
version = "v1"
kind = "Secret"

log_level = 2
"@

# UTF-8 OHNE BOM schreiben (TOML-Parser mag kein BOM)
[System.IO.File]::WriteAllText("$cfgDir\config.toml", $toml)
Get-Content "$cfgDir\config.toml"
```

## 3. Server starten + Health-Check

```powershell
Start-Process -FilePath "$dir\kubernetes-mcp-server.exe" `
  -ArgumentList "--config", "$cfgDir\config.toml" `
  -WindowStyle Hidden

Start-Sleep -Seconds 2
Invoke-RestMethod "http://127.0.0.1:9090/healthz"   # erwartet 200/OK
```

Stoppen / neu starten (nach Config-Änderungen):

```powershell
Get-Process kubernetes-mcp-server -ErrorAction SilentlyContinue | Stop-Process
```

> Autostart (optional): eine **Aufgabenplanung** (Scheduled Task) „Bei Anmeldung“ anlegen, die
> `kubernetes-mcp-server.exe --config "$env:USERPROFILE\.config\kubernetes-mcp-server\config.toml"`
> ausführt.

## 4. Beim sbx MCP-Gateway registrieren

```powershell
sbx mcp add k8s --url http://localhost:8080/mcp --skip-ssrf-check
sbx mcp ls
```

> `--skip-ssrf-check` ist nötig, weil `localhost` (Loopback) sonst als SSRF-Kandidat gewarnt wird —
> hier ist der Server vertrauenswürdig und läuft lokal.

## 5. In der Sandbox verwenden

Beim Erstellen der Sandbox als statischen MCP-Server mitgeben (neben dem IntelliJ-MCP):

```powershell
sbx run opencode `
    --kit ./opencode-agent/ `
    --template docker.cloudsmith.io/dboeckli/sbx/sbx-opencode-tooling:local `
    --skills=off `
    --static-mcp idea `
    --static-mcp k8s
```

`--static-mcp` akzeptiert auch Kommaseparierung (`--static-mcp idea,k8s`). In eine **laufende**
Sandbox laden: `sbx mcp load k8s --sandbox <name>`.

In der Sandbox erscheinen die Tools als `mcp-gateway_*` (z. B. `mcp-gateway_pods_list`,
`mcp-gateway_resources_get`, `mcp-gateway_helm_list`). Beispiel-Prompts: „Liste alle Pods in
Namespace default“, „Zeig die Logs von Pod X“, „Welche Helm-Releases laufen?“.

> **Read-only:** Durch `read_only = true` sind nur lesende Tools sichtbar
> (`pods_list`, `pods_log`, `resources_get`, `helm_list`, …) — keine `pods_delete`/`helm_install`.
> `Secrets` sind zusätzlich per `denied_resources` ausgesperrt.

## 6. Sandbox-Permission-Whitelist (Follow-up, Kit)

Die Kit-Whitelist ist **deny-by-default**. Die bestehenden Muster (`mcp-gateway_get_*`,
`mcp-gateway_list_*`, `mcp-gateway_read*`, …) decken die K8s-Toolnamen **nicht** ab
(z. B. `mcp-gateway_pods_list`, `mcp-gateway_events_list`). Für die volle Nutzung müssen die
K8s-Read-only-Tools in den Agent-Configs freigegeben werden:

- OpenCode/Mammouth: `permission` in `opencode.jsonc`
- Claude Code: `permissions.allow` in `settings.json`
- Mistral Vibe: `pre_tool`-Guard (`vibe-mcp-guard.py`)

Das ist ein eigener Kit-Schritt (siehe #40).

## Betrieb

| Aktion | Befehl |
|--------|--------|
| Version prüfen | `& "$env:USERPROFILE\.local\bin\kubernetes-mcp-server.exe" --version` |
| Server neu starten | `Get-Process kubernetes-mcp-server \| Stop-Process` (danach neu starten) |
| kubeconfig-Rotation | Docker Desktop rotiert Zertifikate — der Server liest die Datei neu; im Zweifel neu starten |
| Registrierung entfernen | `sbx mcp rm k8s` |

## Sicherheit (Kurz)

- `port` + `bind_address = "127.0.0.1"` → Server nur lokal erreichbar, kein offener Port im LAN.
- `read_only = true` + `disable_destructive`/`denied_resources` → nur lesende, nicht-destruktive Tools.
- kubeconfig/Credentials bleiben **ausschließlich** im Host-Prozess; die Sandbox sieht nur MCP.

## Referenzen (via ctx7 / GitHub)

- Config-Referenz: `containers/kubernetes-mcp-server` → `docs/configuration.md`
- Releases (Windows-Binary): https://github.com/containers/kubernetes-mcp-server/releases
- sbx MCP-Gateway: `npx ctx7 docs /docker/docs "sbx mcp add register MCP server url"`
