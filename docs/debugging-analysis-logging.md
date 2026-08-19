# Debugging, Analyzing & Logging

Wie du das Sandbox-Kit beobachtest, analysierst und debuggen kannst — von den Log-Dateien im
Sandbox bis zu den Validierungs-/Drift-Checks und dem IntelliJ MCP. Alle PowerShell-Befehle laufen
auf dem **Windows-Host** (Docker Desktop), die `sbx exec`-Befehle greifen in eine **laufende**
Sandbox.

## Logging

### Log-Dateien in der Sandbox

| Log | Inhalt | Entstehung |
|-----|--------|-----------|
| `/var/log/sbx-kit-install.log` | Tooling-Installation Schritt für Schritt (`install-tooling.sh`) | `setup.install` beim Sandbox-Build |
| `/var/log/sbx-kit-startup.log` | Startup-Hooks des Dispatchers (`/etc/durable-startup.d/`) | jeder Sandbox-Start |
| `/var/log/dockerd.log` | isolierter Docker-Daemon der Sandbox | Sandbox-Laufzeit |
| `/var/log/dpkg.log` | apt-Paket-Installationen | `setup.install` |
| `/var/log/bootstrap.log`, `/var/log/alternatives.log` | distro-Init / Alternativen | Image-Build |
| `~/.config/sandbox-kit/startup-checks.report` | aktueller `[startup-checks]`-Report | jeder Session-Start |

### Install-Log-Format (`/var/log/sbx-kit-install.log`)

Der `setup.install` ruft npm/apt als **Inline-Commands** und die restlichen Tools **einzeln pro Tool**
(`install-tooling.sh shfmt|jdk|maven|docker|compose|kubectl|helm|helm4`) auf — so zeigt die
`sbx run`-Konsole jedes Tool als eigene Zeile (Spinner beim Start → ✓ beim Abschluss). Jeder Lauf
loggt `start`/`done` (Tool, Dauer, kumulative Gesamtzeit, Wall-Clock-Timestamp):

```
[install-tooling] 2026-08-19T10:24:27+02:00 phase=shfmt start
[install-tooling] 2026-08-19T10:24:28+02:00 step=shfmt elapsed=1s total=1s
[install-tooling] 2026-08-19T10:24:28+02:00 phase=shfmt done total=1s
[install-tooling] 2026-08-19T10:24:28+02:00 phase=jdk start
[install-tooling] 2026-08-19T10:24:57+02:00 step=jdk elapsed=29s total=30s
[install-tooling] 2026-08-19T10:24:57+02:00 phase=jdk done total=30s
...
[install-tooling] 2026-08-19T10:26:01+02:00 phase=helm4 done total=99s
```

- `elapsed` = Dauer des letzten Schritts, `total` = Zeit seit Tool-Start, Timestamp = Wall-Clock.
- Die Log-Zeilen gehen per `tee -a` sowohl nach `/var/log/sbx-kit-install.log` als auch nach stdout.
- **Konsole (`sbx run`)**: `sbx` selbst rendert jeden Install-Command als Spinner und schluckt dessen
  stdout — pro Tool siehst du also Start (Spinner-Zeile) und Abschluss (✓ mit Dauer). Die Detailzeilen
  (`step=…`) landen im Log-File. Setup-Output wird von `sbx` **nicht** aufbewahrt — für frische Logs
  die Sandbox neu erstellen (`sbx rm <name>` + `sbx run …`).
- **Fehlschlag-Diagnose**: Das erste Tool ohne `phase=… done` ist fehlgeschlagen — das Script bricht
  bei `set -euo pipefail` sofort ab.

### Logs von außen anzeigen (`sbx exec`)

```powershell
sbx exec opencode-sandbox cat /var/log/sbx-kit-install.log
sbx exec opencode-sandbox cat /var/log/sbx-kit-startup.log
sbx exec opencode-sandbox bash -c 'cat /var/log/sbx-kit-install.log /var/log/sbx-kit-startup.log'
```

Live während eines Builds:

```powershell
sbx exec opencode-sandbox -- tail -f /var/log/sbx-kit-install.log
```

### Log-Format erweitern / ändern

Die Timestamp-Logik steckt in `log_step()`, `log_phase_start()`, `log_phase_done()` und im
Phasen-Dispatch (`npm|apt|tools|all`) von `files/home/.local/bin/install-tooling.sh`. Die
Phasen-Commands referenzieren die drei Specs (`spec.yaml`, `mammouth-agent/`, `claude-zurich-agent/`).
**Alle drei Kit-Kopien identisch halten** (Root, `mammouth-agent/`, `claude-zurich-agent/`) — der
Drift-Check schlägt sonst fehl:

```powershell
cp files\home\.local\bin\install-tooling.sh mammouth-agent\files\home\.local\bin\install-tooling.sh
cp files\home\.local\bin\install-tooling.sh claude-zurich-agent\files\home\.local\bin\install-tooling.sh
```

