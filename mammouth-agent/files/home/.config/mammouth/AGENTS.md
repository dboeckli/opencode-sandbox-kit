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

## Git commits (Nachfragen-Pflicht)

Mache **niemals unaufgefordert Commits**: `git commit`, `git push`, PR-Erstellung und ähnliche Git-Operationen nur mit expliziter Zustimmung des Users ausführen. Ansonsten Änderungen stehen lassen und am Ende den User fragen, ob ein Commit erstellt werden soll.

<!-- sandbox-tools -->
This sandbox is provisioned by the mammouth-agent kit. The following tools are installed and available:

## Mammouth Code docs

Mammouth Code is not in Context7 (no `/mammouth-ai/code` library). Use the official docs at
**https://info.mammouth.ai/docs/mammouth-code** for Mammouth-specific behavior (installation, update/uninstall,
`mammouth -c`, model effort levels via `Ctrl+P`/`Ctrl+T`). The API docs live at
**https://info.mammouth.ai/docs/api-quick-start**. Since Mammouth Code is an OpenCode fork, OpenCode docs
(`npx ctx7 docs /anomalyco/opencode <query>` or `/websites/opencode_ai`) apply for CLI/configuration details.

## IntelliJ IDEA MCP

The IntelliJ MCP server is connected via `host.docker.internal:64342/sse`. Tools are prefixed with `idea_` and
exposed via a **permission-whitelist** in `~/.config/mammouth/opencode.jsonc` (Deny-by-Default, nur lesende
Operationen erlaubt): `idea_get_*`, `idea_list_*`, `idea_search_*`, `idea_read*`, `idea_generate_*`,
`idea_xdebug_get_*`, `idea_xdebug_list_*` sowie einzeln `idea_analyze_calls`, `idea_git_status`,
`idea_lint_files`, `idea_skill_search`, `idea_fetch_query_result`, `idea_preview_table_data`,
`idea_test_database_connection`, `idea_introspect_schema`, `idea_run_inspection_kts`,
`idea_validate_inspection_kts`. Schreibende/ausführende Tools (`idea_apply_patch`, `idea_execute_terminal_command`,
`idea_execute_tool`, `idea_build_project`, `idea_execute_sql_query`, Debugger-Steuerung, ...) sind versteckt
und nicht aufrufbar. `idea_execute_run_configuration` ist nur mit Bestätigung und nur für die im
Run-Config-Guard (`~/.config/mammouth/plugins/intellij-run-config-guard.js`) erlaubte Config
(`local-test-kits-validate-only`) möglich. Use them to interact with the IntelliJ IDE on the Windows host:
navigate code, run inspections, and query the database. These tools require IntelliJ IDEA to be running on the
host with the MCP server plugin enabled.
Docs: `npx ctx7 docs /websites/jetbrains_help <query>` (JetBrains product docs, general); `/jetbrains/intellij-sdk-docs` (plugin SDK), `/jetbrains/intellij-community` (platform/MCP).

## Context7

Docs-as-a-service CLI for libraries/frameworks. See the `<!-- context7 -->` section above.
The Context7 CLI is authenticated via `CONTEXT7_API_KEY` (set to the `proxy-managed` placeholder in the
sandbox; the proxy replaces it with the real key on requests to `context7.com`). That gives a higher
rate limit — no extra setup needed. `echo $CONTEXT7_API_KEY` shows `proxy-managed`, never the real key.

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

These skills are loaded automatically by the agent when a task matches their description.
Docs: `npx ctx7 docs /vercel-labs/skills <query>` (Skills CLI).

## Java / Maven

- JDK (Liberica) 25 at `/usr/local/java` (`JAVA_HOME` set), `java`, `javac`
- Maven 3.9.16 at `/opt/maven`, `mvn`
- **Spring Boot** — `/spring-projects/spring-boot` (framework docs)
- Docs: `npx ctx7 docs <libraryId> <query>` — e.g. `/apache/maven`, `/spring-projects/spring-boot`

## Docker CLI

`docker` CLI is installed and connects to the isolated Docker daemon inside the sandbox microVM. Use it to build/pull/run containers. The Docker socket is not the host socket.

