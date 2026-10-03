# Sandbox startup checks

The startup checks run **automatically** at the start of each session:
- **OpenCode**: a server plugin (`~/.config/opencode/plugins/startup-checks.js`) runs the checks immediately at plugin load, injects the report into the system prompt via `experimental.chat.system.transform`, and writes it to `~/.config/sandbox-kit/startup-checks.report` for the TUI sidebar plugin.
- **OpenCode TUI**: an auto-session plugin (`~/.config/opencode/plugins/auto-session.tsx`, registered in `tui.json`) creates a new session at startup and navigates directly into the session view, so the sidebar info panel is visible immediately (no first prompt needed). The `startup-checks-tui.tsx` plugin shows three blocks in that panel (`sidebar_content` slot): **Startup checks** (order 150), **Skills** (order 155, lists `~/.agents/skills/` dirs containing `SKILL.md`) and **MCP & Host Systems** (order 160, live reachability via `check-infra.sh`, refreshed every 10s).
- **Claude Code**: a `SessionStart` hook (`~/.config/sandbox-kit/run-checks-hook.sh`, registered in `managed-settings.json` under `/etc/claude-code/`) passes the report as a system message.

The actual checks live in `~/.config/sandbox-kit/run-checks.sh`. You only need to read this file or run the script manually when the automatic report is missing or a check fails.

The **MCP & Host Systems** sidebar box runs `~/.config/sandbox-kit/check-infra.sh` (live from the TUI, every 10s). It stacks each entry vertically (one per line), covering two groups:
- **MCP servers** reachable through the sbx MCP gateway via `~/.local/bin/mcp-check.sh`: `mcp-gateway` (gateway handshake succeeded), `mcp-idea` (IntelliJ tools present, detected by `get_symbol_info`) and `mcp-k8s` (Kubernetes tools present, detected by `pods_list`). Since the sandbox holds **no** kubeconfig (host-side Kubernetes MCP server, issue #40), reachability is verified with an MCP handshake (`initialize` → `notifications/initialized` → `tools/list`).
- **Host systems**: `docker-host` (optional Docker Desktop host daemon, `docker -H tcp://host.docker.internal:2375 info`).

Output format: **line 1** = MCP servers (space-separated, `mcp-gateway:OK mcp-idea:OK mcp-k8s:OK`), **line 2+** = host systems, one per line (`docker-host:OK`) — each `FAIL` per component. The TUI splits all tokens on whitespace and renders each on its own line. All probes are bounded by `timeout`, so the box never hangs. The sandbox-internal Docker daemon is **not** shown here (it is part of the startup report as `docker`). Manual run:

```
bash ~/.config/sandbox-kit/check-infra.sh
```

## Manual run

```
bash ~/.config/sandbox-kit/run-checks.sh
```

**Manuelle Verifikation der IntelliJ-MCP-Erreichbarkeit vom Host** (PowerShell oder WSL):

```bash
sbx exec opencode-sandbox bash -c 'curl -s -o /dev/null -w "HTTP %{http_code}\n" -m 3 http://host.docker.internal:64615/sse'
```

Erwartet: `HTTP 200`. Das SSE-Endpoint hält die Verbindung offen — `-m 3` beendet curl nach 3s; nur der HTTP-Code zählt, ein `FEHLER`-Exit ist dabei normal.

> **Hinweis (Issue #57):** Der Check prüft nur, dass der IntelliJ-Server auf dem Host läuft (Voraussetzung für den
> sbx MCP Gateway). Die eigentliche MCP-Verbindung läuft über den Gateway: Host-Registrierung
> `sbx mcp add idea --url http://localhost:64615/stream --skip-ssrf-check` + Sandbox mit `--static-mcp idea`
> (bzw. `sbx mcp load idea --sandbox`). Port 64615 seit IDEA 2026.2.2, Legacy 64342 — falls die IDE einen
> abweichenden Port meldet (Settings → Tools → MCP Server), diesen übernehmen.

## Checks

| # | Check | Command |
|---|-------|---------|
| 1 | Context7 | `npx ctx7 --help` |
| 2 | IntelliJ MCP | `curl -s -o /dev/null -w '%{http_code}' http://host.docker.internal:64615/sse` (Port 64615 seit IDEA 2026.2.2, Legacy 64342; Fallback `127.0.0.1`/`localhost`, je 3 Versuche mit 1s Pause; erwartet 200/206) |
| 3 | gh CLI | `gh auth status` |
| 4 | Java / Maven | `java -version` and `mvn -version` |
| 5 | Docker CLI | `docker version` (isolated daemon in the microVM) |
| 5b | Docker host daemon | `docker -H tcp://host.docker.internal:2375 version` (optional Docker Desktop host daemon; FAIL = "Expose daemon" nicht aktiv oder Docker Desktop down) |
| 6 | kubectl | `kubectl version --client` (CLI only; no kubeconfig in the sandbox) |
| 6b | MCP servers | `bash ~/.local/bin/mcp-check.sh` (one MCP handshake via the sbx gateway → `mcp-gateway:OK`, `mcp-idea:OK` when the IntelliJ tools are present, `mcp-k8s:OK` when the Kubernetes tools are present) |
| 7 | Helm | `helm version` |
| 7b | Kafka CLI | `kafka-topics.sh --version` |
| 8 | Skills | `skills ls -g` |

## Report format

```
[startup-checks] ctx7:OK intellij-mcp:OK gh:OK java/maven:OK docker:OK docker-host:FAIL kubectl:OK mcp-gateway:OK mcp-idea:OK mcp-k8s:OK helm:OK kafka:OK skills:OK sonar:OK
```

A check is `FAIL` when its command errors. In the first reply, briefly confirm the status and suggest fixes for any `FAIL` (e.g. missing GitHub secret, IntelliJ not running).
