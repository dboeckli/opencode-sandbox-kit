# Prerequisites: Host + Sandbox

Alle Voraussetzungen, damit das Kit (`sbx run opencode|claude|mammouth|mistral-vibe`) funktioniert.
Host = Windows (PowerShell/CMD, Standard) oder Ubuntu-WSL; Sandbox = Docker-MicroVM, die das Kit installiert.

## Host (Windows / Ubuntu-WSL)

| Voraussetzung | Beschreibung | Benötigt für |
|---------------|--------------|--------------|
| **Docker Desktop** (Windows) | Laufender Docker Daemon — nativ **oder** Ubuntu-WSL-Setup (Laufzeitumgebung dort: **Ubuntu 26.04**) | Sandbox-Ausführung |
| **`sbx` CLI** | Docker Sandbox CLI, `sbx` im PATH | Sandbox erstellen / verwalten |
| **KVM-Zugriff (WSL2)** | Zugriff auf `/dev/kvm` für die MicroVM (nerdbox) | Sandbox-VM starten |
| **IntelliJ IDEA** | MCP-Server (2025.2+ integriert) auf `127.0.0.1:64615` (Port 64615 seit IDEA 2026.2.2, davor 64342); einmalig `sbx mcp add idea --url http://localhost:64615/stream --skip-ssrf-check` (Gateway-Weg, Issue #57). Die Sandbox erreicht den Server **nur** über den Gateway — direkte Host-Ports sind nicht allow-listed (Issue #163) | IntelliJ MCP (optional) |
| **Kubernetes MCP Server** | Host-seitiger MCP-Server (`containers/kubernetes-mcp-server`, native Windows-Binary via `local-scripts/install-kubernetes-mcp-server.ps1`) + `sbx mcp add k8s …`; Details: `docs/mcp/kubernetes-mcp-server.md` (Issue #40) | Kubernetes MCP (optional) |
| **Docker MCP Server** | Lokaler Docker-MCP-Server via `uv`/`uvx` (`dboeckli/mcp-server-docker`-Fork, Tag `@v<pin>`, inkl. Docker-/Buildx-Introspektion `buildx_*`/`system_*`/`image_*`/`container_inspect`) + `sbx mcp add docker …` (absoluter `uvx`-Pfad); Details: `docs/mcp/docker-mcp-server.md` (Issue #165/#250) | Host-Docker MCP (optional) |
| **API-Keys / Secrets** | Globale Secrets, vom Proxy verwaltet — liegen nie im Sandbox-Filesystem | je nach Agent (siehe unten) |

### Clipboard (Kopieren/Einfügen)

Sandbox → Host-**Textkopie** ist seit sbx **v0.51** opt-in (`clipboard.textCopy`, Default `false`); ohne Opt-in
antwortet der von `sbx` injizierte Clipboard-Shim (`wl-copy`/`xclip`/`xsel` → `sbx-clipboard-write`) mit HTTP 403.
Text-**Paste** (Host → Sandbox) braucht keine Einstellung (läuft terminal-seitig); Bild-Paste (`Ctrl+V` für
Screenshots) braucht `clipboard.imagePaste`.

```powershell
sbx settings set clipboard.textCopy true      # Sandbox → Host-Clipboard (Pi/OpenCode-Copy)
sbx settings set clipboard.imagePaste true    # optional: Bilder/Screenshots einfügen
```

Die Settings gelten sofort für laufende Sandboxes (kein Recreate). Verifikation: `sbx settings get clipboard.textCopy`
→ `true`, in der Sandbox `printf test | wl-copy` → Exit 0. Symptome/Fehlermeldungen: `docs/troubleshooting.md`.

### Secrets registrieren (`sbx secret set <service>`)

| Service | Agent | Key-Quelle |
|---------|-------|-----------|
| `github` | alle | GitHub-PAT (Name `opencode-sandbox-kit-github-token`), Scopes `read:org`, `read:packages`, `read:project`, `read:user` |
| `github-maven` | alle | Klassisches PAT (nur Scope `read:packages`) für GitHub Packages Maven — `https://github.com/settings/tokens` |
| `anthropic` | Claude | https://console.anthropic.com — interaktiv, `-f` zum Überschreiben |
| `mammouth` | Mammouth | https://mammouth.ai/app/account/settings/api |
| `deepseek` | Pi (Default), OpenCode, Mammouth | DeepSeek (`DEEPSEEK_API_KEY`, `api.deepseek.com`) — https://platform.deepseek.com/api_keys |
| `mistral` | Mistral Vibe, OpenCode, Mammouth, Pi | Built-in-Service (`MISTRAL_API_KEY`, `api.mistral.ai`) — https://console.mistral.ai/ |
| `zai` | OpenCode, Mammouth, Mistral Vibe, Pi | Z.AI (GLM, OpenAI-kompatibler Provider) — https://z.ai/manage-apikey/apikey-list |
| `context7` | alle | https://context7.com/dashboard |
| `openrouter` | OpenCode, Pi | Built-in-Service des opencode-Templates; Pi deklariert ihn im v3-Kit (`OPENROUTER_API_KEY`) |
| `google` | OpenCode, Pi | https://aistudio.google.com/apikey (OpenCode: Built-in-Service; Pi: `GEMINI_API_KEY`) |
| `stackoverflow` | alle | https://stackapps.com/applications (Fallback-Quelle) |
| `cloudsmith` | alle | https://cloudsmith.io/user/settings/api-keys/ |
| `sonarcloud` | alle | SonarCloud API-Token (Web-API) — https://sonarcloud.io/account/security |
| `codeberg` | alle | Codeberg API-Token (Forgejo-API) — https://codeberg.org/user/settings/applications |

## Sandbox (im Kit-Image eingebacken)

Quelle der Wahrheit: `opencode-v3-agent/files/home/.local/bin/install-tooling.sh` + `install-tooling-user.sh`
(identische Kopien in allen Kits; Drift-Check via `local-test-kits.py --validate-only`).
Doku-Tabellen: `AGENTS.md` → "Tools installed by the kit", `README.md` → Tool-Tabelle.

### Root-Tooling (`install-tooling.sh`, Setup-Install)

| Tool | Version | Pfad |
|------|---------|------|
| Node.js | 26.13.0 | `/opt/node`, Symlinks `/usr/local/bin/{node,npm,npx,corepack}` (npm-CLIs wie renovate ≥43) |
| Liberica JDK | 25.0.5+11 | `/usr/local/java` (`JAVA_HOME`) — alle Kits; alle JDK-Binaries via Symlink in `/usr/local/bin` |
| Apache Maven | 3.10.0 | `/opt/maven`, Symlink `/usr/local/bin/mvn` |
| uv | 0.13.8 (inkl. `uvx`) | `/usr/local/bin/{uv,uvx}` (Kit-Tooling; ersetzt Base-uv 0.13.4, Issue #284) |
| Docker CLI | 29.9.3 | aus dem Base-Image (`docker.io/sbx/shell-docker-image:latest`, alle Kits; isolierter Daemon in der Sandbox-VM) |
| Docker Compose | 5.7.0 (Plugin) | aus dem Base-Image (alle Kits) |
| kubectl | latest stable | `/usr/local/bin/kubectl` (Build: v1.37.2) |
| Helm | 4.3.1 | `/usr/local/bin/helm` (+ `helm4` Symlink) |
| Apache Kafka CLI | 4.4.0 (Scala 2.13) | `/opt/kafka` + `kafka-*.sh`-Wrapper in `/usr/local/bin` |
| shfmt | 3.14.1 | `/usr/local/bin/shfmt` |
| ctx7 | latest | npm global (`/usr/local/share/npm-global/bin`) |
| skills | latest | npm global (vercel-labs) |
| prettier | latest | npm global |
| renovate | latest | npm global |
| Bruno CLI (`bru`) | 4.3.0 | npm global (`@usebruno/cli`, gepinnt; Renovate) |
| MCP Inspector CLI (`mcp-inspector`, `mcpdo`) | 2.13.0 | npm global (`@modelcontextprotocol/inspector`, gepinnt; Renovate) |
| jq, python3, pip, python3-yaml | distro | apt |

> **opencode-v3/claude-v3/mammouth/mistral-vibe/pi (Issue #254):** Alle fünf basieren auf `docker.io/sbx/shell-docker-image:latest@sha256:160a9e3f5cd4bafb39bb9db3a839cb5a468a5a3eff394d8c90fbc1f2635abd00` (Digest-gepinnt; Renovate) —
> Node/npm, Docker CLI, Compose und Buildx kommen aus dem Base-Image; Liberica JDK, Maven, uv (inkl. `uvx`,
> Issue #284), Node-Pin usw. installiert weiterhin `install-tooling.sh` (wie in allen Kits).

### Agent-User-Tooling (`install-tooling-user.sh`, user 1000)

| Tool | Ziel |
|------|------|
| skills-Bundle | `~/.agents/skills/` (dboeckli: camel-matrix, cc-best-practices, cron-schedule-planner, project-references, skill-best-practices; Superpowers: 15 Methodik-Skills inkl. brainstorming, TDD, systematic-debugging) |
| Claude statusline | `~/.claude/statusline.sh` |
| Repsy-Doku (offline) | `~/docs/repsy-docs/` (Shallow-Clone von `github.com/repsyio/repsy-docs`) |

### Agent-spezifisch

| Agent | Zusätzlich installiert | Konfiguration |
|-------|-----------------------|---------------|
| OpenCode v3 | v3-Workload (`opencode-v3-agent/`, Image `sbx-opencode`; Basis `docker.io/sbx/shell-docker-image:latest`, OpenCode-CLI via npm `opencode-ai` auf 1.x gepinnt) | `~/.config/opencode/opencode.jsonc` + `AGENTS.md` + Plugins |
| Claude Code v3 | v3-Workload (`claude-v3-agent/`, Image `sbx-claude`; Basis `docker.io/sbx/shell-docker-image:latest`, Claude-CLI via npm `@anthropic-ai/claude-code` gepinnt); managed-settings + `claude-entrypoint` (Settings/Gateway-Merge) | `~/.claude/settings.json` + `CLAUDE.md` + `~/.claude.json` (MCP-Gateway) |
| Mammouth Code | v3-Workload (`mammouth-agent/mammouth-agent.yaml`); Image `sbx-mammouth` mit CLI + Tooling | `~/.config/mammouth/opencode.jsonc` + `AGENTS.md` |
| Mistral Vibe | v3-Workload-Image (`uv tool install mistral-vibe==<pin>`, `docker.io/domboeckli/sbx-mistral-vibe:<pin>`) | `~/.vibe/config.toml` (MCP-Gateway) + `~/.vibe/hooks.toml` (Read-only-Guard) + `~/.vibe/AGENTS.md` |
| Pi | v3-Workload-Image (`docker.io/sbx/shell-docker-image:latest`-Basis + Kit-Tooling + `@earendil-works/pi-coding-agent`, `docker.io/domboeckli/sbx-pi-agent:<pin>`; kein OpenCode im Image) | `~/.pi/agent/settings.json` + `mcp.json` (MCP-Gateway) + `extensions/mcp-guard.ts` (Read-only-Guard, gemeinsame Allow-Liste) + `AGENTS.md` |

## Netzwerk (Sandbox, Deny-by-Default)

Nur Hosts aus `network-policy@1` im jeweiligen v3-Descriptor (OpenCode v3/Claude v3/Mammouth/Mistral Vibe/Pi) sind erreichbar.
Doku: `network-policy.md` in den `files/home/`-Kopien der Kits. Enforced durch den
Sandbox-Proxy (`mcp-gateway`), der auch die `proxy-managed`-Credential-Injection übernimmt.

## Verifikation

- Host-Validierung: `python local-test/local-test-kits.py --validate-only` (bzw. IntelliJ-Config `local-test-kits-validate-only`)
- Volltest: `python local-test/local-test-kits.py` (alle 5 Szenarien)
- Laufzeit-Checks: `bash ~/.config/sandbox-kit/run-checks.sh` → `[startup-checks] ...`
  (Pi hat kein `run-checks.sh`; der Kit-Check prüft `~/.pi/agent/*` + `pi --version`.)
