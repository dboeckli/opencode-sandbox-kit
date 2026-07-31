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

<!-- sandbox-tools -->
This sandbox is provisioned by the opencode-sandbox-kit. The following tools are installed and available:

## IntelliJ IDEA MCP

The IntelliJ MCP server is connected via `host.docker.internal:64342/sse`. Tools are prefixed with `idea_` (e.g. `idea_search_symbol`, `idea_read_file`, `idea_build_project`, `idea_get_file_problems`, `idea_execute_sql_query`, debugger tools). The full set of available `idea_*` tools is exposed to the agent automatically by the MCP server — they appear in the tool list at the start of every session. Use them to interact with the IntelliJ IDE on the Windows host: navigate code, run inspections, build, debug, and query the database. These tools require IntelliJ IDEA to be running on the host with the MCP server plugin enabled.

## Context7

Docs-as-a-service CLI for libraries/frameworks. See the `<!-- context7 -->` section above.

## Skills CLI

`skills` (vercel-labs) manages reusable agent skills. Installed skills live in `~/.agents/skills/` and are auto-loaded. Manage with:
- `skills ls` / `skills ls -g` — list installed skills
- `skills add <package>` — add a skill package (e.g. `skills add -g https://github.com/dboeckli/ai-agent-skills.git`)
- `skills remove [skills]` / `skills update` — remove / update skills

Installed skills (from [dboeckli/ai-agent-skills](https://github.com/dboeckli/ai-agent-skills)):
- **camel-matrix** — generates an AsciiDoc compatibility matrix for Apache Camel Spring Boot, Spring Boot, and Apache CXF versions by running `camel-springboot-matrix.sh`. Use when asked to generate/update the Camel compatibility matrix or check Camel Spring Boot version compatibility.
- **cc-best-practices** — guidance on using Claude Code effectively (context management, verification, explore-plan-implement workflow, prompting, parallel sessions).
- **project-references** — look up conventions/patterns from GitHub repos checked out under `~/projects/referenzen/` (Helm charts, K8s manifests, Docker Compose, CI/CD). Cite the source project when adopting a pattern.
- **skill-best-practices** — guide for creating/structuring/improving SKILL.md files.

These skills are loaded automatically by OpenCode when a task matches their description.

## Java / Maven

- JDK (Liberica) 25 at `/usr/local/java` (`JAVA_HOME` set), `java`, `javac`
- Maven 3.9.16 at `/opt/maven`, `mvn`
- Docs: `npx ctx7 docs <libraryId> <query>` — e.g. `/apache/maven`, `/spring-projects/spring-boot`

## Docker CLI

`docker` CLI is installed and connects to the isolated Docker daemon inside the sandbox microVM. Use it to build/pull/run containers. The Docker socket is not the host socket.
Docs: `npx ctx7 docs /docker/docs <query>` (e.g. `/docker/docs` for the Docker docs, `/docker/compose`, `/dockerfile`).

## kubectl

`kubectl` (latest stable) at `/usr/local/bin/kubectl`. No cluster is pre-configured; check `kubectl config current-context` or configure a kubeconfig as needed.
Docs: `npx ctx7 docs <libraryId> <query>` — e.g. `/kubernetes/kubectl`.

## Related tooling docs (not installed, docs via ctx7)

These tools are not installed in the sandbox, but their documentation is available via Context7:
- **Helm** — `/helm/helm-www` (Kubernetes package manager, charts)
- **Renovate** — `/renovatebot/renovate` (automated dependency updates, PRs)
- **Dependabot** — `/dependabot/dependabot-core` (GitHub dependency updates / security)

## gh (GitHub CLI)

`gh` is available and authenticated via a proxy-injected token. `gh auth status` should work. Run `gh --help` to see all commands (repo, pr, issue, release, api, auth, ...). Use it for GitHub operations (repos, PRs, issues).

## Startup checks

A plugin injects a `[startup-checks] ...` report (Context7, IntelliJ MCP, gh, Java/Maven, Docker, kubectl, skills) into the system prompt at the start of the session. When you see it, briefly confirm the tooling status in your first reply and continue. If any check reports FAIL, mention it and suggest a fix. Do not re-run the checks yourself.
<!-- sandbox-tools -->
