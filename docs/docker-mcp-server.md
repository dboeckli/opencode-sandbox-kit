# Docker-MCP-Server auf dem Windows-Host (lokal via `uvx`)

Issue: [#165](https://codeberg.org/dboeckli/opencode-sandbox-kit/issues/165) — Host-Docker-Zugriff aus
der Sandbox **ohne offenen `2375`-Port** (siehe [#71](https://codeberg.org/dboeckli/opencode-sandbox-kit/issues/71)).

**Entscheid:** Host-Docker-Zugriff über einen **lokalen Docker-MCP-Server**
([`ckreiling/mcp-server-docker`](https://github.com/ckreiling/mcp-server-docker), Python), der
**host-seitig via `uvx`** gestartet und beim **sbx MCP Gateway** registriert wird
(`sbx mcp add --command …`). Die Sandbox spricht ausschließlich MCP; der direkte `2375`-Port entfällt
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
> sind beliebige Operationen möglich (inkl. `container run -v /:/host`). Nur für Dev-Hosts; die
> begrenzende Schicht ist die **Sandbox-Permission-Whitelist** (read-only `allow`, Write `ask`).

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
uvx mcp-server-docker==0.3.0
```

Erststart lädt das Paket aus PyPI; danach startet der **stdio-MCP-Server** (keine Ausgabe, wartet auf
JSON-RPC). Mit `Ctrl+C` beenden.

> **Version pinnen** (empfohlen): Der Server ist ein Drittanbieter-Paket (Community, Solo-Maintainer) →
> reproduzierbare Version `mcp-server-docker==<v>` statt „latest". Der Pin wird via Renovate
> (`.github/renovate.json`, PyPI) getrackt und im Validate-Check (`local-test-kits.py`) gegen die
> latest PyPI-Version geprüft.

## 3. Beim sbx MCP Gateway registrieren

`--command` + `--args` registrieren den Server als **host-lokalen stdio-Server**; sbx startet den Prozess
selbst. **Wichtig:** `--command` läuft im Kontext des sbx-Host-Daemons — dieser erbt **nicht** den
Terminal-PATH, in dem `uvx` ggf. nur über einen winget-Shim auflösbar ist. Deshalb den **absoluten Pfad**
verwenden (genau wie beim K8s-MCP):

```powershell
(Get-Command uvx).Source
sbx mcp add docker --command (Get-Command uvx).Source --args "mcp-server-docker==0.3.0"
sbx mcp ls
sbx mcp inspect docker
```

> Ohne absoluten Pfad registriert `sbx mcp add docker --command "uvx" …` zwar erfolgreich (`sbx mcp ls`
> = `ready`), aber der Gateway-Prozess findet `uvx` nicht und startet den Server nicht → in der Sandbox
> `mcp-docker:FAIL` (siehe Troubleshooting).
>
> Alternativ ohne `uvx`-Shim: `--command (Get-Command uv).Source --args "tool,run,mcp-server-docker==0.3.0"`.

## 4. Sandbox mit Docker-MCP starten

```powershell
sbx run opencode `
    --kit ./opencode-agent/ `
    --template docker.cloudsmith.io/dboeckli/sbx/sbx-opencode-tooling:local `
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

- **`allow`** (read-only): `list_containers`, `list_images`, `list_networks`, `list_volumes`,
  `fetch_container_logs`, `container_stats`.
- **`ask`** (schreibend): `create_container`, `run_container`, `recreate_container`, `start_container`,
  `stop_container`, `remove_container`, `pull_image`, `push_image`, `build_image`, `remove_image`,
  `create_network`, `remove_network`, `create_volume`, `remove_volume`.

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
| `mcp-docker:FAIL` in der Sandbox (Startup-Check/Sidebar), aber `mcp-k8s:OK` | Der Gateway-Prozess findet `uvx` nicht (Daemon-PATH ≠ Terminal-PATH). **Fix:** mit absolutem Pfad neu registrieren (`sbx mcp rm docker`, dann `sbx mcp add docker --command (Get-Command uvx).Source --args "mcp-server-docker==0.3.0"`), danach `sbx mcp load docker --sandbox <name>` bzw. Sandbox neu erstellen. |
| `sbx mcp add` ok, aber keine Docker-Tools im `tools/list` | Server ist nicht Teil der `--static-mcp`-Menge der Sandbox (Set ist beim Erstellen fixiert) → `sbx mcp load docker --sandbox <name>` oder neu erstellen. |
| Erster Check kurz `FAIL`, danach `OK` | `uvx` löst das gepinnte Paket beim ersten Start auf (Download) → kurzer Start-Timeout; erneut prüfen. |
| Tool-Fehler „Cannot connect to the Docker daemon" | Docker Desktop läuft nicht oder der Benutzer ist nicht in `docker-users` (Host-Docker-Socket nötig). |

## Betrieb

| Aktion | Befehl |
|--------|--------|
| Update (neue Version) | Renovate-PR für `docs/docker-mcp-server.md` (`mcp-server-docker==<v>`) mergen, dann auf dem Host neu registrieren: `sbx mcp rm docker` + `sbx mcp add docker --command (Get-Command uvx).Source --args "mcp-server-docker==<neu>"`; laufende Sandbox: `sbx mcp load docker --sandbox <name>` |
| Status prüfen | `sbx mcp ls` (Status `ready`), `sbx mcp inspect docker` (Command/Args) |
| In Sandbox prüfen | `sbx exec <name> bash -lc 'bash ~/.local/bin/mcp-check.sh'` → `mcp-docker:OK` |
| Nachladen in laufende Sandbox | `sbx mcp load docker --sandbox <name>` |
| Registrierung entfernen | `sbx mcp rm docker` |

## Verifikation

- **Host:** `sbx mcp ls` zeigt `docker`; `sbx mcp inspect docker` zeigt Command/Args (absoluter `uvx`-Pfad + `mcp-server-docker==0.3.0`).
- **Sandbox:** MCP-Handshake `tools/list` enthält die Docker-Tools; ein Read-Tool (`list_containers`)
  läuft ohne Prompt, ein Write-Tool (`run_container`) löst den `ask`-Prompt aus.
- **Nach Phase 2:** `host.docker.internal:2375` (+ `localhost`/`127.0.0.1`) aus allen `spec.yaml` +
  `network-policy.md` entfernt; der `docker-host`-Check (`run-checks.sh` 5b) ersetzt/entfernt.

## Sicherheit (Kurz)

- Kein offener Host-Port mehr in der Sandbox-Allowlist (statt `2375`).
- Der MCP-Server + Docker-Socket bleiben host-seitig; die Sandbox sieht nur MCP-Tools.
- Begrenzung = Sandbox-Permission-Whitelist (read-only `allow`, Write `ask`).

## Verwandt

- #165 (Ticket), #71 (`2375` aus der Allowlist), #40 (K8s-MCP-Muster), #160 (Allowlist zentral pflegen),
  #163 (IntelliJ-MCP-Direkt-Bypass).
