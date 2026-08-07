# v1 → v2 Migration: opencode-sandbox-kit

Plan für die Migration beider Kits auf die **v2-Kit-Grammatik** (`schemaVersion: "2"`).
Voraussetzung: `sbx` **v0.38.0+** (strikte v2-Grammatik, inkl. `setup.startup` und striktem
Decoding). Die v1-Migration ist ein **Breaking Change**, keine additive Änderung: Ein
v1-Feld in einer `"2"`-Spec ist ein **harter Decode-Fehler** (`KnownFields(true)`), keine
stille Faltung.

> **Wichtig:** Diese Migration wird **separat in einem eigenen Feature-Branch** durchgeführt.
> Der aktuelle Stand auf `main` (v1 + `persistent.sh`-Settings-Merge) bleibt unverändert
> funktionsfähig. Dieser Plan dient als Arbeitsgrundlage für den Branch.

---

## 0. Teilaufgaben (durchnummerierte Arbeitsliste)

Die Migration wird in folgende Teilaufgaben zerlegt. Reihenfolge ist verbindlich
(0.x = Vorbereitung, 1.x = Mixin, 2.x = Mammouth, 3.x = Verifikation, 4.x = Doku).

### 0 — Vorbereitung

1. **Feature-Branch anlegen**: `git checkout main && git pull && git checkout -b feat/kit-spec-v2`
2. **Migrationsskript verfügbar machen**: `docker/sbx-kits-contrib` klonen (z. B.
   `/tmp/sbx-kits-contrib`) und `scripts/README.md` lesen, um den tatsächlichen
   Abdeckungsgrad des `migrate-v1-to-v2.go`-Skripts zu prüfen (Rest per Hand).
3. **Migrationsskript lokal testen**: auf einer Kopie (nicht im Repo) einmal
   `go run scripts/migrate-v1-to-v2.go <copy>` ausführen und das Ergebnis-Diff prüfen.

### 1 — Mixin-Kit (Root-`spec.yaml`)

4. **Mixin-Spec automatisch migrieren**: `go run scripts/migrate-v1-to-v2.go .` — prüfen,
   dass `schemaVersion: "2"`, `permissions.network.allow`, `setup.install` und die
   v2-`credentials[]`-Form entstanden sind; `spec.yaml.bak` vorhanden.
5. **`setup.startup` für Claude-settings.json einbauen** (manuelle Nacharbeit): den
   `persistent.sh`-Merge (aktuell Zeile ~164) in einen `setup.startup`-Block verschieben
   (jq-DeepMerge-Snippet, `user: "1000"`), damit die Kit-settings.json nach jedem
   Container-Start re-applied wird.
6. **`setup.files` prüfen**: klären, ob v1 `settings:` genutzt wurde (laut Plan: nein) —
   falls nein, kein Handlungsbedarf; nur verifizieren, dass `files/`-Tree unverändert gilt.
7. **Port-Suffixe in `permissions.network.allow` erhalten**: sicherstellen, dass
   `:443`/`:64342`-Einträge (v. a. `host.docker.internal:64342`) nach der Migration
   erhalten bleiben (erweiterte Muster werden noch nicht enforced).

### 2 — Mammouth-Agent-Kit (`mammouth-agent/spec.yaml`)

8. **Mammouth-Spec automatisch migrieren**: `go run scripts/migrate-v1-to-v2.go ./mammouth-agent`
   — prüfen: `agentInstructions.filename`/`content`, flaches `sandbox.entrypoint`,
   `permissions.network.allow`, `setup.install`, v2-`credentials[]`.
9. **`environment.variables` für `MAMMOUTH_API_KEY`/`CONTEXT7_API_KEY` bereinigen**:
   Duplikat-Verdacht klären — `proxyManaged: true` setzt den `proxy-managed`-Sentinel
   in v2 implizit; die expliziten `environment.variables`-Einträge entfallen, außer für
   Nicht-Credential-Variablen.