Enthält auch das **docker compose**-Plugin (5.4.0, `/usr/local/lib/docker/cli-plugins/docker-compose`) — `docker compose up` funktioniert für Projekte mit `compose.yaml`.
Docs: `npx ctx7 docs /docker/docs <query>` (e.g. `/docker/docs` for the Docker docs, `/docker/compose`, `/dockerfile`).

**sbx CLI** (auf dem Host via PowerShell): Offline-Referenz aller `--help`-Outputs unter `~/sbx-cli.md` — sie liegt im Kit-Bundle (`files/home/sbx-cli.md`, v0.38.0).

## kubectl

`kubectl` (latest stable) at `/usr/local/bin/kubectl`. No cluster is pre-configured; check `kubectl config current-context` or configure a kubeconfig as needed.
Docs: `npx ctx7 docs <libraryId> <query>` — e.g. `/kubernetes/kubectl`.

## Helm

`helm` 3.21.3 (v3) at `/usr/local/bin/helm`, `helm4` 4.2.4 (v4) at `/usr/local/bin/helm4`. Downloads charts from OCI registries (`helm pull`, `helm push`, `helm upgrade --install`). `get.helm.sh` ist in der Network-Allowlist. v3 ist der Default auf dem PATH (kokuwaio/helm-maven-plugin 6.17.0 ist nicht v4-kompatibel); v4 liegt als `helm4` parallel und kann explizit aufgerufen werden.
Docs: `npx ctx7 docs /helm/helm-www <query>` (Kubernetes package manager, charts).

## Runtime tools / CLIs (docs via ctx7)

Docs for other installed runtime tools:
- **Node.js** — `/nodejs/node` (runtime, `node`, `npm exec`/`npx`)
- **npm** — `/npm/cli` (package manager)
- **Git** — `/git/htmldocs` (version control)
- **jq** — `/jqlang/jq` (JSON processor)
- **Renovate** — `/renovatebot/renovate` (dependency updates; inkl. `renovate-config-validator` — Config validieren: `renovate-config-validator .github/renovate.json`)

> **`npm_config_bin_links` ist bereits global gesetzt** (`spec.yaml` → `environment.variables`, Wert `false`).
> Kein `export npm_config_bin_links=...` vor npm- oder Build-Kommandos nötig — die Variable steht schon in der
> Umgebung; ein erneutes Exportieren ist redundant.

## Related tooling docs (not installed, docs via ctx7)

These tools are not installed in the sandbox, but their documentation is available via Context7:
- **Dependabot** — `/dependabot/dependabot-core` (GitHub dependency updates / security)

## Languages / formats (docs via ctx7)

Docs for the languages and file formats used in this sandbox:
- **Python** — `/python/cpython` (language reference, stdlib)
- **Bash** — `/websites/devdocs_io_bash` (GNU Bash Reference Manual)
- **YAML / `.yml` / `.yaml`** — `/yaml/yaml-spec` (YAML 1.2 specification)
- **JSON / `.json`** — `/websites/json` (JSON data format); `.jsonc` (JSON with comments): `/eslint/json`

## gh (GitHub CLI)

`gh` is available and authenticated via a proxy-injected token. `gh auth status` should work. Run `gh --help` to see all commands (repo, pr, issue, release, api, auth, ...). Use it for GitHub operations (repos, PRs, issues).
Docs: `npx ctx7 docs /cli/cli <query>` (GitHub CLI).

## OpenCode

OpenCode is an agent CLI (and the base for Mammouth Code). For configuration of `opencode.json`, agents, skills, and MCP servers:
Docs: `npx ctx7 docs /anomalyco/opencode <query>`.

## Network policy

Deny-by-default: the sandbox only reaches the hosts listed in `network-policy.md` (in this directory).
Check it before any outbound request (`curl`, `npm`, `git clone`, `websearch`, `webfetch`, ...).
Anything not listed is blocked (HTTP 403).

The list is enforced by the sandbox proxy (`mcp-gateway`, the "mcp-gateway Connected" entry in the
MCP list) — `network-policy.md` only informs you so you avoid blocked calls.