## Analyzing

### sbx CLI Offline-Referenz (`~/sbx-cli.md`)

Alle `--help`-Outputs der v0.38.0-Binary liegen offline unter `~/sbx-cli.md` (Kit-Bundle
`files/home/sbx-cli.md`, identisch in den drei Kit-Kopien) — die sbx CLI selbst ist **nicht** in
Context7. Detaillierte Hintergrunddoku (Kits, Policy, Proxy): `npx ctx7 docs /docker/docs <query>`.

**Aktualisieren:** `python local-test/regenerate-sbx-doc.py [<version>]` (Default: `SBX_VERSION` aus
`.github/workflows/validate.yml`, ggf. `v0.39.0` übergeben — die Doku muss den Renovate-verwalteten
Pin spiegeln, nicht das neueste Release). Der Validate-only-Lauf (`local-test-kits.py --validate-only`)
vergleicht die dokumentierte Version mit dem gepinnten `SBX_VERSION` und schlägt fehl bei Abweichung
(Hinweis aufs Regen-Skript).

### Kit validieren (`sbx kit validate`)

Läuft auf dem Host (Docker Desktop) — `sbx` ist **nicht** im Sandbox-Image installiert:

```powershell
sbx kit validate .                            # Mixin-Kit (OpenCode/Claude)
sbx kit validate ./mammouth-agent             # Mammouth Agent-Kit
sbx kit inspect . --output json | jq '.warnings'   # erwartet: []
```

Automatisiert via `local-test-kits.py` bzw. IntelliJ-Config `local-test-kits-validate-only`:

```powershell
python local-test\local-test-kits.py --validate-only
```

### Install-Script-Drift-Check

`local-test-kits.py` prüft, dass die Install-Skripte in allen drei Kit-Kopien identisch sind
(`check_install_scripts_sync`). Nur diese Kopien anfassen und synchron halten:

- `files/home/.local/bin/install-tooling.sh` → `mammouth-agent/…`, `claude-zurich-agent/…`
- `files/home/.local/bin/install-tooling-user.sh` → dito
- `files/home/.local/bin/regenerate-kubeconfig.py` → dito

### Startup-Checks

Der `[startup-checks]`-Report (Context7, IntelliJ MCP, gh, Java/Maven, Docker, kubectl, Helm, Skills)
wird beim Session-Start injiziert und nach `~/.config/sandbox-kit/startup-checks.report` geschrieben.
Manuell neu ausführen:

```bash
bash ~/.config/sandbox-kit/run-checks.sh
```

Ein `FAIL` = Tool nicht erreichbar/fehlt. Referenz: `~/.config/sandbox-kit/startup-checks.md`.

### Netzwerk-Analyse: Blocked requests

Deny-by-Default-Proxy: geblockte Requests aus der Sandbox via Policy-Log anzeigen:

```powershell
sbx policy log opencode-sandbox
```

(Nur Hosts aus `permissions.network.allow` sind erreichbar; alles andere → HTTP 403. Der
`local-test-kits.py`-Lauf prüft das automatisch via `blocked_requests()`.)

### Stack-Overflow-API-Versions-Check

`local-test-kits.py --validate-only` vergleicht die in `~/stackexchange-api.md` dokumentierte
API-Version mit dem offiziellen Change-Log — schlägt fehl, wenn eine neuere Version existiert
(Doku-Dateien + `api_revision` aktualisieren). Beide Kit-Kopien
(`files/home/`, `mammouth-agent/files/home/`) identisch halten.

### IntelliJ: Probleme statisch analysieren

Über den IntelliJ MCP direkt inspizieren (nur lesende Tools, Whitelist):

- `idea_get_file_problems` — Inspection-Errors/Warnings einer Datei
- `idea_search_in_files_by_regex` / `idea_search_symbol` — schnelle Suche im Projekt
- `idea_generate_psi_tree`, `idea_run_inspection_kts` — Inspections entwickeln/testen

## Debugging

### IntelliJ MCP-Verbindung testen

Der IntelliJ MCP-Forwarder läuft auf Windows unter `127.0.0.1:64342`. Aus der Sandbox über
`host.docker.internal:64342` (darf **nicht** auf `127.0.0.1` geändert werden — das wäre der
Container-Loopback):

```bash
sbx exec opencode-sandbox bash -c 'curl -s -o /dev/null -w "HTTP %{http_code}\n" -m 3 http://host.docker.internal:64342/sse'
```

Erwartet: `HTTP 200`. Details + WSL/Firewall-Varianten: README → Troubleshooting.

### IntelliJ MCP über die Permission-Whitelist