10. **`persistent.sh`-Entscheidung umsetzen**: klären, ob die Env-Exports (`JAVA_HOME`,
    `PATH`, Modell-Variablen) komplett in `setup.startup` verlagert werden (Empfehlung)
    oder `persistent.sh` bestehen bleibt. Kein doppeltes Schreiben.

### 3 — Verifikation

11. **`sbx kit validate`** für beide Kits (`.`, `./mammouth-agent`): 0 Fehler, 0 WARN.
12. **`sbx kit inspect`** für beide Kits: `--output json | jq '.warnings'` → `[]` bzw. `null`.
13. **Sandbox-Start-Tests** (Windows-Host): `sbx run opencode` und `sbx run mammouth` mit
    den v2-Kits; IntelliJ MCP + ctx7 erreichbar, Mammouth installiert.
14. **Claude-settings.json-Neustart-Test**: Sandbox neu starten und prüfen, dass `statusLine`,
    `mcpServers`, `permissions`, `hooks` per `setup.startup` wiederhergestellt sind.
15. **E2E lokal**: `python local-test/local-test-kits.py` (bzw. IntelliJ-Run-Config
    `local-test-kits`) — alle 3 Szenarien grün.
16. **CI**: `.github/workflows/e2e.yml`-Run grün.

### 4 — Doku

17. **AGENTS.md-Caveat aktualisieren**: Abschnitt "Kit-spec v1/v2" ersetzen — v2 ist jetzt
    stabil, keine v1-WARN-Tabelle mehr.
18. **README.md aktualisieren**: Erwähnungen von `commands`/`caps` auf `setup`/`permissions`
    umstellen.
19. **DoD abhaken + Merge-Vorbereitung**: Checkliste in Abschnitt 7 durchgehen, Branch auf
    `main` mergen.

---

## 1. Zielbild

| Aspekt | Vorher (v1) | Nachher (v2) |
|---|---|---|
| Schema | `schemaVersion: "1"` | `schemaVersion: "2"` |
| Netzwerk | `caps.network.allow` | `permissions.network.allow` (Top-Level) |
| Credentials | `credentials[]` (v1-Form) | `credentials[]` mit `apiKey.name` + `.inject[]` |
| Env | `environment.variables` (nur mammouth) | v2-Block `environment` (falls beibehalten) |
| Install | `commands.install` | `setup.install` |
| Start | `persistent.sh`-Merge (Hack) | `setup.startup` (offiziell, idempotent, `user: "1000"`) |
| Agent-Context | `sandbox.aiFilename` / `agentContext:` | Top-Level `agentInstructions:` |
| Entrypoint | `sandbox.entrypoint.run` | flaches `sandbox.entrypoint` |
| Warnings | v1-Folding-Warnungen | `sbx kit inspect` → `warnings: []` |

---

## 2. Werkzeug

Offizielles Migrationsskript aus `sbx-kits-contrib`:

```bash
go run scripts/migrate-v1-to-v2.go <kit-dir>
```

- Schreibt `spec.yaml` **in place** neu, Original bleibt als `spec.yaml.bak`.
- Lauf auf bereits-v2-Spec ist ein No-Op (kein `.bak`).
- Nutzt denselben Normalize-Pass wie der Engine-Loader → bleibt mit der Loader-Logik synchron.
- **Derzeit nicht im Repo vorhanden** — `scripts/` ist leer. Vor der Migration muss das
  Skript in den Feature-Branch geholt werden (Entscheidung: vendor? oder `go run` aus einem
  Checkout von `docker/sbx-kits-contrib`? → siehe Schritt 3).

Nach Migration verifizieren:

```bash
sbx kit validate ./spec.yaml          # bzw. ./ (Kit-Root)
sbx kit inspect ./ --output json | jq '.warnings'
# Erwartet: null oder [] — jedes Warnings-Element ist ein TODO
```

---

## 3. Ablauf (Reihenfolge)

### Schritt 0 — Ausgangslage sichern

