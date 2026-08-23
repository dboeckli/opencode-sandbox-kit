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
5. **Stack Overflow API** — **letzte Quelle** bei konkreten Fehlermeldungen (Exception-Stacktraces, Build-Fehler, Plugin-Konflikte) mit leerem Context7-Ergebnis; nur als direkter API-Call gegen `api.stackexchange.com`, **nie** via `websearch`/`webfetch`. Fragt den Benutzer vor jedem Call explizit um Erlaubnis.

**Failure handling:** if IntelliJ MCP, Context7 (`npx ctx7`), or the GitHub API (`gh api`) is unavailable or fails (not running, error, not found, timeout, rate limit, 403), tell the user immediately which source failed and how the result is affected, then fall back per the steps above. Do not silently degrade.

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

> **Helm-OCI-Pull aus Cloudsmith:** `docker.cloudsmith.io` + `dl.cloudsmith.io` sind in der
> Netzwerk-Allowlist — Helm-Pull von `oci://docker.cloudsmith.io/…` (z. B. rest-mvc-Subcharts)
> funktioniert (Blob-Download via `dl.cloudsmith.io`). Ein `helm registry login`
> für `docker.cloudsmith.io` ist in der Sandbox nicht möglich (Credential-Injection
> nur für die API-Domains).

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

## Verification

Before declaring a task done, verify it: run the project's build/test/lint commands (see the repo's `AGENTS.md`/`README`) and report the output as evidence, iterating until they pass. For non-trivial changes, use a fresh-context subagent to review the diff.

## Response style

Token-efficient responses: telegram style, no filler/pleasantries, no full-file dumps — show only changed lines/methods. Detect the project's stack from the repo; never assume a framework (e.g. Spring Boot). Full rules: `response-style.md` (in this directory).

## Git commits (Nachfragen-Pflicht)

Mache **niemals unaufgefordert Commits**: `git commit`, `git push`, PR-Erstellung und ähnliche Git-Operationen nur mit expliziter Zustimmung des Users ausführen. Ansonsten Änderungen stehen lassen und am Ende den User fragen, ob ein Commit erstellt werden soll.

<!-- sandbox-tools -->
This sandbox is provisioned by the opencode-sandbox-kit. The following tools are installed and available:

## IntelliJ IDEA MCP

Connected via `host.docker.internal:64342/sse`; tools prefixed with `idea_` (symbol search, read file, build, inspect problems, SQL, debugger) and listed each session. Interacts with the IDE on the Windows host (requires IntelliJ running). Primary documentation source for the project itself (see lookup priority). Access is restricted to a read-only whitelist configured in `~/.claude/settings.json` (`permissions`); `idea_execute_run_configuration` is further limited to `local-test-kits-validate-only` by the PreToolUse hook `~/.config/sandbox-kit/intellij-run-config-guard.sh`.

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

## Java / Maven

- JDK (Liberica) 25 at `/usr/local/java` (`JAVA_HOME` set), `java`, `javac`
- Maven 3.9.16 at `/opt/maven`, `mvn`
- Spring Boot, Apache Camel, CXF, Commons Lang, HttpClient, Tomcat, POI — see `context7-tools.md`

## Docker CLI

`docker` CLI is installed and connects to the isolated Docker daemon inside the sandbox microVM. Use it to build/pull/run containers. The Docker socket is not the host socket.

Enthält auch das **docker compose**-Plugin (5.4.0, `/usr/local/lib/docker/cli-plugins/docker-compose`) — `docker compose up` funktioniert für Projekte mit `compose.yaml`.

**sbx CLI** (auf dem Host via PowerShell): Offline-Referenz aller `--help`-Outputs unter `~/sbx-cli.md` — sie liegt im Kit-Bundle (`files/home/sbx-cli.md`, v0.38.0).

## kubectl

`kubectl` (latest stable) at `/usr/local/bin/kubectl`. No cluster is pre-configured; check `kubectl config current-context` or configure a kubeconfig as needed.

## Helm

Helm 3.21.3 (v3) at `/usr/local/bin/helm`, Helm 4.2.4 (v4) at `/usr/local/bin/helm4`. Downloads charts from OCI registries (`helm pull`, `helm push`, `helm upgrade --install`). `get.helm.sh` ist in der Network-Allowlist. v3 ist der Default auf dem PATH (kokuwaio/helm-maven-plugin 6.17.0 ist nicht v4-kompatibel); v4 liegt als `helm4` parallel und kann explizit aufgerufen werden.

## Runtime tools / CLIs

Installed runtime CLIs — Node.js, npm, Git, jq, Go, pip, curl, GNU Make — see `context7-tools.md`.

> **`npm_config_bin_links` ist bereits global gesetzt** (`spec.yaml` → `environment.variables`, Wert `false`).
> Kein `export npm_config_bin_links=...` vor npm- oder Build-Kommandos nötig — die Variable steht schon in der
> Umgebung; ein erneutes Exportieren ist redundant.

## Renovate

Renovate (inkl. `renovate-config-validator`) via npm global installiert. Config validieren: `renovate-config-validator .github/renovate.json`.

## Related tooling (not installed)

Not installed in the sandbox, but documented via Context7: Dependabot — see `context7-tools.md`.

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

Versions: do not assume the installed or latest version. Check the installed version with `opencode --version`, and always fetch the latest release from GitHub Releases via `gh api repos/anomalyco/opencode/releases/latest --jq '.tag_name'` (ctx7 does not track the CLI version). When versioning matters, also fetch the release notes via `gh api repos/anomalyco/opencode/releases/latest --jq '.body'` — note that online docs/ctx7 may describe a newer version than what is installed.

## Network policy

Deny-by-default: the sandbox only reaches the hosts listed in `network-policy.md` (in this directory). Check it before any outbound request (`curl`, `npm`, `git clone`, web search, ...). Anything not listed is blocked (HTTP 403).

The list is enforced by the sandbox proxy (`mcp-gateway`, the "mcp-gateway Connected" entry in the MCP list) — `network-policy.md` only informs you so you avoid blocked calls.

## Startup checks

A SessionStart hook runs the sandbox checks and passes a `[startup-checks] ...` report (Context7, IntelliJ MCP, gh, Java/Maven, Docker, kubectl, helm, skills) as a system message at the start of the session. When you receive it, briefly confirm the tooling status in your first reply and continue. If any check reports FAIL, mention it and suggest a fix. Do not re-run the checks yourself.
<!-- sandbox-tools -->