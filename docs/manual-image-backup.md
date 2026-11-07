# Manuelles Image-Backup (Cloudsmith → Docker Hub)

Einmaliges, **manuelles** Backup der sbx-Tooling-/Agent-Images von
`docker.cloudsmith.io/dboeckli/sbx/…` nach **Docker Hub** — als Ausfallsicherung, wenn
die Cloudsmith-Bandwidth-Quote erschöpft ist.

> **Kein CI-Vorgang.** Das ist ein Notfall-/Einmal-Backup, das auf dem Windows-Host
> (Docker Desktop) ausgeführt wird. Der reguläre, multi-arch Publish läuft weiter über
> die `.github/workflows/build-and-publish-*-image.yml`.

## Hintergrund

- Die Cloudsmith-OSS-Quote ist **pro Namespace** (`dboeckli`) und war zuletzt
  ausgeschöpft → Downloads/Blobs liefern **HTTP 402** (Reset: siehe
  `GET /v1/quota/oss/history/dboeckli/`).
- Betroffene Images:
  - `docker.cloudsmith.io/dboeckli/sbx/sbx-opencode`
  - `docker.cloudsmith.io/dboeckli/sbx/sbx-claude`
  - `docker.cloudsmith.io/dboeckli/sbx/sbx-mammouth`
  - `docker.cloudsmith.io/dboeckli/sbx/sbx-mistral-vibe`
  - `docker.cloudsmith.io/dboeckli/sbx/sbx-pi-agent`
- **Ein Copy (`skopeo copy`/`crane copy`/`docker pull`+`tag`+`push`) ist derzeit nicht
  möglich**, weil er die Cloudsmith-Blobs liest (402).
- **Ausweg:** Die Images aus den lokal gecachten Docker-Hub-**Basis-Images** + Kit-Dockerfiles
  **neu bauen** (kein Cloudsmith nötig) und nach Docker Hub pushen.

## Voraussetzungen

