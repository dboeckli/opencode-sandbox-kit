# Plan: sbx-Version in E2E auf v0.38.0 fixieren, Updates via Renovate

Datum: 2026-08-07

## Ziel

`.github/workflows/e2e.yml` holt aktuell **immer `latest`** von
`docker/sbx-releases`. Seit `sbx` v0.38.0 (strikte v2-Grammatik) ist die
bisherige v1-Spec nicht garantiert kompatibel (siehe `v2-migration.md`).

Wir wollen:

1. In der e2e-Pipeline eine **explizite, pimmierte sbx-Version** verwenden
   (Startpunkt: `v0.38.0`).
2. **Renovate** aktualisiert diese Pin automatisch, sobald eine neuere
   `docker/sbx-releases`-Version erscheint (Dependency-Update-PR).

## Hintergrund / Ursache des aktuellen Failures

- `e2e.yml` löst `.../releases/latest` unter `Download sbx (latest release)`
  dynamisch auf → beim nightly cron kommt automatisch jede neue Version rein.
- Mit v0.38.0 bricht das `claude`-Szenario (`MODEL=null`), weil die
  Kit-Referenz `files/home/.claude/settings.kit.json` (Merge) nicht greift —
  der Fix dafür ist separat (siehe Commit-Beschreibung dieses Branches).
- Ziel: Test-Version deterministisch pinnen, Renovate managed den Bump.

## Schritte

### 1. sbx-Version als variable/konstant initiert im Workflow

In `.github/workflows/e2e.yml` Schritt `Download sbx`:

- `VERSION` nicht mehr via `releases/latest`/ curl auflösen, sondern als
  feste Variable im Step definieren (Erklärung unten):

  ```yaml
  - name: Download sbx
    env:
      SBX_VERSION: v0.38.0
    run: |
      set -euo pipefail
      curl -fsSL \
        -H "Authorization: Bearer ${GITHUB_TOKEN}" \
        "https://github.com/docker/sbx-releases/releases/download/${SBX_VERSION}/DockerSandboxes-linux.tar.gz" \
        -o /tmp/DockerSandboxes-linux.tar.gz
      tar xzf /tmp/DockerSandboxes-linux.tar.gz -C /tmp
      echo "using sbx ${SBX_VERSION}"
    ```

  Hinweis: `env` auf Step-Ebene ist der einfachste Renovate-greppbare Ort.
  Alternativ eine dedizierte Versionsdatei/-Zeile im Repo, falls die Version
  an mehreren Stellen gebraucht wird (derzeit nur im Workflow).

### 2. Renovate-Regex-Manager für `docker/sbx-releases`

In `.github/renovate.json` `customManagers` List hinzufügen — analog zu den
bestehenden `spec.yaml`-Regex-Managers:

```json
{
  "customType": "regex",
  "description": "sbx CLI version (.github/workflows/e2e.yml)",
  "managerFilePatterns": [".github/workflows/e2e.yml"],
  "matchStrings": [
    "SBX_VERSION: (?<currentValue>[0-9]+\\.[0-9]+\\.[0-9]+)"
  ],
  "depNameTemplate": "docker/sbx-releases",
  "datasourceTemplate": "github-releases",
  "extractVersionTemplate": "^v(?<version>.*)$"
}
```

Hinweise:
- `extractVersionTemplate: "^v(?<version>.*)$"` — die Release-Tags heißen
  `v0.38.0`, gespeichert wird `0.38.0`. Konsistent mit den bestehenden
  `DOCKER_VER`/`COMPOSE_VER`/`HELM_VER`-Regeln.
- `matchStrings` muss die tatsächlich gewählte Syntax treffen. Falls die
  Version als Step-`env`-Block (`SBX_VERSION: v0.38.0`) steht, ggf. das `v`
  mitmatchen: `SBX_VERSION: v?(?<currentValue>[0-9]+\\.[0-9]+\\.[0-9]+)`.

### 3. Doku aktualisieren

- `AGENTS.md` / `README.md`: Erwähnen, dass die e2e-Pipeline eine gepinnte
  sbx-Version nutzt und Renovate sie verwaltet (statt "latest").

### 4. Validieren + verifizieren

- `.github/renovate.json` mit `renovate-config-validator` prüfen (siehe Kit
  AGENTS.md):
  ```bash
  renovate-config-validator .github/renovate.json
  ```
- e2e-Workflow-Noop: Push auf den Branch, Workflow-übersicht prüfen, dass
  `Verify sbx installation` jetzt `sbx version: v0.38.0` anzeigt (statt latest).
- Optional: lokal testen welchen Tag Renovate erkennt (Dry-Run) — siehe
  unten Fehlersuche / Verification.

## Akzeptanzkriterien

- [ ] `e2e.yml`: sbx-Download nutzt `SBX_VERSION` (kein `latest`).
- [ ] `SBX_VERSION` initial auf `v0.38.0`.
- [ ] `renovate.json`: customManager für `docker/sbx-releases`
      (`github-releases` datasource, `^v` extract).
- [ ] `renovate-config-validator` läuft sauber.
- [ ] e2e-Lauf loggt `using sbx v0.38.0` und `sbx version: v0.38.0`.
- [ ] Ein zukünftiges sbx-Release erzeugt einen Renovate-Update-PR.

## Offene Punkte / Risiken

- **Renovate-Datensource-Pfad**: `github-releases` auf
  `docker/sbx-releases` muss funktionieren (Tag-Format `v0.38.0` + dist
  `DockerSandboxes-linux.tar.gz`). Falls das Asset-Namen-Format variiert,
  kann zusätzlich ein `replacement`/Asset-Match nötig sein.
- **Version in mehreren Dateien**: Sollte `sbx` später zusätzlich in
  `spec.yaml` (Kit) oder lokal-punkt aktiv referenziert werden, dort einen
  `depName`/`matchGlob` übergreifenden RegexManager ergänzen und diese
  Doku-Anpassung erweitern.
- **Pre-Release-Strategie**: Tags wie `v0.38.0-rc1` werden von Renovate ohne
  `allowedVersions` nicht als Update-Kandidat gezogen. Falls Pre-Releases in
  Zukunft relevant, `matchUpdateTypes`/`prCreation` anpassen.
- **Workflow-Hardwiring**: Die hat derzeit genau einen Downloadort; falls
  `sbx` sich zukünftig in zwei Untersссии à la "sbx core + installers" teilt,
  muss $SBX_VERSION-Tupel angelegt werden.

## Quellen

- sbx releases: https://github.com/docker/sbx-releases/releases
- Renovate customRegexManager doc:
  https://docs.renovatebot.com/configuration-options/#custommanagers
- Renovate regex manager Beispiele (ctx7 `/renovatebot/renovate`).