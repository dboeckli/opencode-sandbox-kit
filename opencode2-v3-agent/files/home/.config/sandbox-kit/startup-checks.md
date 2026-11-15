# Sandbox startup checks

The startup checks run **automatically** at the start of each session:
- **OpenCode 2 (server)**: `~/.config/opencode/plugins/startup-checks/index.js` (V2 plugin API) runs the checks once at plugin load, injects the report into the session context via `ctx.session.hook("context", …)` and writes it to `~/.config/sandbox-kit/startup-checks.report`.
- **OpenCode 2 (TUI)**: `~/.config/opencode/tui-plugins/startup-checks-tui/tui.tsx`, registered in `~/.config/opencode/cli.json`, reads the report and shows a short toast when the TUI starts (`all OK` or the failing checks) and renders three session-sidebar panels: **Startup checks** (the full report, including `mcp-gateway` and `mcp-tools`), **Skills** and **MCP &amp; Host Systems** (live `check-infra.sh` probes).

The actual checks live in `~/.config/sandbox-kit/run-checks.sh`. You only need to read this file or run the script manually when the automatic report is missing or a check fails.

> **V2-Sidebar (korrigiert):** Die V1-TUI (`tui.json`) entfällt, aber Sidebar-Slots gibt es in V2 weiterhin —
> nur mit Punkt-Notation und über die Claim-API: `context.ui.slot({ append: "sidebar.content", render })`
> (`SlotMap` in `@opencode/plugin/tui`; `sidebar_content` aus V1 existiert nicht). Das Kit rendert damit dieselben
> drei Panels wie das opencode-v3-Kit, statt nur den Toast zu zeigen. Ein Auto-Session-Plugin (V1) ist weiterhin
> nicht portiert — V2 startet selbst in einer Session.

`~/.config/sandbox-kit/check-infra.sh` covers the MCP servers reachable through the sbx MCP gateway via `~/.local/bin/mcp-check.sh`: `mcp-gateway` (gateway handshake succeeded), `mcp-idea` (IntelliJ tools present, detected by `get_symbol_info`), `mcp-k8s` (Kubernetes tools present, detected by `pods_list`), `mcp-docker` (Docker tools present, detected by `docker_list_containers`), `mcp-client` (the agent config declares the gateway URL — without it no `mcp-gateway_*` tools reach the agent even though every probe is OK; issue #139) and `mcp-tools` (deep: `opencode mcp list` performs a real handshake through the agent's own MCP client and must report the gateway as connected; falls back to `mcp-client` when the CLI has no `mcp list` command). Since the sandbox holds **no** kubeconfig (host-side Kubernetes MCP server, issue #40) and **no** host-Docker port (local Docker MCP server, issue #165), reachability is verified with an MCP handshake (`initialize` → `notifications/initialized` → `tools/list`).

Output format: space-separated tokens (`mcp-gateway:OK mcp-idea:OK mcp-k8s:OK mcp-docker:OK mcp-client:OK mcp-tools:OK`), each `FAIL` per component. All probes are bounded by `timeout`. The sandbox-internal Docker daemon is part of the startup report as `docker`. Manual run:

```
bash ~/.config/sandbox-kit/check-infra.sh
```

## Manual run

```
bash ~/.config/sandbox-kit/run-checks.sh
```

> **Hinweis (Issue #57 / #163):** IntelliJ MCP wird **nur über den sbx MCP Gateway** geprüft
> (`mcp-idea:OK` in Check 6b). Ein direkter Host-Port-Probe (`host.docker.internal:64615`/`:64342`)
> ist bewusst **nicht** erlaubt (Proxy → HTTP 403), damit der Agent die `mcp-gateway_*`-Whitelist
> nicht per `curl` umgehen kann. Host-Registrierung:
> `sbx mcp add idea --url http://localhost:64615/stream --skip-ssrf-check` + Sandbox mit
> `--static-mcp idea` (bzw. `sbx mcp load idea --sandbox`).

## Checks

| # | Check | Command |
|---|-------|---------|
| 1 | Context7 | `npx ctx7 --help` |
| 3 | gh CLI | `gh auth status` |
| 4 | Java / Maven | `java -version` and `mvn -version` |
| 5 | Docker CLI | `docker version` (isolated daemon in the microVM) |
| 6 | kubectl | `kubectl version --client` (CLI only; no kubeconfig in the sandbox) |
| 6b | MCP servers | `bash ~/.local/bin/mcp-check.sh` (one MCP handshake via the sbx gateway → `mcp-gateway:OK`, `mcp-idea:OK` when the IntelliJ tools are present, `mcp-k8s:OK` when the Kubernetes tools are present, `mcp-docker:OK` when the Docker tools are present, `mcp-client:OK` when the agent config declares the gateway; with `MCP_CHECK_DEEP=1` also `mcp-tools:OK` when the agent's own client reports the gateway as connected) |
| 7 | Helm | `helm version` |
| 7b | Kafka CLI | `kafka-topics.sh --version` |
| 7c | Bruno CLI | `bru --version` (pinned `@usebruno/cli`) |
| 7d | MCP Inspector CLI | `command -v mcp-inspector` (pinned `@modelcontextprotocol/inspector`) |
| 8 | Skills | `skills ls -g` |

## Report format

```
[startup-checks] ctx7:OK gh:OK java/maven:OK docker:OK kubectl:OK mcp-gateway:OK mcp-idea:OK mcp-k8s:OK mcp-docker:OK mcp-client:OK mcp-tools:OK helm:OK kafka:OK bruno:OK mcp-inspector:OK skills:OK sonar:OK
```

A check is `FAIL` when its command errors. In the first reply, briefly confirm the status and suggest fixes for any `FAIL` (e.g. missing GitHub secret, IntelliJ not running).
