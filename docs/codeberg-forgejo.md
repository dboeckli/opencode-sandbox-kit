# Codeberg (Forgejo) — Betriebshinweise

Codeberg (`codeberg.org/dboeckli/opencode-sandbox-kit`) ist die kanonische Quelle; GitHub ist ein
Push-Mirror. Dieses Dokument sammelt die weiterhin relevanten Codeberg-/Forgejo-Betriebsdetails
(Netzwerk, Actions/Workflows, Runner, Variablen/Secrets, Renovate).

## Sandbox erreicht Codeberg

- `codeberg.org` ist in der Network-Allowlist (PR #143).
- Der Sandbox-Proxy injiziert den Codeberg-Token **unabhängig vom gesendeten Auth-Header** —
  jeder Request an `codeberg.org` wird als Token-Owner authentifiziert. Damit funktionieren
  **Git-Read und Git-Push** aus der Sandbox (verifiziert: `git ls-remote` + Push-Dry-Run).
  Git über HTTPS nutzt zwar Basic-Auth, der Proxy überschreibt den `Authorization`-Header
  jedoch mit `token <codeberg-pat>`.

## Forgejo Actions — Unterschiede (verifiziert)

| GitHub Actions | Forgejo Actions |
|----------------|-----------------|
| `.github/workflows/` | `.forgejo/workflows/` (auch `.gitea/workflows/`) |
| `runs-on: ubuntu-latest` | Runner-Label (Codebergs gehostet: `codeberg-tiny/small/medium[-lazy]`; sonst `host`/custom) — `ubuntu-latest` existiert nicht |
| Default-Image Ubuntu | Default-Image **Debian bookworm** (Tools via `apt-get` nachinstallieren) |
| `actions/checkout@v7` | fully-qualified `https://code.forgejo.org/actions/checkout@v6` empfohlen |
| `${{ github.* }}` | `github`-Context ist **identisch** zum `forgejo`-Context (`forgejo.*`) |
| `${{ secrets.GITHUB_TOKEN }}` | `${{ forgejo.token }}` / `${{ github.token }}` (Auto-Token für Codeberg) |
| `$GITHUB_OUTPUT`/`_ENV`/`_PATH` | gleichwertig (`$FORGEJO_*`; `GITHUB_*` als Alias vorhanden) |
| `permissions:` | **ignoriert** (weggelassen) |
| `continue-on-error:` (Job-Ebene) | **ignoriert** (Step-Ebene unterstützt) |
| reusable `workflow_call` | unterstützt; `secrets: inherit` unterstützt; lokaler Pfad `./.forgejo/workflows/x.yml` |
| `schedule` (cron) | unterstützt (UTC; optional `timezone`) |

- **`DEFAULT_ACTIONS_URL`** ist per Default `https://data.forgejo.org` (nicht `code.forgejo.org`);
  fully-qualified URLs vermeiden Mehrdeutigkeit.
- **`vars`** ist u. a. in `runs-on` und `strategy` verfügbar (`${{ vars.X || 'default' }}`).

## Workflows (`.forgejo/workflows/`)

- `validate.yml` — Kit-Validierung + Sync-/Pin-Checks; **nur `workflow_dispatch`** (manuell).
  Runner: `${{ vars.RUNNER_LABEL || 'codeberg-small' }}` (Codebergs gehosteter Runner).

Sonst **keine** Forgejo-Pipelines: `e2e`, `build-and-publish-*` und `cleanup-cloudsmith` existieren
nur unter `.github/workflows/` und laufen auf **GitHub-Runnern** (Status wird an Codeberg gemeldet).

## Runner-Anforderungen + Repo-Variablen

Codeberg **hostet** Forgejo-Actions-Runner (Open Alpha, kostenlos, public+FLOSS):
Labels `codeberg-tiny` (1 CPU/2G/2 min, **Kapazität 3**), `codeberg-small`
(2/4/5 min, **Kapazität 2**), `codeberg-medium` (4/8/10 min, **Kapazität 1**) +
`-lazy`-Varianten; Default-Image `ghcr.io/catthehacker/ubuntu:act-latest`
(GitHub-kompatibel, mit `sudo`/`apt`). Achtung: `codeberg-medium` hat nur Kapazität 1 →
Jobs hängen oft stundenlang (Codeberg/Community#2849) → `codeberg-tiny`/`-small` bevorzugen.
Weitere Grenzen: kein Docker-Daemon (Image-Builds nur podman/buildah), nur amd64, knappe Zeitlimits.

Runner-Labels sind über Repo-**Variablen** konfigurierbar (Defaults in Klammern):

| Variable | Default | Verwendung |
|----------|---------|------------|
| `RUNNER_LABEL` | `codeberg-small` | validate, cleanup, build prepare/merge, amd64-Build |
| `RUNNER_ARM64` | `arm64` | arm64-Build (nativer arm64-Runner) |
| `RUNNER_E2E` | `self-hosted` | e2e-Szenarien (Host-Modus) |

- **`validate`/`cleanup`:** laufen auf Codebergs gehostetem Runner (`codeberg-medium`)
  ohne self-hosted Runner.
- **`build-and-publish-*`:** Docker + Buildx + arm64 **nativ** (kein QEMU) → auf Codebergs
  gehostetem Runner **nicht** möglich (kein Docker-Daemon) → vorerst self-hosted oder GitHub.
- **`e2e`:** **Docker + KVM** (`/dev/kvm`, `kernel.apparmor_restrict_unprivileged_userns=0`)
  + Secret-Service (gnome-keyring/dbus) → nur self-hosted oder vorerst GitHub.

## Secrets/Variablen auf Codeberg

- **Variablen:** `DOCKER_USERNAME`, `IMAGE_PREFIX` (Default `docker.io/domboeckli`),
  `CLOUDSMITH_USERNAME` (nur Cloudsmith-Modus),
  optional `RUNNER_LABEL`/`RUNNER_ARM64`/`RUNNER_E2E`.
- **Secrets:** `DOCKER_PAT`, `CLOUDSMITH_API_KEY` (nur Cloudsmith-Modus); optional `GH_TOKEN` (echtes GitHub-PAT, damit der
  `gh auth status`-Check im e2e scharf läuft — ohne GH_TOKEN wird ein Fake genutzt und der Check im
  `--ci`-Modus übersprungen). Die Kit-e2e-Fake-Secrets werden im Workflow selbst gesetzt.

## Dependency-Updates (Renovate)

- **Dependabot entfernt** (GitHub-only, unvereinbar mit dem `--mirror`-Push).
- **Renovate self-hosted:** `.github/workflows/renovate.yml` läuft auf **GitHub-Runnern**, aber mit
  `RENOVATE_PLATFORM=forgejo` + `RENOVATE_ENDPOINT=https://codeberg.org` → Renovate legt seine
  Update-PRs auf **Codeberg** an. Der GitHub-Runner ist nur die Ausführungsmaschine.
- Config: `.github/renovate.json` — `github-actions`-Manager aktiviert (ersetzt Dependabot);
  die Pin-Manager (SBX_VERSION/TEMPLATE_VERSION) decken `.github/workflows/` **und**
  `.forgejo/workflows/` ab. Der `github-actions`-Manager erkennt auch `.forgejo/workflows/`
  (inkl. `https://code.forgejo.org/...`-URLs).
- Nötige Secrets (GitHub): `CODEBERG_FOR_RENOVATE_TOKEN` = Codeberg-PAT mit `write:repository` (+ `write:issue`)
  sowie `RENOVATE_GITHUB_TOKEN` = GitHub-PAT (public read, keine Scopes nötig) für die `github-releases`-Datasources.
  Ohne GitHub-Token überspringt Renovate alle GitHub-Dependencies (`docker/sbx-releases`, `helm/helm`, …) und das
  Dependency Dashboard #7 (unser lesbarer Report) bleibt unvollständig.
- Die GitHub-**Renovate-App muss deinstalliert** werden (sonst erzeugt sie GitHub-PRs, die der
  `--mirror`-Push löscht).

## Offene Punkte / Risiken

- **`local-test/local-test-kits.py` liest Pins aus `.github/workflows/`** (`SBX_VERSION`,
  `TEMPLATE_VERSION`). Solange `.github/workflows/` (Mirror) existiert, passt das; bei einem
  Entfernen der GitHub-Workflows muss das Skript auf `.forgejo/workflows/` umgestellt werden.
- **Doppelte CI:** Solange die GitHub-Workflows bestehen und GitHub Actions aktiv sind, laufen
  Pushes (via Mirror) auch dort. Empfehlung: GitHub Actions stilllegen, sobald Codeberg grün ist.
- **Mirror vs. GitHub-Bots:** Der `--mirror`-Push löscht GitHub-Refs, die auf Codeberg fehlen —
  GitHub-Bots (Dependabot/Renovate-App) und GitHub-only Tags/Releases sind damit unvereinbar.
  Daher Renovate self-hosted gegen Codeberg; **Releases/Tags auf Codeberg anlegen**.
- **Multi-Arch ohne arm64-Runner:** dann arm64-Matrix-Eintrag/Label entfernen (amd64-only).
- **e2e-KVM:** zentrale Machbarkeitsfrage; ggf. e2e vorerst auf GitHub belassen.
- **GitHub-Packages-Maven / `gh` / sbx-CLI-Download / Docker Hub**: bleiben externe GitHub-/Drittdienste.

> **Aktueller Stand (Übergang):** CI läuft auf **GitHub** (via Push-Mirror). Alle
> `.forgejo/workflows` sind vorerst auf **`workflow_dispatch`** (kein Auto-Trigger), damit die
> Codeberg-Runner-Queue nicht bei jedem Push hängt. Aktivierung nach Klärung des Runner-Themas.
