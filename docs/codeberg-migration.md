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
| `runs-on: ubuntu-latest` | Runner-Label (z. B. `docker`, `host`, custom) — `ubuntu-latest` existiert nicht |
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

## Portierte Workflows (`.forgejo/workflows/`)

- `validate.yml` — Kit-Validierung + Sync-/Pin-Checks; Runner: `${{ vars.RUNNER_LABEL || 'docker' }}`.
- `cleanup-cloudsmith.yml` — Cloudsmith-Cleanup + Recycle-Bin-Purge (nightly/master-push/dispatch).
- `build-and-publish-{opencode,claude,mammouth,mistral-vibe}-image.yml` — Forgejo-nativ:
  **plain `docker`/`docker buildx`** statt der GitHub-JS-Actions (`setup-buildx`/`login`/`build-push`),
  fully-qualified Checkout, native Multi-Arch.
- `e2e.yml` — 4 Agent-Szenarien via `local-test/local-test-kits.py --ci`; ruft die Build-Workflows
  per `workflow_call`/`secrets: inherit` auf.

Die `.github/workflows/` bleiben vorerst bestehen (GitHub-Mirror); sie sind aber **nicht** mehr
die kanonische CI. Die Build-Ports lesen den Template-Pin aus `.forgejo/workflows/validate.yml`.

## Runner-Anforderungen + Repo-Variablen

Forgejo-Runner-Labels sind über Repo-**Variablen** konfigurierbar (Defaults in Klammern):

| Variable | Default | Verwendung |
|----------|---------|------------|
| `RUNNER_LABEL` | `docker` | validate, cleanup, build prepare/merge, amd64-Build |
| `RUNNER_ARM64` | `arm64` | arm64-Build (nativer arm64-Runner) |
| `RUNNER_E2E` | `self-hosted` | e2e-Szenarien (Host-Modus) |

- **`validate`/`cleanup`:** nur `curl`/`tar`/`python3` + Netz → Shared- oder Self-hosted-Runner.
- **`build-and-publish-*`:** Docker + Buildx + Docker-Hub/Cloudsmith-Login; arm64 **nativ**
  (kein QEMU — `uv tool install` scheitert unter QEMU-arm64).
- **`e2e`:** **Docker + KVM** (`/dev/kvm`, `kernel.apparmor_restrict_unprivileged_userns=0`) +
  Secret-Service-Setup (gnome-keyring/dbus) → **self-hosted Runner im Host-Modus**.
  Machbarkeit (KVM im Forgejo-Job, nested virtualization) ist noch zu beweisen.

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
5. **Runner** registrieren: Docker-fähig (Build) + arm64 (Multi-Arch) + Host/KVM (e2e);
   Labels passend zu den Variablen.
6. **Verifizieren:** `validate.yml` im Actions-Tab starten; danach Build-Workflow (build-only) und
   e2e.

## Offene Punkte / Risiken

- **`local-test/local-test-kits.py` liest Pins aus `.github/workflows/`** (`SBX_VERSION`,
  `TEMPLATE_VERSION`). Solange `.github/workflows/` (Mirror) existiert, passt das; bei einem
  Entfernen der GitHub-Workflows muss das Skript auf `.forgejo/workflows/` umgestellt werden.
- **Doppelte CI:** Solange die GitHub-Workflows bestehen und GitHub Actions aktiv sind, laufen
  Pushes (via Mirror) auch dort. Empfehlung: GitHub Actions stilllegen, sobald Codeberg grün ist.
- **Renovate auf Codeberg/Forgejo:** kein Hosted-Renovate. Optionen: self-hosted Renovate
  (Forgejo-Actions) oder manuelle Versionspflege; Übergangsweise auf GitHub belassen.
- **Multi-Arch ohne arm64-Runner:** dann arm64-Matrix-Eintrag/Label entfernen (amd64-only).
- **e2e-KVM:** zentrale Machbarkeitsfrage; ggf. e2e vorerst auf GitHub belassen.
- **GitHub-Packages-Maven / `gh` / sbx-CLI-Download / Docker Hub**: bleiben externe GitHub-/Drittdienste.

## Checkliste (aus #114)

- [x] Netzwerk-Allowlist + Doku (`codeberg.org`)
- [x] Codeberg-Konto/Repo + Import (Issues/Labels/Releases/Branches)
- [x] Git-Remotes: `origin` → Codeberg, `github` → Mirror-Remote
- [x] `.forgejo/workflows/` vollständig portiert (validate, cleanup, build-and-publish-*, e2e)
- [x] README-Badges/Links auf Codeberg
- [ ] Push-Mirror Codeberg → GitHub (Host/UI)
- [ ] Actions aktivieren + Variablen/Secrets setzen (Host)
- [ ] Runner (Docker/arm64/KVM) bereitstellen + Machbarkeit beweisen (Host)
- [ ] CI-Pipeline (`validate` + `e2e`) läuft grün auf Codeberg
- [ ] GitHub Actions stilllegen (nach grünem Codeberg-CI)
- [ ] „Mindestens ein Projekt zieht das Kit von Codeberg" verifizieren
