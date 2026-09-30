# Migration nach Codeberg (Issue #114)

Arbeits-/Entscheidungsdokument für den Umzug des Kits nach Codeberg (Forgejo).

## Entscheidungen

- **Codeberg ist kanonisch:** `codeberg.org/dboeckli/opencode-sandbox-kit` ist die
  **Schreib-Quelle** (`origin`).
- **GitHub ist Mirror:** das GitHub-Repo bleibt als **Push-Mirror** bestehen → die
  bestehenden Kit-Referenzen (`git+https://github.com/dboeckli/opencode-sandbox-kit.git#dir=…`)
  in allen onboardeten Projekten bleiben gültig; keine Cross-Repo-Massenänderung nötig.
- **CI:** voller Forgejo-Actions-Umzug. `validate`/`cleanup` sind portiert; `build-and-publish-*`
  und `e2e` ebenfalls (Runner-Verifikation offen).
- **Netzwerk:** `codeberg.org` + `*.codeberg.org` in `permissions.network.allow` und den
  `network-policy.md` der Kits (bereits gemerged, PR #143).

## Wichtig: Sandbox erreicht Codeberg (Korrektur)

Die frühere Annahme („Sandbox kann Codeberg nicht erreichen") ist **überholt**:

- `codeberg.org` ist in der Network-Allowlist (PR #143).
- Der Sandbox-Proxy injiziert den Codeberg-Token **unabhängig vom gesendeten Auth-Header** —
  jeder Request an `codeberg.org` wird als Token-Owner authentifiziert. Damit funktionieren
  **Git-Read und Git-Push** aus der Sandbox (verifiziert: `git ls-remote` + Push-Dry-Run).
  Git über HTTPS nutzt zwar Basic-Auth, der Proxy überschreibt den `Authorization`-Header
  jedoch mit `token <codeberg-pat>`.

Daraus folgt: Die frühere Begründung für „GitHub als Schreib-Target" entfällt; Codeberg ist
jetzt primär.

## Git-Remotes (lokal)

```
origin  https://codeberg.org/dboeckli/opencode-sandbox-kit.git   (kanonisch, push)
github  https://github.com/dboeckli/opencode-sandbox-kit.git     (Mirror, push)
```

Der Mirror wird **auf Codeberg** konfiguriert (Push-Mirror → GitHub). Per API ist das nur mit
dem **echten** GitHub-PAT möglich (`POST /repos/{owner}/{repo}/push_mirrors`, siehe
`CreatePushMirrorOption`: `remote_address`, `remote_username`, `remote_password`); in der
Sandbox liegt der GitHub-Token nur als Sentinel vor → **UI-Schritt** (oder API mit echtem PAT).

## Forgejo Actions — bekannte Unterschiede (verifiziert)

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

- **Variablen:** `DOCKER_USERNAME`, `CLOUDSMITH_USERNAME`, `CLOUDSMITH_NAMESPACE`, `CLOUDSMITH_REPO`,
  optional `RUNNER_LABEL`/`RUNNER_ARM64`/`RUNNER_E2E`.
- **Secrets:** `DOCKER_PAT`, `CLOUDSMITH_API_KEY`; optional `GH_TOKEN` (echtes GitHub-PAT, damit der
  `gh auth status`-Check im e2e scharf läuft — ohne GH_TOKEN wird ein Fake genutzt und der Check im
  `--ci`-Modus übersprungen). Die Kit-e2e-Fake-Secrets werden im Workflow selbst gesetzt.

## Host-Schritte auf Codeberg (konkret)

1. **Repo-Import:** erledigt (Migrate von GitHub; Issues/Labels/Milestones/Releases/Branches übernommen).
2. **Push-Mirror nach GitHub:** Repo → *Settings → Repository → Mirror Settings* → **Push-Mirror**
   auf `https://github.com/dboeckli/opencode-sandbox-kit.git` (Intervall z. B. 1 h) mit einem
   GitHub-PAT (`repo`-Scope). Alternativ API `POST /repos/dboeckli/opencode-sandbox-kit/push_mirrors`.
3. **Actions aktivieren:** Repo → *Settings → Actions* (Unit/Workflows) einschalten.
4. **Variablen/Secrets** setzen (siehe oben).
5. **Runner:** für `validate`/`cleanup` nichts zu tun — Codebergs gehosteter Runner
   (`codeberg-medium`) genügt. Nur für `build-and-publish-*` (Docker) und `e2e` (Docker+KVM)
   einen self-hosted Runner registrieren (oder diese vorerst auf GitHub lassen).
6. **Verifizieren:** `validate.yml` im Actions-Tab starten; danach Build-Workflow (build-only) und
   e2e.

## Dependency-Updates (Renovate)

- **Dependabot entfernt** (GitHub-only, unvereinbar mit dem `--mirror`-Push).
- **Renovate self-hosted:** `.github/workflows/renovate.yml` läuft auf **GitHub-Runnern**, aber mit
  `RENOVATE_PLATFORM=forgejo` + `RENOVATE_ENDPOINT=https://codeberg.org` → Renovate legt seine
  Update-PRs auf **Codeberg** an. Der GitHub-Runner ist nur die Ausführungsmaschine.
- Config: `.github/renovate.json` — `github-actions`-Manager wieder aktiviert (ersetzt Dependabot);
  die Pin-Manager (SBX_VERSION/TEMPLATE_VERSION) deckt jetzt `.github/workflows/` **und**
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

## Checkliste (aus #114)

- [x] Netzwerk-Allowlist + Doku (`codeberg.org`)
- [x] Codeberg-Konto/Repo + Import (Issues/Labels/Releases/Branches)
- [x] Git-Remotes: `origin` → Codeberg, `github` → Mirror-Remote
- [x] `.forgejo/workflows/` vollständig portiert (validate, cleanup, build-and-publish-*, e2e)
- [x] README-Badges/Links auf Codeberg
- [x] Push-Mirror Codeberg → GitHub (UI, `sync_on_commit=true`, interval `8h0m0s`)
- [x] Renovate self-hosted gegen Codeberg (`.github/workflows/renovate.yml` + `renovate.json`); Dependabot entfernt
- [~] Renovate-Aktivierung: GitHub-Secret `CODEBERG_FOR_RENOVATE_TOKEN` setzen + GitHub-Renovate-App deinstallieren (Host)
- [~] Actions aktiviert + Repo-Variablen gesetzt; Secrets (`DOCKER_PAT`, `CLOUDSMITH_API_KEY`) offen
- [ ] Codeberg-Runner/Queue klären (gehostete Runner hängen; `codeberg-*` überlastet)
- [ ] Codeberg-`validate` wieder auf `push`/`pull_request`/`schedule` stellen (aktuell nur `workflow_dispatch`)
- [ ] `build-and-publish`/`e2e` auf Codeberg (self-hosted Runner: Docker/arm64/KVM)
- [ ] CI-Pipeline (`validate` + `e2e`) läuft grün auf Codeberg
- [ ] GitHub Actions stilllegen (nach grünem Codeberg-CI)
- [ ] „Mindestens ein Projekt zieht das Kit von Codeberg" verifizieren

> **Aktueller Stand (Übergang):** CI läuft auf **GitHub** (via Push-Mirror). Alle
> `.forgejo/workflows` sind vorerst auf **`workflow_dispatch`** (kein Auto-Trigger), damit die
> Codeberg-Runner-Queue nicht bei jedem Push hängt. Aktivierung nach Klärung des Runner-Themas.
