<!-- context7 -->
Use the Context7 CLI (`npx ctx7`) to fetch current documentation whenever the user asks about a library, framework, SDK, API, CLI tool, or cloud service — even well-known ones like React, Next.js, Prisma, Express, Tailwind, Django, or Spring Boot. This includes API syntax, configuration, version migration, library-specific debugging, setup instructions, and CLI tool usage. Use even when you think you know the answer — your training data may not reflect recent changes. Prefer this over web search for library docs.

Run `npx ctx7 --help` to see all available commands (login, setup, library, docs, upgrade, ...).

Do not use for: refactoring, writing scripts from scratch, debugging business logic, code review, or general programming concepts.

## Steps

1. Run `npx ctx7 docs <libraryId> <query>` where `<libraryId>` is the library ID in `/org/project` format (e.g. `/facebook/react`) and `<query>` is what to look up in the library's documentation
2. If you don't know the exact library ID, first run `npx ctx7 library "<library name>" "<what to look up>"` to find the best match
3. Pick the best match (ID format: `/org/project`) by: exact name match, description relevance, code snippet count, source reputation (High/Medium preferred), and benchmark score (higher is better). Use version-specific IDs when the user mentions a version
4. Scope each query to a single concept. If the question spans multiple distinct concepts (e.g. routing and auth and caching), make a separate `ctx7 docs` call per concept, unless the question is about how the concepts interact
5. Answer using the fetched docs
<!-- context7 -->

## Context7 tools reference

The full inventory of tools documented via Context7 — with their ctx7 library IDs and GitHub/docs URLs — lives in `context7-tools.md` (in this directory). Tool-specific library IDs are no longer repeated inline below.

## Documentation lookup priority

When you need current information about a library, framework, SDK, API, CLI tool, or cloud service, use this order:

1. **IntelliJ MCP** — `idea_*` tools (`idea_get_symbol_info`, `idea_search_symbol`, `idea_analyze_calls`, `idea_read_file`) are the **primary source for the project itself**: navigate code, get quick documentation, browse external & decompiled dependencies loaded in the IDE. Use it first for project-internal questions. Requires IntelliJ IDEA running on the host.
2. **Context7** — `npx ctx7 docs <libraryId> <query>` (find unknown IDs via `npx ctx7 library "<name>" "<topic>"`) is the **primary source for external library, framework, SDK, API, and CLI documentation**.
3. **GitHub / `gh`** — `gh api` / `gh release` for anything hosted on GitHub and for version/release info (e.g. `gh api repos/anomalyco/opencode/releases/latest`)
4. **Web search** — `websearch` / `webfetch` only as last resort, and only against the allow-listed hosts in the network policy below.

**Failure handling:** if IntelliJ MCP, Context7 (`npx ctx7`), or the GitHub API (`gh api`) is unavailable or fails (not running, error, not found, timeout, rate limit, 403), tell the user immediately which source failed and how the result is affected, then fall back per the steps above. Do not silently degrade.

<!-- sandbox-tools -->
This sandbox is provisioned by the opencode-sandbox-kit. The following tools are installed and available:

## IntelliJ IDEA MCP

Connected via `host.docker.internal:64342/sse`; tools prefixed with `idea_` (symbol search, read file, build, inspect problems, SQL, debugger) and listed each session. Interacts with the IDE on the Windows host (requires IntelliJ running). Primary documentation source for the project itself (see lookup priority).

## Context7

Docs-as-a-service CLI; see the `<!-- context7 -->` section above. Authenticated via `CONTEXT7_API_KEY` (placeholder `proxy-managed`, replaced by the proxy on requests to `context7.com`) — never shows the real key.

## Skills CLI

`skills` (vercel-labs) manages reusable agent skills in `~/.agents/skills/` (auto-loaded):
- `skills ls` / `skills ls -g` — list installed skills
- `skills add <package>` — add a skill package (e.g. `skills add -g https://github.com/dboeckli/ai-agent-skills.git`)
- `skills remove [skills]` / `skills update` — remove / update skills

Installed skills (from [dboeckli/ai-agent-skills](https://github.com/dboeckli/ai-agent-skills)):
- **camel-matrix** — Camel/Spring Boot/CXF compatibility matrix via `camel-springboot-matrix.sh`
- **cc-best-practices** — effective Claude Code usage
- **project-references** — conventions from `~/projects/referenzen/`
- **skill-best-practices** — structuring SKILL.md files

Loaded automatically when a task matches their description.

## Java / Maven

- JDK (Liberica) 25 at `/usr/local/java` (`JAVA_HOME` set), `java`, `javac`
- Maven 3.9.16 at `/opt/maven`, `mvn`
- Spring Boot, Apache Camel, CXF, Commons Lang, HttpClient, Tomcat, POI — see `context7-tools.md`

## Docker CLI

`docker` CLI is installed and connects to the isolated Docker daemon inside the sandbox microVM. Use it to build/pull/run containers. The Docker socket is not the host socket.

## kubectl

`kubectl` (latest stable) at `/usr/local/bin/kubectl`. No cluster is pre-configured; check `kubectl config current-context` or configure a kubeconfig as needed.

## Runtime tools / CLIs

Installed runtime CLIs — Node.js, npm, Git, jq, Go, pip, curl, GNU Make — see `context7-tools.md`.

## Related tooling (not installed)

Not installed in the sandbox, but documented via Context7: Helm, Renovate, Dependabot — see `context7-tools.md`.

## Dependabot & Renovate (Context7 required)

This repository manages `.github/dependabot.yml` and `.github/renovate.json`.
Whenever you create, edit, or validate these configuration files — or change
which tools/ecosystems they cover — ALWAYS fetch the current documentation via
Context7 first (see `context7-tools.md`) and follow it. Do not rely on training
memory; the schemas change.

## Languages / formats

Languages and file formats used in this sandbox (Python, Bash, YAML, JSON, JSONC) — see `context7-tools.md`.

## gh (GitHub CLI)

`gh` is available and authenticated via a proxy-injected token. `gh auth status` should work. Run `gh --help` to see all commands (repo, pr, issue, release, api, auth, ...). Use it for GitHub operations (repos, PRs, issues) and as the primary source for GitHub-hosted docs and version/release information.

## OpenCode

OpenCode is an agent CLI (and the base for Mammouth Code). For configuration of `opencode.json`, agents, skills, and MCP servers, see `context7-tools.md` and the lookup priority rules above.

Versions: do not assume the installed or latest version. Check the installed version with `opencode --version`, and always fetch the latest release from GitHub Releases via `gh api repos/anomalyco/opencode/releases/latest --jq '.tag_name'` (ctx7 does not track the CLI version). When version-specific behavior matters, also fetch the release notes via `gh api repos/anomalyco/opencode/releases/latest --jq '.body'` — note that online docs/ctx7 may describe a newer version than what is installed.

## Network policy

Deny-by-default: the sandbox only reaches the hosts listed in `network-policy.md` (in this directory). Check it before any outbound request (`curl`, `npm`, `git clone`, `websearch`, `webfetch`, ...). Anything not listed is blocked (HTTP 403).

## Startup checks

A plugin injects a `[startup-checks] ...` report (Context7, IntelliJ MCP, gh, Java/Maven, Docker, kubectl, skills) into the system prompt at the start of the session. When you see it, briefly confirm the tooling status in your first reply and continue. If any check reports FAIL, mention it and suggest a fix. Do not re-run the checks yourself.
<!-- sandbox-tools -->
