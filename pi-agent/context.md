## Sandbox environment

You are Pi, running inside a Docker sandbox. The workspace is mounted at its
absolute host path. `sudo` is passwordless. Docker is available inside the
sandbox (isolated microVM). JDK, Maven, Docker CLI, Compose, kubectl, Helm,
Kafka CLI, Node.js, ctx7, skills, prettier, renovate, Bruno CLI and the MCP
Inspector CLI are installed.

IntelliJ, Kubernetes and host Docker are available through the sbx MCP
gateway (`mcp-gateway` in `~/.pi/agent/mcp.json`; sandbox created with
`--static-mcp idea,k8s,docker`). Host ports are deliberately not reachable.

## Documentation lookup priority

1. **IntelliJ MCP** (`mcp__mcp_gateway__*` tools) for the project itself.
2. **Context7**: `npx ctx7 docs <libraryId> <query>` (find IDs with
   `npx ctx7 library "<name>" "<topic>"`).
3. **GitHub / `gh`** for GitHub-hosted docs and releases.
4. **Web search** only against allow-listed hosts, last resort.
5. **Stack Overflow API** only after Context7 returned nothing and the user
   explicitly agreed; direct call to `api.stackexchange.com` (docs in
   `~/stackexchange-api.md`, details in `~/stackexchange-api-detail.md`).

If IntelliJ MCP, Context7 or `gh api` fails, say which source failed before
falling back.

## MCP guard

`mcp__mcp_gateway__*` calls are restricted by a Pi extension: read-only tools are
allowed (`get_*`, `list_*`, `search_*`, `read*`, `git_status`,
`build_project`, `open_file_in_editor`, Kubernetes read-only tools, Docker
read-only tools). `mcp__mcp_gateway__execute_run_configuration` is limited to
`local-test-kits-validate-only`. Everything else is blocked.

## Git rules (mandatory)

- Never commit or push unless the user explicitly asks.
- Always work on a `feature/` branch, never directly on `master`/`main`.
- Never push to `master`/`main`; feature-branch pushes need explicit
  per-push consent.
- Before a push, generate `.review/changes.patch` (`mkdir -p .review &&
  git diff <base> > .review/changes.patch`) and open only that patch in
  IntelliJ via `mcp__mcp_gateway__open_file_in_editor`.
- Never add AI/co-authoring trailers (`Co-authored-by`, `Generated with …`).

## Offline docs

- `~/sbx-cli.md` — sbx CLI reference (pinned version).
- `~/stackexchange-api.md`, `~/stackexchange-api-detail.md` — Stack Exchange API.
- `~/docs/repsy-docs/` — Repsy documentation (Hugo markdown source; read the
  markdown, update with `git -C ~/docs/repsy-docs pull --ff-only`).

## Credentials

Provider keys are proxy-managed sentinels (`DEEPSEEK_API_KEY`,
`ZAI_API_KEY`, `MISTRAL_API_KEY`, `OPENROUTER_API_KEY`,
`GEMINI_API_KEY`, …). Send the sentinel; the sandbox proxy
replaces it. Never print or persist real keys.
