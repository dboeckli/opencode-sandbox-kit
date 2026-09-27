# Migration nach Codeberg (Issue #114)

Arbeits-/Entscheidungsdokument für den Umzug des Kits nach Codeberg (Forgejo).
Kanonische Quelle bleibt vorerst das GitHub-Repo; **GitHub läuft als Mirror weiter**.

## Entscheidungen

- **GitHub-Rolle:** als **Mirror** behalten → bestehende Kit-Referenzen
  (`git+https://github.com/dboeckli/opencode-sandbox-kit.git#dir=…`) in allen onboardeten
  Projekten bleiben gültig; keine Cross-Repo-Massenänderung nötig.
- **Codeberg-Ziel:** `codeberg.org/dboeckli/opencode-sandbox-kit` (User `dboeckli`).
- **CI-Ziel:** voller Forgejo-Actions-Umzug (Option 3) — **Machbarkeit noch zu beweisen**.
- **Netzwerk:** `codeberg.org` + `*.codeberg.org` in `permissions.network.allow` und den
  `network-policy.md` der Kits ergänzt (dieser Branch).

## Arbeitsteilung

**Agent (im Repo, dieser Branch):**
- Netzwerk-Allowlist + Doku (`codeberg.org`).
- `.forgejo/workflows/validate.yml` (Port von `validate.yml`).
- Porting-Regeln/Doku (dieses Dokument).
- Weitere Workflow-Ports (`build-and-publish-*`, `e2e`) nach Runner-Klärung.

**Host/User (Codeberg-UI, nicht aus der Sandbox erreichbar — `codeberg.org` ist blocked):**
- Codeberg-Konto/Repo anlegen.
- **„Migrate repository"** (Host GitHub): Repo + Issues/Labels/Milestones/Releases/Wiki.
- Secrets setzen (siehe unten), Forgejo-Runner bereitstellen.
- GitHub-Repo als Mirror konfigurieren (Mirror-Push von Codeberg nach GitHub oder
  GitHub-Repo auf „mirror" belassen).

## Forgejo Actions — bekannte Unterschiede

| GitHub Actions | Forgejo Actions |
|----------------|-----------------|
| `.github/workflows/` | `.forgejo/workflows/` (auch `.gitea/workflows/`) |
| `runs-on: ubuntu-latest` | Runner-Label des Forgejo-Runners (z. B. `docker`, `host`, custom) — `ubuntu-latest` existiert nicht |
| Default-Image Ubuntu | Default-Image **Debian bookworm** (Tools ggf. per `apt-get` nachinstallieren) |
| `actions/checkout@v7` | `https://code.forgejo.org/actions/checkout@v6` (o. ä. Mirror) |
| `${{ github.* }}` | `${{ forgejo.* }}` (Gitea-Kompatibilität: `github.*` teils vorhanden) |
| `${{ secrets.GITHUB_TOKEN }}` | Auto-Token gilt nur für Codeberg; für GitHub-Zugriffe eigenes Secret nötig |
| `permissions:` | **ignoriert** |
| `continue-on-error:` | **ignoriert** |
| reusable `workflow_call` | unterstützt, aber Runner/Bedarf prüfen |
| `schedule` (cron) | unterstützt (cron) |

## Runner-Anforderungen

- **`validate`** (nur sbx-Download + `sbx kit validate` + Text-Checks): braucht nur `curl`,
  `tar`, `sudo`. Läuft grundsätzlich auf einem **Shared-Runner** (Label `docker`) — Proof offen.
- **`build-and-publish-*-image`** (multi-arch amd64+arm64, buildx, `imagetools`, Provenance/SBOM):
  braucht Docker + Buildx + Docker-Hub-Login. Auf Shared-Runnern i. d. R. nicht verfügbar →
  **self-hosted Runner** mit Docker. Alternativ auf GitHub verbleiben (Mirror).
- **`e2e`** (startet echte `sbx`-Sandboxes): braucht **Docker** + **KVM** (`/dev/kvm`,
  `kernel.apparmor_restrict_unprivileged_userns=0`) + das Secret-Service-Setup
  (gnome-keyring/dbus) für `sbx login`. Läuft nur auf einem **self-hosted Runner**.

Empfehlung: ein self-hosted Forgejo-Runner mit Docker + KVM deckt `validate`, `build-and-publish`
und `e2e` ab. Machbarkeit (KVM in Forgejo-Jobs, nested virtualization) **muss zuerst bewiesen werden**.

## Secrets auf Codeberg

- `DOCKER_USERNAME` (Variable) + `DOCKER_PAT` (Secret): Docker-Hub-Push/Pull (build-and-publish + e2e).
- `GITHUB_TOKEN`/`SBX_RELEASES_TOKEN`: nur falls der sbx-Release-Download ein Token braucht
  (öffentlicher Release → optional).
- Test-Secrets für e2e (fake): `anthropic`, `mammouth`, `mistral`, `zai`, `context7`,
  `openrouter`, `google`, `stackoverflow`, `cloudsmith`, `sonarcloud`, `github-maven`
  (siehe `.github/workflows/e2e.yml`).
- Registry-Credential `docker.io` (siehe e2e-Auth-Step).

## Konsumenten des Kits

Da GitHub Mirror bleibt, sind **keine** Änderungen in den onboardeten Projekten nötig.
Optional/langfristig: `sbx settings set kit.allowedSources` um Codeberg-Host ergänzen und
Kit-Referenzen auf Codeberg umstellen
(`git+https://codeberg.org/dboeckli/opencode-sandbox-kit.git#dir=opencode-agent`).

## Offene Punkte / Risiken

- **Renovate auf Codeberg/Forgejo:** Support/Betrieb unklar. Solange GitHub-Mirror existiert,
  kann Renovate dort weiterlaufen; alternativ manuelle Version-Pflege.
- **Releases/Tags:** Migration übernimmt Releases, sofern vorhanden. Kit-Pins (`SBX_VERSION`,
  `TEMPLATE_VERSION`) sind Renovate-managed.
- **Shared-Runner + `docker`-Label** auf Codeberg: Labels/Verfügbarkeit verifizieren.
- **KVM im Forgejo-Job:** zentrale Machbarkeitsfrage für e2e.
- **GitHub-Packages-Maven / `gh` / sbx-CLI / Docker Hub** bleiben externe GitHub-/Drittdienste.

## Checkliste (aus #114)

- [x] Netzwerk-Allowlist + Doku (`codeberg.org`) — dieser Branch
- [x] `.forgejo/workflows/validate.yml` (Erstport)
- [ ] Codeberg-Konto/Repo + Migration (Host)
- [ ] `.forgejo/workflows/` für `build-and-publish-*` + `e2e`
- [ ] Runner (Docker + KVM) bereitstellen + Machbarkeit beweisen
- [ ] Secrets auf Codeberg setzen
- [ ] GitHub-Repo als Mirror konfigurieren
- [ ] README-Badges/Links auf Codeberg
- [ ] „Mindestens ein Projekt zieht das Kit von Codeberg" verifizieren
