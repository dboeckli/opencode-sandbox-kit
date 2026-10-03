# Sandbox startup checks

The startup checks live in `~/.config/sandbox-kit/run-checks.sh`. Mistral Vibe has no
automatic session hook that injects the report into the system prompt, so run the script
manually for the tooling status:

```
bash ~/.config/sandbox-kit/run-checks.sh
```

`check-infra.sh` (MCP & Host Systems live reachability) is included for parity with the
other kits but is not wired to a TUI sidebar here; run it manually if needed:

```
bash ~/.config/sandbox-kit/check-infra.sh
```

It shows two groups:
- **MCP servers** reachable through the sbx MCP gateway via `~/.local/bin/mcp-check.sh`:
  `mcp-gateway` (gateway handshake succeeded), `mcp-idea` (IntelliJ tools present, detected by
  `get_symbol_info`) and `mcp-k8s` (Kubernetes tools present, detected by `pods_list`). The
  sandbox holds **no** kubeconfig (host-side Kubernetes MCP server, issue #40), so reachability
  is verified with an MCP handshake (`initialize` → `notifications/initialized` → `tools/list`).
- **Host systems**: `docker-host` (optional Docker Desktop host daemon,
  `docker -H tcp://host.docker.internal:2375 info`).

Output format: **line 1** = MCP servers (space-separated, `mcp-gateway:OK mcp-idea:OK mcp-k8s:OK`),
**line 2+** = host systems, one per line (`docker-host:OK`) — each `FAIL` per component. All probes
are bounded by `timeout`, so the check never hangs.

> **Hinweis (Issue #57):** Der IntelliJ-MCP-Check prüft nur, dass der IntelliJ-Server auf dem Host läuft
> (Voraussetzung für den sbx MCP Gateway). Die eigentliche MCP-Verbindung läuft über den Gateway:
> Host-Registrierung `sbx mcp add idea --url http://localhost:64615/stream --skip-ssrf-check` + Sandbox mit
> `--static-mcp idea` (bzw. `sbx mcp load idea --sandbox`). Port 64615 seit IDEA 2026.2.2, Legacy 64342.

## Checks

| # | Check | Command |
|---|-------|---------|
| 1 | Context7 | `npx ctx7 --help` |
| 2 | IntelliJ MCP | `curl -s -o /dev/null -w '%{http_code}' http://host.docker.internal:64615/sse` (Port 64615 seit IDEA 2026.2.2, Legacy 64342; expect 200/206) |
| 3 | gh CLI | `gh auth status` |
| 4 | Java / Maven | `java -version` and `mvn -version` |
| 5 | Docker CLI | `docker version` (isolated daemon in the microVM) |
| 5b | Docker host daemon | `docker -H tcp://host.docker.internal:2375 version` (optional Docker Desktop host daemon; FAIL = "Expose daemon" nicht aktiv oder Docker Desktop down) |
| 6 | kubectl | `kubectl version --client` (CLI only; no kubeconfig in the sandbox) |
| 6b | MCP servers | `bash ~/.local/bin/mcp-check.sh` (one MCP handshake via the sbx gateway → `mcp-gateway:OK`, `mcp-idea:OK` when the IntelliJ tools are present, `mcp-k8s:OK` when the Kubernetes tools are present) |
| 7 | Helm | `helm version` |
| 7b | Kafka CLI | `kafka-topics.sh --version` |
| 8 | Skills | `skills ls -g` |
| 9 | Mistral Vibe | `command -v vibe` |

## Report format

```
[startup-checks] ctx7:OK intellij-mcp:OK gh:OK java/maven:OK docker:OK docker-host:FAIL kubectl:OK mcp-gateway:OK mcp-idea:OK mcp-k8s:OK helm:OK kafka:OK skills:OK sonar:OK vibe:OK
```

A check is `FAIL` when its command errors. In the first reply, briefly confirm the status and suggest fixes for any `FAIL` (e.g. missing GitHub secret, IntelliJ not running).