1. `main` ist aktuell (inkl. `persistent.sh`-Settings-Merge aus dem aktuellen Stand).
2. Feature-Branch anlegen, z. B. `feat/kit-spec-v2`.
3. Migrationsskript verfügbar machen:
   - Empfehlung: `docker/sbx-kits-contrib` klonen und `go run scripts/migrate-v1-to-v2.go`
     verwenden (lockstep mit Loader), **nicht** selbst Hand-migrieren.
   - Prüfen: `scripts/README.md` der Contrib für aktuellen Scope lesen (das Skript deckt
     nicht 100 % ab; Rest per Hand, siehe Abschnitt 5).

### Schritt 1 — Mixin-Kit migrieren (`spec.yaml`, Root)

`go run scripts/migrate-v1-to-v2.go .`

Erwartete automatisierte Änderungen:

- `schemaVersion: "2"`, `kind: mixin` bleibt
- `caps.network.allow` → `permissions.network.allow`
- `commands.install` → `setup.install`
- `credentials[]` → v2-Form (`apiKey.name` + `inject[]`; `scheme: bearer`-Sugar optional)

Manuelle Nacharbeit (Skript deckt nicht ab):

- **`setup.startup` für die Claude-settings.json** — der `persistent.sh`-Merge (aktuell
  Zeile 164 in `spec.yaml`) wird in einen `setup.startup`-Block verschoben:
  ```yaml
  setup:
    startup:
      - command:
          - sh
          - -c
          - |
            if [ -f /home/agent/.claude/settings.json ] && [ -f /home/agent/.claude/settings.kit.json ]; then
              jq -s '.[0] * .[1]' /home/agent/.claude/settings.json /home/agent/.claude/settings.kit.json > /tmp/settings.merged.json \
                && mv /tmp/settings.merged.json /home/agent/.claude/settings.json
            fi
        user: "1000"
        description: Re-apply kit settings.json after template overwrite
  ```
- `setup.files` statt `settings:` (falls v1 `settings:` genutzt wurde — aktuell nicht der Fall).
- Keine `sandbox:`-Block-Felder im Mixin erlaubt (`kind: mixin` verbietet `sandbox:`).

### Schritt 2 — Mammouth-Agent-Kit migrieren (`mammouth-agent/spec.yaml`)

`go run scripts/migrate-v1-to-v2.go ./mammouth-agent`

Erwartete automatisierte Änderungen:

- `schemaVersion: "2"`, `kind: sandbox` bleibt
- `sandbox.aiFilename: AGENTS.md` → `agentInstructions.filename: AGENTS.md`
- `agentContext:` → `agentInstructions.content:` (Top-Level)
- `sandbox.entrypoint.run: [mammouth]` → `sandbox.entrypoint: [mammouth]` (flach)
- `caps.network.allow` → `permissions.network.allow`
- `commands.install` → `setup.install`
- `credentials[]` → v2-Form
- `environment.variables` → prüfen, ob v2-Form beibehalten werden kann (siehe Abschnitt 5,
  "environment")

### Schritt 3 — Verifikation

1. `sbx kit validate .` → keine Fehler, keine WARN
2. `sbx kit validate ./mammouth-agent` → keine Fehler, keine WARN
3. `sbx kit inspect . --output json | jq '.warnings'` → `[]` bzw. `null`
4. `sbx kit inspect ./mammouth-agent --output json | jq '.warnings'` → `[]` bzw. `null`
5. Sandbox-Test (auf Windows-Host): `sbx run opencode --name <test> --kit .` und
   `sbx run mammouth --name <test> --kit ./mammouth-agent/`
6. E2E: `python local-test/local-test-kits.py` (bzw. `--ci` in GitHub Actions)
7. IntelliJ-Run-Config `local-test-kits` verwenden (siehe AGENTS.md)

---

## 4. Feldzuordnung (Referenz)

Aus `SPEC-v2.md` / `v1-migration.md` (offizielle Quelle, `docker/sbx-kits-contrib`):

