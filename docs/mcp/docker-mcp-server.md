# Docker-MCP-Server auf dem Windows-Host (lokal via `uvx`)

Issue: [#165](https://codeberg.org/dboeckli/opencode-sandbox-kit/issues/165) — Host-Docker-Zugriff aus
der Sandbox **ohne offenen `2375`-Port** (siehe [#71](https://codeberg.org/dboeckli/opencode-sandbox-kit/issues/71)).

**Entscheid:** Host-Docker-Zugriff über einen **lokalen Docker-MCP-Server**
([`ckreiling/mcp-server-docker`](https://github.com/ckreiling/mcp-server-docker), Python) — fuer die
Buildx-Abfragen (`docker_buildx_list`/`docker_buildx_history`/`docker_buildx_logs`, Issue #250) der Fork
[`dboeckli/mcp-server-docker`](https://github.com/dboeckli/mcp-server-docker), gestartet aus dem
PyPI-Wheel `mcp-server-docker-dboeckli==0.13.0` (Distribution ≠ Command-Name, Issue #286). Der Server wird
**host-seitig via `uvx`** gestartet und beim **sbx MCP Gateway** registriert (`sbx mcp add --command …`). Die Sandbox spricht ausschließlich MCP; der direkte `2375`-Port entfällt
aus der Netzwerk-Allowlist. Muster wie beim Kubernetes-MCP (Issue #40).

> **Warum nicht das Docker MCP Toolkit?** Verworfen (siehe #165): Der offizielle Katalog hat **keinen**
> Local-Daemon-Manager (nur `dockerhub`/`docker-docs`), und der offizielle `docker`-Passthrough ist
> `type: poci` — die Desktop-CLI lehnt ihn ab (`unsupported server type: poci`).

```text
Sandbox ── MCP ──▶ sbx MCP Gateway (Host) ── stdio ──▶ uvx mcp-server-docker (Host)
                                                              │ Docker-Socket (Host)
                                                              ▼
                                                         docker.sock (Docker Desktop)
```

> [!WARNING]
> **Host-root-äquivalent.** Der Server steuert den Host-Docker-Daemon. Bei Freigabe von Write-Tools
> sind beliebige Operationen möglich (inkl. `container run -v /:/host`). Nur für Dev-Hosts. Die
> `mcp-gateway_*`-Whitelist (read-only `allow`, Write `ask`) ist eine **Agent-Guardrail**, keine
> Netz-/Sandbox-Grenze: Der Gateway ist aus der Sandbox direkt per `curl` erreichbar (Sentinel
> `Bearer proxy-managed`) und führt die Tools aller registrierten Server aus — siehe Issue #229.

> Alle Befehle laufen in **PowerShell auf dem Windows-Host** (nicht in der Sandbox). Den Server
> startet der sbx MCP Gateway als stdio-Prozess — kein manueller Start nötig.

## Voraussetzungen (Host)

- **`uv`/`uvx`** (Astral; bringt eigenes Python mit → Python separat nicht nötig).
- **Docker Desktop** läuft (der Server nutzt den Host-Daemon über `docker.from_env()`).
- **`sbx`** CLI.
- Optional für Variante 2 (containerisiert): ein `mcp-server-docker`-Image.

## 1. `uv` installieren

```powershell
winget install --id=astral-sh.uv -e
# alternativ:
# powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# neue Shell, dann prüfen:
uv --version
uvx --version
```

## 2. Server-Starttest

```powershell
uvx --from "mcp-server-docker-dboeckli==0.13.0" mcp-server-docker
```

Der erste Start lädt das Wheel von PyPI (kein Git-Clone/venv-Build); danach startet der
**stdio-MCP-Server** (keine Ausgabe, wartet auf JSON-RPC). Mit `Ctrl+C` beenden — dabei kann ein `KeyboardInterrupt`/`CancelledError`-Traceback
erscheinen. Das ist **normal** (der Server blockiert auf stdin; die Unterbrechung wird nicht
abgefangen) und kein Fehler.

> **PyPI-Pin (`mcp-server-docker-dboeckli==0.13.0`):** Der Server startet aus dem veröffentlichten Wheel
> (kein Git-Clone/venv-Build mehr; Issue #286). Wichtig: **Distribution ≠ Command** — PyPI
> `mcp-server-docker` gehört zum Upstream und endet bei `0.3.0`; ein bloßes `uvx mcp-server-docker`
> liefert daher die alte Upstream-Version **ohne** `buildx_*`. Deshalb immer
> `--from mcp-server-docker-dboeckli==<v>`. Gepinnt per `==<v>` (ohne `v`-Präfix); Renovate
> (`.github/renovate.json`, PyPI-Datasource) und der Validate-Check (`local-test-kits.py`) prüfen den
> Pin gegen die latest PyPI-Version.
>
> **Versionsdetails:** Changelog/Release-Notes im Upstream-Repo und die **MCP-Registry** (Abschnitt
> unten, `/versions/latest`) sind die Quelle — hier stehen nur die kit-relevanten Änderungen:
>
> - **0.8.0** — alle Tools mit `docker_`-Präfix (behebt die Gateway-Kollision `events_list` mit K8s; Whitelist-Namen).
> - **0.9.0** — Listen-Tools default `format="summary"` (`format="full"` für die Inspect-Daten).
> - **0.11.0** — startet auch ohne erreichbaren Docker-Daemon (`tools/list` ok, Tool-Calls melden den Fehler).
> - **0.12.0** — optionale Safety-Modes (`--disable-destructive`/`--read-only`, per-Tool-Filter); das Kit
>   nutzt sie bewusst **nicht** — die Write-Tools bleiben über die Gateway-`ask`-Regeln einzeln freigebbar.
> - **0.13.0** — neues Read-only-Health-Tool `docker_status` (Daemon-Probe mit 2 s Timeout, strukturierte
>   Antwort `status: ok|degraded` inkl. Server-/Docker-Version, Latenz und redigierten Fehlern statt Exception;
>   bleibt unter `--read-only` verfügbar).

## MCP-Registry-Eintrag (`registry.modelcontextprotocol.io`)

Der Server ist zusätzlich in der **offiziellen MCP-Registry** veröffentlicht. Das ist reine
Metadaten-/Discovery-Information: Die Host-Installation bleibt unverändert beim PyPI-Wheel
(`uvx --from mcp-server-docker-dboeckli==<pin>`), der Kit-Pin wird separat gepflegt (Renovate/
Validate-Check).

- **Name:** `io.github.dboeckli/mcp-server-docker` (Titel „Docker MCP Server“,
  Repository `https://github.com/dboeckli/mcp-server-docker`)
- **Pakete:** PyPI `mcp-server-docker-dboeckli` (stdio) und OCI
  `ghcr.io/dboeckli/mcp-server-docker:<version>` (stdio)
- **Version:** nicht hier gepinnt — die jeweils aktuelle Version liefert `/versions/latest`
  (`_meta.…status=active`, `isLatest: true`). Source of Truth für die Host-Installation bleibt der
  Kit-Pin (PyPI-Wheel).
- **Publish:** seit 0.12.0 automatisch aus dem Release-Workflow (`registry-publish.yml`,
  `workflow_run`-Gate nach erfolgreichen Tag-Builds) — kein manuelles `mcp-publisher` mehr. Der Eintrag
  trägt dieselbe Version wie PyPI/OCI (aktuell `0.13.0`; OCI ab 0.12.1 auch `linux/arm64`).

> **Sandbox-Zugriff:** `registry.modelcontextprotocol.io` steht in der Netzwerk-Allowlist aller
> Agent-Kits (Issue #340) — die Abfrage funktioniert direkt aus der Sandbox (dort `curl`, nicht
> PowerShell):

```bash
curl -s "https://registry.modelcontextprotocol.io/v0.1/servers/io.github.dboeckli%2Fmcp-server-docker/versions/latest" \
  | jq '{name: .server.name, version: .server.version, packages: [.server.packages[].identifier], status: ._meta["io.modelcontextprotocol.registry/official"].status, latest: ._meta["io.modelcontextprotocol.registry/official"].isLatest}'
```

API (Basis `https://registry.modelcontextprotocol.io/v0.1`; der Server-Name ist URL-encodiert als
`io.github.dboeckli%2Fmcp-server-docker`):

| Zweck | Endpoint |
|-------|----------|
| Neueste Version | `GET /servers/io.github.dboeckli%2Fmcp-server-docker/versions/latest` |
| Bestimmte Version | `GET /servers/io.github.dboeckli%2Fmcp-server-docker/versions/<version>` |

```powershell
# Version + Pakete (PyPI/OCI) des Registry-Eintrags abfragen
(Invoke-RestMethod "https://registry.modelcontextprotocol.io/v0.1/servers/io.github.dboeckli%2Fmcp-server-docker/versions/latest").server |
    Select-Object name, version, @{ n = "packages"; e = { $_.packages.identifier } }
```

> Die OCI-Variante (`ghcr.io/dboeckli/mcp-server-docker:<version>`) ist eine Alternative zur
> containerisierten Registrierung (Variante 2 unten), **nicht** der Kit-Default — der sbx MCP
> Gateway startet den Server host-seitig als stdio-Prozess aus dem PyPI-Wheel.

## 3. Beim sbx MCP Gateway registrieren

`--command` + `--args` registrieren den Server als **host-lokalen stdio-Server**; sbx startet den Prozess
selbst. **Wichtig:** `--command` läuft im Kontext des sbx-Host-Daemons — dieser erbt **nicht** den
Terminal-PATH, in dem `uvx` ggf. nur über einen winget-Shim auflösbar ist. Deshalb den **absoluten Pfad**
verwenden (genau wie beim K8s-MCP).

Absoluten `uvx`-Pfad ermitteln:

```powershell
(Get-Command uvx).Source
```

Server registrieren:

```powershell
sbx mcp add docker --command (Get-Command uvx).Source --args "--from,mcp-server-docker-dboeckli==0.13.0,mcp-server-docker"
```

Registrierung prüfen:

```powershell
sbx mcp ls
```

Details anzeigen:

```powershell
sbx mcp inspect docker
```

> Ohne absoluten Pfad registriert `sbx mcp add docker --command "uvx" …` zwar erfolgreich (`sbx mcp ls`
> = `ready`), aber der Gateway-Prozess findet `uvx` nicht und startet den Server nicht → in der Sandbox
> `mcp-docker:FAIL` (siehe Troubleshooting).

Alternativ ohne `uvx`-Shim:

```powershell
sbx mcp add docker --command (Get-Command uv).Source --args "tool,run,--from,mcp-server-docker-dboeckli==0.13.0,mcp-server-docker"
```

### Bestehende Registrierung umstellen

Gilt z. B. beim Wechsel vom Git-Tag auf das PyPI-Wheel (oder von der alten Upstream-Distribution
`mcp-server-docker==0.3.0`). Erst die alte Registrierung entfernen:

```powershell
sbx mcp rm docker
```

Dann den Fork registrieren:

```powershell
sbx mcp add docker --command (Get-Command uvx).Source --args "--from,mcp-server-docker-dboeckli==0.13.0,mcp-server-docker"
```

Laufende Sandbox nachladen (die `--static-mcp`-Menge ist beim Erstellen fixiert) bzw. neu erstellen:

```powershell
sbx mcp load docker --sandbox <name>
```

### Tool-Aktivierung (Server-seitig, ab 0.12.0)

Der Server registriert standardmäßig alle **37** Tools; seit 0.12.0 lässt sich das schon bei der
Registrierung einschränken. Ein gefiltertes Tool fehlt in `tools/list` und ein Aufruf liefert
`Unknown tool`:

| Modus | Flag | Tools |
|-------|------|-------|
| Default | – | 37 |
| Keine destruktiven | `--disable-destructive` (Alias `--no-destructive`) | 32 — ohne `docker_remove_container`, `docker_remove_image`, `docker_remove_network`, `docker_remove_volume`, `docker_recreate_container` |
| Read-only | `--read-only` | 23 — nur Tools mit `readOnlyHint=true` (inkl. `docker_status`) |

- `--read-only` ist strenger und gewinnt, wenn beide Flags gesetzt sind.
- Pro Tool: `--enable-tools <name>` (übersteuert den Modus, wiederholbar) und `--disable-tools <name>`;
  derselbe Name in beiden Listen bricht den Start mit Fehlermeldung ab.
- Env-Pendants (z. B. für die containerisierte Variante): `MCP_SERVER_DOCKER_READ_ONLY`,
  `MCP_SERVER_DOCKER_DISABLE_DESTRUCTIVE` (bzw. `…_NO_DESTRUCTIVE`), `MCP_SERVER_DOCKER_ENABLE_TOOLS`,
  `MCP_SERVER_DOCKER_DISABLE_TOOLS`.
- Die Flags kommen in dieselbe `--args`-Liste wie `--from`/`mcp-server-docker`. Mehrere Tool-Namen als
  **wiederholtes Flag** angeben — Kommas trennen die Prozess-Argumente, nicht die Tool-Liste:

```powershell
# read-only (23 Tools)
sbx mcp add docker --command (Get-Command uvx).Source --args "--from,mcp-server-docker-dboeckli==0.13.0,mcp-server-docker,--read-only"

# ohne destruktive Tools (32), zusätzlich docker_stop_container gesperrt
sbx mcp add docker --command (Get-Command uvx).Source --args "--from,mcp-server-docker-dboeckli==0.13.0,mcp-server-docker,--disable-destructive,--disable-tools,docker_stop_container"
```

> **Kit-Default bleibt „alle 37“ + Gateway-Whitelist.** Die Write-Tools bleiben so über die `ask`-Regeln
> einzeln freigebbar. Der Server-Filter ist eine **harte** Grenze (Tool existiert nicht), die
> Gateway-Whitelist nur eine Agent-Guardrail (Issue #229); beides ist kombinierbar. `--read-only` im
> Server nimmt dem Agenten allerdings die `ask`-Freigabe für Write-Tools komplett.

## 4. Sandbox mit Docker-MCP starten

```powershell
sbx run ./opencode-v3-agent/ `
    --skills=off `
    --static-mcp idea,k8s,docker `
    . `
    "C:\development\maven-repo:ro"
```

`--static-mcp` ist eine kommaseparierte Liste; das Set wird beim **Erstellen** der Sandbox fixiert. In eine
**laufende** Sandbox nachladen: `sbx mcp load docker --sandbox <name>`.

## 5. Permission-Whitelist (Kit)

Die Tools des Servers erscheinen (wie bei K8s) als `mcp-gateway_<tool>`. Gating (Deny-by-Default,
letzte passende Regel gewinnt) — die Listen gelten für den Default (37 Tools); ein Server-Filter
(Abschnitt 3, Tool-Aktivierung) kann das Set vorher verkleinern:

- **`allow`** (read-only): `docker_list_containers`, `docker_list_images`, `docker_list_networks`,
  `docker_list_volumes`, `docker_fetch_container_logs`, `docker_buildx_list`, `docker_buildx_history`,
  `docker_buildx_logs`, `docker_buildx_du`, `docker_buildx_inspect`, `docker_system_df`, `docker_system_info`,
  `docker_version`, `docker_status`, `docker_image_inspect`, `docker_image_history`, `docker_container_inspect`,
  `docker_container_processes`, `docker_container_stats`, `docker_container_health`, `docker_network_inspect`,
  `docker_volume_inspect`, `docker_events_list`.
- **`ask`** (schreibend): `docker_create_container`, `docker_run_container`, `docker_recreate_container`,
  `docker_start_container`, `docker_stop_container`, `docker_remove_container`, `docker_pull_image`,
  `docker_push_image`, `docker_build_image`, `docker_remove_image`, `docker_create_network`,
  `docker_remove_network`, `docker_create_volume`, `docker_remove_volume`.

> **Namenskollision `events_list` (gelöst in 0.8.0):** Der Kubernetes-MCP-Server bietet ebenfalls ein
> `events_list`. Der Gateway-Namespace ist flach und **global eindeutig**: bei einem Duplikat lehnt der
> Gateway den **gesamten** Server ab (`502 … tool "events_list" … collides with an existing tool
> already registered for server "k8s"`), er führt die Namen nicht zusammen. Deshalb präfixt
> mcp-server-docker seit 0.8.0 alle Tools mit `docker_`; `docker_events_list` ist eine eigene Allow-Regel
> (`mcp-gateway_docker_events_list`), getrennt von `mcp-gateway_events_list` (K8s).

> **`docker_container_stats` ist Tool *und* Resource (Issue #264):** Seit Fork-Release 0.6.1 bietet der
> Server den Container-Stats-Snapshot zusätzlich als Tool an (`docker_container_stats(container_id)`,
> One-Shot-Snapshot); die Resource `docker://containers/{container_id}/stats` bleibt daneben bestehen.
> Deshalb steht `docker_container_stats` zu Recht in der `allow`-Liste oben.

## Variante 2 — containerisiert (optional)

Statt `uvx` den Server als Container starten (Host-Docker via Socket-Mount):

```powershell
# im geklonten Repo:
docker build -t mcp-server-docker .
sbx mcp add docker --command (Get-Command docker).Source --args "run,-i,--rm,-v,/var/run/docker.sock:/var/run/docker.sock,mcp-server-docker"
```

> Auch hier den **absoluten `docker`-Pfad** verwenden (`(Get-Command docker).Source`) — der Gateway-Daemon
> erbt nicht den Terminal-PATH.

## Troubleshooting

| Symptom | Ursache / Fix |
|---------|---------------|
| `mcp-docker:FAIL` in der Sandbox (Startup-Check/Sidebar), aber `mcp-k8s:OK` | Der Gateway-Prozess findet `uvx` nicht (Daemon-PATH ≠ Terminal-PATH). **Fix:** mit absolutem Pfad neu registrieren (`sbx mcp rm docker`, dann `sbx mcp add docker --command (Get-Command uvx).Source --args "--from,mcp-server-docker-dboeckli==0.13.0,mcp-server-docker"`), danach `sbx mcp load docker --sandbox <name>` bzw. Sandbox neu erstellen. |
| `mcp-docker:FAIL` mit Diagnostic `"status":"degraded"` (stderr) | Der MCP-Server läuft, aber der **Host-Docker-Daemon** ist nicht erreichbar (z. B. Docker Desktop gestoppt). Seit 0.13.0 prüft der Startup-Check das über das Read-only-Tool `docker_status` (Status `ok`/`degraded`, 2 s Timeout). Docker Desktop starten, Check erneut ausführen. |
| `sbx mcp load docker` scheitert mit `502 … tool "events_list" … collides with an existing tool already registered for server "k8s"` | Auf dem Host läuft noch **0.7.0** mit unpräfixierten Tool-Namen. **Fix:** auf den Pin neu registrieren (`sbx mcp rm docker` + `add …==<pin>`, siehe oben) und `sbx mcp load docker --sandbox <name>`; erst danach `mcp-docker:OK` erwarten. |
| `sbx mcp add` ok, aber keine Docker-Tools im `tools/list` | Server ist nicht Teil der `--static-mcp`-Menge der Sandbox (Set ist beim Erstellen fixiert) → `sbx mcp load docker --sandbox <name>` oder neu erstellen. |
| Erster Check kurz `FAIL`, danach `OK` | `uvx` lädt das PyPI-Wheel beim ersten Start → kurzer Start-Timeout (Gateway-Startprobe); erneut prüfen. |
| Tool-Fehler „Cannot connect to the Docker daemon" | Docker Desktop läuft nicht oder der Benutzer ist nicht in `docker-users` (Host-Docker-Socket nötig). |

## Betrieb

| Aktion | Befehl |
|--------|--------|
| Update (neue Version) | Renovate-PR für `docs/mcp/docker-mcp-server.md` (`mcp-server-docker-dboeckli==<v>`) mergen, dann auf dem Host neu registrieren: `sbx mcp rm docker` + `sbx mcp add docker --command (Get-Command uvx).Source --args "--from,mcp-server-docker-dboeckli==<neu>,mcp-server-docker"`; laufende Sandbox: `sbx mcp load docker --sandbox <name>` |
| Status prüfen | `sbx mcp ls` (Status `ready`), `sbx mcp inspect docker` (Command/Args) |
| In Sandbox prüfen | `sbx exec <name> bash -lc 'bash ~/.local/bin/mcp-check.sh'` → `mcp-docker:OK` (seit 0.13.0 inkl. `docker_status`-Health-Probe: `OK` nur bei erreichbarem Host-Daemon; ältere Host-Registrierungen fallen auf Tool-Presence zurück) |
| Nachladen in laufende Sandbox | `sbx mcp load docker --sandbox <name>` |
| Registrierung entfernen | `sbx mcp rm docker` |

## Verifikation

- **Host:** `sbx mcp ls` zeigt `docker`; `sbx mcp inspect docker` zeigt Command/Args (absoluter `uvx`-Pfad + `mcp-server-docker-dboeckli==0.13.0`).
- **Sandbox:** MCP-Handshake `tools/list` enthält die Docker-Tools (`docker_list_containers`, …); ein
  Read-Tool (`docker_list_containers`) läuft ohne Prompt, ein Write-Tool (`docker_run_container`) löst den
  `ask`-Prompt aus. Der Startup-Check (`mcp-check.sh`) ruft seit 0.13.0 `docker_status` auf: `mcp-docker:OK`
  bedeutet dann **auch**, dass der Host-Daemon erreichbar ist (`status: ok`); `degraded` → `mcp-docker:FAIL`
  mit Diagnostic auf stderr.
- **Nach Phase 2:** `host.docker.internal:2375` (+ `localhost`/`127.0.0.1`) aus allen `spec.yaml` +
  `network-policy.md` entfernt; der `docker-host`-Check (`run-checks.sh` 5b) ersetzt/entfernt.

## Sicherheit (Kurz)

- Kein offener Host-Port mehr in der Sandbox-Allowlist (statt `2375`).
- Der MCP-Server + Docker-Socket bleiben host-seitig; die Sandbox sieht nur MCP-Tools.
- Begrenzung = **Agent-Guardrail** (`mcp-gateway_*`-Whitelist, read-only `allow`, Write `ask`), **keine**
  Netz-/Sandbox-Grenze: Der Gateway ist aus der Sandbox per `curl` erreichbar (Issue #229).
- Details + lokale Mitigationen: [mcp-gateway-security.md](mcp-gateway-security.md).

## Verwandt

- #165 (Ticket), #71 (`2375` aus der Allowlist), #40 (K8s-MCP-Muster), #160 (Allowlist zentral pflegen),
  #163 (IntelliJ-MCP-Direkt-Bypass), #229 (Gateway-Bypass + Mitigationen).