- Windows-Host mit **Docker Desktop** und Docker-Hub-Login (`docker login`).
- Kit-Repo unter `C:\development\projects\opencode-sandbox-kit`.
- Basis-Images auf Docker Hub (lokal gecacht oder werden gezogen): OpenCode v3 nutzt die
  Docker-verwaltete `docker.io/sbx/shell-docker-image:latest` (Issue #254), Claude `docker/sandbox-templates:claude-code-docker-0.10.0`,
  Mammouth/Vibe/Pi `docker/sandbox-templates:shell-docker-0.10.0`.
- Docker-Hub-Namespace = `DOCKER_USER` (z. B. `domboeckli`).

## Variablen (PowerShell)

```powershell
$DH  = "domboeckli"       # Docker Hub Namespace (= DOCKER_USER), bitte prüfen
# Backup-Tag = OpenCode-CLI-Pin bzw. Basis-Pin je Template-Familie:
$TAG_OPENCODE = "1.19.5"  # OPENCODE_VERSION (OpenCode-CLI, npm opencode-ai, 1.x)
$TAG_SHELL = "0.10.0"     # shell-docker — Mistral Vibe/Mammouth
$TAG_CLAUDE   = "0.10.0"  # TEMPLATE_VERSION_CLAUDE (claude-code-docker)
$TAG_VIBE     = "0.10.0"  # shell-docker (Mistral Vibe)
cd C:\development\projects\opencode-sandbox-kit
docker login
```

## Build-Kontexte / Build-Args

| Image | Context | Dockerfile | Build-Args (Default) |
|-------|---------|-----------|----------------------|
| opencode-v3 | `opencode-v3-agent` | `opencode-v3-agent/opencode-v3-agent.yaml` (v3) | `BASE_IMAGE=docker.io/sbx/shell-docker-image:latest`, `OPENCODE_VERSION=1.19.5` |
| claude-v3 | `claude-v3-agent` | `claude-v3-agent/claude-v3-agent.yaml` (v3) | `BASE_IMAGE=claude-code-docker-0.10.0` |
| mammouth | `mammouth-agent` | `mammouth-agent/mammouth-agent.yaml` (v3) | `BASE_IMAGE=shell-docker-0.10.0`, `MAMMOUTH_VERSION=1.18.31.2` |
| mistral-vibe | `mistral-vibe-agent` | `mistral-vibe-agent/mistral-vibe-agent.yaml` (v3) | `BASE_IMAGE=shell-docker-0.10.0`, `VIBE_VERSION=3.0.4` |

## 1. opencode-v3 — bauen + pushen

```powershell
docker build -f opencode-v3-agent/opencode-v3-agent.yaml -t "$DH/sbx-opencode:$TAG_OPENCODE" opencode-v3-agent
docker push  "$DH/sbx-opencode:$TAG_OPENCODE"
```

## 2. claude-v3 — bauen + pushen

```powershell
docker build -f claude-v3-agent/claude-v3-agent.yaml -t "$DH/sbx-claude:$TAG_CLAUDE" claude-v3-agent
docker push  "$DH/sbx-claude:$TAG_CLAUDE"
```

## 3. mammouth — bauen + pushen

```powershell
docker build -f mammouth-agent/mammouth-agent.yaml -t "$DH/sbx-mammouth:$TAG_SHELL" mammouth-agent
docker push  "$DH/sbx-mammouth:$TAG_SHELL"
```

## 4. mistral-vibe — bauen + pushen

```powershell
docker build -f mistral-vibe-agent/mistral-vibe-agent.yaml -t "$DH/sbx-mistral-vibe:$TAG_VIBE" mistral-vibe-agent
docker push  "$DH/sbx-mistral-vibe:$TAG_VIBE"
```

## Verifikation

```powershell
docker image inspect "$DH/sbx-opencode:$TAG_OPENCODE"     --format '{{.Id}} {{.Architecture}}'
docker image inspect "$DH/sbx-claude:$TAG_CLAUDE"         --format '{{.Id}} {{.Architecture}}'
docker image inspect "$DH/sbx-mammouth:$TAG_SHELL"        --format '{{.Id}} {{.Architecture}}'
docker image inspect "$DH/sbx-mistral-vibe:$TAG_VIBE"     --format '{{.Id}} {{.Architecture}}'
```

Oder über die Docker-Hub-API:

```bash
curl -s "https://hub.docker.com/v2/repositories/$DH/sbx-mistral-vibe/tags/?page_size=5"
```

## Alternative: CI-Publish nach Docker Hub (multi-arch)

Für **amd64+arm64** statt manuellem amd64-Build:
`.github/workflows/backup-images-dockerhub.yml` (manueller Trigger) mit Auswahl

- `image`: `opencode-v3` | `claude-v3` | `mammouth` | `mistral-vibe` | `all`
- `arch`: `amd64` | `arm64` | `both`
- `push`: `true`/`false`
- `tag`: Override (Default = `OPENCODE_VERSION` / `TEMPLATE_VERSION_CLAUDE` bzw. `VIBE_VERSION`)

Baut auf **nativen** Runnern (`ubuntu-latest` / `ubuntu-24.04-arm`) und mergt bei `both`
per `docker buildx imagetools create` zu `<namespace>/sbx-<name>:<tag>`. Kein Cloudsmith
nötig. Credentials: repo-Variable `DOCKER_USERNAME` + repo-Secret `DOCKER_PAT`.

## Verwendung der Backup-Images (sbx run)

Drop-in als Image-Ref. `<tag>` = Backup-Tag der jeweiligen Familie
(z. B. `1.19.5` für OpenCode v3, `0.10.0` für Claude v3/Mistral Vibe/Mammouth).

**OpenCode v3** (v3-Workload):

```powershell
sbx run docker.io/domboeckli/sbx-opencode:<tag> `
    --skills=off `
    --static-mcp idea,k8s,docker
```

**Claude Code v3** (v3-Workload):

```powershell
sbx run docker.io/domboeckli/sbx-claude:<tag> `
    --skills=off `
    --static-mcp idea,k8s,docker
```

**Mammouth Code** (v3-Workload):

```powershell
sbx run docker.io/domboeckli/sbx-mammouth:<tag> `
    --skills=off `
    --static-mcp idea,k8s,docker
```

**Mistral Vibe** (v3-Workload):

```powershell
sbx run docker.io/domboeckli/sbx-mistral-vibe:<tag> `
    --skills=off `
    --static-mcp idea,k8s,docker
```
> Immer `--skills=off` setzen; `.`-Workspace/`:ro`-Mounts wie gewohnt ergänzen.

## Hinweise

- **amd64-only** (Windows-Host). Die Cloudsmith-Images sind multi-arch (amd64+arm64);
  das Backup ist für den Notfall ausreichend. Für multi-arch den regulären CI-Publish
  (`build-and-publish-*-image.yml`) nutzen.
- Builds dauern (apt + JDK 25, Maven, Node 24, Docker CLI, kubectl, Helm, Kafka, …):
  je nach Image mehrere Minuten.
- Es wird **kein Cloudsmith-Zugriff** benötigt; Downloads (apt, JDK via bell-sw/GitHub,
  Maven, Node, PyPI/uv, Mammouth `install.sh`) kommen aus öffentlichen Quellen, der
  Push geht nach Docker Hub.
- Als **Notfall-Pull-Quelle** lassen sich die Images anschließend wie folgt referenzieren
  (Registry-Ref umbiegen). Docker Hub ist der **Default**; der **zentrale Umschalter** `IMAGE_PREFIX`
  (siehe README „Registry umschalten") lässt alle Szenarien automatisch aus Docker Hub ziehen:
  - `IMAGE_PREFIX=docker.io/domboeckli` (Env bzw. Repo-Variable) — `local-test/local-test-kits.py`
    komponiert `<IMAGE_PREFIX>/sbx-<name>:<tag>` und übergibt `--kit-arg imagePrefix=…` an die
    Sandbox-Kits (Mammouth/Mistral).
  - Alternativ gezielt: `OPENCODE_IMAGE_TAG`/`CLAUDE_IMAGE_TAG` (Mixin) bzw. `--template`/`imagePrefix`.
- Optional zusätzlich `-t "$DH/sbx-<name>:latest"` taggen/pushen.
