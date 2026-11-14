# opencode-sandbox-kit

[![Validate Kit](https://github.com/dboeckli/opencode-sandbox-kit/actions/workflows/validate.yml/badge.svg)](https://github.com/dboeckli/opencode-sandbox-kit/actions/workflows/validate.yml)
[![Kit e2e](https://github.com/dboeckli/opencode-sandbox-kit/actions/workflows/e2e.yml/badge.svg)](https://github.com/dboeckli/opencode-sandbox-kit/actions/workflows/e2e.yml)

> **Canonical repository: [Codeberg](https://codeberg.org/dboeckli/opencode-sandbox-kit).** The
> [GitHub repo](https://github.com/dboeckli/opencode-sandbox-kit) is a **read-only mirror** — direct
> pushes/PRs there are ignored and overwritten on the next sync. Please use **Codeberg** for issues,
> pull requests and releases.

Docker Sandbox Kit for OpenCode / Mammouth Code / Claude Code / Mistral Vibe / Pi (Kit-Spec v3), tailored to the Spring Boot ecosystem — ctx7 plus IntelliJ/Kubernetes/Host-Docker MCP via the sbx MCP Gateway, with pre-baked Java/Maven build tooling.

Enthält zusätzlich dedizierte Agent-Kits:

- **Mammouth Code** — `mammouth-agent/` (**Kit-Spec v3**, `kind: workload`), eigenes Image `docker.io/domboeckli/sbx-mammouth`, Entrypoint `mammouth-entrypoint` (seedet die Model-Picker-Favoriten, dann `exec mammouth`).
- **Mistral Vibe** — `mistral-vibe-agent/` (**Kit-Spec v3**, `kind: workload`), eigenes gepinntes Image, Entrypoint `vibe --agent auto-approve`.
- **OpenCode v3** — `opencode-v3-agent/` (**Kit-Spec v3**, `kind: workload`), eigenes Image `docker.io/domboeckli/sbx-opencode` (baut auf `docker.io/sbx/shell-docker-image:latest` auf, OpenCode-CLI via npm `opencode-ai` auf 1.x gepinnt).
- **Claude Code v3** — `claude-v3-agent/` (**Kit-Spec v3**, `kind: workload`), eigenes Image `docker.io/domboeckli/sbx-claude` (baut auf `docker.io/sbx/shell-docker-image:latest` auf, Claude-CLI via npm `@anthropic-ai/claude-code` gepinnt).
- **Pi Coding Agent** — `pi-agent/` (**Kit-Spec v3**, `kind: workload`), eigenes gepinntes Image `docker.io/domboeckli/sbx-pi-agent`, Entrypoint `pi`; identisches Tooling wie die anderen Kits, MCP-Gateway direkt in `~/.pi/agent/mcp.json`, Read-only-Guard als Pi-Extension.

> **Setup-Anleitung:** [`INSTALL.md`](INSTALL.md) — Voraussetzungen, Docker-Desktop-Setup, IntelliJ MCP, Secrets (`sbx secret set`), Verifikation.

> **Troubleshooting & Caveats:** [`docs/troubleshooting.md`](docs/troubleshooting.md) — KVM/WSL2, IntelliJ-MCP, Mistral-Rate-Limits, Kit-Spec v3, Skills.

## Quickstart

### Lokale Entwicklung (opencode-sandbox-kit)

Zuerst ins geklonte Repo wechseln — die Kit-Pfade (`./opencode-v3-agent/`, `./claude-v3-agent/`, `./mammouth-agent/`, `./mistral-vibe-agent/`, `./pi-agent/`) sind relativ:

```powershell
cd C:\development\projects\opencode-sandbox-kit
```

> **Hinweis (Ressourcen & Cache):** Ohne `-m`/`--cpus` bekommt jede Sandbox per Default **50 % des
> Host-RAM** (bei 32 GB ≈ 15.8 GiB) und alle Host-Cores. Beim `sbx run` explizit begrenzen, z. B.
> `-m 6g --cpus 4` (gilt nur bei der Erzeugung — bestehende Sandbox vorher `sbx rm`). Das erste
> `sbx run ./<kit>/` baut das Kit kalt (mehrere Minuten); Folgeläufe sind schneller, solange der
> gemeinsame Buildx-Builder `sbx-kits` erhalten bleibt (`--stop-active` statt `--remove-active`,
> kein `buildx prune`). Details: [`docs/docker-disk-cleanup.md`](docs/docker-disk-cleanup.md).

> **Clipboard (optional):** Sandbox → Host-Textkopie ist seit sbx v0.51 opt-in — einmalig
> `sbx settings set clipboard.textCopy true` (plus `clipboard.imagePaste true` für Screenshots). Ohne das
> schlägt Copy in Pi/OpenCode fehl (Pi meldet irreführend „Clipboard unavailable …"). Details:
> [`docs/prerequisites.md`](docs/prerequisites.md), [`docs/troubleshooting.md`](docs/troubleshooting.md).

Beispiel lokal mit Ressourcen-Limits (empfohlen):

```powershell
sbx run ./opencode-v3-agent/ `
    --skills=off `
    --static-mcp idea,k8s,docker `
    -m 6g --cpus 4 `
    . `
    "C:\development\maven-repo:ro"
```

Vor dem lokalen Start einmalig die Run-Config `build-and-publish-<agent>-image` ausführen — sie baut/pusht den Tag `:local`:

- [`build-and-publish-opencode-v3-image`](.run/build-and-publish-opencode-v3-image.run.xml)
- [`build-and-publish-claude-v3-image`](.run/build-and-publish-claude-v3-image.run.xml)
- [`build-and-publish-mammouth-image`](.run/build-and-publish-mammouth-image.run.xml)
- [`build-and-publish-mistral-vibe-image`](.run/build-and-publish-mistral-vibe-image.run.xml)
- [`build-and-publish-pi-image`](.run/build-and-publish-pi-image.run.xml)

**OpenCode v3** (v3-Workload, eigenes Image `docker.io/domboeckli/sbx-opencode:<basever>`):

```powershell
sbx run docker.io/domboeckli/sbx-opencode:local `
    --skills=off `
    --static-mcp idea,k8s,docker `
    . `
    "C:\development\maven-repo:ro"
```

Ohne publiziertes Image baut `sbx` das Kit direkt aus dem Verzeichnis:

```powershell
sbx run ./opencode-v3-agent/ `
    --skills=off `
    --static-mcp idea,k8s,docker `
    . `
    "C:\development\maven-repo:ro"
```

**Claude Code v3** (v3-Workload, eigenes Image `docker.io/domboeckli/sbx-claude:<basever>`):

```powershell
sbx run docker.io/domboeckli/sbx-claude:local `
    --skills=off `
    --static-mcp idea,k8s,docker `
    . `
    "C:\development\maven-repo:ro"
```

Ohne publiziertes Image baut `sbx` das Kit direkt aus dem Verzeichnis:

```powershell
sbx run ./claude-v3-agent/ `
    --skills=off `
    --static-mcp idea,k8s,docker `
    . `
    "C:\development\maven-repo:ro"
```

**Mammouth Code** (v3-Workload, eigenes Image `docker.io/domboeckli/sbx-mammouth:<mammouth-version>`):

```powershell
sbx run docker.io/domboeckli/sbx-mammouth:local `
    --skills=off `
    --static-mcp idea,k8s,docker `
    . `
    "C:\development\maven-repo:ro"
```

Alternativ baut `sbx` das Kit direkt aus dem Verzeichnis:

```powershell
sbx run ./mammouth-agent/ `
    --skills=off `
    --static-mcp idea,k8s,docker `
    . `
    "C:\development\maven-repo:ro"
```

**Mistral Vibe** (v3-Workload, eigenes Image `docker.io/domboeckli/sbx-mistral-vibe:<vibe-version>`):

```powershell
sbx run docker.io/domboeckli/sbx-mistral-vibe:local `
    --skills=off `
    --static-mcp idea,k8s,docker `
    . `
    "C:\development\maven-repo:ro"
```

Ohne publiziertes Image baut `sbx` das Kit direkt aus dem Verzeichnis:

```powershell
sbx run ./mistral-vibe-agent/ `
    --skills=off `
    --static-mcp idea,k8s,docker `
    . `
    "C:\development\maven-repo:ro"
```

**Pi Coding Agent** (v3-Workload, eigenes Image `docker.io/domboeckli/sbx-pi-agent:<pi-version>`):

```powershell
sbx run docker.io/domboeckli/sbx-pi-agent:local `
    --skills=off `
    --static-mcp idea,k8s,docker `
    . `
    "C:\development\maven-repo:ro"
```

Ohne publiziertes Image baut `sbx` das Kit direkt aus dem Verzeichnis:

```powershell
sbx run ./pi-agent/ `
    --skills=off `
    --static-mcp idea,k8s,docker `
    . `
    "C:\development\maven-repo:ro"
```

### Ohne Clone starten (Release-Images)

Für OpenCode/Claude (Kit-Config per `git+…`) einmalig `kit.allowedSources` setzen (siehe INSTALL.md); die v3-Workloads (Mammouth/Mistral Vibe/Pi) ziehen das Release-Image direkt per Image-Ref. `latest` ist der bewegliche master-Publish — für reproduzierbare Läufe den Pin-Tag verwenden.

Ins Projekt wechseln (wird als Workspace gemountet):

```powershell
cd C:\development\projects\mein-projekt
```

**OpenCode v3** (v3-Workload, Release-Image):

```powershell
sbx run docker.io/domboeckli/sbx-opencode:latest `
    --skills=off `
    --static-mcp idea,k8s,docker `
    . `
    "C:\development\maven-repo:ro"
```

**Mammouth Code** (v3-Workload, Release-Image):

```powershell
sbx run docker.io/domboeckli/sbx-mammouth:latest `
    --skills=off `
    --static-mcp idea,k8s,docker `
    . `
    "C:\development\maven-repo:ro"
```

**Mistral Vibe** (v3-Workload, Release-Image):

```powershell
sbx run docker.io/domboeckli/sbx-mistral-vibe:latest `
    --skills=off `
    --static-mcp idea,k8s,docker `
    . `
    "C:\development\maven-repo:ro"
```

**Pi Coding Agent** (v3-Workload, Release-Image):

```powershell
sbx run docker.io/domboeckli/sbx-pi-agent:latest `
    --skills=off `
    --static-mcp idea,k8s,docker `
    . `
    "C:\development\maven-repo:ro"
```

### CLI-Versionen & Tooling-Image-Tags (gepinnt, Renovate-managed)

Alle Kits nutzen die von Docker verwaltete `docker.io/sbx/shell-docker-image:latest`-Basis und pinnen ihre jeweilige
CLI — **`OPENCODE_VERSION`** (npm `opencode-ai`, bewusst 1.x), **`CLAUDE_VERSION`** (npm `@anthropic-ai/claude-code`),
`MAMMOUTH_VERSION`, `VIBE_VERSION`, `PI_VERSION` — Renovate-managed:

- **OpenCode v3**: `docker.io/domboeckli/sbx-opencode:<tag>` — v3-Workload-Image (Basis `docker.io/sbx/shell-docker-image:latest` + Tooling + Config), `<tag>` = OpenCode-CLI-Version (`OPENCODE_VERSION`)
- **Claude Code v3**: `docker.io/domboeckli/sbx-claude:<tag>` — v3-Workload-Image (Basis + Tooling + Config), Tag = Claude-CLI-Version (`CLAUDE_VERSION`)
- **Mammouth**: `docker.io/domboeckli/sbx-mammouth:<tag>` — v3-Workload, baut auf `docker.io/sbx/shell-docker-image:latest` auf (Tooling **+ Mammouth-CLI** vorgebacken)
- **Mistral Vibe**: `docker.io/domboeckli/sbx-mistral-vibe:<tag>` — eigenes Image, baut auf `docker.io/sbx/shell-docker-image:latest` auf (`<tag>` = Vibe-Version)
- **Pi**: `docker.io/domboeckli/sbx-pi-agent:<tag>` — v3-Workload (Descriptor + Dockerfile), baut auf `docker.io/sbx/shell-docker-image:latest` auf (schmale Shell-Basis; `<tag>` = Pi-Version)

Die Pins werden auf Konsistenz geprüft: `OPENCODE_VERSION`/`CLAUDE_VERSION` als Dockerfile-`ARG`, Konstante in
`local-test/local-test-kits.py` und Variable in `.github/workflows/validate.yml` + `e2e.yml` (Renovate-managed). Die
Basis aller Custom-Workload-Kits (OpenCode v3, Claude v3, Mammouth, Mistral Vibe, Pi) ist bewusst die von Docker
empfohlene, nightly neu gebaute `docker.io/sbx/shell-docker-image:latest` (Digest-gepinnt — Renovate aktualisiert den Digest, wenn das Nightly weiterzieht).
`python local-test/local-test-kits.py --validate-only` **warnt** (gelb) bei neueren Docker-Hub-/npm-Versionen und
schlägt bei Drift fehl.

**Image-Tags** — Schema für alle Agent-Images; `<version>` = `OPENCODE_VERSION` (OpenCode v3)
bzw. `CLAUDE_VERSION` (Claude v3) bzw. die Agent-Version (Mammouth/Mistral Vibe/Pi), `<branch-slug>` = Branch-Name
(lowercase), `<timestamp>` = UTC `YYYYMMDDHHMMSS`:

| Kontext | Tag(s) |
|---------|--------|
| Lokal (Run-Config `build-and-publish-<name>-image`) | `<version>-<branch-slug>.<timestamp>` + `:local` |
| master/main (CI) | `<version>` + `:latest` |
| Feature-Branch / PR (CI) | `<version>-<branch-slug>.<timestamp>` + `<branch-slug>` |

Die Images müssen vor dem ersten Start **publiziert** sein — CI via `.github/workflows/build-and-publish-<name>-image.yml`
(`workflow_dispatch`/Push auf `master`), lokal via Run-Config `build-and-publish-<name>-image`. Für die **lokale
Entwicklung** daher `:local` verwenden (siehe „Lokale Entwicklung"); für Remote-Bezug `:latest`. Details: `AGENTS.md`
→ "Image-Versionierung (Tooling-/Agent-Images)".

### Registry umschalten (Docker Hub ↔ Cloudsmith)

Der Image-Prefix (Registry + Namespace [+ Repo]) ist **zentral** über `IMAGE_PREFIX` steuerbar
(`<IMAGE_PREFIX>/sbx-<name>:<tag>`):

| Registry | `IMAGE_PREFIX` |
|----------|----------------|
| Docker Hub (**Default**) | `docker.io/domboeckli` |
| Cloudsmith (Ausweich) | `docker.cloudsmith.io/dboeckli/sbx` |

Gesetzt wird er an drei Stellen (identischer Wert, Pfad-Komposition ist registry-unabhängig):

1. **CI** — GitHub-**Repo-Variable** `IMAGE_PREFIX` (`.github/workflows/build-and-publish-*-image.yml` + `e2e.yml`
   lesen `vars.IMAGE_PREFIX || 'docker.io/domboeckli'`). Fehlt sie → Docker-Hub-Default.
2. **Lokal/e2e-Runner** — Env `IMAGE_PREFIX` (`local-test/local-test-kits.py`, `local-test/build-and-publish-*.py`;
   zusätzlich in allen IntelliJ-Run-Configs gesetzt).
3. **Agent-Kits** — Mammouth/Mistral Vibe (v3) per Image-Ref
   → `args.imagePrefix`, Default Docker Hub); CI/e2e/local-test übergeben ihn automatisch.

Fertige `sbx run`-Kommandos für die Docker-Hub-Images (4 lokal + 4 remote): [`docs/dockerhub-images.md`](docs/dockerhub-images.md).

**Wechsel zu Cloudsmith** = Repo-Variable/Env explizit auf `docker.cloudsmith.io/dboeckli/sbx` setzen — die
Defaults in Workflows/Specs bleiben Docker Hub. `cleanup-cloudsmith.yml` läuft nur im Cloudsmith-Modus.
Der Cloudsmith-**API**-Service (`api.cloudsmith.io`, Helm-OCI) ist davon unberührt.

#### Nach Cloudsmith wechseln (Prozedur)

Cloudsmith nur als Ausweich nutzen, wenn die OSS-Quote frei ist (Bandwidth = 100 % ⇒ Downloads liefern `HTTP 402`).

```bash
# 1. Quota prüfen (RESET des 30-Tage-Fensters abwarten; angezeigt unter /v1/quota/oss/dboeckli/)
curl -s -H "X-Api-Key: $CLOUDSMITH_API_KEY" https://api.cloudsmith.io/v1/quota/oss/dboeckli/
#    -> bandwidth percentage_used < 100 (inkl. Puffer für den nächsten e2e-Lauf)

# 2. Umschalter umstellen (explizit auf Cloudsmith; Löschen der Variable -> Docker-Hub-Default)
gh variable set IMAGE_PREFIX --body "docker.cloudsmith.io/dboeckli/sbx" --repo dboeckli/opencode-sandbox-kit
```

3. **Cloudsmith-Images auffrischen** — Merge/`workflow_dispatch` auf `master`: die 4 `build-and-publish-*` pushen
   `<pin>` + `latest` nach Cloudsmith (die alten Cloudsmith-Images sind vom Stand vor dem Switch).
4. **Lokal/Ad-hoc:** `IMAGE_PREFIX=docker.cloudsmith.io/dboeckli/sbx` setzen (unset → Docker-Hub-Default);
   manuelle `sbx run --template docker.cloudsmith.io/dboeckli/sbx/sbx-...`.
5. **Docker-Hub-Images:** können liegen bleiben (kein Cleanup-Workflow; optional manuell löschen).

Automatisch wieder aktiv: Cloudsmith-Registry-Credential im e2e (`CLOUDSMITH_USERNAME`/`CLOUDSMITH_API_KEY`) und
`cleanup-cloudsmith.yml`.

### Ubuntu-WSL

Windows-Pfade im WSL-Format (`/mnt/c/...`) verwenden; ins Projekt wechseln (wird als Workspace gemountet):

```bash
cd /mnt/c/development/projects/spring-6-reactive
```

**OpenCode v3** (v3-Workload, Release-Image):

```bash
sbx run docker.io/domboeckli/sbx-opencode:latest \
    --skills=off \
    --static-mcp idea,k8s,docker \
    . \
    "/mnt/c/development/maven-repo:ro"
```

**Claude Code v3** (v3-Workload, Release-Image):

```bash
sbx run docker.io/domboeckli/sbx-claude:latest \
    --skills=off \
    --static-mcp idea,k8s,docker \
    . \
    "/mnt/c/development/maven-repo:ro"
```

**Mammouth Code** (v3-Workload, Release-Image):

```bash
sbx run docker.io/domboeckli/sbx-mammouth:latest \
    --skills=off \
    --static-mcp idea,k8s,docker \
    . \
    "/mnt/c/development/maven-repo:ro"
```

**Mistral Vibe** (v3-Workload, Release-Image):

```bash
sbx run docker.io/domboeckli/sbx-mistral-vibe:latest \
    --skills=off \
    --static-mcp idea,k8s,docker \
    . \
    "/mnt/c/development/maven-repo:ro"
```

Die Sandbox ist eine MicroVM (nerdbox) mit Hypervisor-Isolation, die `sbx` über Docker Desktop orchestriert — kein Container im Host-Daemon. Der IntelliJ-MCP-Server läuft auf dem Host (`localhost:64615`, Port 64615 seit IDEA 2026.2.2) und wird über den **sbx MCP Gateway** (`mcp-gateway.docker.internal`, host-seitig registriert via `sbx mcp add`) in die Sandbox geliefert.

## Architektur

```mermaid
flowchart TB
    Dev["👨‍💻 Developer"]

    subgraph Host["Windows Host"]
        SBX["sbx CLI"]
        IDE["IntelliJ IDEA\nMCP Server :64615"]
        WS["📁 Workspace\nC:\\development\\projects\\..."]
        K8SMCP["☸️ Kubernetes MCP Server (voller Umfang)\nHost-seitig, keine Sandbox-Credentials\nWhitelist: read-only allow, write ask"]
        DOCKERMCP["🐳 Docker MCP Server\nHost-Docker (read-only allow, write ask)"]
        M2["📦 maven-repo (read-only)\nHost-Maven-Cache"]
        Secrets["🔑 Secrets Store\n(OS Keychain)"]
        Hub["🐳 Docker Hub\ndocker.io/domboeckli/sbx-mistral-vibe"]

        subgraph DD["Docker Desktop (Windows Host)"]
            Proxy["🌐 Host-seitiger Proxy\n• Network Policies (allow / deny)\n• Credential Injection\n• Credential Proxy (never enters VM)"]

            subgraph VM["Sandbox MicroVM (nerdbox) — Hypervisor-Isolation"]
                Agent["🤖 AI Coding Agent\n(opencode / claude / mammouth / mistral-vibe)"]
                Dockerd["🐳 Isolierter Docker Daemon"]
                FS["📂 Filesystem Passthrough\n(selber Pfad wie Host)"]
                Kit["🔌 Kit (v3-Workload)\n(Tools, Skills, Config)"]

                Agent -->|"docker CLI"| Dockerd
                Agent -->|"liest / schreibt"| FS
                Agent -->|"MCP Client via sbx MCP Gateway\n(mcp-gateway.docker.internal)"| Proxy
            end

            Proxy -->|"forward"| IDE
            Proxy -->|"MCP (k8s, Whitelist)"| K8SMCP
            Proxy -->|"MCP (Host-Docker)"| DOCKERMCP
        end
    end

    Dev -->|"sbx run / create"| SBX
    SBX -->|"startet"| VM
    SBX -->|"übergibt Workspace"| WS
    SBX -->|"zieht Kit + Image"| Hub
    WS -.->|"Filesystem Passthrough"| FS
    M2 -.->|"read-only Mount"| FS
    Secrets -.->|"injiziert via Proxy"| Proxy
```

**Externe Ziele (über den Sandbox-Proxy):**

```mermaid
flowchart TB
    Proxy["🌐 Sandbox-Proxy\nNetwork Policy + Credential Injection"]
    Proxy -->|"GitHub API / gh CLI"| GH["github.com"]
    Proxy -->|"npm / ctx7 / Maven"| PKG["Package Registries\n(npm, Maven Central, ctx7)"]
    Proxy -->|"LLM API"| LLM["☁️ LLM Provider API\n(DeepSeek / Anthropic / Mammouth / Mistral / Z.AI / OpenRouter / Google)"]
```

## MCP-Server (Host)

Drei host-seitige MCP-Server werden über den **sbx MCP Gateway** in die Sandbox geliefert. Die Client-Verdrahtung
(`mcp-gateway` → `http://mcp-gateway.docker.internal/mcp`) legt `sbx` nur für die **unterstützten** Agenten an
**OpenCode v3** (`~/.config/opencode/opencode.jsonc`), **Claude Code v3** (`~/.claude.json`), **Mammouth**
(`mammouth-agent/files/home/.config/mammouth/opencode.jsonc`) und **Mistral Vibe**
(`mistral-vibe-agent/files/home/.vibe/config.toml`, Issue #139) bringen sie in ihrer Kit-Config selbst mit.
Einmalig host-seitig registrieren, dann die Sandbox mit `--static-mcp` erzeugen:

| Server | Host | Registrierung (einmalig, PowerShell) |
|--------|------|--------------------------------------|
| **IntelliJ MCP** | IntelliJ IDEA (JetBrains MCP Server, Port `64615` seit IDEA 2026.2.2, Endpoint `/stream`) | `sbx mcp add idea --url http://localhost:64615/stream --skip-ssrf-check` |
| **Kubernetes** | `kubernetes-mcp-server` (voller Umfang, Toolsets `core,config,helm`; keine Sandbox-Credentials) | `sbx mcp add k8s --command "$env:USERPROFILE\.local\bin\kubernetes-mcp-server.exe" --args "--config,$env:USERPROFILE\.config\kubernetes-mcp-server\config.toml"` |
| **Docker** | `dboeckli/mcp-server-docker`-Fork via `uvx` (`v0.6.0`: steuert den Host-Docker-Daemon + Docker-/Buildx-Introspektion, Issue #250) | `sbx mcp add docker --command (Get-Command uvx).Source --args "--from,git+https://github.com/dboeckli/mcp-server-docker@v0.6.0,mcp-server-docker"` |

```powershell
sbx run ./opencode-v3-agent/ `
    --skills=off `
    --static-mcp idea,k8s,docker
```

Nachträglich in eine laufende Sandbox laden: `sbx mcp load <name> --sandbox <sandbox-name>`. Die Tools erscheinen als `mcp-gateway_<tool>` (OpenCode/Mammouth/Mistral Vibe), `mcp__mcp-gateway__<tool>` (Claude Code) bzw. `mcp__mcp_gateway__<tool>` (Pi).

**Permission-Modell:** Deny-by-default — nur lesende MCP-Tools sind `allow`; K8s-/Docker-Schreib-/Exec-Tools sind bei OpenCode/Mammouth/Claude `ask` (Freigabe pro Aufruf), bei Mistral Vibe hart `deny` (auto-approve-Hook). `configuration_view` ist gesperrt (würde die Host-`kubeconfig` in die Sandbox liefern).

Details: [Kubernetes-MCP-Server](docs/mcp/kubernetes-mcp-server.md) · [Docker-MCP-Server (Host)](docs/mcp/docker-mcp-server.md) · [IntelliJ MCP Port-Analyse](docs/mcp/intellij-mcp-port.md).

## Dual Agent Support

Das Kit funktioniert mit **OpenCode v3, Claude Code v3, Mammouth Code, Mistral Vibe und Pi** (alles v3-Workloads) –
der Agent wird vom jeweiligen Kit-Image beim `sbx run` bestimmt:

| Agent | Template | Kit |
|-------|----------|-----|
| OpenCode v3 | `docker.io/domboeckli/sbx-opencode` (baut auf `docker.io/sbx/shell-docker-image:latest` auf, OpenCode-CLI via npm gepinnt) | `opencode-v3-agent/` |
| Claude Code v3 | `docker.io/domboeckli/sbx-claude` (baut auf `docker.io/sbx/shell-docker-image:latest` auf, Claude-CLI via npm gepinnt) | `claude-v3-agent/` |
| Mammouth Code | `docker.io/domboeckli/sbx-mammouth` (baut auf `docker.io/sbx/shell-docker-image:latest` auf, Mammouth-CLI gepinnt) | `mammouth-agent/` (v3-Workload, Pin im Descriptor/Dockerfile) |
| Mistral Vibe | `docker.io/domboeckli/sbx-mistral-vibe` (baut auf `docker.io/sbx/shell-docker-image:latest` auf, Vibe via PyPI gepinnt) | `mistral-vibe-agent/` (v3-Workload, eigenes Image) |

Die mehrzeiligen Start-Commands stehen im [Quickstart](#quickstart) oben.

> **Host-MCP-Server via sbx MCP Gateway:** IntelliJ MCP einmalig `sbx mcp add idea --url http://localhost:64615/stream --skip-ssrf-check`
> (Host-Loopback, SSRF-Guard umgehen); Kubernetes und Host-Docker via `sbx mcp add k8s …`/`sbx mcp add docker …`
> (`docs/mcp/kubernetes-mcp-server.md`, `docs/mcp/docker-mcp-server.md`). Dann `--static-mcp idea,k8s,docker` beim Erzeugen
> oder `sbx mcp load <name> --sandbox <sandbox-name>`.
> Die direkten IntelliJ-Host-Ports (`64615`/`64342`) sind bewusst **nicht** in der Sandbox-Allowlist — Zugriff nur
> über den Gateway (sonst wäre die `mcp-gateway_*`-Whitelist per `curl` umgehbar, Issue #163).
> Whitelist und Run-Config-Guard sind Agent-Guardrails, **keine** Netzgrenze: Der Gateway selbst ist aus der
> Sandbox per `curl` erreichbar (Restrisiko, Issue #229). Dasselbe gilt für die mitgelieferte MCP-Inspector-CLI
> (`mcp-inspector --cli`, Issue #231): sie spricht den Gateway direkt an und ist damit ebenfalls ein Weg an der
> Whitelist vorbei — Werkzeug, keine Grenze.
> Alle fünf erhalten dieselben Tools (JDK, Maven, Docker CLI, Helm, Apache Kafka CLI, Bruno CLI, MCP-Inspector CLI, Skills, ctx7) und die
> Host-MCP-Server (IntelliJ/Kubernetes/Docker) über den Gateway
> (`mcp-gateway_<tool>` in OpenCode/OpenCode v3/Mammouth/Mistral Vibe, `mcp__mcp-gateway__<tool>` in Claude Code, `mcp__mcp_gateway__<tool>` in Pi). Die jeweilige
> Konfiguration wird automatisch gelesen:

- **OpenCode v3**: `~/.config/opencode/opencode.jsonc` + `~/.config/opencode/AGENTS.md` — Modell `deepseek/deepseek-flash` (DeepSeek V4.1 Flash); Zusatz-Provider `openrouter`, `google`, `zai` (GLM-5.3-Flash/GLM-5.3 sowie das **gratis** GLM-4.7-Flash via `ZAI_API_KEY`, `sbx secret set zai`) und `mistral` (Mistral-hosted GLM-5.3 `zai-glm-5-3` via `MISTRAL_API_KEY`, `sbx secret set mistral`). Der Model-Picker startet mit einer **Favorites**-Sektion der direkt angebundenen Modelle (DeepSeek V4.1 Flash/V4 Pro, GLM-5.3-Flash/GLM-5.3/GLM-4.7-Flash (gratis) via Z.AI, Mistral-hosted GLM-5.3), geseedet im Entrypoint/Build in `~/.local/state/opencode/model.json` (bestehende Favoriten/Reihenfolge bleiben erhalten, fehlende Seed-Modelle werden bei jedem Start ergänzt)
- **Claude Code v3**: `~/.claude/settings.json` + `~/.claude/CLAUDE.md` + `~/.claude.json` (MCP-Gateway)
- **Mammouth Code**: `~/.config/mammouth/opencode.jsonc` + `~/.config/mammouth/AGENTS.md`
- **Mistral Vibe**: `~/.vibe/config.toml` (MCP-Gateway) + `~/.vibe/hooks.toml` (Read-only-Guard) + `~/.vibe/AGENTS.md`
- **Pi**: `~/.pi/agent/settings.json` (Default-Modell) + `~/.pi/agent/mcp.json` (MCP-Gateway) + `~/.pi/agent/extensions/mcp-guard.ts` (Read-only-Guard) + `~/.pi/agent/AGENTS.md`

### Mammouth Code Agent-Kit

[Mammouth Code](https://info.mammouth.ai/docs/mammouth-code/) ist ein Open-Source-Fork von OpenCode.
Da `sbx` keinen eingebauten `mammouth`-Agenten kennt, liegt unter `mammouth-agent/` ein **eigenes
v3-Workload** (`kind: workload`, Name `mammouth`) – analog zum Pi-Kit:

- **Base-Image**: `docker.io/sbx/shell-docker-image:latest` (Mammouth ist ein OpenCode-Fork;
  Docker-verwaltete Custom-Workload-Basis, kein Semver-Pin — Issue #254)
- **Entrypoint**: `mammouth-entrypoint` (seedet Favoriten, dann `exec mammouth`)
- **Auth**: `credential@1` für `api.mammouth.ai` (`name: MAMMOUTH_API_KEY`, `proxyManaged: true`,
  `inject` als `Authorization: Bearer`) — kit-spec v3
- **Tools**: installiert dieselben Tools wie die anderen Kits (JDK, Maven, Docker CLI, kubectl, Helm, Apache Kafka CLI, Bruno CLI, MCP-Inspector CLI, ctx7, Skills)
- **Config**: `~/.config/mammouth/opencode.jsonc` + `~/.config/mammouth/AGENTS.md`

Die Konfiguration liegt unter `~/.config/mammouth/` (XDG-app `mammouth`):

- **Modell**: `deepseek/deepseek-flash` (DeepSeek V4.1 Flash) als Default; Zusatz-Provider `zai` (GLM-5.3-Flash/GLM-5.3 sowie das **gratis** GLM-4.7-Flash via `ZAI_API_KEY`, `sbx secret set zai`) und `mistral` (Mistral-hosted GLM-5.3 `zai-glm-5-3` via `MISTRAL_API_KEY`, `sbx secret set mistral`). Der Model-Picker startet mit derselben **Favorites**-Sektion wie OpenCode (DeepSeek V4.1 Flash/V4 Pro, GLM-5.3-Flash/GLM-5.3/GLM-4.7-Flash (gratis) via Z.AI, Mistral-hosted GLM-5.3), geseedet in `~/.local/state/mammouth/model.json` (Mammouth ist ein OpenCode-Fork, gleiches Schema; bestehende Favoriten/Reihenfolge bleiben erhalten, fehlende Seed-Modelle werden bei jedem Start ergänzt). Der Seed läuft **im Entrypoint** (`mammouth-entrypoint` → `seed-mammouth-model-favorites.py`) und beim Image-Build — nicht über Lifecycle-`startup`, weil dieser erst **nach** dem TUI-Start läuft und Mammouth seinen In-Memory-Stand (ohne Favoriten) zurückschreibt. Änderungen an `model.json` bei laufendem TUI wirken erst nach einem Mammouth-Neustart.
- **IntelliJ/Kubernetes/Docker MCP**: über den sbx MCP Gateway (`mcp-gateway_<tool>`); da `sbx` Mammouth nicht als
  Agent-Integration kennt, ist der Gateway im Kit **explizit** verdrahtet (`mcp`-Block in `opencode.jsonc` →
  `http://mcp-gateway.docker.internal/mcp`, `Bearer proxy-managed`, Issue #139) — keine direkte `mcp.idea`-Config
- **Plugins**: Startup-Checks + Auto-Session (identisch zu OpenCode, da Fork)
- **PATH**: `mammouth`-Binary via Symlink `/usr/local/bin/mammouth` aufgelöst; `JAVA_HOME` via Dockerfile-`ENV` (v3)

**Installation** — das Image `docker.io/domboeckli/sbx-mammouth` backt Mammouth beim **Image-Build**, gepinnt auf
**v1.18.31.2** (`ARG MAMMOUTH_VERSION` im `mammouth-agent/mammouth-agent.dockerfile`, ausgeführt als User `agent`;
Pin via Renovate `mammouth-ai/code`; `local-test-kits.py --validate-only` warnt bei neuerem
GitHub-Release) und legt einen Symlink `/usr/local/bin/mammouth` an, damit der Entrypoint den
Agenten findet. Manuell nur nötig, wenn die Sandbox bereits läuft:

```bash
curl -fsSL https://code.mammouth.ai/install.sh | VERSION=1.18.31.2 bash
```

**Update/Uninstall:** `mammouth upgrade` bzw. `mammouth uninstall`.

> **Auth / Secret / Verifikation:** siehe [`INSTALL.md`](INSTALL.md#5-secrets-registrieren) — API-Key, `sbx secret set mammouth`, Platzhalter-Check.

### Mistral Vibe Agent-Kit

[Mistral Vibe](https://github.com/mistralai/mistral-vibe) ist Mistrals Open-Source-Coding-Agent (Python-CLI,
PyPI `mistral-vibe`). Da `sbx` keinen eingebauten `mistral-vibe`-Agenten kennt und Vibe kein vorgefertigtes
`docker/sandbox-templates`-Image ist, liegt unter `mistral-vibe-agent/` ein **eigenes Sandbox-Kit**
(v3-Workload, Name `mistral-vibe`) — nach dem [Docker-Guide](https://docs.docker.com/guides/mistral-vibe-sandbox/):

- **Base-Image**: eigenes, gepinntes Image `docker.io/domboeckli/sbx-mistral-vibe:<vibe-version>` — gebaut aus
  `docker.io/sbx/shell-docker-image:latest` + `uv tool install mistral-vibe==<pin>` (siehe `mistral-vibe-agent/mistral-vibe-agent.dockerfile`).
  Publiziert **multi-arch (linux/amd64 + linux/arm64)** via
  `.github/workflows/build-and-publish-mistral-vibe-image.yml`: pro Architektur ein **nativer** Runner
  (`ubuntu-latest` / `ubuntu-24.04-arm`), Per-Arch-Image mit der Architektur im **Repo-Namen**
  (`docker.io/domboeckli/sbx-mistral-vibe-amd64` / `-arm64`), danach Manifest-Merge zum Multi-Arch-Index unter
  `docker.io/domboeckli/sbx-mistral-vibe` (`docker buildx imagetools create`; `uv tool install` läuft nicht unter QEMU-arm64).
- **Launch**: `sandbox.entrypoint: [vibe, "--agent", "auto-approve"]` in der spec (für `kind: sandbox` startet sbx ohne `entrypoint` die Default-Shell); das Dockerfile-`CMD` bleibt für `docker run`.
- **Auth**: Kit-deklarierter Service `mistral` → `MISTRAL_API_KEY` (Built-in-Service `mistral`, Sentinel
  `proxy-managed`, Proxy injiziert `Authorization: Bearer` für `api.mistral.ai`).
- **Start-Modell GLM-5.3-Flash (Z.AI)**: `spec.yaml` pinnt `VIBE_ACTIVE_MODEL=glm-flash` (Env-Layer gewinnt,
  ein persistierter `/model`-Wechsel leakt nicht in den nächsten Start); `~/.vibe/config.toml` setzt
  `active_model = "glm-flash"` und definiert
  Z.AI als OpenAI-kompatiblen Provider (`[[providers]]` `zai` → `https://api.z.ai/api/paas/v4`, `ZAI_API_KEY`;
  `[[models]]` `glm-flash` → `glm-5.3-flash`). **GLM-5.3 (Flagship) ist ebenfalls direkt über Z.AI wählbar**
  (Alias `glm-5.3` → `glm-5.3`, gleicher Provider/Key; ~10x Preis, stärker bei Agent-/Coding-Benchmarks), ebenso
  das **kostenlose GLM-4.7-Flash** (Alias `glm-4.7-flash`, leichtgewichtig, 200K Kontext).
  Alle gibt es **nur direkt bei Z.AI** (nicht über Mistral); Kit-Service `zai`
  (`sbx secret set zai`, Key: https://z.ai/manage-apikey/apikey-list).
- **Alternative ohne Z.AI-Key**: Mistral hostet GLM 5.3 selbst (`zai-glm-5-3`, Alias `glm`, Provider `mistral`,
  gleiche `MISTRAL_API_KEY`) — in der TUI per `/model` wählbar.
- **Config**: `~/.vibe/config.toml` (MCP-Gateway auf `http://mcp-gateway.docker.internal/mcp` + GLM-Provider/-Modelle),
  `~/.vibe/hooks.toml` + `~/.config/sandbox-kit/vibe-mcp-guard.py` (Read-only-Guard für die IntelliJ-MCP-Tools,
  da `auto-approve` das Permission-System umgeht) und `~/.vibe/AGENTS.md`.
- **Tools**: dieselben wie die anderen Kits (JDK, Maven, Docker CLI, kubectl, Helm, Apache Kafka CLI, Bruno CLI, MCP-Inspector CLI, ctx7, Skills).

> **Modell-Verfügbarkeit (wichtig):** **GLM-5.3-Flash** (`glm-5.3-flash`), **GLM-5.3** (`glm-5.3`) und
> **GLM-4.7-Flash** (`glm-4.7-flash`, gratis) sind direkt bei Z.AI verfügbar (`api.z.ai`, Provider `zai`, `ZAI_API_KEY`, `sbx secret set zai`) — **nicht über
> Mistral**. Über Mistral (la Plateforme) sind nur **`zai-glm-5-3`** und **`zai-glm-5-2`** verfügbar (Provider
> `mistral`, `MISTRAL_API_KEY`). Default ist GLM-5.3-Flash über den Z.AI-Provider; `glm` (Mistral-hosted
> `zai-glm-5-3`) ist die key-freie Alternative.

> **Image-Publish:** Das Image wird in CI gebaut (multi-arch amd64+arm64; native Runner + `imagetools create`). Der e2e-Workflow
> ruft den (auch manuell per `workflow_dispatch` startbaren) `build-and-publish-mistral-vibe-image.yml` als
> `publish-image`-Job **vor** der Szenario-Matrix auf. Gepusht wird nur auf `master`/`main`/Nightly (`push: true`);
> auf Branches/PRs läuft der Build nur (`push: false`) — das `e2e`-Szenario baut dann das **lokale Kit-Verzeichnis**
> (Branch-Stand). Das **frisch gebaute Branch-Image** prüft der Build-Job selbst: er lädt es (`load`) und vergleicht
> `vibe --version` im Image mit `ARG VIBE_VERSION` (`docker run --entrypoint vibe <img> --version`). Manuell: Workflow
> `Publish Mistral Vibe image` → *Run workflow*.
>
> **Tags:** `master`/`main` → `<pin>` (z. B. `2.25.5`) **und** `latest`. Feature-Branch/PR (nur gebaut, nicht
> gepusht) würde semver-Prerelease `<pin>-<branch-slug>.<YYYYMMDDHHMMSS>` plus beweglicher Tag `<branch-slug>`
> tragen. Das `e2e`-Szenario nutzt auf `master`/Nightly den Release-Tag `<pin>` (Image-Ref
> `<IMAGE_PREFIX>/sbx-mistral-vibe:<pin>`), auf Branches/PRs das lokale Kit-Verzeichnis. Der Pin steht in
> `mistral-vibe-agent/mistral-vibe-agent.yaml` (`args.version.default`) und im Dockerfile (`ARG VIBE_VERSION`).
>
> **Lokal (Windows-Host):** IntelliJ-Run-Config **`build-and-publish-mistral-vibe-image`** (baut + pusht) — Tag wie beim
> Feature-Branch-Build (`<pin>-<branch-slug>.<timestamp>`, semver) **plus** beweglicher Tag `local`.
>
> Build + push + lokal laden:
> ```powershell
> python local-test\build-and-publish-mistral-vibe-image.py
> ```
> Nur pushen:
> ```powershell
> python local-test\build-and-publish-mistral-vibe-image.py --no-load
> ```
> Nur bauen:
> ```powershell
> python local-test\build-and-publish-mistral-vibe-image.py --build-only
> ```
> Neben dem Push in die Registry wird das Image in den **lokalen Docker-Daemon** geladen (zweiter,
> gecachter Build).
> Voraussetzung: `docker` (Docker Desktop) mit `docker login` (Push nach Docker Hub). Der Vibe-Pin und
> `args.version.default` im Descriptor werden per Renovate (PyPI `mistral-vibe`) gemeinsam aktualisiert.

> **Auth / Secret / Verifikation:** siehe [`INSTALL.md`](INSTALL.md#mistral-authentication) — `sbx secret set mistral`, Platzhalter-Check.

### Pi Coding Agent-Kit (Kit-Spec v3)

[Pi](https://pi.dev) (`@earendil-works/pi-coding-agent`) ist ein minimaler, erweiterbarer Coding-Agent.
Das Kit liegt unter `pi-agent/` und ist bewusst als **Kit-Spec v3** umgesetzt (`# syntax=docker/sandbox-kit:3`,
`schemaVersion: "3"`, `kind: workload`) — Descriptor `pi-agent/pi-agent.yaml` + `pi-agent/pi-agent.dockerfile`.
v3 benötigt `sbx` ≥ v0.45 (Repo-Pin: v0.53.0). **v3-Kits lassen sich nicht mit v1/v2-Kits kombinieren**
(`--template` entfällt); das Pi-Kit ist ein eigenständiger Workload.

- **Image**: `docker.io/domboeckli/sbx-pi-agent:<pi-version>` — baut auf `docker.io/sbx/shell-docker-image:latest`
  auf (schmale Shell-Basis) und backt **dasselbe Tooling wie die anderen Kits** (Node 26, JDK, Maven, Docker CLI/Compose, kubectl, Helm, Kafka,
  shfmt, ctx7, skills, prettier, renovate, Bruno CLI, MCP-Inspector) plus Pi `1.5.0` (Pin im Descriptor,
  `buildArg: PI_VERSION`). Die Tooling-Skripte sind identische Kopien (`local-test-kits.py --validate-only` prüft Drift).
- **Launch**: `ENTRYPOINT ["pi"]` im Dockerfile; Entrypoint/Config kommen aus dem Image, nicht aus einem `sandbox:`-Block.
- **Config**: `~/.pi/agent/settings.json` (`defaultProvider: deepseek`, `defaultModel: deepseek-flash`),
  `~/.pi/agent/mcp.json` (eingebautes MCP, Gateway `http://mcp-gateway.docker.internal/mcp`, `Bearer proxy-managed`),
  `~/.pi/agent/extensions/mcp-guard.ts` (Read-only-Whitelist + Run-Config-Guard, gemeinsame Allow-Liste)
  und `~/.pi/agent/AGENTS.md` (Sandbox-Regeln via `agent-context`-Capability).
- **Auth**: `credential@1`-Capabilities für `deepseek`, `zai`, `mistral`, `openrouter`, `google` (`GEMINI_API_KEY`),
  `context7`, `stackoverflow`, `cloudsmith`, `github-maven`, `sonarcloud`, `codeberg` — alle `proxyManaged`
  (Sentinel `proxy-managed`). Secret-Registrierung: `sbx secret set deepseek` (Default-Modell), optional
  `sbx secret set zai`/`mistral`/`openrouter`/`google`.
- **Startup**: Lifecycle-Capability importiert die Proxy-CA in die JDK-`cacerts` und schreibt `~/.m2/settings.xml`
  (Proxy-Routing, `github-maven`, Host-Cache) — identisch zum OpenCode-Kit.
- **Publish**: `.github/workflows/build-and-publish-pi-image.yml` (multi-arch amd64+arm64, native Runner +
  `imagetools create`; Build mit `-f pi-agent/pi-agent.yaml`). Lokal: Run-Config `build-and-publish-pi-image`
  bzw. `python local-test\build-and-publish-pi-image.py` (Tag `<pi-version>-<branch-slug>.<timestamp>` + `local`).
- **Tags**: master `<pi-version>` + `latest`; Branch/PR `<pi-version>-<slug>.<ts>` + `<slug>`; lokal `local`.
  Der e2e-Workflow zieht auf master/schedule das Release-Image, auf Branches/PRs baut `sbx` das lokale Kit-Verzeichnis.

> **Auth / Secret / Verifikation:** siehe [`INSTALL.md`](INSTALL.md) — `sbx secret set deepseek` (Default), weitere
> Provider optional; Platzhalter-Check via `sbx exec <sandbox> env`.

### Claude Code Konfiguration

`~/.claude/settings.json` enthält:

- **Modell**: `claude-sonnet-4-6` als Default (`"model"`). Zusätzlich per Env-Variablen abgesichert
  (`ANTHROPIC_DEFAULT_SONNET_MODEL` + `ANTHROPIC_MODEL` via Kit-`environment.variables`), damit das Template
  die settings.json nicht mit einem Default-Modell (Opus 5) überschreiben kann.
- **IntelliJ MCP**: über den sbx MCP Gateway (`mcp__mcp-gateway__<tool>`), keine direkte `mcpServers.idea`-Config
- **StatusLine**: `bash ~/.claude/statusline.sh` – zeigt Modell, Kontext-Tokens, Kosten, geänderte Zeilen und Session-Dauer
- **SessionStart-Hook**: führt die Sandbox-Checks aus und übergibt den Report als System-Message
  (StatusLine + Hooks liegen in `managed-settings.json` unter `/etc/claude-code/` – höchste Precedence,
  Template-sicher, kein Settings-Race beim Start, siehe [session-start-hook-fix.md](docs/session-start-hook-fix.md))
- **Permission-Whitelist + Run-Config-Guard**: siehe Abschnitt "IntelliJ MCP Zugriff einschränken"

> **Hinweis:** Der Entrypoint `claude-entrypoint` merged die Kit-Felder aus `settings.kit.json` (und das
> MCP-Gateway in `~/.claude.json`) **vor** dem CLI-Start — u.a. `defaultMode: default` (damit `permissions.ask`
> für die K8s-Schreib-/Exec-Tools greift) und die Permission-Listen. Das Modell wird zusätzlich fest über die
> Env-Variablen erzwungen. Nach Änderungen am Kit das Image neu bauen (`build-and-publish-claude-v3-image`).

Die StatusLine (`~/.claude/statusline.sh`) wird beim Sandbox-Build aus
[dboeckli/ai-agent-skills](https://github.com/dboeckli/ai-agent-skills) installiert.

## Automatisierter Kit-Test

Die 5 Agent-Szenarien (OpenCode v3, Claude v3, Mammouth, Mistral Vibe, Pi) lassen sich lokal automatisiert testen —
`local-test-kits.py` (cross-platform, Windows + Linux/macOS) validiert alle Kits, prüft die
Secrets, baut pro Szenario eine Sandbox, prüft Tools/Config/Startup-Checks und räumt danach auf.

Als **Workspace** mounten die Szenarien den **Repo-Root** (`--workspace <pfad>` bzw. `$WORKSPACE_DIR`
übersteuert; Default ist nicht das Aufrufverzeichnis). Der Test startet den Agenten nicht und schreibt
nichts ins Workspace.

Alle 5 Szenarien (ohne `--keep`: Sandboxes werden wieder entfernt):

```bash
python local-test/local-test-kits.py
```

Sandboxes nach dem Test behalten:

```bash
python local-test/local-test-kits.py --keep
```

Nur Kit-Validierung, keine Sandboxes:

```bash
python local-test/local-test-kits.py --validate-only
```

Lokales Testen in **Windows PowerShell** (Docker Desktop nativ):

Alle 5 Szenarien (ohne `--keep`: Sandboxes werden wieder entfernt):

```powershell
python .\local-test\local-test-kits.py
```

Sandboxes nach dem Test behalten:

```powershell
python .\local-test\local-test-kits.py --keep
```

Nur Kit-Validierung, keine Sandboxes:

```powershell
python .\local-test\local-test-kits.py --validate-only
```

Voraussetzungen: Docker läuft (auf Windows nativ oder im Ubuntu-WSL-Setup), `sbx` im PATH,
globale Secrets gesetzt (`github`, `github-maven`, `anthropic`, `mammouth`, `mistral`, `context7`).
Das Mistral-Vibe-Szenario nutzt lokal den zuletzt **lokal** gebauten Stand (`<IMAGE_PREFIX>/sbx-mistral-vibe:local`, Default Docker Hub, gesetzt von der Run-Config `build-and-publish-mistral-vibe-image`) — also vorher einmal `python local-test\build-and-publish-mistral-vibe-image.py` ausführen. CI/e2e nutzt dagegen `VIBE_IMAGE_TAG`: auf `master`/Nightly den Release-Tag `<pin>`, auf Branches/PRs das publizierte Master-`:latest` (das Branch-Image wird stattdessen im Build-Job auf den Pin geprüft).

### GitHub Actions (CI)

Die Tests laufen zusätzlich automatisiert in GitHub Actions (`.github/workflows/`):

- **`validate.yml`** — bei jedem Push/PR + nightly (03:00 UTC): installiert eine **gepinnte `sbx`-Version**
  (`SBX_VERSION`, aktuell `v0.53.0`), meldet sich via `sbx login` an Docker an (`DOCKER_USERNAME`/`DOCKER_PAT`,
  mit Secret-Service-Setup — sbx >= v0.47.0 verlangt eine Docker-Session für `sbx kit validate`; bei Fork-PRs
  übersprungen, da keine Secrets), validiert die v3-Kits über den Kit-Builder (`sbx kit validate` ohne
  `--offline`; `./opencode-v3-agent/`, `./claude-v3-agent/`, `./mammouth-agent/`, `./mistral-vibe-agent/`,
  `./pi-agent/`) und prüft, dass die Install-Skript-Kopien
  (`files/home/.local/bin/`) in allen Kits identisch sind, sowie dass der Vibe-Image-Tag in
  `args.version.default` im Descriptor zum `ARG VIBE_VERSION` im Dockerfile passt.
- **`e2e.yml`** — bei jedem Push/PR + wöchentlich Montag (03:05 UTC, nach `validate.yml`): baut echte Sandboxes für
  alle 5 Szenarien (`local-test-kits.py opencode-v3|claude-v3|mammouth|mistral-vibe|pi --ci --skip-v3-builder`) mit KVM-Zugriff,
  `sbx login` (`DOCKER_USERNAME`/`DOCKER_PAT`) + Cloudsmith-Registry-Credential (`CLOUDSMITH_USERNAME`/`CLOUDSMITH_API_KEY`, nur wenn `IMAGE_PREFIX` auf Cloudsmith zeigt) und Fake-API-Keys (nur Proxy-Wiring, keine echten Calls).
  Fork-PRs laufen nicht (keine Secrets-Exposition).
- **`build-and-publish-mistral-vibe-image.yml`** — baut/publiziert das gepinnte Vibe-Image (multi-arch amd64+arm64 über native Runner + `imagetools create`)
  unter `<IMAGE_PREFIX>` (Repo-Variable `IMAGE_PREFIX`, Default `docker.io/domboeckli` — siehe „Registry umschalten"). Wird vom `e2e`-Workflow als `publish-image`-Job vor der Matrix aufgerufen; zusätzlich manuell
  via `workflow_dispatch` (Build-only möglich über den `push`-Input). Bei `push: false` (Branch/PR) lädt der Build das Image (`load`) und ein Verify-Step prüft die eingebackene Vibe-Version gegen `ARG VIBE_VERSION`
  (`docker run --entrypoint vibe <img> --version`); analog prüft `build-and-publish-mammouth-image.yml` die Mammouth-CLI-Version gegen `ARG MAMMOUTH_VERSION`.
- **`cleanup-cloudsmith.yml`** — **nur Cloudsmith-Modus** (`IMAGE_PREFIX` startet mit `docker.cloudsmith.io`); löscht Feature-Branch-Image-Snapshots aus `dboeckli/sbx`
  (Tag-Muster `<basever>-<branch-slug>.<YYYYMMDDHHMMSS>` + Moving-Tag `<slug>`; Master-Images
  `<basever>`/`latest` bleiben). Auslöser: **push auf `master`** (Feature-Images nach dem Merge
  obsolet → alle löschen), **nightly 04:25 UTC** (verwaiste Snapshots älter als `max-age-days`) und
  `workflow_dispatch` mit `dry-run` (Default an). Skript:
  `.github/workflows/scripts/cleanup-cloudsmith.py` (analog zu `spring-6-rest-mvc`).
  Zusätzlich werden **untagged Kind-Manifeste** (Plattform/Attestation) gelöscht, die von **keinem**
  verbleibenden Index mehr referenziert werden (echte Orphans); Live-Images (`<basever>`/`latest`)
  bleiben unangetastet (Referenz-Check via Registry-API, fail-safe).
  In den Image-Builds ist `provenance`/`sbom` **deaktiviert** (keine Attestation-Manifeste → weniger
  Package-Bloat).
  Zusätzlich leert die Pipeline den **Recycle Bin** (`purge-cloudsmith-recycle-bin.py`, hard delete):
  soft-gelöschte Packages zählen 7 Tage weiter gegen das Storage-Kontingent; endgültiges Löschen gibt
  Speicher sofort frei (via `purge-recycle-bin` steuerbar, Default an).

> Die **gepinnte `sbx`-Version** (`SBX_VERSION`) wird von Renovate aktualisiert
> (`customManager` für `docker/sbx-releases`, `github-releases`-Datasource).
>
> Die Offline-Referenz `opencode-v3-agent/files/home/sbx-cli.md` (→ `~/sbx-cli.md` in der Sandbox) wird per
> `python local-test/regenerate-sbx-doc.py [<version>]` aus der Release-Binary neu erzeugt
> (Default: `SBX_VERSION` aus `validate.yml`). `local-test-kits.py --validate-only` vergleicht die
> dokumentierte Version mit dem gepinnten `SBX_VERSION` und schlägt fehl bei Abweichung
> (inkl. Hinweis aufs Regen-Skript).
>
> `--validate-only` prüft zusätzlich die **CLI-Pins**: `OPENCODE_VERSION` (npm `opencode-ai`, 1.x) und
> `CLAUDE_VERSION` (npm `@anthropic-ai/claude-code`) als Konstanten in `local-test-kits.py`, Drift-Check gegen die
> gleichnamigen Variablen in `.github/workflows/validate.yml`/`e2e.yml` und die Dockerfile-Pins; die gemeinsame Basis der
> Custom-Workload-Kits (`docker.io/sbx/shell-docker-image:latest`) wird gegen die erwartete Docker-verwaltete Basis
> geprüft (Konstante `SHELL_BASE_IMAGE_EXPECTED` und die Doku-Digests werden per Renovate-Custom-Manager im selben
> gruppierten PR wie die Dockerfiles mitgezogen), die **Mammouth-CLI-Pin** (`VERSION=` im spec-install) gegen das latest GitHub-Release (`mammouth-ai/code`)
> und die **Mistral-Vibe-Pin** (`ARG VIBE_VERSION` im Dockerfile, Image-Tag in der spec, gemeinsame Custom-Workload-Basis)
> gegen die latest PyPI-Version (`mistral-vibe`) — alle **warnen** (gelb), sobald eine neuere Version
> existiert (Renovate-Tracking, s. o.). Die **Bruno-CLI-Pin** (`@usebruno/cli@<v>` in allen drei Specs +
> Tooling-Dockerfiles) wird auf Drift geprüft (fail) und gegen die latest npm-Version verglichen (warn).
> Dasselbe gilt für die **MCP-Inspector-Pin** (`@modelcontextprotocol/inspector@<v>`, Issue #231).

## Startup Checks

Beim Start jeder Session prüft das Kit automatisch die Tooling-Verfügbarkeit
(Context7, gh, Java/Maven, Docker, kubectl, MCP-Gateway/IntelliJ/Kubernetes, Helm, Kafka, Bruno, MCP-Inspector, Skills, SonarCloud) und zeigt den
Report als `[startup-checks] ...` an:

```
[startup-checks] ctx7:OK gh:OK java/maven:OK docker:OK kubectl:OK mcp-gateway:OK mcp-idea:OK mcp-k8s:OK mcp-docker:OK mcp-client:OK mcp-tools:OK helm:OK kafka:OK bruno:OK mcp-inspector:OK skills:OK sonar:OK
```

- **OpenCode**: Ein Server-Plugin führt die Checks sofort beim Start aus, injiziert den Report in den
  System-Prompt und schreibt ihn nach `~/.config/sandbox-kit/startup-checks.report`. Ein TUI-Plugin
  (Auto-Session) startet direkt im Session-View, sodass die Sidebar mit den Blöcken **Startup checks**,
  **Skills** und **MCP & Host Systems** sofort sichtbar ist – ohne ersten Prompt. Der
  **MCP & Host Systems**-Block zeigt live (alle 10s, via `~/.config/sandbox-kit/check-infra.sh`) die
  **MCP-Server** über den sbx-Gateway (`~/.local/bin/mcp-check.sh`: ein MCP-Handshake → `mcp-gateway`, `mcp-idea`,
  `mcp-k8s`, `mcp-docker`, `mcp-client` (Agent-Config deklariert den Gateway) und `mcp-tools` (Startup-Report: `mammouth`/`opencode mcp list` verbindet real über den Agent-Client; die 10s-TUI-Box nutzt die schnelle Variante); die Sandbox hält **keine** kubeconfig (Issue #40) und **keinen** Host-Docker-Port
  (Issue #165)). MCP-Server stehen in einer Zeile. Gebounded per `timeout`.
- **Claude Code**: Ein `SessionStart`-Hook übergibt den Report als System-Message (registriert in `managed-settings.json` unter `/etc/claude-code/`).
- **Mammouth Code** (Agent-Kit): Da Fork von OpenCode, werden dieselben Server-/TUI-Plugins aus `~/.config/mammouth/plugins/` geladen.
- **Mistral Vibe** (Agent-Kit): Kein Auto-Hook (Vibe hat keinen Session-Hook für den Report) — die Checks laufen manuell; `check-infra.sh` ist nur der Parity wegen enthalten.
- **Manuell**: `bash ~/.config/sandbox-kit/run-checks.sh`
- **Referenz**: `~/.config/sandbox-kit/startup-checks.md`

Der Agent bestätigt den Status in der ersten Antwort und schlägt bei einem `FAIL` einen Fix vor.

## Installierte Tools

| Tool | Version | Installiert in |
|------|---------|---------------|
| Node.js | 26.13.0 | `/opt/node` → Symlinks in `/usr/local/bin` (npm-CLIs wie renovate ≥43) |
| Liberica JDK | 25.0.5+11 | `/usr/local/java` |
| Apache Maven | 3.10.0 | `/opt/maven` |
| Docker CLI | 29.9.3 | `/usr/local/bin/docker` (opencode-v3 aus Base; sonst 27.5.1) |
| Docker Compose | 5.7.0 (Plugin) | Base-Image bzw. `/usr/local/lib/docker/cli-plugins/docker-compose` |
| kubectl | latest stable | `/usr/local/bin/kubectl` (Build: v1.37.2) |
| Helm | 4.3.1 | `/usr/local/bin/helm` (+ `helm4` Symlink) |
| Apache Kafka CLI | 4.4.0 (Scala 2.13) | `/opt/kafka` + `kafka-*.sh`-Wrapper in `/usr/local/bin` |
| ctx7 | latest | npm global |
| skills | 1.5.21 | npm global (vercel-labs) |
| renovate | latest | npm global |
| Bruno CLI (`bru`) | 4.3.0 | npm global (`@usebruno/cli`, gepinnt; Renovate) |
| MCP Inspector CLI (`mcp-inspector`) | 2.13.0 | npm global (`@modelcontextprotocol/inspector`, gepinnt; Renovate) |
| MCP-Verbindungs-CLI (`mcpdo`, gleiches npm-Paket; Subcommands `connect`/`tools/list`/`tools/call`) | 2.13.0 | npm global (`@modelcontextprotocol/inspector`, gepinnt; Renovate) |
| jq | distro | apt (StatusLine-Abhängigkeit) |

> **opencode-v3/mammouth/mistral-vibe/pi (Issue #254):** Alle vier basieren auf `docker.io/sbx/shell-docker-image:latest` —
> Node/npm, Docker CLI, Compose und Buildx kommen aus dem Base-Image; Liberica JDK, Maven, Node-Pin usw. installiert
> weiterhin `install-tooling.sh` (wie in allen Kits).

`JAVA_HOME` wird via Kit-`environment.variables` in jeder Shell verfügbar gemacht (Java/Maven liegen über
Symlinks bereits in `/usr/local/bin` und damit auf dem PATH).

## Skills

Das Kit installiert zwei Skill-Bundles nach `~/.agents/skills/` (als `user: "1000"`, via `skills add -g`).

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

> **Superpowers nur als Skills, kein Plugin:** Das OpenCode-Plugin von Superpowers wird bewusst
> **nicht** aktiviert — es gibt also keine automatische Methodik-Injektion/Auto-Trigger beim
> Session-Start; Skills werden bei Bedarf über das `skill`-Tool geladen. So bleiben die Kit-Regeln
> (Feature-Branch, kein Auto-Commit, `target/review`-Diff, Run-Config-Guard) maßgeblich. Update:
> `skills update`.

Skills landen in `~/.agents/skills/` (werden als `user: "1000"` installiert).

> **API-Keys & Secrets:** [`INSTALL.md`](INSTALL.md#5-secrets-registrieren) — alle Services (`sbx secret set`), Konsolen-URLs, Proxy/Platzhalter-Details, Verifikation.

## References

- [Debugging, Analyzing & Logging](docs/debugging-analysis-logging.md)
- [Kubernetes-MCP-Server](docs/mcp/kubernetes-mcp-server.md)
- [Docker-MCP-Server (Host)](docs/mcp/docker-mcp-server.md)
- [MCP-Gateway: Trust-Boundary & lokale Mitigationen](docs/mcp/mcp-gateway-security.md)
- [IntelliJ MCP Port-Analyse](docs/mcp/intellij-mcp-port.md)
- [Session-Start-Hook-Fix (Claude)](docs/session-start-hook-fix.md)
- [sbx CLI Offline-Referenz](opencode-v3-agent/files/home/sbx-cli.md) (`~/sbx-cli.md` in der Sandbox, v0.53.0 — generiert aus der Release-Binary)
- [Codeberg Repo](https://codeberg.org/dboeckli/opencode-sandbox-kit) (kanonisch) — GitHub-Mirror: <https://github.com/dboeckli/opencode-sandbox-kit>
- [Codeberg/Forgejo-Betriebshinweise](docs/codeberg-forgejo.md)
- [Docker Sandbox Kits](https://docs.docker.com/ai/sandboxes/customize/kits/)
- [Kit Spec Reference](https://docs.docker.com/ai/sandboxes/customize/kit-reference/)
- [Docker Blog — AI Coding Agent Horror Stories: Security Risks](https://www.docker.com/blog/ai-coding-agent-horror-stories-security-risks/)