| v1 | v2 |
|---|---|
| `kind: agent` | `kind: sandbox` |
| `agent:` Block | `sandbox:` Block |
| `sandbox.aiFilename` | `agentInstructions.filename` |
| `memory:` / `agentContext:` | `agentInstructions.content` |
| `sandbox.entrypoint.run` | `sandbox.entrypoint` (flaches Array) |
| `sandbox.entrypoint.args` | `sandbox.command.default` |
| `sandbox.entrypoint.ttyArgs` | `sandbox.command.interactive` |
| `sandbox.entrypoint.pipeMode` | **dropped** (kein v2-Pendant) |
| `sandbox.resources.memoryMB` | `sandbox.resources.memory` (Byte-Size-String) |
| `credentials.sources` + `network.serviceDomains` + `network.serviceAuth` + `environment.proxyManaged` | `credentials[]` (`apiKey.name` + `.inject`) |
| Standalone `oauth:` | `credentials[].oauth` |
| `network.allowedDomains` | `permissions.network.allow` |
| `network.deniedDomains` | `permissions.network.deny` |
| `network.publishedPorts` / Top-Level `publishedPorts` | Top-Level `ports` |
| `commands:` / `commands.initFiles` | `setup:` / `setup.files` |
| `settings:` | **dropped** (Agent-Setup nach `setup.files`) |
| `kitDir` | **dropped** |
| `sandbox.persistence` | **dropped** (stattdessen `volumes:`) |
| Top-Level `tmpfs:` | `volumes[]` mit `type: tmpfs` (strict-rejected in v2!) |

### v2-spezifische Felder (Neu)

- `setup.startup[]`: läuft bei **jedem** Container-Start, muss idempotent sein,
  `command` ist **exec-style argv** (`["sh", "-c", "..."]`), Default-`user: "1000"`.
- `setup.install[]`: läuft **einmal** bei Sandbox-Erstellung, Default-`user: "0"`.
- `setup.files[]`: Datei-Writes beim Start; `path` absolut, nur `${WORKDIR}`-Placeholder.
- `permissions.network.allow`-Einträge: alle `credentials[].apiKey.inject[].domain` und
  `credentials[].sshAgent.hosts[]` **MÜSSEN** in der Allow-Liste stehen (kein Auto-Derive).

---

## 5. Risiken & Besonderheiten (im Repo-Kontext)

1. **`credentials[].apiKey.name` vs. `environment.variables`** (mammouth):
   In v1 setzt das Mammouth-Kit `environment.variables` für `MAMMOUTH_API_KEY`/`CONTEXT7_API_KEY`
   auf `proxy-managed`. In v2 ist das **implizit** — `proxyManaged: true` setzt den Sentinel
   automatisch. `environment.variables` für diese Keys entfällt (Duplikat-Verdacht prüfen;
   evtl. behalten für Nicht-Credential-Variablen).

2. **`persistent.sh`-Zeilen**: In v2 wird `setup.startup` der **offizielle** Ort für die
   Env-Exports (`JAVA_HOME`, `PATH`, Modell-Variablen). Der `persistent.sh`-Ansatz kann
   ersetzt werden — ABER: `persistent.sh` wird auch von anderen Mechanismen gesourct.
   **Entscheidung nötig:** `setup.startup`-Block komplett (statt `>> /etc/sandbox-persistent.sh`)
   oder `persistent.sh` beibehalten und nur den Settings-Merge nach `setup.startup` ziehen?
   Empfehlung: Env-Exports in `setup.startup` verlagern, `persistent.sh`-Zeilen aus `install`
   entfernen (kein doppeltes Schreiben).

3. **`agentInstructions` vs. `files/home/.config/opencode/AGENTS.md`**: Der
   `agentContext:` (mammouth) wird zu `agentInstructions.content`. Das Mixin-Kit legt
   `AGENTS.md`-Regeln zusätzlich als Datei in `files/` ab. Beides bleibt möglich —
   `agentInstructions` ist nur der Kit-getragene Context.

