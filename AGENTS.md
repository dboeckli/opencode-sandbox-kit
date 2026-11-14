# opencode-sandbox-kit

Sandbox Kit (mixin) for OpenCode / Mammouth Code / Claude Code / Mistral Vibe / Pi with ctx7 and IntelliJ MCP; OpenCode v3 workload as migration pilot.
Repo: https://codeberg.org/dboeckli/opencode-sandbox-kit (kanonisch) — GitHub-Mirror: https://github.com/dboeckli/opencode-sandbox-kit

## Environment (wichtig!)

Der Agent läuft in einer **Docker-Sandbox** (MicroVM). Das Kit ist aber ein **Windows-Setup** — der Host
(IntelliJ MCP auf `localhost:64615`, Port 64615 seit IDEA 2026.2.2, Legacy 64342; in die Sandbox **nur** über den
sbx MCP Gateway, die direkten Host-Ports sind bewusst nicht allow-listed, Issue #163) läuft immer auf Windows:

- **Agent-Sandbox** (hier): Agent-Laufzeit — ich teste Linux-Tools (`ctx7`, `curl`, ...), Versions-Checks und Doku-Recherche. `sbx` ist hier **nicht** verfügbar (nicht im Sandbox-Image installiert).
- **Windows/PowerShell** (User, **Standard**): Alle Sandbox-Befehle (`sbx run`, `sbx exec`, `sbx template rm`, `sbx secret set`) führt der User in PowerShell aus — Docker Desktop läuft nativ auf Windows.
- **Ubuntu-WSL** (User, Alternative): Die Sandbox-Befehle laufen auch aus einem Ubuntu-WSL-Setup heraus (Laufzeitumgebung dort: **Ubuntu 26.04**) — inkl. Host-MCP-Zugriff über den sbx MCP Gateway (`host.docker.internal` für Docker) und der Secret-Injection. Der Host bleibt derselbe: IntelliJ auf Windows.
- Dokus (AGENTS.md/README) müssen **PowerShell-Syntax** verwenden.

## Diff-Review in IntelliJ (Pflicht)

Nach Änderungen **nur** den Diff als **Patch-Datei** in IntelliJ öffnen — die einzelnen geänderten Dateien
werden nicht mehr zusätzlich geöffnet (der MCP-Server hat kein Diff-Tool; `open_file_in_editor` auf eine
`.patch`-Datei liefert den Diff-View):

- Verzeichnis `target/review/` (liegt unter dem gitignorierten `target/`).
- `mkdir -p target/review && git diff <base> > target/review/changes.patch` (`<base>` z. B. `master...HEAD`, sonst `git diff`/`git diff HEAD`).
- Danach **nur** `target/review/changes.patch` mit `mcp-gateway_open_file_in_editor` öffnen.

## Git commits (Nachfragen-Pflicht)

Mache **niemals unaufgefordert Commits**: `git commit`, `git push`, PR-Erstellung und ähnliche Git-Operationen
nur mit expliziter Zustimmung des Users ausführen. Ansonsten Änderungen stehen lassen und am Ende den User fragen,
ob ein Commit erstellt werden soll.

## Feature Branches (Pflicht)

Bei **jeder Änderung** an diesem Repository immer **zuerst einen Feature Branch anlegen** (falls noch nicht
vorhanden), dessen Name mit `feature/` beginnt (z. B. `feature/mein-feature`). Direktes Committen auf `master`
ist nicht erlaubt. Nach Änderungen den Feature Branch committen/pushen und den User fragen, ob ein PR erstellt
werden soll.

### Kein Push auf `master`/`main` (Pflicht)

Der Agent pusht **niemals** direkt auf `master`/`main` — auch nicht, wenn zuvor allgemein Commits/Pushes
freigegeben wurden. Ausnahme ausschließlich: Der User verlangt den Push auf `master`/`main` **explizit** in
derselben Anweisung (z. B. „push auf master"). Standard ist immer der Feature Branch + Frage nach einem PR.
Der `.githooks/pre-push`-Hook blockt solche Pushes zusätzlich; ein Bypass (`git push --no-verify`) nur nach
ausdrücklicher User-Anweisung.

### Kein Push ohne vorherige Nachfrage (Pflicht)

Jeder `git push` — auch auf einen Feature Branch — erfolgt **nur nach vorheriger, expliziter Zustimmung** des
Users (pro Push, nicht pauschal für die Session). Nach dem Commit den User fragen, ob gepusht werden soll; ohne
Antwort kein Push. Force-Push und `git push --no-verify` sind ebenfalls zustimmungspflichtig.

**Vor jedem Push wird der Diff präsentiert**: Patch erzeugen (`mkdir -p target/review && git diff <base> > target/review/changes.patch`)
und mit `mcp-gateway_open_file_in_editor` in IntelliJ öffnen (bzw. `git diff` ausgeben). Erst nach Freigabe des
Diffs wird gepusht.

### Lokaler Schutz (pre-push-Hook)

Zusätzlich zum Server-seitigen Schutz blockiert der versionierte Hook `.githooks/pre-push` versehentliche
Pushes nach **GitHub** (read-only Mirror), direkte Pushes auf `master`/`main` **und** ausgehende Commit-Messages
mit Co-Authoring-/AI-Attribution-Trailern (`Co-authored-by:`, `Assisted-by:`, „Generated with …"-Footer, 🤖).
Einmalig pro Clone aktivieren:

```bash
git config core.hooksPath .githooks
```

### Co-Authoring/AI-Attribution entfernen (commit-msg-Hook)

Der versionierte Hook `.githooks/commit-msg` entfernt solche Trailer **beim Committen** (`.githooks` via
`core.hooksPath`). In der **Sandbox** wird derselbe Hook als **globaler** Hook für den `agent`-User installiert
(`~/.config/git/hooks/commit-msg` + `git config --global core.hooksPath`, via `install-tooling-user.sh`), damit
Agent-Commits in allen Repos bereinigt werden. Hinweis: ein globales `core.hooksPath` ersetzt die Hook-Suche,
d.h. repo-lokale `.git/hooks` werden in der Sandbox ignoriert (Repos mit eigenem `core.hooksPath` behalten ihre).

### Feature Branch mit GitHub-Issue (Zusatzregel)

Gehört zu einem Feature Branch ein GitHub-Issue, gilt zusätzlich:

- **Namenskonvention:** `feature/<issue-nummer>-<kurzer-text>` — Issue-Nummer direkt nach `feature/`, danach ein
  Dash, danach ein kurzer Text mit **maximal 4 Wörtern** (z. B. `feature/66-github-packages-maven`).
- **Verdrahtung:** Der Branch wird im Issue verlinkt (Feld „Development"/Linked Branches). Am saubersten legt man
  den Branch **direkt über die GitHub-GraphQL-Mutation `createLinkedBranch`** an (`issueId` + `oid` = Base-SHA +
  `name`) — sie erstellt und verlinkt den Branch in einem Schritt. Alternativ `gh issue develop <nummer> --name <branch>`.
  **Nicht** vorher per REST/Git anlegen: `createLinkedBranch` verknüpft nur frisch angelegte Branches, sonst
  schlägt die Verknüpfung fehl (`linkedBranch: null`).

## GitHub Actions: `action_required` — Build manuell freigeben (Pflicht)

Endet ein CI-Lauf nach Push/PR mit **`action_required`** (typisch: kein Job gestartet, PR-Status
„Expected — Waiting" bzw. `BLOCKED`), liegt das in der Regel an der **manuellen Freigabepflicht für
geänderte Pipelines** (`.github/workflows/*.yml` wurde im Branch/PR geändert). Den **Entwickler
darauf hinweisen, den Build im GitHub-UI manuell freizugeben** (Actions-Tab → Run → „Review" /
Approve) und die Freigabe abwarten. **Keine Workarounds** zur Umgehung der Freigabe: kein
Close/Reopen des PRs, kein Rerun über die API, kein Force-Push/Empty-Commit.

## Commands

- `python local-test/local-test-kits.py --validate-only` — validate all kits (v3 via kit builder); run it after every change and report the output as evidence before committing
- `sbx mcp add idea --url http://localhost:64615/stream --skip-ssrf-check` — einmalig (IntelliJ MCP auf dem Host registrieren; Voraussetzung für `--static-mcp idea`, siehe Abschnitt "IntelliJ MCP")
- `sbx mcp add k8s …` / `sbx mcp add docker …` — einmalig (host-seitigen Kubernetes- bzw. lokalen Docker-MCP-Server am sbx MCP Gateway registrieren; Voraussetzung für `--static-mcp …k8s…`/`…docker…`, siehe `docs/mcp/kubernetes-mcp-server.md` bzw. `docs/mcp/docker-mcp-server.md`)
- Test the OpenCode v3 workload (Kit-Spec v3, eigenes Image `docker.io/domboeckli/sbx-opencode`): Image bauen (Run-Config `build-and-publish-opencode-v3-image`, Tag `:local`) oder direkt aus dem Verzeichnis starten:
  ```powershell
  sbx run ./opencode-v3-agent/ `
      --skills=off `
      --static-mcp idea,k8s,docker
  ```
- Test the Claude Code v3 workload (Kit-Spec v3, eigenes Image `docker.io/domboeckli/sbx-claude`): Image bauen (Run-Config `build-and-publish-claude-v3-image`, Tag `:local`) oder direkt aus dem Verzeichnis starten:
  ```powershell
  sbx run ./claude-v3-agent/ `
      --skills=off `
      --static-mcp idea,k8s,docker
  ```
- Run the dedicated Mammouth agent kit (v3 workload, entrypoint `mammouth-entrypoint` — seedet die Model-Picker-Favoriten vor dem TUI-Start, dann `exec mammouth`; eigenes Image `docker.io/domboeckli/sbx-mammouth`, Tooling + CLI vorgebacken — kein `--template`). Für die lokale Entwicklung `:local` verwenden (vorher Run-Config `build-and-publish-mammouth-image`); Release via `build-and-publish-mammouth-image.yml` (`workflow_dispatch`/Push auf `master`):
  ```powershell
  sbx run docker.io/domboeckli/sbx-mammouth:local `
      --skills=off `
      --static-mcp idea,k8s,docker
  ```
- Run the dedicated Mistral Vibe agent kit (v3 workload; eigenes gepinntes Image `docker.io/domboeckli/sbx-mistral-vibe:<vibe-version>`, Descriptor + Dockerfile — kein `--template` nötig). Für die lokale Entwicklung `:local` verwenden (vorher Run-Config `build-and-publish-mistral-vibe-image`); Release-Image via `build-and-publish-mistral-vibe-image.yml` (`workflow_dispatch`/Push auf `master`):
  ```powershell
  sbx run docker.io/domboeckli/sbx-mistral-vibe:local `
      --skills=off `
      --static-mcp idea,k8s,docker
  ```
- Run the dedicated Pi agent kit (Kit-Spec v3, `kind: workload`; eigenes Image `docker.io/domboeckli/sbx-pi-agent:<pi-version>`, Descriptor + Dockerfile, Entrypoint `pi` — kein `--template`, kein `--kit-arg`). Für die lokale Entwicklung `:local` verwenden (vorher Run-Config `build-and-publish-pi-image`); Release-Image via `build-and-publish-pi-image.yml` (`workflow_dispatch`/Push auf `master`). Alternativ baut `sbx` direkt aus dem Verzeichnis:
  ```powershell
  sbx run ./pi-agent/ `
      --skills=off `
      --static-mcp idea,k8s,docker
  ```
- Run the OpenCode v3 workload from a published registry image:
  ```powershell
  sbx run docker.io/domboeckli/sbx-opencode:latest `
      --skills=off `
      --static-mcp idea,k8s,docker
  ```
- Use the kit with another project:
  ```powershell
  sbx run ./opencode-v3-agent/ `
      --skills=off `
      --static-mcp idea,k8s,docker `
      "C:\development\projects\spring-6-reactive"
  ```
- Kubernetes- + Host-Docker-Support + Maven-Host-Cache: Kubernetes über den host-seitigen Kubernetes-MCP-Server und Host-Docker über den lokalen Docker-MCP-Server (`--static-mcp idea,k8s,docker`, kein kubeconfig-Mount, kein offener `2375`-Port) und Host-Maven-Repo (read-only) mounten (kubectl/helm im Sandbox-Cluster; Maven nutzt den lokalen Cache, Issue #87):
  ```powershell
  sbx run ./opencode-v3-agent/ `
      --skills=off `
      --static-mcp idea,k8s,docker `
      . `
      "C:\development\maven-repo:ro"
  ```
- Kubernetes- + Host-Docker-Support (Claude Code v3):
  ```powershell
  sbx run ./claude-v3-agent/ `
      --skills=off `
      --static-mcp idea,k8s,docker `
      . `
      "C:\development\maven-repo:ro"
  ```
- Kubernetes- + Host-Docker-Support (Mammouth Code):
  ```powershell
  sbx run docker.io/domboeckli/sbx-mammouth:local `
      --skills=off `
      --static-mcp idea,k8s,docker `
      . `
      "C:\development\maven-repo:ro"
  ```
- Kubernetes- + Host-Docker-Support (Mistral Vibe):
  ```powershell
  sbx run docker.io/domboeckli/sbx-mistral-vibe:local `
      --skills=off `
      --static-mcp idea,k8s,docker `
      . `
      "C:\development\maven-repo:ro"
  ```
- `sbx settings set kit.allowedSources --% "[\"docker.io/\",\"github.com/dboeckli/\",\"codeberg.org/dboeckli/\"]"` — allow GitHub and Codeberg as kit source (required once before remote Git)
- `--skills=off` gehört in **jedes** `sbx run`/`sbx create`: der Host-Shared-Skills-Store wird nicht gemountet (Trust Boundary); die Kit-Skills kommen aus `dboeckli/ai-agent-skills`, nicht vom Host. Nur bei Sandbox-Erstellung wirksam — bestehende Sandbox neu erstellen. Doku: https://docs.docker.com/ai/sandboxes/workflows/agent-skills/
- ctx7 ist im Kit-Image eingebacken (`npm install -g ctx7` im Dockerfile); `npx ctx7 setup --opencode` konfiguriert nur ctx7 für OpenCode (nicht Teil des Kits)
- `npx ctx7 docs /docker/docs <query>` — sbx CLI / sandbox documentation (ctx7 library ID: `/docker/docs`; deckt Commands/Flags + Manuels ab — inkl. generierter CLI-Referenz `data/sbx_cli/*.yaml` —, indexiert aber den Docs-`main`-Branch statt unseres Pins; `/docker/sbx-releases` liefert nur Installation/Releases. Exakte `--help`-Dumps der gepinnten Version: `~/sbx-cli.md`)
- `python local-test/local-test-kits.py` — automate the 5 scenarios (OpenCode v3/Claude v3/Mammouth/Mistral Vibe/Pi): validate kits, check secrets, create sandboxes, run startup checks (**inkl. MCP-Client-Verdrahtung pro Sandbox**: `mcp-client` + `mcp-tools` via `MCP_CHECK_DEEP=1`), remove sandboxes (`--keep` to keep them)
- `python local-test/local-test-kits.py --ci` — CI mode (used by GitHub Actions `.github/workflows/e2e.yml`): fake API keys, no real mammouth/mistral API call (only proxy env wiring)
- `python local-test/local-test-kits.py --validate-only` — only `sbx kit validate` (all kits), no secrets check; v3 kits are always validated through the kit builder (also in full runs; `--skip-v3-builder` falls back to the offline probe for CI scenario runs) (`sbx kit validate ./<kit>/` without `--offline`, builder sandbox `sbx-kit-builder`; falls back to the offline probe with a warning when Docker/KVM is unavailable). No sandbox start (default is starting the sandboxes); includes the Stack Exchange + sbx CLI offline-doc update checks, the install-script sync check, die **Pin-Checks** (`OPENCODE_VERSION` [OpenCode-CLI, npm `opencode-ai`, 1.x] und `CLAUDE_VERSION` [Claude-CLI, npm `@anthropic-ai/claude-code`] in `local-test-kits.py` gegen `validate.yml`/`e2e.yml` + Dockerfile-Pins; Basis aller Custom-Workload-Kits = Docker-verwaltete `docker.io/sbx/shell-docker-image:latest`, Issue #254), den **Mammouth-CLI-Versions-Check** (Pin vs. latest GitHub-Release `mammouth-ai/code`), den **Mistral-Vibe-Versions-Check** (Dockerfile-Pin + spec-Image-Tag + gemeinsame Custom-Workload-Basis vs. latest PyPI `mistral-vibe`), den **Docker-MCP-Server-Versions-Check** (Pin Fork `dboeckli/mcp-server-docker@v<v>` in `docs/mcp/docker-mcp-server.md` vs. latest GitHub-Release des Forks, Issue #250), den **Bruno-CLI-Versions-Check** (Pin `@usebruno/cli@<v>` in allen vier Kit-Specs + Tooling-Dockerfiles, Drift-Check + latest npm), den **MCP-Inspector-Versions-Check** (`@modelcontextprotocol/inspector@<v>`, Issue #231, gleiches Muster), den **Pi-Versions-Check** (Descriptor/Dockerfile-Pin + gemeinsame Custom-Workload-Basis vs. latest npm `@earendil-works/pi-coding-agent`) und den **Node-Baseline-Check** (Issue #138: prüft per Docker best-effort die Node-Version der Basis `docker.io/sbx/shell-docker-image:latest`; warnt, sobald sie ≥ 24 sind → dann `install-tooling.sh node` + `nodejs.org`-Allowlist entfernen)
- `python local-test/regenerate-sbx-doc.py [<version>]` — regenerate `opencode-v3-agent/files/home/sbx-cli.md` (all `--help` outputs) from the pinned `docker/sbx-releases` release binary and sync all five kit copies (OpenCode v3/Claude v3/Mammouth/Mistral Vibe/Pi) (default: `SBX_VERSION` from `.github/workflows/validate.yml`; pass an explicit version like `v0.39.0` to override). `local-test-kits.py --validate-only` fails when the documented version diverges from the (Renovate-managed) pin and tells you to run this script
- GitHub Actions `.github/workflows/validate.yml` + `.github/workflows/e2e.yml` + `.github/workflows/build-and-publish-mistral-vibe-image.yml` + `.github/workflows/build-and-publish-opencode-v3-image.yml` + `.github/workflows/build-and-publish-claude-v3-image.yml` + `.github/workflows/build-and-publish-mammouth-image.yml` + `.github/workflows/build-and-publish-pi-image.yml` — install a **pinned sbx** (env `SBX_VERSION`, currently `v0.53.0`, mantained via Renovate customManager `docker/sbx-releases`); **Pins** (env `OPENCODE_VERSION`/`CLAUDE_VERSION` in beiden Workflows + explizite Konstanten in `local-test-kits.py`: `OPENCODE_VERSION` per npm-Datasource `opencode-ai` [1.x], `CLAUDE_VERSION` per npm `@anthropic-ai/claude-code`; Basis aller Custom-Workload-Kits ist die Docker-verwaltete `docker.io/sbx/shell-docker-image:latest`, Issue #254); e2e **und validate** signs in to Docker via `sbx login` (variable `DOCKER_USERNAME` + secret `DOCKER_PAT`; sbx >= v0.47.0 braucht eine Docker-Session für `sbx kit validate`, Secret-Service-Setup wie im e2e) and stores the Cloudsmith registry credential **only when `IMAGE_PREFIX` starts with `docker.cloudsmith.io`** (variable `CLOUDSMITH_USERNAME` + secret `CLOUDSMITH_API_KEY`; im Docker-Hub-Modus entfällt das Registry-Secret, `sbx login` genügt), registers fake sandbox secrets, runs `local-test-kits.py --ci`. **Registry zentral via Repo-Variable `IMAGE_PREFIX`** (Default `docker.io/domboeckli`; Cloudsmith `docker.cloudsmith.io/dboeckli/sbx`), gelesen von allen `build-and-publish-*-image.yml` + `e2e.yml` (`vars.IMAGE_PREFIX || 'docker.io/domboeckli'`). `build-and-publish-mistral-vibe-image.yml` baut/pusht das Vibe-Image; `build-and-publish-pi-image.yml` das Pi-v3-Image (multi-arch amd64+arm64 über native Runner `ubuntu-latest`/`ubuntu-24.04-arm`; Per-Arch-Image unter `<name>-amd64`/`<name>-arm64`, Merge zum Index unter `<name>` via `imagetools create`) — reusable (`workflow_call`), wird vom e2e vor der Matrix aufgerufen; zusätzlich manuell via `workflow_dispatch`. Tags: master `<pin>` + `latest`, Feature-Branch `<pin>-<branch-slug>.<timestamp>` (semver) + `<branch-slug>`; das e2e übergibt Tag + Registry je Kit (`--template`, Image-Ref für v3-Workloads, `--kit-arg` für Mistral Vibe)

- **Cleanup (Cloudsmith-only):** `.github/workflows/cleanup-cloudsmith.yml` löscht Feature-Branch-Image-Snapshots aus `dboeckli/sbx` (Tag-Muster `<basever>-<slug>.<YYYYMMDDHHMMSS>` + Moving-Tag `<slug>`; Master-Images `<basever>`/`latest` bleiben). Läuft nur im Cloudsmith-Modus (`IMAGE_PREFIX` startet mit `docker.cloudsmith.io`); im Docker-Hub-Modus übersprungen. Auslöser: **push auf `master`** (alle Feature-Images, da nach Merge obsolet), **nightly 04:25 UTC** (verwaiste Snapshot älter als `max-age-days`) und `workflow_dispatch` (`dry-run` Default an). Skript: `.github/workflows/scripts/cleanup-cloudsmith.py` (optional `SLUG`; child-aware: löscht auch untagged Orphans, die von keinem verbleibenden Index referenziert werden, fail-safe). Zusätzlich leert die Pipeline den **Recycle Bin** (hard delete, `purge-cloudsmith-recycle-bin.py`), da soft-gelöschte Packages 7 Tage weiter gegen das Storage-Kontingent zählen (`purge-recycle-bin`, Default an).

## Image-Versionierung (Agent-Images)

Betrifft `sbx-opencode`, `sbx-claude`, `sbx-mammouth`, `sbx-mistral-vibe` und `sbx-pi-agent`.
Basis-Version `<basever>`:
- **opencode-v3**: `OPENCODE_VERSION` (OpenCode-CLI, npm `opencode-ai`, bewusst 1.x) = `ARG OPENCODE_VERSION`; Basis `docker.io/sbx/shell-docker-image:latest@sha256:969457e4d3eb99b913985875dab829e41924e5435255356546ccefea56c5d6ea` (Digest-gepinnt; Renovate, Issue #254)
- **claude-v3**: `CLAUDE_VERSION` (Claude-CLI, npm `@anthropic-ai/claude-code`) = `ARG CLAUDE_VERSION`; Basis `docker.io/sbx/shell-docker-image:latest` (nightly, kein Semver-Pin, Issue #254)
- **mammouth**: die Mammouth-CLI-Version = `ARG MAMMOUTH_VERSION` im Dockerfile
- **mistral-vibe**: die Vibe-Version = `ARG VIBE_VERSION`
- **pi**: die Pi-Version = `ARG PI_VERSION`

`<slug>` = Branch-Name (lowercase, Nicht-Alphanumerisches → `-`); `<ts>` = UTC `YYYYMMDDHHMMSS`
(Semver-Prerelease, kein `+`). Identische Logik in `.github/workflows/build-and-publish-<name>-image.yml`
und `local-test/build-and-publish-<name>-image.py` (`<name>` = `opencode-v3`/`claude-v3`/`mammouth`/`mistral-vibe`/`pi`).

**Registry (zentraler Umschalter):** Alle Images liegen unter dem Prefix `IMAGE_PREFIX` (Registry + Namespace
[+ Repo] ohne Image-Namen; Image = `<IMAGE_PREFIX>/sbx-<name>:<tag>`). Default Docker Hub
`docker.io/domboeckli` (in CI über die Repo-Variable, lokal über Env/Run-Config gesetzt); Cloudsmith
`docker.cloudsmith.io/dboeckli/sbx` ist der Ausweich-Registry. Quelle: GitHub-Repo-Variable
`vars.IMAGE_PREFIX` (CI, Fallback im Workflow = Docker Hub), Env `IMAGE_PREFIX` (`local-test-kits.py` + `local-test/build-and-publish-*.py`),
`args.imagePrefix` (`mammouth-agent`/`mistral-vibe-agent` spec, via `--kit-arg imagePrefix=…`). Umschalten =
Repo-Variable/Env setzen; **zurück** = Default (Variable löschen). Der Cloudsmith-Login/-Registry-Secret sowie
`cleanup-cloudsmith.yml` greifen nur im Cloudsmith-Modus (`IMAGE_PREFIX` startet mit `docker.cloudsmith.io`).

**Wechsel nach Cloudsmith** (Details/Commands: README → „Registry umschalten → Nach Cloudsmith wechseln"):
erst Cloudsmith-Quote prüfen (`curl -H "X-Api-Key: $CLOUDSMITH_API_KEY" https://api.cloudsmith.io/v1/quota/oss/dboeckli/`
→ bandwidth `percentage_used` < 100, sonst `HTTP 402`), dann `IMAGE_PREFIX` (Repo-Variable/Env) explizit auf
`docker.cloudsmith.io/dboeckli/sbx` setzen, danach master-Publish zum Auffrischen der Cloudsmith-Images.

| Kontext | Auslöser | Tag(s) |
|---------|----------|--------|
| Lokal | Run-Config `build-and-publish-<name>-image` | `<basever>-<slug>.<ts>` + `:local` |
| CI – master/main | Push/Merge auf `master`, `workflow_dispatch` auf master | `<basever>` + `:latest` |
| CI – Feature-Branch | Push auf Branch, `workflow_dispatch` auf Branch | `<basever>-<slug>.<ts>` + `<slug>` |
| CI – PR (gleiches Repo) | `pull_request` | wie Feature-Branch (`GITHUB_HEAD_REF` = Quell-Branch) |
| CI – Fork-PR | `pull_request` aus Fork | kein Publish (keine Docker-Hub-Secrets → Job übersprungen) |

Verwendung:
- `:local` → `local-test-kits-{opencode-v3,claude-v3,mammouth,mistral-vibe,pi}` (Default von `OPENCODE_V3_IMAGE_TAG`,
  `CLAUDE_V3_IMAGE_TAG`, `MAMMOUTH_IMAGE_TAG`, `VIBE_IMAGE_TAG`, `PI_IMAGE_TAG`).
- Release-Tag `<basever>` bzw. Remote `:latest` (README/AGENTS-Startcommands, z. B. `…:1.19.5` für
  OpenCode v3 bzw. `…:0.10.0` für Claude v3/Mistral Vibe/Mammouth).
- e2e-Szenario (`<AGENT>_IMAGE_TAG`): auf `master`/`schedule` der Release-Tag `<basever>` (= `version_tag`-Output
  des Publish-Jobs), auf **Branches/PRs das publizierte Master-`:latest`** (Branch-Images werden nicht gepusht).
  Das frisch gebaute Branch-Image prüft stattdessen der Build-Job selbst auf den Pin (`load` +
  `docker run --entrypoint <tool> <img> --version` == Pin, nur `push: false`). Übergabe per
  Image-Ref `<IMAGE_PREFIX>/sbx-<name>:<tag>` (alle Kits sind v3-Workloads).

Eigenschaften:
- **Nicht inhaltsgebunden:** Der Tag hängt nur an `<basever>`. Tool-/CLI-Versionsbumps ändern ihn nicht —
  ein Master-Publish **überschreibt** `<basever>` und `:latest` (Tags sind nicht unveränderlich).
- Feature-/PR-Tags sind durch `<slug>.<ts>` eindeutig; der bewegliche `<slug>`-Tag zeigt auf den letzten
  Build des Branch. `:latest` gibt es nur auf master.
## Testing (lokale Verifikation per IntelliJ Run-Configs)

> **Wichtig:** In der Sandbox-Laufzeit ist `sbx` **nicht** verfügbar (nicht im Sandbox-Image installiert — unabhängig
> von WSL). Validierung und Sandbox-Tests laufen daher auf dem Windows-Host via PowerShell (Docker Desktop nativ) —
> der Agent erreicht sie über den IntelliJ MCP (`mcp-gateway_execute_run_configuration` bzw.
> `mcp__mcp-gateway__execute_run_configuration`) mit den Run-Configs in `.run/`.
> `idea_execute_run_configuration` (Legacy-Name der Direkt-Config) ist dabei nicht mehr relevant.
> Der Aufruf mit der Config **ohne** `waitForExit=false` timeout't nach 15 min, obwohl der Test
> (~8 min) evtl. noch läuft — dann Prozessstatus via `idea_execute_terminal_command` + `Get-Process python` prüfen.

IntelliJ Run-Configs (`.run/*.run.xml`; die `local-test-kits-*` rufen `local-test/local-test-kits.py` auf, die `build-and-publish-*-image`-Configs die jeweiligen Publish-Skripte):

| Config | PARAMETERS | Zweck |
|--------|-----------|-------|
| `local-test-kits-full` | *(leer)* | Alle 5 Szenarien (OpenCode v3/Claude v3/Mammouth/Mistral Vibe/Pi): validate + Secrets + Sandbox |
| `local-test-kits-validate-only` | `--validate-only` | Nur `sbx kit validate` (alle Kits; v3 via Kit-Builder), keine Sandbox |
| `local-test-kits-opencode-v3` | `opencode-v3` | Nur OpenCode-v3-Workload (Sandbox) |
| `local-test-kits-claude-v3` | `claude-v3` | Nur Claude-v3-Workload (Sandbox) |
| `local-test-kits-mammouth` | `mammouth` | Nur Mammouth-Szenario (Sandbox) |
| `local-test-kits-mistral-vibe` | `mistral-vibe` | Nur Mistral-Vibe-Szenario (Sandbox) |
| `local-test-kits-pi` | `pi` | Nur Pi-Szenario (v3-Workload, Sandbox) |
| `build-and-publish-pi-image` | — | Baut/pusht das Pi-v3-Image lokal (`local-test/build-and-publish-pi-image.py`, `buildx -f pi-agent/pi-agent.yaml`; Tag `<pi-version>-<branch-slug>.<timestamp>` + `local`, Log `target/build-and-publish-pi-image.log`); das `local-test-kits-pi`-Szenario testet danach `:local` bzw. baut das Verzeichnis |
| `build-and-publish-mistral-vibe-image` | — | Baut/pusht das Vibe-Image lokal (`local-test/build-and-publish-mistral-vibe-image.py`, Tag `<pin>-<branch-slug>.<timestamp>` + `local`); schreibt die Konsolen-Ausgabe (inkl. docker/buildx) zusätzlich nach `target/build-and-publish-mistral-vibe-image.log` (gitignored); `--build-only` baut ohne Push. Das lokale `local-test-kits-mistral-vibe`-Szenario testet danach den `:local`-Tag |
| `build-and-publish-mammouth-image` | — | Baut/pusht das Mammouth-Image lokal (`local-test/build-and-publish-mammouth-image.py`, Tag `<mammouth-version>-<branch-slug>.<timestamp>` + `local`, Log `target/build-and-publish-mammouth-image.log`); das `local-test-kits-mammouth`-Szenario nutzt danach `MAMMOUTH_IMAGE_TAG=local` (v3) |
| `build-and-publish-opencode-v3-image` | — | Baut/pusht das OpenCode-v3-Workload-Image lokal (`local-test/build-and-publish-opencode-v3-image.py`, Tag `<basever>-<branch-slug>.<timestamp>` + `local`, Log `target/build-and-publish-opencode-v3-image.log`); das `local-test-kits-opencode-v3`-Szenario nutzt `OPENCODE_V3_IMAGE_TAG=local` bzw. baut das Verzeichnis |
| `build-and-publish-claude-v3-image` | — | Baut/pusht das Claude-v3-Workload-Image lokal (`local-test/build-and-publish-claude-v3-image.py`, Tag `<basever>-<branch-slug>.<timestamp>` + `local`, Log `target/build-and-publish-claude-v3-image.log`); das `local-test-kits-claude-v3`-Szenario nutzt `CLAUDE_V3_IMAGE_TAG=local` bzw. baut das Verzeichnis |

Alle Configs nutzen dasselbe SDK (`~\AppData\Local\Microsoft\WindowsApps\python3.exe`), WORKING_DIRECTORY
`$PROJECT_DIR$` (Repo-Root = Sandbox-Workspace), `PYTHONUNBUFFERED=1`. Neue Config in `.run/` anlegen = nur eine XML-Datei mit passendem
`PARAMETERS`; IntelliJ erkennt sie (die `get_run_configurations`-Liste kann kurz veraltet sein — direkt per Namen starten
funktioniert trotzdem). Die `local-test-kits.py`-Läufe schreiben ihre gesamte Ausgabe zusätzlich nach
`target/local-test-kits-<agent>.log` (Tee, gitignored), analog zu den `build-and-publish-*.log`.

Die Sandbox-Szenarien mounten als Workspace den **Repo-Root** (`--workspace <pfad>` bzw.
`$WORKSPACE_DIR` übersteuert; kein Temp-Dir mehr — Default ist bewusst nicht das Aufrufverzeichnis).
Der Test startet den Agenten nicht und schreibt nichts ins Workspace.

Äquivalente PowerShell-Befehle:

```powershell
python local-test\local-test-kits.py --validate-only   # nur Validierung (v3 via Kit-Builder)
python local-test\local-test-kits.py opencode-v3       # nur OpenCode-v3-Workload
python local-test\local-test-kits.py claude-v3         # nur Claude-v3-Workload
python local-test\local-test-kits.py mammouth          # nur Mammouth-Sandbox
python local-test\local-test-kits.py mistral-vibe      # nur Mistral-Vibe-Sandbox
python local-test\local-test-kits.py                   # alle Szenarien
```

## IntelliJ MCP: Permission-Whitelist + Run-Config-Guard

Der IntelliJ-MCP-Server läuft auf dem Windows-Host und wird über den **sbx MCP Gateway** in die Sandbox geliefert
(dokumentierter Weg, Issue #57): einmalig `sbx mcp add idea --url http://localhost:64615/stream --skip-ssrf-check`
registrieren (SSRF-Guard blockt Loopback; `/stream` = Streamable HTTP, nicht `/sse`), dann beim Erzeugen
`--static-mcp idea` setzen (oder `sbx mcp load idea --sandbox` in laufende Sandbox). Die Agent-Configs enthalten
**keine** direkte `mcp.idea`-Konfiguration — die Gateway-Verbindung (`mcp-gateway`) legt `sbx` automatisch nur für
seine **unterstützten Agenten** an (OpenCode: `~/.config/opencode/opencode.json`, Claude Code: `~/.claude.json`).
**Mammouth** ist keine sbx-Integration und bringt den `mcp`-Block selbst mit
(`mammouth-agent/files/home/.config/mammouth/opencode.jsonc`, Issue #139), **Mistral Vibe** analog in
`~/.vibe/config.toml`. Tool-Präfixe:
`mcp-gateway_<tool>` (OpenCode/Mammouth) bzw. `mcp__mcp-gateway__<tool>` (Claude Code) — der frühere direkte
`idea_`/`mcp__idea__`-Prefix existiert nicht mehr.

**Kein direkter Host-Port in der Sandbox:** `host.docker.internal:64615`/`:64342` (und `localhost`/`127.0.0.1`)
stehen bewusst **nicht** in `permissions.network.allow` — der Proxy blockt sie mit HTTP 403. Sonst könnte jeder
Sandbox-Prozess per `curl` die `mcp-gateway_*`-Whitelist und den Run-Config-Guard umgehen (Issue #163). Der
Startup-Check prüft IntelliJ deshalb ausschließlich über den Gateway (`mcp-idea`), nicht per Direkt-Probe.

> **Restrisiko (Issue #229):** Der `mcp-gateway` selbst ist aus der Sandbox per `curl` erreichbar
> (`Authorization: Bearer proxy-managed`) und aggregiert die Tools aller Server. Whitelist und
> Run-Config-Guard wirken nur bei **Agenten-Tool-Aufrufen**, nicht bei direktem JSON-RPC — sie sind
> Guardrails, keine Sandbox-Grenze. K8s läuft mit `read_only=false`, Docker-MCP ist host-root-äquivalent.
> Die mitgelieferte MCP-Inspector-CLI (`mcp-inspector --cli`, Issue #231) ist genau so ein direkter
> JSON-RPC-Client — nützlich zum Debuggen, aber ebenfalls ein Weg an der Whitelist vorbei.

Der Zugriff auf die IntelliJ-MCP-Tools ist für **OpenCode v3, Claude Code v3,
Mammouth Code und Mistral Vibe (Agent-Kits)** per **Whitelist** eingeschränkt — Deny-by-Default, standardmäßig
nur lesende Operationen erlaubt (K8s-Schreib-/Exec-Tools bei OpenCode v3/Mammouth/Claude v3 per `ask` freigebbar, siehe unten).
Die Config liegt je Agent-Location vor:

- **OpenCode v3 / Mammouth** (OpenCode-Fork, nutzt dieselben `permission`-Regeln und Plugin-Hooks):
  `permission`-Block in `opencode-v3-agent/files/home/.config/opencode/opencode.jsonc` und
  `mammouth-agent/files/home/.config/mammouth/opencode.jsonc`: breites `"mcp-gateway_*": "deny"` zuerst, danach
  **K8s-`ask`-Gruppen** (Toolset-Präfixe `pods_*`/`resources_*`/`helm_*`/`kiali_*`/`vm_*`/`tekton_*`/`netobserv_*`/`kcp_*`)
  und schließlich gezielte `allow`-Regeln. **Reihenfolge zählt** — opencode wertet die letzte passende Rule aus
  (`findLast`), deshalb Deny → Ask → Allow: ein nicht explizit erlaubtes K8s-Schreib-/Exec-Tool (z. B.
  `pods_delete`, `helm_install`) löst einen interaktiven Prompt aus (On-the-fly-Freigabe pro Aufruf), die
  dokumentierten Read-only-Tools bleiben `allow`.
- **Claude Code v3**: `permissions`-Block in `claude-v3-agent/files/home/.claude/settings.json` (+ `settings.kit.json`).
  Kein Deny-by-Default wie bei OpenCode, sondern eine explizite `allow`-Whitelist (nur-lesende MCP-Tools als
  `mcp__mcp-gateway__<tool>`), eine `ask`-Liste (K8s-Schreib-/Exec-Tools, On-the-fly-Freigabe) und eine
  `deny`-Blocklist für die schreibenden/ausführenden IntelliJ-Tools. Das Profil ist auf
  `defaultMode: default` gesetzt (in `settings.kit.json` verankert; der `claude-entrypoint`-Merge sichert es vor
  dem CLI-Start) — **nicht** mehr `bypassPermissions`: nur so greift `permissions.ask`; dafür prompten
  jetzt auch nicht-gelistete Built-in-Tools (`Bash`/`Edit`/`Write`). Der Run-Config-Guard läuft als **PreToolUse-Hook** (siehe unten) statt als Plugin.
  Hooks + statusLine liegen **nicht** in der user-`settings.json`, sondern in der `managed-settings.json`
  unter `/etc/claude-code/` (im Image gebacken): höchste Precedence, wird vom Template nicht überschrieben —
  umgeht die Race Condition, bei der das Template die user-`settings.json` beim Start überschreibt (siehe
  `session-start-hook-fix.md`). Doppeltes Feuern wird vermieden, weil `claude-v3-agent/files/home/.claude/settings.json` und
  `settings.kit.json` bewusst **keine** `hooks`/`statusLine` mehr enthalten.
- **Pi**: `~/.pi/agent/extensions/mcp-guard.ts` (Pi-Extension, `tool_call`-Hook) erzwingt dieselbe
  Read-only-Whitelist + Run-Config-Guard; Pi hat kein `permission`-System, deshalb hart `deny` statt `ask`.
- **Mistral Vibe**: `~/.vibe/config.toml` verdrahtet den Gateway (`[[mcp_servers]]`, `transport = "streamable-http"`,
  `url = "http://mcp-gateway.docker.internal/mcp"`, static auth `Authorization: Bearer proxy-managed`) — Vibe ist
  kein unterstützter Template-Agent, das Kit bringt die Config selbst mit. Die Whitelist läuft als
  `pre_tool`-Hook (`~/.vibe/hooks.toml` → `~/.config/sandbox-kit/vibe-mcp-guard.py`), weil das Image Vibe mit
  `--agent auto-approve` startet (approvt alle Tool-Calls, umgeht das Permission-System). Der Hook matcht
  `mcp-gateway_*` und erlaubt dieselbe Read-only-Liste; `strict = true` (fail closed).
- **Erlaubt (nur lesend, OpenCode/Mammouth/Vibe-Pattern)**: `mcp-gateway_get_*`, `mcp-gateway_list_*`,
  `mcp-gateway_search_*`, `mcp-gateway_read*`, `mcp-gateway_generate_*`, `mcp-gateway_xdebug_get_*`,
  `mcp-gateway_xdebug_list_*` sowie einzeln `mcp-gateway_analyze_calls`, `mcp-gateway_git_status`,
  `mcp-gateway_lint_files`, `mcp-gateway_fetch_query_result`, `mcp-gateway_preview_table_data`,
  `mcp-gateway_test_database_connection`, `mcp-gateway_introspect_schema`, `mcp-gateway_run_inspection_kts`,
  `mcp-gateway_validate_inspection_kts`, `mcp-gateway_build_project` (kompiliert das Projekt im IntelliJ —
  bewusst erlaubt, ohne ask), `mcp-gateway_open_file_in_editor` (öffnet Dateien im IntelliJ-Editor —
  bewusst erlaubt, ohne ask) sowie die **K8s-Read-only-Tools** des host-seitigen Kubernetes-MCP-Servers
  (`docs/mcp/kubernetes-mcp-server.md`, Issue #40): `mcp-gateway_api_resources_list`,
  `mcp-gateway_events_list`, `mcp-gateway_helm_list`,
  `mcp-gateway_namespaces_list`, `mcp-gateway_nodes_log`, `mcp-gateway_nodes_stats_summary`,
  `mcp-gateway_nodes_top`, `mcp-gateway_pods_get`, `mcp-gateway_pods_list`,
  `mcp-gateway_pods_list_in_namespace`, `mcp-gateway_pods_log`, `mcp-gateway_pods_top`,
  `mcp-gateway_projects_list`, `mcp-gateway_resources_get`, `mcp-gateway_resources_list`
  (`configuration_view` bewusst gesperrt — würde die kubeconfig inkl. Client-Cert/Key in die Sandbox liefern)
  sowie die **Docker-MCP-Read-only-Tools** des lokalen Docker-MCP-Servers (`docs/mcp/docker-mcp-server.md`,
  Issue #165/#250): `mcp-gateway_list_containers`, `mcp-gateway_list_images`, `mcp-gateway_list_networks`,
  `mcp-gateway_list_volumes`, `mcp-gateway_fetch_container_logs`, `mcp-gateway_buildx_list`,
  `mcp-gateway_buildx_history`, `mcp-gateway_buildx_logs`.
  Der Server selbst läuft im **vollen Umfang** (`read_only = false`, Standard-Toolsets
  `core`/`config`/`helm`); diese Whitelist begrenzt den Agenten trotzdem. Die dokumentierten Read-only-Tools bleiben `allow`; alle übrigen
  K8s-/Docker-Write-Tools (`pods_delete`, `pods_exec`, `pods_run`, `resources_create_or_update`,
  `resources_delete`, `helm_install`, `vm_*`, `tekton_*`, `run_container`, `remove_container`,
  `build_image`, `create_volume`, …) sind bei OpenCode/Mammouth/Claude **`ask`** (On-the-fly-Freigabe pro Aufruf).
  `configuration_view` bleibt `deny`.
  Claude listet die erlaubten Tools einzeln als `mcp__mcp-gateway__<tool>` in `permissions.allow`, die
  K8s-Schreib-/Exec-Tools in `permissions.ask`.
  > **Produktions-No-Go:** `denied_resources` für `Secret` ist in der Host-Config bewusst deaktiviert
  > (sonst bricht das `helm`-Toolset — Helm speichert Releases als Secrets). Dadurch können
  > `resources_get`/`resources_list` **Cluster-Secrets inkl. `.data` lesen**. Nur für Entwicklungs-Cluster
  > (Docker Desktop): `docs/mcp/kubernetes-mcp-server.md#sicherheit-kurz`.
- **`ask`**: `mcp-gateway_execute_run_configuration` (Claude: `mcp__mcp-gateway__execute_run_configuration`) —
  braucht Bestätigung und wird zusätzlich durch den Run-Config-Guard auf `local-test-kits-validate-only` begrenzt.
- **On-the-fly-Freigabe (`ask`) bei OpenCode/Mammouth/Claude**: `ask` erzeugt einen interaktiven Prompt pro
  Tool-Aufruf (das Gegenstück zur URL-Allow-Schaltung im sbx-GUI). OpenCode/Mammouth via `permission`,
  Claude via `permissions.ask` + `defaultMode: default` (dadurch prompten auch nicht-gelistete Built-in-Tools
  wie `Bash`/`Edit`/`Write`). **Mistral Vibe** startet mit `--agent auto-approve`, dessen `pre_tool`-Hook nur
  `allow`/`deny` kennt (kein `ask`) — dort bleiben die K8s-Schreib-/Exec-Tools hart deny; On-the-fly ist bei
  Vibe nur durch Ändern des Approval-Modells möglich.
- **Versteckt (deny)**: alle schreibenden/ausführenden Tools (`apply_patch`, `execute_terminal_command`,
  `execute_tool`, `reformat_file`, `rename_refactoring`,
  Notebook-Schreibzugriffe, `xdebug_set_*`, `xdebug_run_to_line`,
  `xdebug_control_session`, `xdebug_start_debugger_session`, DB-Connection-Änderungen, ...) sowie die
  Gateway-Meta-Tools (`code-mode`, `mcp-exec`, `mcp-find`, `mcp-add`, `mcp-config-set`) — via `visibleTools()`
  nicht einmal sichtbar (OpenCode) bzw. in `permissions.deny` (Claude).

**Run-Config-Guard**: Das Permission-System sieht bei
MCP-Tools nie die Tool-Inputs (immer `resource: "*"`), daher ist `configurationName` nur im Hook sichtbar.
- OpenCode v3/Mammouth (`opencode-v3-agent/files/home/.config/opencode/plugins/intellij-run-config-guard.js` und
  `mammouth-agent/files/home/.config/mammouth/plugins/intellij-run-config-guard.js`): Plugin-Hook
  `tool.execute.before` auf Tool `mcp-gateway_execute_run_configuration`. Erlaubt dort ausschließlich die
  Run-Config `local-test-kits-validate-only` und blockt alle anderen mit einem Fehler.
- Claude Code v3 (`claude-v3-agent/files/home/.config/sandbox-kit/intellij-run-config-guard.sh`): PreToolUse-Hook gematcht auf
  `mcp__mcp-gateway__execute_run_configuration`. Liest `tool_input.configurationName` aus dem Hook-Payload; erlaubt
  `local-test-kits-validate-only` (exit 0 = pass), blockt alles andere (`permissionDecision: deny`, exit 2).
  Andere MCP-Tools passieren den Hook unverändert.
- Mistral Vibe (`mistral-vibe-agent/files/home/.config/sandbox-kit/vibe-mcp-guard.py`, verdrahtet über
  `~/.vibe/hooks.toml`): `pre_tool`-Hook gematcht auf `mcp-gateway_*`. Kombiniert Read-only-Whitelist und
  Run-Config-Guard: erlaubt die Read-only-Tools, `mcp-gateway_execute_run_configuration` nur für
  `local-test-kits-validate-only`, blockt alles andere.

> **Voraussetzung (Option A, self-contained-Bruch):** Ohne Host-Registrierung (`sbx mcp add idea …`) und ohne
> `--static-mcp idea`/`sbx mcp load` sind keine IntelliJ-MCP-Tools verfügbar. Das ist der dokumentierte
> Docker-Sandboxes-Weg (zentrale MCP-Registry am Host) und der Grund, warum das Kit keine direkte `mcp.idea`-
> Konfiguration mehr mitbringt. Details/Verifikation: Issue #57.

> **Model-Picker-Favoriten:** OpenCode hat keine Config für Gruppen/Reihenfolge — die Sektionen sind fest (Favorites → Recent → Provider). Das Kit seedet `~/.local/state/opencode/model.json` (Entrypoint + Image-Build), damit die direkt angebundenen Modelle als **Favorites** oben stehen (`ctrl+f` toggelt; bestehende Favoriten/Reihenfolge werden nicht überschrieben, per `ctrl+f` entfernte Seed-Modelle werden beim nächsten Start wieder ergänzt). Gilt für das `opencode-v3-agent`-Kit (`~/.local/state/opencode/model.json`) und das `mammouth-agent`-Kit (`~/.local/state/mammouth/model.json`; Mammouth ist ein OpenCode-Fork mit demselben `{recent,favorite,variant}`-Schema).
> **Reihenfolge (Mammouth):** `setup.startup` läuft **nach** dem Sandbox-Entrypoint — Mammouth liest `model.json` beim TUI-Start und schreibt den In-Memory-Stand (ohne die zu spät geseedeten Favoriten) beim ersten Model-/Variant-Wechsel zurück. Deshalb läuft der Seed beim Agent-Kit **im Entrypoint** (`mammouth-entrypoint` → `seed-mammouth-model-favorites.py`, idempotent, Fallback auf `mammouth` bei alten Images) und zusätzlich beim Image-Build; der `setup.startup`-Hook bleibt für bestehende Sandboxes. Ein nachträgliches Seeden bei laufendem TUI zeigt keine Favoriten — Mammouth neu starten.
>
> **Änderungen an `opencode.jsonc`/Plugins werden beim Start geladen (kein Hot-Reload)** — nach Anpassungen
> opencode/mammouth neu starten.

## GitHub Authentication

> **`sbx secret` (v0.38+):** Seit v0.38 ist das `-g`-Flag bei `sbx secret set` entfernt — Service-Secrets sind
> standardmäßig **global**, der Service ist ein Positionsargument (`sbx secret set github` statt
> `sbx secret set -g github`). Mit `--sandbox <name>` wird ein Secret auf eine Sandbox gescoped.
> Kit-deklarierte Services (context7, deepseek, openrouter, mammouth, github-maven) funktionieren identisch zu den Built-ins.
> **Neu:** Third-Party-v2-Kits benötigen pro Service ein **Credential-Binding** (`credentials.yaml`,
> Windows: `%APPDATA%\sbx\credentials.yaml`) — beim ersten Lauf interaktiv abgefragt, in CI vorab anlegen.

Für `gh` CLI in der Sandbox ein persönliches GitHub-Token (Name: `opencode-sandbox-kit-github-token`) erstellen und als Secret speichern:

```powershell
sbx secret set github -t "<github-token>"
```

Das Token wird via Proxy automatisch injiziert – `gh auth status` sollte in der Sandbox funktionieren.

### GitHub Packages Maven (`github-maven`)

Maven-Builds, die ein Artifact aus **GitHub Packages** (`maven.pkg.github.com`) auflösen, brauchen ein
**separates** klassisches PAT (nur Scope `read:packages`) — GitHub Packages akzeptiert kein OAuth-Token
(`gho_…`) und das `github`-Secret bleibt unverändert für `gh`/`git push`:

```powershell
# 1. Klassisches PAT mit Scope read:packages anlegen: https://github.com/settings/tokens
# 2. Secret registrieren
sbx secret set github-maven -t "<classic-pat-read-packages>"
```

In der Sandbox wirkt das Kit so (Lifecycle-Startup, `opencode-v3-agent/opencode-v3-agent.yaml`):
- `~/.m2/settings.xml` wird geschrieben mit einem `<proxies>`-Block (`gateway.docker.internal:3128` — Maven muss
  **durch den Sandbox-Proxy routen**, damit die Credential-Injection greifen kann) und dem Server `github`
  (`<password>${env.GITHUB_MAVEN_TOKEN}</password>`).
- Die Proxy-CA wird in die JDK-`cacerts` importiert (Java/Maven müssen das TLS-Intercept des Proxys vertrauen).
- Der Proxy injiziert den echten `ghp_…`-Token als `Authorization: Bearer <pat>` bei Requests an
  `maven.pkg.github.com` (GitHub Packages akzeptiert den klassischen PAT als Bearer; die `scheme: basic`-Injection
  des Proxys funktioniert nicht und wird nicht verwendet). Der Token liegt nie im Sandbox-Filesystem.
`gh auth status` zeigt weiterhin den vollen OAuth-Token des `github`-Secrets.

> **Wichtig:** Nur echte Maven-Builds (`./mvnw validate` etc.) sind repräsentativ — `mvn dependency:get` ignoriert
> settings-`<proxies>` und läuft an der Injection vorbei (401 ist dort ein Fehlalarm).


### Maven Host-Cache wiederverwenden (optional)

Jede Sandbox lädt Dependencies neu. Um den **lokal gefüllten** Maven-Cache des Hosts zu nutzen, den Host
`~/.m2/repository` **read-only** mounten (keine Credentials, nur Artefakte):

```powershell
sbx run ./opencode-v3-agent/ `
    --skills=off `
    --static-mcp idea,k8s,docker `
    . `
    "C:\development\maven-repo:ro"
```

Der Lifecycle-Startup erkennt den Mount (`/c/Users/<user>/.m2/repository`, `/c/*/maven-repo` oder `/c/*/m2-repository`) und ergänzt ein aktives Profil mit
`<repository id="host-cache" url="file://…">` (snapshots disabled). Maven prüft dann: Sandbox-lokal → Host-Cache
(`file://`, kopiert lokal statt Netz) → echte Remotes (Central/GitHub Packages). Ohne Mount bleibt settings.xml
unverändert. Neu geladene Artefakte landen nur im Sandbox-lokalen Repo; der Host-Cache bleibt read-only.

## Anthropic Authentication

Für Claude Code in der Sandbox wird der Anthropic API-Key als Secret gespeichert und vom Proxy verwaltet – der Key liegt nie im Sandbox-Filesystem:

```powershell
sbx secret set anthropic
```

Es wird davon ausgegangen, dass `ANTHROPIC_API_KEY` nicht als Env-Variable gesetzt ist – der Key wird interaktiv eingegeben. Falls bereits ein OAuth-Token existiert, wird nachgefragt – mit `-f` überschreiben:

```powershell
sbx secret set anthropic -f
```

In der Sandbox sollte `env | grep -i ANTHROPIC` leer sein, während API-Calls über den Proxy trotzdem funktionieren.

## Context7 Authentication

Für höheres Rate-Limit kann ein Context7 API-Key (https://context7.com/dashboard) verwendet werden.
Das Kit deklariert den Service `context7` (`credentials[].apiKey` mit `name: CONTEXT7_API_KEY`,
`proxyManaged: true`). Den Key als Secret registrieren – der Key liegt nie im Sandbox-Filesystem:

```powershell
sbx secret set context7
```

In der Sandbox ist `CONTEXT7_API_KEY=proxy-managed` gesetzt (Platzhalter); die ctx7-CLI sendet
`Authorization: Bearer proxy-managed`, der Proxy ersetzt den Platzhalter transparent bei Requests
an `context7.com`. `echo $CONTEXT7_API_KEY` zeigt nie den echten Key.

## OpenRouter Authentication

OpenRouter ist als zusätzlicher Provider im OpenCode-Setup konfiguriert (`provider.openrouter` in
`opencode-v3-agent/files/home/.config/opencode/opencode.jsonc`, DeepSeek bleibt Default-Modell). `openrouter` ist
als **Kit-deklariertes Credential** im v3-Deskriptor hinterlegt (`credential@1`, `proxyManaged: true`). Den Key
als Secret registrieren; der Deskriptor setzt `OPENROUTER_API_KEY=proxy-managed`, der Proxy injiziert den echten
Key bei Requests an `openrouter.ai` – der Key liegt nie im Sandbox-Filesystem:

```powershell
sbx secret set openrouter
```

In der Sandbox ist `OPENROUTER_API_KEY=proxy-managed` gesetzt (Platzhalter); OpenCode sendet
`Authorization: Bearer proxy-managed`, der Proxy ersetzt den Platzhalter transparent bei Requests
an `openrouter.ai`. `echo $OPENROUTER_API_KEY` zeigt nie den echten Key.

## Google Authentication

Google Gemini ist als zusätzlicher Provider im OpenCode-Setup konfiguriert (`provider.google` in
`opencode-v3-agent/files/home/.config/opencode/opencode.jsonc`, DeepSeek bleibt Default-Modell). `google` ist als
**Kit-deklariertes Credential** im v3-Deskriptor hinterlegt (wie `openrouter`, `credential@1`,
`proxyManaged: true`). Den Key als
Secret registrieren; der Deskriptor setzt den Platzhalter `GOOGLE_GENERATIVE_AI_API_KEY=proxy-managed`,
der Proxy injiziert den echten Key bei Requests an `generativelanguage.googleapis.com` – der Key liegt nie im Sandbox-Filesystem:

```powershell
# 1. API-Key erstellen: https://aistudio.google.com/apikey
# 2. Secret registrieren
sbx secret set google
```

In der Sandbox ist `GOOGLE_GENERATIVE_AI_API_KEY=proxy-managed` gesetzt (Platzhalter); OpenCode sendet
den Platzhalter als Key, der Proxy ersetzt ihn transparent bei Requests
an `generativelanguage.googleapis.com`. `echo $GOOGLE_GENERATIVE_AI_API_KEY` zeigt nie den echten Key.

### Token-Scopes (aktuell konfiguriert)

| Scope | Beschreibung |
|-------|-------------|
| `read:org` | Organisationen lesen |
| `read:packages` | Packages lesen |
| `read:project` | Projects lesen |
| `read:user` | Benutzerdaten lesen |

> **Hinweis:** Für Private-Repo-Zugriff, Push oder PR/Issue-Erstellung wird zusätzlich das `repo`-Scope benötigt. Dies kann via `gh auth refresh -h github.com -s repo` nachgefordert werden.

## Stack Overflow Authentication

Stack Overflow ist eine **optionale Fallback-Quelle** (`api.stackexchange.com`) bei konkreten
Fehlermeldungen (Exception-Stacktraces, Build-Fehler, Plugin-Konflikte), wenn Context7 **keine
Ergebnisse** liefert. Den API-Key anlegen unter https://stackapps.com/applications (Application
registrieren, dann `key` kopieren). Das Kit deklariert den Service `stackoverflow`
(`credentials[].apiKey` mit `name: STACKOVERFLOW_API_KEY`, `proxyManaged: true`). Den Key als
Secret registrieren – der Key liegt nie im Sandbox-Filesystem:

```powershell
sbx secret set stackoverflow
```

In der Sandbox ist `STACKOVERFLOW_API_KEY=proxy-managed` gesetzt (Platzhalter); der Agent sendet
`Authorization: Bearer proxy-managed`, der Proxy ersetzt den Platzhalter transparent bei Requests
an `api.stackexchange.com`. `echo $STACKOVERFLOW_API_KEY` zeigt nie den echten Key.

Die API-Doku liegt **offline im Kit**: `opencode-v3-agent/files/home/stackexchange-api.md` → `~/stackexchange-api.md`
(kompakte Endpoint-Tabelle, generische Parameter, API-Version `api_revision`); Detail-Doku mit allen
Parametern je Methode in `~/stackexchange-api-detail.md` (nur bei Bedarf lesen). Das spart Kontext —
die Website https://api.stackexchange.com/docs wird nur noch bei Unklarheiten abgerufen. Die
API-Version (`api_revision`) kann per `GET /2.3/info?site=stackoverflow` verifiziert werden.
Der **Update-Check** läuft im Validate-Script (`local-test/local-test-kits.py --validate-only`,
IntelliJ-Config `local-test-kits-validate-only`): er vergleicht die dokumentierte Version in den
Doku-Dateien mit dem offiziellen Change-Log (`https://api.stackexchange.com/docs/change-log`) und
**schlägt fehl**, wenn eine neuere Version existiert (Doku-Dateien + `api_revision` aktualisieren).
Alle Kits führen identische Kopien (`opencode-v3-agent/files/home/`, `mammouth-agent/files/home/`, ...),
weil jeder Agent sein eigenes
`files/home/`-Mapping hat.

Nutzungsregeln (siehe `opencode-v3-agent/context.md` bzw. `claude-v3-agent/context.md`):
- **Letzte Quelle** in der Abfragehierarchie (nach Context7/anderen Quellen, nur bei leeren Ergebnissen).
- **Vor jedem API-Call** fragt die KI den Benutzer explizit um Erlaubnis.
- **Nie** über `websearch`/`webfetch`, nur als direkter API-Call gegen `api.stackexchange.com`.

## Cloudsmith Authentication

Cloudsmith ist eine Artifact-Hosting-Plattform (Maven/NuGet/Npm/PyPI/Docker/etc.). Doku ist via
Context7 verfügbar (`npx ctx7 docs /websites/cloudsmith <query>` bzw.
`/cloudsmith-io/cloudsmith-api` für die API-Bindings, z. B. Uploads über FilesApi).
Den API-Key anlegen unter
https://cloudsmith.io/user/settings/api-keys/. Das Kit deklariert den Service `cloudsmith`
(`credentials[].apiKey` mit `name: CLOUDSMITH_API_KEY`, `proxyManaged: true`). Den Key als
Secret registrieren – der Key liegt nie im Sandbox-Filesystem:

```powershell
sbx secret set cloudsmith
```

In der Sandbox ist `CLOUDSMITH_API_KEY=proxy-managed` gesetzt (Platzhalter); der Agent sendet
`X-Api-Key: proxy-managed`, der Proxy ersetzt den Platzhalter transparent bei Requests an
`api.cloudsmith.io` (REST-API) und `upload.cloudsmith.io` (Package-Upload).
`echo $CLOUDSMITH_API_KEY` zeigt nie den echten Key.

> **Helm-OCI-Pull aus Cloudsmith:** `helm.oci.cloudsmith.io` + `docker.cloudsmith.io` + `dl.cloudsmith.io` sind in der
> Netzwerk-Allowlist (`permissions.network.allow`) enthalten — Helm-Pull von
> `oci://docker.cloudsmith.io/…` (z. B. rest-mvc-Subcharts) funktioniert in der Sandbox
> (Blob-Download via `dl.cloudsmith.io`). Ein `helm registry login`
> für `docker.cloudsmith.io` ist in der Sandbox nicht möglich (Credential-Injection
> nur für die API-Domains); für lokale Helm-Pull-Tests den `CLOUDSMITH_API_KEY` direkt verwenden.

## SonarCloud Authentication

SonarCloud (`https://sonarcloud.io`) stellt die CI-Analyse-Ergebnisse (Quality Gate, Issues,
Measures, Coverage) über die Web-API bereit — Ergebnis-Abfrage aus der Sandbox (kein `sonar-scanner`
in der Sandbox; Scans bleiben in der CI). Das Kit deklariert den Service `sonarcloud`
(`credentials[].apiKey` mit `name: SONAR_TOKEN`, `proxyManaged: true`); `sonarcloud.io` +
`*.sonarcloud.io` stehen in `permissions.network.allow`. Token anlegen unter
https://sonarcloud.io/account/security und als Secret registrieren — der Key liegt nie im
Sandbox-Filesystem:

```powershell
sbx secret set sonarcloud
```

In der Sandbox ist `SONAR_TOKEN=proxy-managed` gesetzt (Platzhalter); der Agent sendet
`Authorization: Bearer proxy-managed`, der Proxy ersetzt den Platzhalter transparent bei Requests
an `sonarcloud.io`. `echo $SONAR_TOKEN` zeigt nie den echten Key.

Beispiel (Quality Gate; `<key>` = SonarCloud-Projekt-Key):

```bash
curl -s -H "Authorization: Bearer $SONAR_TOKEN" \
  "https://sonarcloud.io/api/qualitygates/project_status?projectKey=<key>"
```

## Codeberg Authentication

Codeberg (`https://codeberg.org`) ist die **kanonische Kit-Quelle** (Forgejo; GitHub bleibt Mirror)
und bietet eine **Forgejo-REST-API** (`https://codeberg.org/api/v1/`). Das Kit deklariert den Service
`codeberg` (`credentials[].apiKey` mit `name: CODEBERG_TOKEN`, `proxyManaged: true`, Header
`Authorization: token <TOKEN>`); `codeberg.org` + `*.codeberg.org` stehen in
`permissions.network.allow`. Token anlegen unter https://codeberg.org/user/settings/applications
(Scopes z. B. `write:repository`, `write:issue`) und als Secret registrieren — der Key liegt nie im
Sandbox-Filesystem:

```powershell
sbx secret set codeberg
```

In der Sandbox ist `CODEBERG_TOKEN=proxy-managed` gesetzt (Platzhalter); der Agent sendet
`Authorization: token proxy-managed`, der Proxy ersetzt den Platzhalter transparent bei Requests
an `codeberg.org` (Forgejo-API). `echo $CODEBERG_TOKEN` zeigt nie den echten Key.

Beispiel:

```bash
curl -s -H "Authorization: token $CODEBERG_TOKEN" https://codeberg.org/api/v1/user
```

> **Git über HTTPS** (Clone/Push) funktioniert **direkt aus der Sandbox**: Der Proxy überschreibt den
> `Authorization`-Header bei Requests an `codeberg.org` unabhängig davon, was Git sendet (auch anonyme
> bzw. Basic-Auth-Requests werden zum Token-Owner authentifiziert). Kein Credential-Helper nötig
> (verifiziert: `git ls-remote` + Push aus der Sandbox). `CODEBERG_TOKEN=proxy-managed` genügt.

## Offline Dokumentation (Repsy)

Die Repsy-Doku (Maven/Helm/NuGet/Npm/PyPI/Cargo/Docker auf `repo.repsy.io`) ist
**nicht in Context7** verfügbar. Das Kit checked den Hugo-Markdown-Source beim `setup.install`
(als User 1000) offline nach `~/docs/repsy-docs/` aus — Shallow-Clone (ohne Theme-Submodule,
nur `content/`), idempotent (`git pull --ff-only` bei erneutem Install):

```bash
git clone --depth 1 --single-branch https://github.com/repsyio/repsy-docs.git ~/docs/repsy-docs
```

Der Agent liest bei Bedarf **direkt den Markdown-Source** (token-effizienter als HTML-Parsing
der gerenderten Site) und kann per `git -C ~/docs/repsy-docs pull --ff-only` aktualisieren. Der
Clone läuft über `opencode-v3-agent/files/home/.local/bin/install-tooling-user.sh` (alle Kit-Kopien, Drift-Check
greift automatisch) — `github.com` ist bereits in der Network-Allowlist, keine spec.yaml-Änderung
nötig.

## Skills (Superpowers + eigene Skills)

Beim `setup.install` (User 1000) werden zwei Skill-Bundles nach `~/.agents/skills/` installiert
(`skills add -g -y …`; das CLI legt zusätzlich Symlinks in den Agent-Verzeichnissen an, u. a.
`~/.claude/skills/` und `~/.vibe/skills/`).

### Superpowers ([obra/superpowers](https://github.com/obra/superpowers))

- **brainstorming** — Spezifikation/Brainstorming vor kreativer Arbeit
- **writing-plans** — Implementierungsplan aus Spec/Requirements
- **executing-plans** — Plan inline (ohne Subagents) selbst ausführen
- **test-driven-development** — echtes Red/Green-TDD vor Implementierung
- **systematic-debugging** — Bugs/Testfehler systematisch analysieren, bevor Fixes vorgeschlagen werden
- **verification-before-completion** — Beweis vor Erfolgsmeldung (Verifikationskommandos laufen lassen)
- **requesting-code-review** — Review anfordern vor Merge
- **receiving-code-review** — Review-Feedback technisch prüfen statt blind umsetzen
- **subagent-driven-development** — Plan über Subagents ausführen
- **dispatching-parallel-agents** — unabhängige Aufgaben parallel verteilen
- **using-git-worktrees** — isolierter Workspace via Git-Worktree
- **finishing-a-development-branch** — Branch-Integration abschließen
- **diagnosing-superpowers** — Fehlerdiagnose im Superpowers-Ablauf
- **using-superpowers** — Einstieg: Skills finden und anwenden
- **writing-skills** — neue Skills schreiben/prüfen

### Meine Skills ([dboeckli/ai-agent-skills](https://github.com/dboeckli/ai-agent-skills))

- **camel-matrix** — Camel Spring Boot Kompatibilitätsmatrix
- **cc-best-practices** — Claude Code Best Practices
- **cron-schedule-planner** — GitHub-Actions-Cron-Zeitpläne: Übersicht, Kollisionen, Umverteilung
- **project-references** — Referenzprojekt-Suche
- **skill-best-practices** — SKILL.md Schreib-Guide

**Superpowers nur als Skill-Bundle, kein Plugin (bewusst, „Option A“):** Superpowers' OpenCode-Plugin
(`"plugin": ["superpowers@git+…"]` in `opencode.jsonc`) wird **nicht** verwendet. Damit fehlen die
automatische Methodik-Injektion beim Session-Start/Auto-Trigger — die Skills werden bei Bedarf über
das `skill`-Tool geladen. Das vermeidet konkurrierende Instruktionen zu den Kit-Regeln
(Feature-Branch-Pflicht, kein Auto-Commit, `target/review`-Diff, Run-Config-Guard); **bei Konflikt gelten
die Kit-Regeln**. Kein Versions-Pin (Upstream-`main`, Update via `skills update`).

Die Installation läuft über `opencode-v3-agent/files/home/.local/bin/install-tooling-user.sh` (alle
Kit-Kopien, Drift-Check) mit eigenem Guard (`~/.agents/skills/using-superpowers`), damit
vorgebackene Images ohne Superpowers beim Sandbox-Start nachinstallieren; `github.com` ist in der
Network-Allowlist. Der e2e-Check (`local-test-kits.py`) prüft `using-superpowers` sowie
`systematic-debugging`/`verification-before-completion`.

## Layout

- `opencode-v3-agent/opencode-v3-agent.yaml` — v3 workload descriptor (Issue #242; Entrypoint `opencode-entrypoint`, Credentials inkl. openrouter/google, lifecycle)
- `opencode-v3-agent/opencode-v3-agent.dockerfile` — OpenCode-v3-Image (`docker.io/sbx/shell-docker-image:latest`-Basis + Kit-Tooling + Config/Plugins; OpenCode-CLI via npm `opencode-ai` auf 1.x gepinnt; Favoriten-Seeding im Entrypoint)
- `opencode-v3-agent/files/home/.config/opencode/` — OpenCode config (Permission-Whitelist für IntelliJ-MCP-Tools via sbx MCP Gateway `mcp-gateway_*`; Provider `deepseek`/`openrouter`/`google`/`zai` (GLM, `ZAI_API_KEY`)/`mistral` (Mistral-hosted GLM `zai-glm-5-3`, `MISTRAL_API_KEY`); keine direkte `mcp.idea`-Konfiguration, siehe Abschnitt "IntelliJ MCP: Permission-Whitelist + Run-Config-Guard")
- `opencode-v3-agent/files/home/.config/opencode/plugins/intellij-run-config-guard.js` — OpenCode-Plugin: erlaubt `mcp-gateway_execute_run_configuration` nur für `local-test-kits-validate-only`
- `claude-v3-agent/claude-v3-agent.yaml` — Claude-Code-v3-Workload-Descriptor (`kind: workload`, Issue #242; Credentials anthropic/github/context7, `agent-context` → `~/.claude/CLAUDE.md`, lifecycle CA/Maven)
- `claude-v3-agent/claude-v3-agent.dockerfile` — Claude-v3-Image (shell-docker-image-Basis + Kit-Tooling + `.claude`/`.claude.json` + managed-settings; Claude-CLI via npm `@anthropic-ai/claude-code` gepinnt; Entrypoint `claude-entrypoint`)
- `claude-v3-agent/files/home/.claude/` — Settings/Permission-Whitelist/Doku (Permission-Whitelist `mcp__mcp-gateway__*`; keine `mcpServers.idea`-Konfiguration, siehe Abschnitt "IntelliJ MCP: Permission-Whitelist + Run-Config-Guard")
- `claude-v3-agent/files/home/.config/sandbox-kit/intellij-run-config-guard.sh` — Claude Code PreToolUse-Hook: erlaubt `mcp__mcp-gateway__execute_run_configuration` nur für `local-test-kits-validate-only`
- `claude-v3-agent/files/home/.local/bin/claude-config.py` + `claude-entrypoint.sh` — merged MCP-Gateway + Kit-Settings vor dem CLI-Start
- `mammouth-agent/mammouth-agent.yaml` — v3 workload descriptor (`kind: workload`, `args.version`/`buildArg: MAMMOUTH_VERSION`, credentials, network-policy, agent-context, lifecycle)
- `mammouth-agent/mammouth-agent.dockerfile` — Mammouth image (shell-docker-image base + Kit-Tooling + Mammouth-CLI, `ENTRYPOINT [mammouth-entrypoint]`; Favoriten-Seeding im Entrypoint + Build)
- `mammouth-agent/files/home/.local/bin/mammouth-entrypoint.sh` — Entrypoint-Wrapper: seedet die Favoriten VOR dem TUI-Start, dann `exec mammouth` (der `setup.startup`-Hook läuft erst danach und verlöre das Race)
- `mammouth-agent/files/home/.local/bin/seed-mammouth-model-favorites.py` — idempotenter Seeder (Favoriten-Liste, Order bleibt, fehlende Modelle werden angehängt); wird im Entrypoint, im `setup.startup`-Hook und beim Image-Build ausgeführt
- `mammouth-agent/files/home/.config/mammouth/` — Mammouth config for the agent kit (Provider `deepseek`, `zai`, `mistral`)
- `mistral-vibe-agent/mistral-vibe-agent.yaml` — v3 workload descriptor (kind: workload, name `mistral-vibe`, args/VIBE_VERSION, credentials, network-policy, agent-context, lifecycle)
- `mistral-vibe-agent/mistral-vibe-agent.dockerfile` — Vibe-Image (shell-docker-image + Kit-Tooling + `uv tool install mistral-vibe==<pin>`, `ENTRYPOINT [vibe, --agent, auto-approve]`)
- `pi-agent/pi-agent.yaml` — v3 workload descriptor (Kit-Spec v3, `kind: workload`, `args.version`/`buildArg: PI_VERSION`, `provides`, `capabilities`: network-policy, credential, agent-context, lifecycle)
- `pi-agent/pi-agent.dockerfile` — Pi image (shell-docker-image base + Kit-Tooling + `@earendil-works/pi-coding-agent`, `ENTRYPOINT [pi]`; kein OpenCode im Image)
- `pi-agent/files/home/.pi/agent/` — `settings.json` (deepseek/deepseek-flash), `mcp.json` (MCP-Gateway), `extensions/mcp-guard.ts` (Read-only-Whitelist + Run-Config-Guard, gemeinsame Allow-Liste)
- `pi-agent/files/home/.local/bin/pi-startup-{ca,maven}.sh` — Lifecycle-Startup (Proxy-CA in JDK-cacerts, `~/.m2/settings.xml` inkl. Host-Cache)
- `pi-agent/context.md` — Sandbox-`AGENTS.md` via `agent-context@1`
- `mistral-vibe-agent/mistral-vibe-agent.dockerfile` — pinned Vibe image (shell-docker-image + Kit-Tooling + `uv tool install mistral-vibe==<pin>`, `ENV VIBE_ACTIVE_MODEL=glm-flash`); Build/Publish via `.github/workflows/build-and-publish-mistral-vibe-image.yml`
- `mistral-vibe-agent/files/home/.vibe/config.toml` — MCP-Gateway-Verdrahtung (`[[mcp_servers]]` → `mcp-gateway.docker.internal/mcp`, `Bearer proxy-managed`) + Default-Modell GLM-5.3-Flash (Z.AI-Provider `zai`) + GLM-5.3 direkt via Z.AI (`glm-5.3`) + GLM-4.7-Flash gratis (`glm-4.7-flash`) + Mistral-hosted GLM (`glm` → `zai-glm-5-3`)
- `mistral-vibe-agent/files/home/.vibe/hooks.toml` + `files/home/.config/sandbox-kit/vibe-mcp-guard.py` — pre_tool-Read-only-Guard für die IntelliJ-MCP-Tools (auto-approve umgeht das Permission-System)
- `docs/prerequisites.md` — kompakte Übersicht aller Voraussetzungen (Host + Sandbox + Secrets + Netzwerk)

## Dual agent support

Das Kit funktioniert mit **OpenCode v3, Claude Code v3, Mammouth Code, Mistral Vibe und Pi** (alles v3-Workloads) – der Agent wird vom jeweiligen Kit-Image beim `sbx run` bestimmt. Die **Versionen sind gepinnt**: alle fünf basieren auf der Docker-verwalteten `docker.io/sbx/shell-docker-image:latest@sha256:969457e4d3eb99b913985875dab829e41924e5435255356546ccefea56c5d6ea` (Digest-gepinnt; Renovate, Issue #254) und pinnen ihre jeweilige CLI (`OPENCODE_VERSION` npm `opencode-ai` 1.x; `CLAUDE_VERSION` npm `@anthropic-ai/claude-code`; `MAMMOUTH_VERSION`; `VIBE_VERSION`; `PI_VERSION`) — zentrale Source of Truth: `OPENCODE_VERSION`/`CLAUDE_VERSION` in `.github/workflows/validate.yml`/`e2e.yml` (Renovate); alle Kits als v3-Workload via Descriptor/Dockerfile. `local-test-kits.py --validate-only` **warnt** (gelb), sobald eine neuere OpenCode-1.x-/Template-/CLI-Version existiert. Die Images müssen vor dem Start publiziert sein: CI via `.github/workflows/build-and-publish-{opencode-v3,claude-v3,mammouth,mistral-vibe,pi}-image.yml` (`workflow_dispatch`/Push auf `master`), lokal via Run-Config `build-and-publish-<name>-image` (setzen zusätzlich den beweglichen Tag `:local`).

```powershell
sbx mcp add idea --url http://localhost:64615/stream --skip-ssrf-check

sbx run ./opencode-v3-agent/ `
    --skills=off `
    --static-mcp idea,k8s,docker
sbx run docker.io/domboeckli/sbx-mammouth:local `
    --skills=off `
    --static-mcp idea,k8s,docker
sbx run docker.io/domboeckli/sbx-mistral-vibe:local `
    --skills=off `
    --static-mcp idea,k8s,docker
```

Alle fünf erhalten dieselben Tools (JDK, Maven, Docker CLI, Helm, Apache Kafka CLI, Bruno CLI, MCP-Inspector CLI, Skills, ctx7) und die
Host-MCP-Server (IntelliJ / Kubernetes / Docker) via **sbx MCP Gateway**
(Voraussetzung: einmalig `sbx mcp add idea --url http://localhost:64615/stream --skip-ssrf-check`, `sbx mcp add k8s …`
und `sbx mcp add docker …`, Sandbox mit `--static-mcp idea,k8s,docker` erzeugen oder `sbx mcp load <name> --sandbox`).
Die jeweilige Config wird automatisch gelesen:
- OpenCode v3 (Workload `opencode-v3-agent/`): `~/.config/opencode/opencode.jsonc` + `~/.config/opencode/AGENTS.md` — Modell `deepseek/deepseek-flash` (DeepSeek V4.1 Flash)
- Claude Code v3 (Workload `claude-v3-agent/`): `~/.claude/settings.json` + `~/.claude/CLAUDE.md` (via `agent-context`) + `~/.claude.json` (MCP-Gateway) — dieselben Kit-Felder; der Entrypoint `claude-entrypoint` merged Settings + Gateway vor dem CLI-Start, die Hooks/statusLine kommen aus `/etc/claude-code/managed-settings.json`.
- Mammouth Code: `~/.config/mammouth/opencode.jsonc` + `~/.config/mammouth/AGENTS.md` (nur Agent-Kit)
- Mistral Vibe: `~/.vibe/config.toml` (MCP-Gateway) + `~/.vibe/hooks.toml` (Read-only-Guard) + `~/.vibe/AGENTS.md` (nur Agent-Kit)
- Pi: `~/.pi/agent/settings.json` (Default-Modell) + `~/.pi/agent/mcp.json` (MCP-Gateway) + `~/.pi/agent/extensions/mcp-guard.ts` (Read-only-Guard) + `~/.pi/agent/AGENTS.md` (nur Agent-Kit)

> **Mammouth Code**: Das Image `docker.io/domboeckli/sbx-mammouth` backt die Mammouth-CLI beim Image-Build —
> **gepinnt auf v1.18.31.2** (`ARG MAMMOUTH_VERSION` im `mammouth-agent/mammouth-agent.dockerfile`, Renovate
> `mammouth-ai/code`; `--validate-only` warnt bei neuerem Release) + Symlink `/usr/local/bin/mammouth` für den Entrypoint. API-Key als `MAMMOUTH_API_KEY` (Provider `mammouth-ai`, Base-URL `https://api.mammouth.ai/v1`), konfiguriert via `credentials[].apiKey` (`name`/`proxyManaged`/`inject`) im Kit.

> **Mistral Vibe**: Installiert das Agent-Kit als eigenes gepinntes Image (`mistral-vibe-agent/mistral-vibe-agent.dockerfile`: shell-docker-image + Kit-Tooling + `uv tool install mistral-vibe==<pin>`, Renovate `mistral-vibe` PyPI). API-Key via Built-in-Service `mistral` (`MISTRAL_API_KEY`, `api.mistral.ai`, Sentinel `proxy-managed`). Launch via Dockerfile-`ENTRYPOINT [vibe, --agent, auto-approve]`. Image muss vor dem ersten Start publiziert sein (`build-and-publish-mistral-vibe-image.yml`, workflow_dispatch).

## Tools installed by the kit

> Die Tooling-Installation ist in allen Kit-Specs dedupliziert: `setup.install` nutzt für die
> **schweren Tools** `bash /home/agent/.local/bin/install-tooling.sh <tool>` — **einen Command pro Tool**
> (`node|shfmt|jdk|maven|docker|compose|kubectl|helm|kafka`, Default `all`), damit die `sbx run`-Konsole
> jedes Tool als eigene Zeile (Spinner → ✓) zeigt. npm/apt-Pakete sind als Inline-Commands direkt in
> den Specs (`npm_config_bin_links=true npm install -g ctx7` usw., `apt-get update && …`). Die Skripte
> liegen als identische Kopien in den `files/home/.local/bin/`-Bundles der Kits (kein separates
> Kanonik-Verzeichnis). **Versionsänderungen**
> (Node.js, JDK, Maven, Docker, Compose, Helm, Kafka, shfmt) in einer Kit-Kopie machen, dann die anderen identisch halten
> (`opencode-v3-agent/files/home/.local/bin/`, `mammouth-agent/files/home/.local/bin/`, `mistral-vibe-agent/files/home/.local/bin/`) → der Validate-only-Lauf
> (`local-test-kits-validate-only`) schlägt bei Drift fehl.

| Tool | Source |
|------|--------|
| Node.js 26.13.0 | nodejs.org (`/opt/node` → Symlinks in `/usr/local/bin`; npm-CLIs wie renovate ≥43) |
| Liberica JDK 25.0.5+11 | GitHub Releases (bell-sw) — alle Kits; alle JDK-Binaries (`java`, `javac`, `jar`, `javadoc`, `jshell`, `keytool`, …) via Symlink in `/usr/local/bin` |
| Apache Maven 3.10.0 | dlcdn.apache.org |
| Docker CLI 29.9.3 | aus dem Base-Image (`docker.io/sbx/shell-docker-image:latest`, alle Kits; Issue #254) |
| Docker Compose 5.7.0 (Plugin) | aus dem Base-Image (alle Kits; Issue #254) |
| kubectl (latest stable) | dl.k8s.io (Build: v1.37.2) |
| Helm 4.3.1 | get.helm.sh |
| Apache Kafka CLI 4.4.0 (Scala 2.13) | dlcdn.apache.org (Fallback archive.apache.org) (`/opt/kafka` + `kafka-*.sh`-Wrapper in `/usr/local/bin`) |
| ctx7 | npm |
| skills | npm (vercel-labs) |
| prettier | npm |
| renovate | npm |
| Bruno CLI (`bru`) 4.3.0 | npm (`@usebruno/cli`, gepinnt; Renovate-Custom-Manager) |
| MCP Inspector CLI (`mcp-inspector`) 2.13.0 | npm (`@modelcontextprotocol/inspector`, gepinnt; Renovate-Custom-Manager) |
| MCP-Verbindungs-CLI (`mcpdo`, gleiches npm-Paket; Subcommands `connect`/`tools/list`/`tools/call`) 2.13.0 | npm (`@modelcontextprotocol/inspector`, gepinnt; Renovate-Custom-Manager) |

> **opencode-v3/mammouth/mistral-vibe/pi (Issue #254):** Alle vier basieren auf `docker.io/sbx/shell-docker-image:latest` —
> Node/npm, Docker CLI, Compose, Buildx, Python, Go und uv kommen aus dem Base-Image und werden **nicht** neu
> installiert. Die Kit-Tooling-Schleife installiert `node shfmt jdk maven kubectl helm kafka` (JDK = Liberica, wie
> in allen Kits).

> **`npm_config_bin_links`:** Die npm-Install-Kommandos laufen mit explizitem Prefix
> `npm_config_bin_links=true` (`install-tooling.sh`), damit die globalen CLIs als Symlinks nach
> `/usr/local/share/npm-global/bin` landen. Zur Laufzeit setzt das Kit dagegen
> `ENV npm_config_bin_links=false` (Dockerfile aller v3-Images), damit npm-Aufrufe des Agents keine
> bin-link-Seiteneffekte erzeugen. **Die Variable ist damit bereits global gesetzt — kein
> `export npm_config_bin_links=...` vor npm- oder Build-Kommandos nötig (redundant).**
> Siehe dazu auch `README.md` → "npm bin-links: Install vs. Laufzeit".

> **Helm 4:** `helm` und `helm4` zeigen beide auf Helm 4.3.1 (`/usr/local/bin/helm`; `helm4` ist ein Symlink darauf). Renovate trackt die Version über `HELM_VER`.

> **Apache Kafka CLI:** Die Kafka-Distribution liegt unter `/opt/kafka`; `install-tooling.sh` legt für jedes
> `bin/*.sh` einen Wrapper in `/usr/local/bin` an, der das Skript per absolutem Pfad ausführt (die Skripte
> lösen ihr `base_dir` über `$(dirname $0)/..` auf — ein Symlink würde das brechen). `dlcdn.apache.org` +
> `archive.apache.org` (Fallback für ältere, von dlcdn entfernte Releases) sind in der Network-Allowlist.
> Der Tarball wird erst von dlcdn, bei Fehler von `archive.apache.org` geladen (`run_kafka`). Renovate trackt
> `KAFKA_VER` NICHT gegen `org.apache.kafka:kafka_2.13` (Maven), sondern gegen die Binary-Distro auf dlcdn
> (custom Datasource `custom.apache-kafka`, `format: html`) — Maven-Artifacts werden publiziert, bevor der
> Tarball auf den Apache-Mirrors liegt; ein Maven-Bump auf eine noch nicht veröffentlichte Distro bricht den
> Image-Build (`kafka-topics.sh` fehlt → fail-closed Verify, exit 127). Zusätzlich prüft
> `local-test-kits.py --validate-only` die Tarball-Verfügbarkeit (dlcdn ODER archive).

## Mammouth Authentication

Für Mammouth Code wird der API-Key als Secret registriert und via Proxy als `MAMMOUTH_API_KEY` injiziert –
der Key liegt nie im Sandbox-Filesystem. Es gibt keinen eingebauten Provider wie bei `anthropic`/`github`,
daher den Kit-deklarierten Service `mammouth` nutzen:

```powershell
# Kit-deklarierter Service (wie sbx secret set anthropic)
sbx secret set mammouth
```

Der Key stammt aus https://mammouth.ai/app/account/settings/api.

> **Wichtig:** `MAMMOUTH_API_KEY` ist in der Sandbox auf den Platzhalter `proxy-managed` gesetzt (wie
> `ANTHROPIC_API_KEY` bei Claude). Das Agent-Kit setzt sie via `credentials[].apiKey.name` + `proxyManaged: true`
> (kit-spec v2). Der Proxy ersetzt den Platzhalter transparent bei Requests an `api.mammouth.ai`. `env | grep -i MAMMOUTH` in der
> Sandbox zeigt `MAMMOUTH_API_KEY=proxy-managed` (nie den echten Key).

Verifikation:

```powershell
sbx secret ls                                                    # Secret ist registriert
sbx exec mammouth-sandbox bash -c 'curl -s https://api.mammouth.ai/v1/models -H "Authorization: Bearer $MAMMOUTH_API_KEY" | head'
```

## Mistral Authentication

Für Mistral Vibe wird der API-Key als Secret registriert und via Proxy als `MISTRAL_API_KEY` injiziert –
der Key liegt nie im Sandbox-Filesystem. `mistral` ist ein **Built-in-Service** von `sbx` (mappt auf
`MISTRAL_API_KEY` + `api.mistral.ai`); das Kit deklariert `credentials[].service: mistral`:

```powershell
# Built-in-Service (wie sbx secret set anthropic)
sbx secret set mistral
```

Der Key stammt aus https://console.mistral.ai/.

> **Wichtig:** `MISTRAL_API_KEY` ist in der Sandbox auf den Platzhalter `proxy-managed` gesetzt (wie
> `ANTHROPIC_API_KEY` bei Claude). Der Proxy ersetzt den Platzhalter transparent bei Requests an
> `api.mistral.ai`. `env | grep -i MISTRAL` in der Sandbox zeigt `MISTRAL_API_KEY=proxy-managed`
> (nie den echten Key).

Verifikation:

```powershell
sbx secret ls                                                    # Secret ist registriert
sbx exec mistral-vibe-sandbox bash -c 'curl -s https://api.mistral.ai/v1/models -H "Authorization: Bearer $MISTRAL_API_KEY" | head'
```

> **Credential-Binding:** Kit-deklarierte Services (Third-Party-v2-Kits) brauchen ein Binding — für `mistral`
> in `~/.config/sbx/credentials.yaml`: `mistral: apiKey.domains: [api.mistral.ai]` (oder interaktiv beim ersten
> Start bestätigen). Ohne Binding wird nur der Sentinel gesetzt, der echte Key aber nicht injiziert
> (`sbx create`: „no binding authorizes this service"); `local-test-kits.py` schlägt dann fehl.

> **Start-Modell GLM-5.3-Flash (Z.AI):** `mistral-vibe-agent/mistral-vibe-agent.dockerfile` setzt zusätzlich
> `environment.variables.VIBE_ACTIVE_MODEL: "glm-flash"` (Env-Layer überschreibt `active_model`; `/model` wechselt
> weiterhin für die aktuelle Session). `mistral-vibe-agent/files/home/.vibe/config.toml` setzt
> `active_model = "glm-flash"` und deklariert Z.AI als OpenAI-kompatiblen Provider (`[[providers]]` `zai`,
> `ZAI_API_KEY`, `api.z.ai`) + `[[models]]` `glm-flash` → `glm-5.3-flash` sowie das Flagship `glm-5.3`
> (Alias `glm-5.3`, gleicher Provider/Key) und das kostenlose `glm-4.7-flash` (Alias `glm-4.7-flash`). Alle gibt es
> **nicht über Mistral** → eigener Service `zai`
> (`sbx secret set zai`, Key https://z.ai/manage-apikey/apikey-list, Binding
> `zai: apiKey.domains: [api.z.ai]`). Alternative: Mistral-hosted `zai-glm-5-3` (Alias `glm`, Provider `mistral`).
>
> **Plan vs. Guthaben (wichtig):** Der Mistral-**Plan** steuert Rate-Limits + Modellzugriff, nicht das Guthaben.
> **Free mode** (Default, inkl. $10/mo API-Credits) → `429` (Rate-Limit) und `403 tier_not_allowed` für
> Third-Party-Modelle (GLM); höhere Limits + Mistral-GLM nur mit **bezahltem Plan** (Pro/Team). Z.AI direkt:
> `429` = Z.AI-Guthaben nicht aktiv/leer (https://z.ai/manage-apikey/billing).

## Netzwerk-Policy (Deny-by-Default)

- **Quelle**: `network-policy@1` im jeweiligen v3-Descriptor (OpenCode v3/Claude v3/Mammouth/Mistral Vibe/Pi). Nur gelistete
  Domains sind erreichbar, alles andere → HTTP 403.
- **Enforcement**: Nicht das Kit, sondern die Sandbox selbst erzwingt die Liste — über den **Sandbox-Proxy**
  (`mcp-gateway`, `mcp-gateway.docker.internal`). Er ist der einzige Netzwerk-Ausgang; `sbx` trägt ihn für seine **unterstützten Agenten**
  (OpenCode/Claude) automatisch als `mcp-gateway`-MCP-Server in die Agent-Config ein (daher „mcp-gateway Connected“
  in OpenCode — kein Fehler). Die Agent-Kits **Mammouth/Vibe** verdrahten ihn selbst (Issue #139). Derselbe Proxy macht die
  **Credential-Injection** (`proxy-managed`-Platzhalter → echter Key, siehe Auth-Abschnitte oben).
- **`files/home/.../network-policy.md` ist rein informativ**: Nur Doku der Allow-Liste in den Agent-Instructions
  (damit der Agent geblockte Calls vermeidet). Erzwingt nichts. Bei Änderungen an `permissions.network.allow`
  synchron aktualisieren (4 Dateien: OpenCode, Claude, Mammouth, Mistral Vibe; Pi hat keine `network-policy.md`-Kopie — die Allowlist steht im v3-Descriptor).

## Docker Sandbox / sbx Dokumentation

Offizielle Docker-Doku für Sandbox-Kits, Templates und Custom Agents:

- **`~/sbx-cli.md`** — **Offline-Referenz der sbx CLI** (alle `--help`-Outputs, generiert aus der
  v0.53.0-Release-Binary; identische Kopien in allen Kit-Bundles)
- [Templates](https://docs.docker.com/ai/sandboxes/customize/templates/) — Custom Template-Images bauen (Base-Images, Dockerfile, `sbx template save`/`load`)
- [Kits](https://docs.docker.com/ai/sandboxes/customize/kits/) — Kit-Übersicht (`kind: mixin` vs. `kind: sandbox`)
- [Kit Reference](https://docs.docker.com/ai/sandboxes/customize/kit-reference/) — spec.yaml-Felder (`sandbox`, `network`, `credentials`, `commands`, `agentContext`)
- [Kit Examples](https://docs.docker.com/ai/sandboxes/customize/kit-examples/) — Beispiel-Kits
- [Build an Agent](https://docs.docker.com/ai/sandboxes/customize/build-an-agent/) — eigenes Agent-Kit bauen (Amp-Tutorial)

## Caveats

- **Docker Socket**: Jede Sandbox hat einen **isolierten Docker Daemon** im eigenen MicroVM (`docker info` zeigt den Sandbox-Namen als Servername) – kein Host-Socket-Mount nötig. Host-Docker-Zugriff (Container des Hosts sehen/steuern) läuft über einen **lokalen Docker-MCP-Server** (`mcp-server-docker` via `uvx`, host-seitig via `sbx mcp add docker …` registriert; siehe `docs/mcp/docker-mcp-server.md`, Issue #165) — **kein offener `2375`-Port** mehr; die Permission-Whitelist gatet die Tools (read-only `allow`, Write `ask`).
- **Pre-installed opencode**: Das Base-Image enthält eine eigene OpenCode CLI. `npm install -g` überschreibt sie, aber bei Abweichungen ist die Base-Image-Version die Ursache.
- **Skills in `~/.agents/skills/`**: Werden via `skills add -g` mit `user: "1000"` installiert (dboeckli-Bundle + Superpowers, siehe „Skills“), damit sie beim `agent`-User landen.
- **Mammouth Code**: Wird vom Agent-Kit (`mammouth-agent/`) automatisch installiert und ausschließlich über das Agent-Kit betrieben (`sbx run --skills=off ./mammouth-agent/`).
- **Claude Code v3**: `claude-v3-agent/` ist ein v3-Workload (Issue #242). v3 braucht sbx >= v0.45, ist nicht mit v1/v2 kombinierbar; Start per Image-Ref (`sbx run <IMAGE_PREFIX>/sbx-claude:<tag>`) oder Verzeichnis. Image-Bootstrap: `build-and-publish-claude-v3-image.yml`.
- **OpenCode v3**: `opencode-v3-agent/` ist ein v3-Workload (Issue #242). v3 braucht sbx >= v0.45, ist nicht mit v1/v2 kombinierbar; Start per Image-Ref (`sbx run <IMAGE_PREFIX>/sbx-opencode:<tag>`) oder Verzeichnis. Image-Bootstrap: `build-and-publish-opencode-v3-image.yml`.
- **Pi**: Wird über das Agent-Kit (`pi-agent/`) als v3-Workload betrieben (`sbx run --skills=off ./pi-agent/`); v3 braucht sbx >= v0.45, ist nicht mit v1/v2-Kits kombinierbar, und `--template`/`--kit-arg imageTag` entfallen. Image-Bootstrap: `build-and-publish-pi-image.yml` (workflow_dispatch).
- **Mistral Vibe**: Wird über das Agent-Kit (`mistral-vibe-agent/`) als v3-Workload betrieben (`sbx run --skills=off ./mistral-vibe-agent/`); v3 braucht sbx >= v0.45, ist nicht mit v1/v2-Kits kombinierbar, `--template`/`--kit-arg imageTag` entfallen. Version steckt im Image (`ARG VIBE_VERSION`). Image-Bootstrap: `build-and-publish-mistral-vibe-image.yml` (workflow_dispatch).
- **Kit-spec v3**: Alle Kits sind v3-Workloads (`schemaVersion: "3"`, `kind: workload`, Descriptor + Dockerfile). Validieren via `sbx kit validate ./<kit>/` (ohne `--offline`, Kit-Builder-Sandbox `sbx-kit-builder`) bzw. buildx/e2e und `sbx kit inspect ... --json | jq '.warnings'` (erwartet `[]`). v3-Kits sind nicht mit v1/v2-Kits kombinierbar (`--template`/`--kit` entfallen).
