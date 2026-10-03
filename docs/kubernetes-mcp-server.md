# Kubernetes-MCP-Server auf dem Windows-Host (PowerShell)

Issue: [#40](https://codeberg.org/dboeckli/opencode-sandbox-kit/issues/40) — Kubernetes-Zugriff
aus der Sandbox **ohne Credentials in der Sandbox**.

**Entscheid:** Der Kubernetes-Zugriff läuft über einen **Host-seitigen MCP-Server**
([`containers/kubernetes-mcp-server`](https://github.com/containers/kubernetes-mcp-server),
Go, aktive Pflege) im **stdio-Modus**, den der **sbx MCP-Gateway** auf dem Host startet
(`sbx mcp add --command`). Die Sandbox spricht ausschließlich MCP mit dem Gateway; die
Host-`kubeconfig` (Client-Zertifikat/-Key) verlässt den Host-Prozess nie. Read-only wird zentral
im MCP-Server erzwungen.

```
Sandbox ── MCP ──▶ sbx MCP-Gateway (Host) ── stdio ──▶ kubernetes-mcp-server (Host, sbx-gestartet)
                                                              │ kubeconfig (Host)
                                                              ▼
                                                      kube-apiserver (Docker Desktop)
```

> Alle Befehle laufen in **PowerShell auf dem Windows-Host** (nicht in der Sandbox).
> Es gibt **keinen** offenen Port und **keinen** manuellen Start — sbx startet/stoppt den
> stdio-Prozess selbst.

> [!WARNING]
> **Betrieb gegen Produktions-Cluster ist ein No-Go.** Die Standard-Config verzichtet auf
> `denied_resources` für `Secret` — sonst funktioniert das `helm`-Toolset nicht (Helm v3 legt
> Releases als Secrets ab). Dadurch können die generischen Tools (`resources_get`/`resources_list`)
> **Kubernetes-Secrets vollständig lesen** (`.`-`data`, base64). Für Produktion entweder diesen
> MCP-Server nicht einsetzen oder das unten dokumentierte `denied_resources`-Block aktivieren
> (dann fallen `helm_list`/`helm_get`/`helm_status` weg). Details: Abschnitt **Sicherheit**.

## Voraussetzungen

- Docker Desktop mit aktiviertem **Kubernetes**; kubeconfig unter `%USERPROFILE%\.kube\config`.
- `sbx` CLI auf dem Host verfügbar (Sandbox-Kit).
- Der Kubernetes-Context wird aus der Host-kubeconfig gelesen (Docker Desktop nutzt Client-Cert-Auth).

## 1. Server installieren (native Windows-Binary)

Empfohlen über das Host-Skript im Repo (idempotent, erkennt die Architektur, prüft die Version):

```powershell
# aus dem Repo-Root
.\local-scripts\install-kubernetes-mcp-server.ps1                    # gepinnte Version (Renovate-tracked; PATH wird gesetzt)
# oder explizit:
.\local-scripts\install-kubernetes-mcp-server.ps1 -Version v0.0.67
# immer die aktuelle Release-Version:
.\local-scripts\install-kubernetes-mcp-server.ps1 -Version latest
# ohne PATH-Eintrag:
.\local-scripts\install-kubernetes-mcp-server.ps1 -AddToPath:$false
```

<details><summary>Manuell (ohne Skript)</summary>

```powershell
$dir = "$env:USERPROFILE\.local\bin"
New-Item -ItemType Directory -Force -Path $dir | Out-Null

# Aktuelle Release-Version ermitteln (oder fest pinnen, z. B. "v0.0.67")
$ver = (Invoke-RestMethod "https://api.github.com/repos/containers/kubernetes-mcp-server/releases/latest").tag_name

$url = "https://github.com/containers/kubernetes-mcp-server/releases/download/$ver/kubernetes-mcp-server-windows-amd64.exe"
Invoke-WebRequest -Uri $url -OutFile "$dir\kubernetes-mcp-server.exe"
Unblock-File "$dir\kubernetes-mcp-server.exe"
& "$dir\kubernetes-mcp-server.exe" --version
```

Optional dauerhaft in den PATH (neue Shells):

```powershell
[Environment]::SetEnvironmentVariable(
  "Path",
  "$dir;" + [Environment]::GetEnvironmentVariable("Path", "User"),
  "User")
```

</details>

## 2. Konfiguration anlegen (`config.toml`, stdio)

Empfohlen über das Host-Skript (schreibt die TOML UTF-8 ohne BOM; **scheitert, wenn keine Installation vorhanden ist**):

```powershell
.\local-scripts\configure-kubernetes-mcp-server.ps1
# Optionen: -ReadOnly:$false -Toolsets core,config,helm -Force
```

<details><summary>Manuell (ohne Skript)</summary>

```powershell
$cfgDir = "$env:USERPROFILE\.config\kubernetes-mcp-server"
New-Item -ItemType Directory -Force -Path $cfgDir | Out-Null

# Windows-Pfad mit Forward-Slashes (Go akzeptiert das)
$kubeconfig = (Resolve-Path "$env:USERPROFILE\.kube\config").Path -replace '\\', '/'

$toml = @"
# --- Sicherheit: nur lesende Tools ---
read_only = true

# --- Toolsets (core = Pods/Events/Resources, config = kubeconfig, helm = Releases) ---
toolsets = ["core", "config", "helm"]

# --- Cluster-Zugriff aus der Host-kubeconfig ---
kubeconfig = "$kubeconfig"
cluster_provider_strategy = "kubeconfig"

# --- Logging: stdout ist im stdio-Modus für das MCP-Protokoll reserviert ---
log_file = "stderr"
log_level = 2

# ============================================================================
# WARNING - DEVELOPMENT / NON-PRODUCTION ONLY
# No `denied_resources` entry: the generic tools (resources_get/resources_list)
# can read Kubernetes Secrets IN FULL (base64 .data). Required by the helm
# toolset, because Helm v3 stores releases as Secrets.
# NEVER point this configuration at a production cluster.
# For production, re-enable the block below (helm tools stop working):
# ============================================================================
# [[denied_resources]]
# group = ""
# version = "v1"
# kind = "Secret"
"@

# UTF-8 OHNE BOM schreiben (TOML-Parser mag kein BOM)
[System.IO.File]::WriteAllText("$cfgDir\config.toml", $toml)
Get-Content "$cfgDir\config.toml"
```

> **Wichtig:** Im stdio-Modus **kein** `port`/`bind_address`/`metrics_port` setzen — sonst läuft
> der Server als HTTP und spricht kein stdio.

</details>

## 3. Beim sbx MCP-Gateway registrieren (startet den Server)

`--command` + `--args` registrieren den Server als **host-lokalen stdio-Server**; sbx startet den
Prozess selbst und proxied ihn in die Sandbox.

```powershell
sbx mcp add k8s `
  --command "$env:USERPROFILE\.local\bin\kubernetes-mcp-server.exe" `
  --args "--config,$env:USERPROFILE\.config\kubernetes-mcp-server\config.toml"

sbx mcp ls
```

> `--args` ist eine **kommaseparierte** Liste (hier: `--config` + Pfad). `$env:USERPROFILE` löst
> PowerShell automatisch zum Benutzerprofil auf — kein `<user>`-Platzhalter nötig. Das
> Configure-Skript gibt den fertigen Befehl (mit aufgelöstem Pfad) am Ende aus.

## 4. In der Sandbox verwenden

Beim Erstellen der Sandbox als statischen MCP-Server mitgeben (neben dem IntelliJ-MCP):

```powershell
sbx run opencode `
    --kit ./opencode-agent/ `
    --template docker.cloudsmith.io/dboeckli/sbx/sbx-opencode-tooling:local `
    --skills=off `
    --static-mcp idea,k8s
```

`--static-mcp` nimmt eine **kommaseparierte Liste** (`idea,k8s`); alternativ wiederholt
(`--static-mcp idea --static-mcp k8s`) oder gemischt — alle Formen akkumulieren. In eine
**laufende** Sandbox laden: `sbx mcp load k8s --sandbox <name>`.

Vollständiges Startbeispiel mit Host-Maven-Cache (Issue #87) — der `.kube:ro`-Mount entfällt,
der MCP-Server liest die Host-kubeconfig:

```powershell
sbx run opencode `
    --kit ./opencode-agent/ `
    --template docker.cloudsmith.io/dboeckli/sbx/sbx-opencode-tooling:local `
    --skills=off `
    --static-mcp idea,k8s `
    . `
    "C:\development\maven-repo:ro"
```

In der Sandbox erscheinen die Tools als `mcp-gateway_*` (z. B. `mcp-gateway_pods_list`,
`mcp-gateway_resources_get`, `mcp-gateway_helm_list`). Beispiel-Prompts: „Liste alle Pods in
Namespace default", „Zeig die Logs von Pod X", „Welche Helm-Releases laufen?".

> **Health-Check:** `~/.local/bin/mcp-check.sh` macht einen MCP-Handshake gegen den sbx-Gateway
> (`initialize` → `notifications/initialized` → `tools/list`) und meldet `mcp-gateway:OK`
> (Gateway erreichbar), `mcp-idea:OK` (IntelliJ-Tools vorhanden) und `mcp-k8s:OK`
> (Read-only-k8s-Tools vorhanden, erkannt an `pods_list`). Er läuft im Startup-Check
> (`run-checks.sh`) und im TUI-Sidebar-Block „MCP & Host Systems" (`check-infra.sh`, alle 10s),
> zusammen mit `docker-host` (externes Host-System). Er ersetzt den früheren
> `kubectl get nodes`-Check, der ohne kubeconfig in der Sandbox nicht mehr funktioniert.

> **Read-only:** Durch `read_only = true` sind nur lesende Tools sichtbar
> (`pods_list`, `pods_log`, `resources_get`, `helm_list`, …) — keine `pods_delete`/`helm_install`.
>
> [!WARNING]
> **Secrets sind NICHT ausgesperrt.** Das ist für `helm_list`/`helm_get`/`helm_status` nötig
> (Helm v3 legt Releases als Secrets ab: `sh.helm.release.v1.*`), bedeutet aber, dass
> `resources_get` mit `kind=Secret` **jedes Secret inkl. `.data` (base64) lesen** kann.
> **Gegen Produktions-Cluster ein No-Go** — erst recht, weil die Sandbox keine Credentials
> halten soll und der Agent die Werte in seinen Kontext aufnimmt. Für Produktion das
> `denied_resources`-Block in der Config aktivieren und auf das `helm`-Toolset verzichten.

## 5. Sandbox-Permission-Whitelist (Kit)

Die Kit-Whitelist ist **deny-by-default**. Die bestehenden Muster (`mcp-gateway_get_*`,
`mcp-gateway_list_*`, `mcp-gateway_read*`, …) decken die K8s-Toolnamen **nicht** ab (die Tools
enden auf `_list`/`_get`/`_log`/`_top`). Die **K8s-Read-only-Tools** sind daher explizit
freigegeben (in allen vier Agent-Configs):

- OpenCode/Mammouth: `permission` in `opencode.jsonc`
- Claude Code: `permissions.allow` in `settings.json` (+ `settings.kit.json`)
- Mistral Vibe: `pre_tool`-Guard (`vibe-mcp-guard.py`)

Freigegeben (nur lesend, aus den Toolsets `core`/`helm`): `events_list`, `helm_list`,
`namespaces_list`, `nodes_log`, `nodes_stats_summary`, `nodes_top`, `pods_get`, `pods_list`,
`pods_list_in_namespace`, `pods_log`, `pods_top`, `projects_list`, `resources_get`,
`resources_list`.

> Die Whitelist regelt nur, **welche Tools** der Sandbox-Agent aufrufen darf — sie sagt nichts
> über die gelesenen Ressourcen. `resources_get`/`resources_list` sind Teil der Whitelist und
> können daher (da `Secret` serverseitig nicht mehr denied ist) Secrets lesen. Siehe Warning oben.

> **`configuration_view` bewusst gesperrt:** Das `config`-Toolset liefert die Host-kubeconfig
> inkl. Client-Zertifikat/-Key als YAML in die Sandbox und würde das Sicherheitsziel von #40
> (keine Credentials in der Sandbox) unterlaufen.

## Betrieb

| Aktion | Befehl |
|--------|--------|
| Update (neue Version) | Renovate PR für den `-Version`-Pin in `local-scripts/install-kubernetes-mcp-server.ps1` mergen. Dann laufende Sandboxes/den sbx-gestarteten Prozess beenden (Windows sperrt die `.exe`) und `.\local-scripts\install-kubernetes-mcp-server.ps1` ausführen (installiert die gepinnte Version). Ad-hoc: `-Version latest` |
| Version prüfen | `& "$env:USERPROFILE\.local\bin\kubernetes-mcp-server.exe" --version` |
| Config ändern | `.\local-scripts\configure-kubernetes-mcp-server.ps1 -Force`, dann Sandbox neu starten (sbx startet den Prozess neu) |
| Laufenden Prozess stoppen | `Get-Process kubernetes-mcp-server -ErrorAction SilentlyContinue \| Stop-Process` |
| kubeconfig-Rotation | Docker Desktop rotiert Zertifikate → Prozess neu starten (Sandbox neu erstellen oder `sbx mcp load k8s --sandbox <name>`) |
| Registrierung entfernen | `sbx mcp rm k8s` |

## Sicherheit (Kurz)

- **stdio, kein Listen-Port** → der Server ist von außen nicht erreichbar; nur der sbx-Gateway spricht mit ihm.
- `read_only = true` → nur lesende Tools, keine `pods_delete`/`helm_install`/`resources_delete`.
- kubeconfig/Credentials bleiben **ausschließlich** im Host-Prozess; die Sandbox sieht nur MCP.
  `configuration_view` ist in der Kit-Whitelist gesperrt (würde die kubeconfig inkl. Client-Cert/Key liefern).

> [!CAUTION]
> **Produktions-No-Go (Option A, Standard-Config):** `denied_resources` für `Secret` ist **deaktiviert**,
> weil das `helm`-Toolset sonst nicht funktioniert (Helm v3 = Releases als Secrets). Damit kann der
> Sandbox-Agent über `resources_get`/`resources_list` **alle Cluster-Secrets inkl. `.data` lesen**
> (z. B. Helm-Release-Values, DB-/LDAP-/Kafka-/Registry-Passwörter). Für Produktions-Cluster ist dieser
> Betrieb nicht zulässig — dort entweder den MCP-Server weglassen oder `denied_resources` aktivieren
> (Helm-Tools entfallen dann).

## Referenzen (via ctx7 / GitHub)

- Config-Referenz: `containers/kubernetes-mcp-server` → `docs/configuration.md`
- Releases (Windows-Binary): https://github.com/containers/kubernetes-mcp-server/releases
- sbx MCP-Gateway: `npx ctx7 docs /docker/docs "sbx mcp add register MCP server url"`