OpenCode/Mammouth: `"idea_*": "deny"` zuerst, danach gezielte `allow`-Regeln (Reihenfolge zählt —
`findLast`-Semantik). Claude Code: explizite `allow`-Whitelist in `settings.json`. Schreibende/
ausführende Tools sind gar nicht sichtbar.

### Run-Config-Guard & `idea_execute_run_configuration`

`idea_execute_run_configuration` braucht Bestätigung und ist per Guard auf die Run-Config
`local-test-kits-validate-only` begrenzt (OpenCode-Plugin bzw. Claude PreToolUse-Hook). Andere
Run-Configs werden mit einem Fehler geblockt.

> **Timeout-Verhalten**: `idea_execute_run_configuration` mit `waitForExit=true` timeout't nach
> **15 min**, obwohl der Test (~8 min) evtl. noch läuft — dann den Prozessstatus via
> `idea_execute_terminal_command` + `Get-Process python` prüfen (bzw. `waitForExit=false` nutzen).
>
> **Project-Path beachten**: IntelliJ läuft auf dem Windows-Host — der `projectPath` muss ein
> Host-Pfad sein (z. B. `C:\development\projects\opencode-sandbox-kit`), nicht der Sandbox-Pfad
> (`/Users/...`). Sonst liefert `idea_get_run_configurations` eine leere Liste.

### Sandbox-Startup-Hooks debuggen

Beim Start laufen Hooks aus `/etc/durable-startup.d/*` — Ergebnis im Dispatcher-Log:

```bash
cat /var/log/sbx-kit-startup.log
# === dispatcher run ... ===
# > /etc/durable-startup.d/002-startup-opencode-sandbox-kit/000-cmd.sh
# ok ...   ← "ok" = Hook erfolgreich
```

Kein `ok` / Abbruch = Hook fehlgeschlagen. Das Log-Format (`> ` / `ok ` / `=== dispatcher run ===`)
schreibt der **Dispatcher des Base-Templates** — Timestamps pro Zeile kann das Kit hier nicht ergänzen
(anders als beim Install-Log, das `install-tooling.sh` selbst schreibt). Der einzige Timestamp ist die
`=== dispatcher run <UTC> ===`-Startzeit oben.

| Hook | Quelle | Was passiert |
|------|--------|--------------|
| `001-startup-opencode/000-cmd.sh` | Base-Template (root) | `apt-get update` (Paketlisten vorwärmen, Fehler toleriert) |
| `001-startup-opencode/001-cmd.sh` | Base-Template (agent) | `~/.config/opencode/opencode.json` schreiben → registriert den `mcp-gateway` (Proxy) als Remote-MCP-Server |
| `002-startup-opencode-sandbox-kit/000-cmd.sh` | Kit `setup.startup` (agent) | `~/.claude/settings.json` mit `settings.kit.json` mergen (nach Template-Overwrite — Python-Merge, korrekte Array-Behandlung) |
| `002-startup-opencode-sandbox-kit/001-cmd.sh` | Kit `setup.startup` (agent) | `regenerate-kubeconfig.py` → `~/.kube/config` aus dem read-only Host-Kubeconfig-Mount regenerieren (idempotent, No-op ohne Mount) |

Das `002-…-sandbox-kit`-Verzeichnis wird vom Template aus dem `setup.startup`-Abschnitt der Kit-Spec
generiert (`spec.yaml`, `mammouth-agent/spec.yaml`, `claude-zurich-agent/spec.yaml`); die
Hook-Skripte landen als `000-cmd.sh`, `001-cmd.sh`, … in Namensreihenfolge.

### Kit-Spec v2 / sbx-Version

v2-Grammatik verlangt **sbx v0.38+** — ein v1-Feld in einer `"2"`-Spec ist ein harter Decode-Fehler.
Diagnose: `sbx kit validate .` + `sbx kit inspect . --output json | jq '.warnings'` (erwartet `[]`).

## Zusammenfassung der Kommandos

| Ziel | Befehl |
|------|--------|
| Install-Log ansehen | `sbx exec <sandbox> cat /var/log/sbx-kit-install.log` |
| Install-Log live folgen | `sbx exec <sandbox> -- tail -f /var/log/sbx-kit-install.log` |
| Startup-Hooks prüfen | `sbx exec <sandbox> cat /var/log/sbx-kit-startup.log` |
| Kit validieren | `sbx kit validate .` + `sbx kit inspect . --output json \| jq '.warnings'` |
| Drift + SO-API-Check | `python local-test\local-test-kits.py --validate-only` |
| Blocked requests | `sbx policy log <sandbox>` |
| Startup-Checks (in Sandbox) | `bash ~/.config/sandbox-kit/run-checks.sh` |
| IntelliJ MCP testen | `sbx exec <sandbox> bash -c 'curl -s -o /dev/null -w "HTTP %{http_code}\n" -m 3 http://host.docker.internal:64342/sse'` |
