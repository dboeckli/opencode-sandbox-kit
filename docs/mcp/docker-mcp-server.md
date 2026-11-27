# Docker-MCP-Server auf dem Windows-Host (lokal via `uvx`)

Issue: [#165](https://codeberg.org/dboeckli/opencode-sandbox-kit/issues/165) — Host-Docker-Zugriff aus
der Sandbox **ohne offenen `2375`-Port** (siehe [#71](https://codeberg.org/dboeckli/opencode-sandbox-kit/issues/71)).

**Entscheid:** Host-Docker-Zugriff über einen **lokalen Docker-MCP-Server**
([`ckreiling/mcp-server-docker`](https://github.com/ckreiling/mcp-server-docker), Python) — fuer die
Buildx-Abfragen (`docker_buildx_list`/`docker_buildx_history`/`docker_buildx_logs`, Issue #250) der Fork
[`dboeckli/mcp-server-docker`](https://github.com/dboeckli/mcp-server-docker), gestartet aus dem
PyPI-Wheel `mcp-server-docker-dboeckli==0.12.1` (Distribution ≠ Command-Name, Issue #286). Der Server wird
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
uvx --from "mcp-server-docker-dboeckli==0.12.1" mcp-server-docker
```

Der erste Start lädt das Wheel von PyPI (kein Git-Clone/venv-Build); danach startet der
**stdio-MCP-Server** (keine Ausgabe, wartet auf JSON-RPC). Mit `Ctrl+C` beenden — dabei kann ein `KeyboardInterrupt`/`CancelledError`-Traceback
erscheinen. Das ist **normal** (der Server blockiert auf stdin; die Unterbrechung wird nicht
abgefangen) und kein Fehler.

> **PyPI-Pin (`mcp-server-docker-dboeckli==0.12.1`):** Der Server startet aus dem veröffentlichten Wheel
> (kein Git-Clone/venv-Build mehr; Issue #286). Wichtig: **Distribution ≠ Command** — PyPI
> `mcp-server-docker` gehört zum Upstream und endet bei `0.3.0`; ein bloßes `uvx mcp-server-docker`
> liefert daher die alte Upstream-Version **ohne** `buildx_*`. Deshalb immer
> `--from mcp-server-docker-dboeckli==<v>`.
>
> **0.10.0 — `docker_recreate_container` mit `preserve_configuration`:** Mit
> `preserve_configuration=true` wird der Container aus seiner inspizierten Konfiguration neu gebaut
> (Environment, Mounts/Volume-Identität, Netzwerke, Ports, Labels, Healthcheck, Restart-Policy); das
> Ersatz-Image wird **vor** dem Stop geprüft, bei Fehlschlag wird die Original-Konfiguration
> wiederhergestellt und der vorherige Running-State beibehalten. Default (Stop/Remove/Run) unverändert.
>
> **Breaking in 0.9.0 — Listen-Tools default `format="summary"`:** `docker_list_containers`,
> `docker_list_images` und `docker_list_volumes` liefern standardmäßig eine kompakte `docker ps`-Zeile
> **ohne** Health-Logs, verschachteltes Image-Objekt, Labels und Digests. Für die bisherigen
> Inspect-Daten `format="full"` übergeben (`full` kappt `Health.Log`-Einträge auf 500 Zeichen).
> Zusätzlich: `docker_run_container` mit `detach=false` liefert `{mode:"attached", output, truncated,
> bytes}` statt zu scheitern; `docker_fetch_container_logs` und die attached-Ausgabe sind auf die letzten
> **20 KiB** begrenzt und melden `truncated` + Original-Bytezahl; `docker_build_image` nutzt `rm`/`forcerm`
> (keine Intermediate-Container nach fehlgeschlagenen Builds); Label-Filter gehen in Docker-CLI-Map-Form raus.
>
> **0.8.2 — Label-Filter + Docker-Desktop-Sichtbarkeit:** `docker_list_containers` mit Label-Filter nutzt
> jetzt die Map-Form und löst Treffer per ID auf — auf Docker Desktop werden damit auch die
> Kubernetes-Container sichtbar, die ein ungefiltertes Listing ausblendet (der „1 von 37“-Teil von #64
> ist damit geklärt: Docker-Desktop-Verhalten, kein Server-Bug).
>
> **0.8.1 — Listen-Tools liefern ein JSON-Array:** `docker_list_*`/`docker_buildx_*` geben jetzt ein
> einzelnes JSON-Array zurück statt aneinandergeketteter Einzelobjekte (upstream
> [#64](https://github.com/dboeckli/mcp-server-docker/issues/64), behoben mit
> [PR #65](https://github.com/dboeckli/mcp-server-docker/pull/65)) — Ergebnisse sind damit direkt
> parsebar.
>
> **Breaking in 0.8.0 — Tool-Präfix `docker_`:** Alle 36 Tools tragen jetzt das Präfix `docker_`
> (`list_containers` → `docker_list_containers`), damit der flache Gateway-Namespace kollisionsfrei
> bleibt — insbesondere `events_list` → `docker_events_list` (der Kubernetes-MCP-Server bietet ebenfalls
> `events_list`). Resource-URIs (`docker://…`) und der Prompt `docker_compose` bleiben unverändert; bei
> bestehenden Whitelists/Prompts sind die Tool-Namen anzupassen.
>
> Enthalten sind die Buildx-Abfragen
> (`docker_buildx_list`/`docker_buildx_history`/`docker_buildx_logs`, Upstream-PR
> `ckreiling/mcp-server-docker#78`, Issue #250) plus die Docker-/Buildx-Introspektion (`docker_buildx_du`,
> `docker_buildx_inspect`, `docker_system_df`, `docker_system_info`, `docker_version`, `docker_image_inspect`,
> `docker_image_history`, `docker_container_inspect`, `docker_container_processes`,
> `docker_container_stats`). v0.7.0 ergänzt `docker_container_health`, `docker_network_inspect`,
> `docker_volume_inspect` und `docker_events_list` (alle read-only). v0.6.0 ergänzt einen optionalen
> Server-Read-only-Mode (`--read-only` / `MCP_SERVER_DOCKER_READ_ONLY=1`); das Kit nutzt ihn bewusst
> **nicht** — die Write-Tools bleiben über die Gateway-`ask`-Regeln einzeln freigebbar. Gepinnt per `==<v>`
> (ohne `v`-Präfix); Renovate (`.github/renovate.json`, PyPI-Datasource) und der Validate-Check
> (`local-test-kits.py`) prüfen den Pin gegen die latest PyPI-Version.

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
sbx mcp add docker --command (Get-Command uvx).Source --args "--from,mcp-server-docker-dboeckli==0.12.1,mcp-server-docker"
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
sbx mcp add docker --command (Get-Command uv).Source --args "tool,run,--from,mcp-server-docker-dboeckli==0.12.1,mcp-server-docker"
```

### Bestehende Registrierung umstellen

Gilt z. B. beim Wechsel vom Git-Tag auf das PyPI-Wheel (oder von der alten Upstream-Distribution
`mcp-server-docker==0.3.0`). Erst die alte Registrierung entfernen:

```powershell
sbx mcp rm docker
```

Dann den Fork registrieren:

```powershell
sbx mcp add docker --command (Get-Command uvx).Source --args "--from,mcp-server-docker-dboeckli==0.12.1,mcp-server-docker"
```

Laufende Sandbox nachladen (die `--static-mcp`-Menge ist beim Erstellen fixiert) bzw. neu erstellen:

```powershell
sbx mcp load docker --sandbox <name>
```

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
letzte passende Regel gewinnt):

- **`allow`** (read-only): `docker_list_containers`, `docker_list_images`, `docker_list_networks`,
  `docker_list_volumes`, `docker_fetch_container_logs`, `docker_buildx_list`, `docker_buildx_history`,
  `docker_buildx_logs`, `docker_buildx_du`, `docker_buildx_inspect`, `docker_system_df`, `docker_system_info`,
  `docker_version`, `docker_image_inspect`, `docker_image_history`, `docker_container_inspect`,
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
| `mcp-docker:FAIL` in der Sandbox (Startup-Check/Sidebar), aber `mcp-k8s:OK` | Der Gateway-Prozess findet `uvx` nicht (Daemon-PATH ≠ Terminal-PATH). **Fix:** mit absolutem Pfad neu registrieren (`sbx mcp rm docker`, dann `sbx mcp add docker --command (Get-Command uvx).Source --args "--from,mcp-server-docker-dboeckli==0.12.1,mcp-server-docker"`), danach `sbx mcp load docker --sandbox <name>` bzw. Sandbox neu erstellen. |
| `sbx mcp load docker` scheitert mit `502 … tool "events_list" … collides with an existing tool already registered for server "k8s"` | Auf dem Host läuft noch **0.7.0** mit unpräfixierten Tool-Namen. **Fix:** auf den Pin neu registrieren (`sbx mcp rm docker` + `add …==<pin>`, siehe oben) und `sbx mcp load docker --sandbox <name>`; erst danach `mcp-docker:OK` erwarten. |
| `sbx mcp add` ok, aber keine Docker-Tools im `tools/list` | Server ist nicht Teil der `--static-mcp`-Menge der Sandbox (Set ist beim Erstellen fixiert) → `sbx mcp load docker --sandbox <name>` oder neu erstellen. |
| Erster Check kurz `FAIL`, danach `OK` | `uvx` lädt das PyPI-Wheel beim ersten Start → kurzer Start-Timeout (Gateway-Startprobe); erneut prüfen. |
| Tool-Fehler „Cannot connect to the Docker daemon" | Docker Desktop läuft nicht oder der Benutzer ist nicht in `docker-users` (Host-Docker-Socket nötig). |

## Betrieb

| Aktion | Befehl |
|--------|--------|
| Update (neue Version) | Renovate-PR für `docs/mcp/docker-mcp-server.md` (`mcp-server-docker-dboeckli==<v>`) mergen, dann auf dem Host neu registrieren: `sbx mcp rm docker` + `sbx mcp add docker --command (Get-Command uvx).Source --args "--from,mcp-server-docker-dboeckli==<neu>,mcp-server-docker"`; laufende Sandbox: `sbx mcp load docker --sandbox <name>` |
| Status prüfen | `sbx mcp ls` (Status `ready`), `sbx mcp inspect docker` (Command/Args) |
| In Sandbox prüfen | `sbx exec <name> bash -lc 'bash ~/.local/bin/mcp-check.sh'` → `mcp-docker:OK` |
| Nachladen in laufende Sandbox | `sbx mcp load docker --sandbox <name>` |
| Registrierung entfernen | `sbx mcp rm docker` |

## Verifikation

- **Host:** `sbx mcp ls` zeigt `docker`; `sbx mcp inspect docker` zeigt Command/Args (absoluter `uvx`-Pfad + `mcp-server-docker-dboeckli==0.12.1`).
- **Sandbox:** MCP-Handshake `tools/list` enthält die Docker-Tools (`docker_list_containers`, …); ein
  Read-Tool (`docker_list_containers`) läuft ohne Prompt, ein Write-Tool (`docker_run_container`) löst den
  `ask`-Prompt aus.
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
