# Prerequisites: Host + Sandbox

Alle Voraussetzungen, damit das Kit (`sbx run opencode|claude|mammouth`) funktioniert.
Host = Windows (PowerShell/CMD, Standard) oder Ubuntu-WSL; Sandbox = Docker-MicroVM, die das Kit installiert.

## Host (Windows / Ubuntu-WSL)

| Voraussetzung | Beschreibung | Benötigt für |
|---------------|--------------|--------------|
| **Docker Desktop** (Windows) | Laufender Docker Daemon — nativ **oder** Ubuntu-WSL-Setup (Laufzeitumgebung dort: **Ubuntu 26.04**) | Sandbox-Ausführung |
| **`sbx` CLI** | Docker Sandbox CLI, `sbx` im PATH | Sandbox erstellen / verwalten |
| **KVM-Zugriff (WSL2)** | Zugriff auf `/dev/kvm` für die MicroVM (nerdbox) | Sandbox-VM starten |
| **IntelliJ IDEA** | MCP-Server (2025.2+ integriert) auf `127.0.0.1:64342` + Firewall-Freigabe Port 64342; einmalig `sbx mcp add idea --url http://localhost:64342/stream --skip-ssrf-check` (Gateway-Weg, Issue #57) | IntelliJ MCP (optional) |
| **API-Keys / Secrets** | Globale Secrets, vom Proxy verwaltet — liegen nie im Sandbox-Filesystem | je nach Agent (siehe unten) |

### Secrets registrieren (`sbx secret set <service>`)

| Service | Agent | Key-Quelle |
|---------|-------|-----------|
| `github` | alle | GitHub-PAT (Name `opencode-sandbox-kit-github-token`), Scopes `read:org`, `read:packages`, `read:project`, `read:user` |
| `anthropic` | Claude | https://console.anthropic.com — interaktiv, `-f` zum Überschreiben |
| `mammouth` | Mammouth | https://mammouth.ai/app/account/settings/api |
| `context7` | alle | https://context7.com/dashboard |
| `openrouter` | OpenCode | Built-in-Service des opencode-Templates (nicht im Kit deklariert) |
| `google` | OpenCode | https://aistudio.google.com/apikey (Built-in-Service) |
| `stackoverflow` | alle | https://stackapps.com/applications (Fallback-Quelle) |
| `cloudsmith` | alle | https://cloudsmith.io/user/settings/api-keys/ |

## Sandbox (wird vom Kit via `setup.install` installiert)

Quelle der Wahrheit: `opencode-agent/files/home/.local/bin/install-tooling.sh` + `install-tooling-user.sh`
(identische Kopien in allen drei Kits; Drift-Check via `local-test-kits.py --validate-only`).
Doku-Tabellen: `AGENTS.md` → "Tools installed by the kit", `README.md` → Tool-Tabelle.

### Root-Tooling (`install-tooling.sh`, Setup-Install)

| Tool | Version | Pfad |
|------|---------|------|
| Liberica JDK | 25.0.4 | `/usr/local/java` (`JAVA_HOME`) |
| Apache Maven | 3.9.16 | `/opt/maven`, Symlink `/usr/local/bin/mvn` |
| Docker CLI | 27.5.1 | `/usr/local/bin/docker` (isolierter Daemon in der Sandbox-VM) |
| Docker Compose | 5.4.0 (Plugin) | `/usr/local/lib/docker/cli-plugins/docker-compose` |
| kubectl | latest stable | `/usr/local/bin/kubectl` |
| Helm v3 | 3.21.3 (Default) | `/usr/local/bin/helm` |
| Helm v4 | 4.2.4 | `/usr/local/bin/helm4` — paralleles Binary, explizit aufrufbar |
| shfmt | 3.13.0 | `/usr/local/bin/shfmt` |
| ctx7 | latest | npm global (`/usr/local/share/npm-global/bin`) |
| skills | latest | npm global (vercel-labs) |
| prettier | latest | npm global |
| renovate | latest | npm global |
| jq, python3, pip, python3-yaml | distro | apt |

### Agent-User-Tooling (`install-tooling-user.sh`, user 1000)

| Tool | Ziel |
|------|------|
| skills-Bundle | `~/.agents/skills/` (camel-matrix, cc-best-practices, project-references, skill-best-practices) |
| Claude statusline | `~/.claude/statusline.sh` |
| Repsy-Doku (offline) | `~/docs/repsy-docs/` (Shallow-Clone von `github.com/repsyio/repsy-docs`) |

### Agent-spezifisch

| Agent | Zusätzlich installiert | Konfiguration |
|-------|-----------------------|---------------|
| OpenCode | (Basis-Image bringt CLI mit) | `~/.config/opencode/opencode.jsonc` + `AGENTS.md` |
| Claude Code | managed-settings.json in `/etc/claude-code` (statusLine + Hooks, Template-sicher) | `~/.claude/settings.json` + `CLAUDE.md` |
| Mammouth Code | `curl -fsSL https://code.mammouth.ai/install.sh \| bash` → `~/.mammouth` + Symlink `/usr/local/bin/mammouth` | `~/.config/mammouth/opencode.jsonc` + `AGENTS.md` |

## Netzwerk (Sandbox, Deny-by-Default)

Nur Hosts aus `permissions.network.allow` (`opencode-agent/spec.yaml`/`mammouth-agent/spec.yaml`/`claude-zurich-agent/spec.yaml`) sind erreichbar.
Doku: `opencode-agent/files/home/.config/opencode/network-policy.md` (bzw. Claude/Mammouth-Kopie). Enforced durch den
Sandbox-Proxy (`mcp-gateway`), der auch die `proxy-managed`-Credential-Injection übernimmt.

## Verifikation

- Host-Validierung: `python local-test/local-test-kits.py --validate-only` (bzw. IntelliJ-Config `local-test-kits-validate-only`)
- Volltest: `python local-test/local-test-kits.py` (alle 3 Szenarien)
- Laufzeit-Checks: `bash ~/.config/sandbox-kit/run-checks.sh` → `[startup-checks] ...`