4. **MCP-Permission-Whitelist (opencode.jsonc)**: Unabhängig von der Kit-Spec — keine
   Änderung nötig. Nur verifizieren, dass der Loader die Dateien in `files/` unverändert
   kopiert (v2 `files/`-Tree unverändert gültig).

5. **Port-Muster in `permissions.network.allow`** (`host.docker.internal:64342`):
   v2-Spec weist darauf hin, dass erweiterte Muster (`**.`, CIDR, Port-Ranges) **deklariert,
   aber noch nicht enforced** sind. Die konkreten `:443`/`:64342`-Suffixe müssen weiterhin
   explizit drin bleiben. Bei Migration prüfen, ob die `:443`-Suffixe erhalten bleiben.

6. **`mammouth-agent` referenziert `files/`**: Layout im v2-`files/`-Tree prüfen (die v2-Spec
   unterstützt weiterhin einen `files/`-Baum; Struktur unverändert).

7. **`sbx kit add` (apply to existing sandbox)**: v2-Sandboxen über `sbx run` neu starten;
   `sbx kit add` auf v2-Kits laut Doku unterstützt (VM-State bleibt). E2E-Skript deckt das ab.

8. **`schemaVersion`-Fork**: v1 und v2 können **nicht** in einem File gemischt werden
   (hartes Decode-Fehlverhalten). Daher beide Kits im selben Branch migrieren, nicht einzeln.

---

## 6. Testplan

| # | Test | Erwartung |
|---|---|---|
| 1 | `sbx kit validate .` | OK, keine WARN |
| 2 | `sbx kit validate ./mammouth-agent` | OK, keine WARN |
| 3 | `sbx kit inspect . --output json \| jq '.warnings'` | `[]` |
| 4 | `sbx kit inspect ./mammouth-agent --output json \| jq '.warnings'` | `[]` |
| 5 | `sbx run opencode --name opencode-v2 --kit .` | Sandbox startet, IntelliJ MCP + ctx7 erreichbar |
| 6 | `sbx run mammouth --name mammouth-v2 --kit ./mammouth-agent/` | Sandbox startet, Mammouth installiert |
| 7 | Claude settings.json nach Neustart | `statusLine`, `mcpServers`, `permissions`, `hooks` vorhanden (via `setup.startup`) |
| 8 | `python local-test/local-test-kits.py` (Host, Windows) | alle 3 Szenarien grün |
| 9 | GitHub Actions `.github/workflows/e2e.yml` | grün |

---

## 6.1 Zwischenstand (Stand: 2026-08-07, Feature-Branch `feature/migratte-to-sbx-v2`)

### Was bereits umgesetzt ist

- [x] **T4/T8 — Specs auf v2 migriert** (Mixin `spec.yaml` + `mammouth-agent/spec.yaml`):
  `schemaVersion: "2"`, `permissions.network.allow`, `setup.install`, v2-`credentials[]`
  (`apiKey.name` + `inject[].header/format`), flacher `sandbox.entrypoint`,
  `agentInstructions.filename`/`content`. Port-Suffixe (`:443`, `:64342`) erhalten.
- [x] **T5 — Claude-settings-Merge in `setup.startup`** (statt `persistent.sh`-Hack):
  jq-DeepMerge `/home/agent/.claude/settings.json` × `settings.kit.json`, `user: "1000"`,
  exec-style argv `["sh","-c", ...]`. Registriert in sbx (`→ register 3 startup command(s)`).
- [x] **T9 — redundante `environment.variables`-API-Keys entfernt** (mammouth): v2
  `proxyManaged: true` setzt den `proxy-managed`-Sentinel implizit; die expliziten
  `MAMMOUTH_API_KEY`/`CONTEXT7_API_KEY`-Einträge entfallen (kein Duplikat).
- [x] **T10 — `persistent.sh`-Hack raus**: Env-Exports (`JAVA_HOME`, `ANTHROPIC_*`,
  `npm_config_bin_links`) in den v2-`environment.variables`-Block überführt.
