# Sandbox startup checks

The startup checks run **automatically** at the start of each session:
- **OpenCode**: a server plugin (`~/.config/opencode/plugins/startup-checks.js`) runs the checks, injects the report into the system prompt via `experimental.chat.system.transform`, and writes it to `~/.config/sandbox-kit/startup-checks.report` for the TUI sidebar plugin.
- **OpenCode TUI**: a TUI plugin (`~/.config/opencode/plugins/startup-checks-tui.tsx`, registered in `tui.json`) shows two blocks in the sidebar info panel (`sidebar_content` slot): **Startup checks** (order 150) and **Skills** (order 155, lists `~/.agents/skills/` dirs containing `SKILL.md`).
- **Claude Code**: a `SessionStart` hook (`~/.config/sandbox-kit/run-checks-hook.sh`, registered in `~/.claude/settings.json`) passes the report as a system message.

The actual checks live in `~/.config/sandbox-kit/run-checks.sh`. You only need to read this file or run the script manually when the automatic report is missing or a check fails.

## Manual run

```
bash ~/.config/sandbox-kit/run-checks.sh
```

## Checks

| # | Check | Command |
|---|-------|---------|
| 1 | Context7 | `npx ctx7 --help` |
| 2 | IntelliJ MCP | `curl -s -o /dev/null -w '%{http_code}' http://host.docker.internal:64342/sse` (expect 200/206) |
| 3 | gh CLI | `gh auth status` |
| 4 | Java / Maven | `java -version` and `mvn -version` |
| 5 | Docker CLI | `docker version` (isolated daemon in the microVM) |
| 6 | kubectl | `kubectl version --client` |
| 7 | Skills | `skills ls -g` |

## Report format

```
[startup-checks] ctx7:OK intellij-mcp:OK gh:OK java/maven:OK docker:OK kubectl:OK skills:OK
```

A check is `FAIL` when its command errors. In the first reply, briefly confirm the status and suggest fixes for any `FAIL` (e.g. missing GitHub secret, IntelliJ not running).