## Stack Overflow API (optionale Fallback-Quelle)

Stack Overflow ist die **letzte Quelle** in der Abfragehierarchie (SO-1). Sie wird **nie** über
`websearch`/`webfetch` genutzt (SO-3) — nur als direkter API-Call gegen `api.stackexchange.com`.

Auslöser (SO-4) sind konkrete Fehlermuster bei **leerem Context7-Ergebnis** (und anderen
Quellen): Exception-Stacktraces, Build-Fehler, Plugin-Konflikte.

Die KI fragt den Benutzer **vor jedem API-Call explizit um Erlaubnis** (SO-2):

> «Context7 liefert keine Ergebnisse. Darf ich Stack Overflow durchsuchen?»

Erst nach Zustimmung erfolgt der Call, z. B.
`curl "https://api.stackexchange.com/2.3/search?site=stackoverflow" -H "Authorization: Bearer $STACKOVERFLOW_API_KEY"`.
Doku zur API: **lokal in `~/stackexchange-api.md`** (kompakte Endpoint-Tabelle, generische
Parameter, API-Version `api_revision`) — offline, spart Kontext. Detail-Doku (alle Parameter je
Methode) in `~/stackexchange-api-detail.md` nur bei Bedarf lesen; die Website
https://api.stackexchange.com/docs nur noch bei Unklarheiten abrufen.
Ohne registriertes Secret (`sbx secret set stackoverflow`) oder ohne Zustimmung wird der Call
nicht ausgeführt.

## Cloudsmith

Cloudsmith ist eine Artifact-Hosting-Plattform (Maven/NuGet/Npm/PyPI/Docker/etc.). Doku via
Context7 (`npx ctx7 docs /websites/cloudsmith <query>`, API-Bindings:
`/cloudsmith-io/cloudsmith-api`, z. B. Uploads über FilesApi). API-Key unter
https://cloudsmith.io/user/settings/api-keys/, als Secret registrieren (`sbx secret set cloudsmith`).
In der Sandbox ist `CLOUDSMITH_API_KEY=proxy-managed` gesetzt; der Agent sendet
`X-Api-Key: proxy-managed`, der Proxy ersetzt den Platzhalter transparent bei Requests an
`api.cloudsmith.io` (REST-API) und `upload.cloudsmith.io` (Package-Upload) – der Key liegt
nie im Sandbox-Filesystem.

> **Helm-OCI-Pull aus Cloudsmith:** `docker.cloudsmith.io` ist in der Netzwerk-Allowlist —
> Helm-Pull von `oci://docker.cloudsmith.io/…` (z. B. rest-mvc-Subcharts) funktioniert. Ein
> `helm registry login` für `docker.cloudsmith.io` ist in der Sandbox nicht möglich
> (Credential-Injection nur für die API-Domains).

## Offline documentation (Repsy)

Die Repsy-Doku (Maven/Helm/NuGet/Npm/PyPI/Cargo/Docker auf `repo.repsy.io`) ist **nicht in
Context7** verfügbar. Der Hugo-Markdown-Source liegt offline im Checkout
`~/docs/repsy-docs/` (Shallow-Clone von https://github.com/repsyio/repsy-docs, installiert via
`setup.install`).

Wenn die Repsy-Doku benötigt wird: **direkt im Markdown-Source lesen** (token-effizienter als
HTML-Parsing der Website), z. B.:

```bash
ls ~/docs/repsy-docs/content/            # maven, helm, nuget, npm, pypi, cargo, go, ruby, docker, ...
grep -r "repo.repsy.io" ~/docs/repsy-docs/content/maven/
```

Aktualisieren (falls neuere Doku erwartet wird):

```bash
git -C ~/docs/repsy-docs pull --ff-only --quiet
```

## Startup checks

A hook injects a `[startup-checks] ...` report (Context7, IntelliJ MCP, gh, Java/Maven, Docker, kubectl, helm, skills, mammouth) into the system prompt at the start of the session. When you see it, briefly confirm the tooling status in your first reply and continue. If any check reports FAIL, mention it and suggest a fix. Do not re-run the checks yourself.
<!-- sandbox-tools -->