- [x] **T11 — `sbx kit validate`** (beide Kits, via IntelliJ Run-Config `local-test-kits-validate-only`): **VALID**, keine WARN.
- [x] **T12 — warnings leer**: Offizieller Loader (`spec.LoadArtifactFromBytes` aus
  `docker/sbx-kits-contrib/spec`, für beide Specs: `warnings=0`.

### Offenes Problem: Sandbox-Start (T13) scheitert bei `skills add` (exit 127)

> **GELÖST (2026-08-07).** Ursache war **nicht** der Executor-PATH, sondern die in v2 neu
> als `environment.variables` injizierte `npm_config_bin_links=false`: sbx reicht die
> `environment.variables` auch an die Install-Kommandos weiter (in v1 lag der Wert nur in
> `persistent.sh` und galt damit **nicht** für den Install-Executor). Mit
> `bin_links=false` erzeugt `npm install -g` **keinen** globalen Bin-Symlink — es existiert
> schlicht kein `skills`-Binary → exit 127. Zusätzlich war der im Kit referenzierte Pfad
> falsch: Der Symlink liegt (wegen `NPM_CONFIG_PREFIX=/usr/local/share/npm-global`) unter
> `/usr/local/share/npm-global/bin/skills`, **nicht** `/usr/local/bin/skills`.

**Symptom** (`sbx run opencode --name test-opencode-sandbox --kit . --debug`):

```
✗ sh -c 'export PATH=/usr/local/bin:/usr/bin:/bin:$PATH; /usr/local/bin/skills add -g -y --all …' (user=1000, exit 127)
WARN: mcp gateway teardown
ERROR: failed to create sandbox: failed to apply kit to sandbox
```

**Fix (in beiden Kits `spec.yaml` + `mammouth-agent/spec.yaml`):**
1. `npm install -g`-Schritte (ctx7/skills/prettier/renovate) mit `npm_config_bin_links=true`
   prefixen, damit die globalen Bin-Symlinks trotz `environment.variables`-Wert `false`
   erzeugt werden.
2. `skills add`-Befehl auf den korrekten Pfad `/usr/local/share/npm-global/bin/skills`
   (bzw. PATH-Export inkl. `/usr/local/share/npm-global/bin`) umgestellt.

**Verifiziert:** `sbx create opencode … --kit .` → alle 15 Install-Schritte ✓, Sandbox
erstellt; `sbx exec` zeigt `which skills ctx7 prettier renovate` + alle 4 Skills in
`~/.agents/skills`.

**Zu erledigen danach (ungeändert):**
- T13–T16 Sandbox-Start (opencode/mammouth), Claude-settings-Neustart-Test, E2E (Host) + CI.
- T17/T18 Doku: AGENTS.md-Caveat "Kit-spec v1/v2" ersetzen; README.md-Erwähnungen von
  `commands`/`caps` auf `setup`/`permissions` umstellen; README-Referenzen auf
  `/etc/sandbox-persistent.sh` aktualisieren (jetzt `environment.variables`)`/`setup`.

---

## 7. Definition of Done

- [ ] Beide Kits auf `schemaVersion: "2"` migriert (Feature-Branch)
- [ ] `sbx kit validate` für beide Kits: 0 Fehler, 0 WARN
- [ ] `sbx kit inspect` für beide Kits: `warnings` leer
- [ ] `setup.startup` re-applyt die Kit-settings.json (Claude `statusLine` überlebt Neustart)
- [ ] Env-Exports sauber in v2 (kein doppeltes `persistent.sh`-Schreiben)
- [ ] E2E lokal (Windows-Host) + GitHub Actions grün
- [ ] AGENTS.md-Caveat "Kit-spec v1/v2" aktualisiert (v2 ist jetzt stabil, v1-WARN-Tabelle ersetzen)
- [ ] README.md-Erwähnungen von `commands`/`caps` auf `setup`/`permissions` aktualisiert
