# Docker-Hub-Images nutzen (statt Cloudsmith)

Kurzreferenz: `sbx run`-Kommandos für die **4 Kits**, die die Images aus **Docker Hub**
(`docker.io/domboeckli/sbx-…`) statt aus Cloudsmith ziehen. Hintergrund und Umschalter:
README → „Registry umschalten (Cloudsmith ↔ Docker Hub)".

Es gibt **4 lokale** Kommandos (Tag `:local`, zuvor lokal gebaut/gepusht) und **4 remote**
Kommandos (publizierte Images, Tag `:latest`).

## Voraussetzungen

- Aktueller Umschalter: `IMAGE_PREFIX=docker.io/domboeckli`
  - CI: Repo-Variable `IMAGE_PREFIX` (`gh variable set IMAGE_PREFIX --body "docker.io/domboeckli" --repo dboeckli/opencode-sandbox-kit`)
  - Lokal: `$env:IMAGE_PREFIX = "docker.io/domboeckli"`
- Images auf Docker Hub (öffentlich, anonym pullbar):
  `domboeckli/sbx-opencode-tooling`, `domboeckli/sbx-claude-tooling`, `domboeckli/sbx-mammouth`, `domboeckli/sbx-mistral-vibe`
- `--skills=off` gehört in **jedes** Kommando (Trust Boundary).
- `--static-mcp idea,k8s,docker` nur, wenn die Host-MCP-Server registriert sind
  (`sbx mcp add idea …` / `k8s` / `docker`); sonst weglassen.
- Workspace/Mounts wie gewohnt ergänzen (Projektpfad, `:ro`-Mounts, …).

## Remote — publizierte Docker-Hub-Images (`:latest`)

PowerShell; der bewegliche `latest`-Tag zeigt auf den letzten `master`-Publish.

**1) OpenCode** (Mixin-Kit)

```powershell
sbx run opencode `
    --kit ./opencode-agent/ `
    --template docker.io/domboeckli/sbx-opencode-tooling:latest `
    --skills=off `
    --static-mcp idea,k8s,docker
```

**2) Claude Code** (Mixin-Kit, Home)

```powershell
sbx run claude `
    --kit ./opencode-agent/ `
    --template docker.io/domboeckli/sbx-claude-tooling:latest `
    --skills=off `
    --static-mcp idea,k8s,docker
```

**3) Mammouth Code** (`kind: sandbox`, eigenes Image)

```powershell
sbx run ./mammouth-agent/ `
    --kit-arg imageTag=latest `
    --kit-arg imagePrefix=docker.io/domboeckli `
    --skills=off `
    --static-mcp idea,k8s,docker
```

**4) Mistral Vibe** (`kind: sandbox`, eigenes Image)

```powershell
sbx run ./mistral-vibe-agent/ `
    --kit-arg imageTag=latest `
    --kit-arg imagePrefix=docker.io/domboeckli `
    --skills=off `
    --static-mcp idea,k8s,docker
```

## Lokal — lokal gebaute/gepushte `:local`-Images

Zuerst je Kit das Image lokal bauen und **nach Docker Hub pushen** (setzt den beweglichen `:local`-Tag):

```powershell
$env:IMAGE_PREFIX = "docker.io/domboeckli"
python local-test\build-and-publish-opencode-image.py       # sbx-opencode-tooling:local
python local-test\build-and-publish-claude-image.py         # sbx-claude-tooling:local
python local-test\build-and-publish-mammouth-image.py       # sbx-mammouth:local
python local-test\build-and-publish-mistral-vibe-image.py   # sbx-mistral-vibe:local
```

Danach (der bewegliche `local`-Tag zeigt auf diesen lokalen Build):

**1) OpenCode**

```powershell
sbx run opencode `
    --kit ./opencode-agent/ `
    --template docker.io/domboeckli/sbx-opencode-tooling:local `
    --skills=off `
    --static-mcp idea,k8s,docker
```

**2) Claude Code**

```powershell
sbx run claude `
    --kit ./opencode-agent/ `
    --template docker.io/domboeckli/sbx-claude-tooling:local `
    --skills=off `
    --static-mcp idea,k8s,docker
```

**3) Mammouth Code**

```powershell
sbx run ./mammouth-agent/ `
    --kit-arg imageTag=local `
    --kit-arg imagePrefix=docker.io/domboeckli `
    --skills=off `
    --static-mcp idea,k8s,docker
```

**4) Mistral Vibe**

```powershell
sbx run ./mistral-vibe-agent/ `
    --kit-arg imageTag=local `
    --kit-arg imagePrefix=docker.io/domboeckli `
    --skills=off `
    --static-mcp idea,k8s,docker
```

## Hinweise

- Die Registry-Kurzform `domboeckli/sbx-…` ist gleichwertig zu `docker.io/domboeckli/sbx-…`
  (Docker Hub = Default-Registry); hier bewusst mit `docker.io/`-Präfix (= Wert von `IMAGE_PREFIX`).
- Kein Host-Registry-Login nötig (öffentliche Images); bei Docker-Hub-Rate-Limit ggf.
  `docker login` / `sbx login` (Konto `domboeckli`, 200 Pulls/h).
- Zurück zu Cloudsmith: README → „Registry umschalten → Zurück nach Cloudsmith (Prozedur)".
