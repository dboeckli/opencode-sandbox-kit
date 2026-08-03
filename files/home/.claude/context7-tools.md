# Context7 Tools – GitHub-Referenz

Alle im Sandbox-Kit (via `AGENTS.md` / `CLAUDE.md`) über Context7 dokumentierten Tools mit ihrer
GitHub-URL. Wo kein offizielles GitHub-Repo existiert, wird die von ctx7 referenzierte Doku-URL
angegeben.

## IntelliJ

| Tool | ctx7 Library-ID | GitHub / URL |
|---|---|---|
| JetBrains Hilfe (allg.) | `/websites/jetbrains_help` | https://www.jetbrains.com/help/ |
| IntelliJ Plugin SDK | `/jetbrains/intellij-sdk-docs` | https://github.com/JetBrains/intellij-sdk-docs |
| IntelliJ Platform | `/jetbrains/intellij-community` | https://github.com/JetBrains/intellij-community |

## Skills

| Tool | ctx7 Library-ID | GitHub / URL |
|---|---|---|
| Skills CLI (vercel-labs) | `/vercel-labs/skills` | https://github.com/vercel-labs/skills |

## Java / Spring / Apache

| Tool | ctx7 Library-ID | GitHub / URL |
|---|---|---|
| Apache Maven | `/apache/maven` | https://github.com/apache/maven |
| Spring Boot | `/spring-projects/spring-boot` | https://github.com/spring-projects/spring-boot |
| Apache Camel | `/apache/camel` | https://github.com/apache/camel |
| Apache CXF | `/websites/cxf_apache` | https://github.com/apache/cxf |
| Apache Commons Lang | `/websites/commons_apache_proper_commons-lang_apidocs` | https://github.com/apache/commons-lang |
| Apache HttpClient | `/apache/httpcomponents-client` | https://github.com/apache/httpcomponents-client |
| Apache Tomcat | `/apache/tomcat` | https://github.com/apache/tomcat |
| Apache POI | `/apache/poi` | https://github.com/apache/poi |

## Docker & Kubernetes

| Tool | ctx7 Library-ID | GitHub / URL |
|---|---|---|
| Docker (Doku) | `/docker/docs` | https://github.com/docker/docs |
| Docker Compose | `/docker/compose` | https://github.com/docker/compose |
| Dockerfile (Referenz) | `/dockerfile` | https://docs.docker.com/reference/dockerfile/ |
| kubectl | `/kubernetes/kubectl` | https://github.com/kubernetes/kubectl |
| Helm | `/helm/helm-www` | https://github.com/helm/helm |

## Runtime-Tools & CLIs

| Tool | ctx7 Library-ID | GitHub / URL |
|---|---|---|
| Node.js | `/nodejs/node` | https://github.com/nodejs/node |
| npm | `/npm/cli` | https://github.com/npm/cli |
| Git | `/git/htmldocs` | https://github.com/git/git |
| jq | `/jqlang/jq` | https://github.com/jqlang/jq |
| Go | `/golang/go` | https://github.com/golang/go |
| pip | `/websites/pip_pypa_io_en_stable` | https://github.com/pypa/pip |
| curl | `/curl/curl` | https://github.com/curl/curl |
| GNU Make | `/websites/gnu_software_make_manual` | https://www.gnu.org/software/make/manual/ |
| gh (GitHub CLI) | `/cli/cli` | https://github.com/cli/cli |
| Python3 / python | `/python/cpython` | https://github.com/python/cpython |
| PowerShell | `/microsoftdocs/powershell-docs` | https://github.com/PowerShell/PowerShell |

## Languages / Formate

| Tool | ctx7 Library-ID | GitHub / URL |
|---|---|---|
| Bash | `/websites/devdocs_io_bash` | https://www.gnu.org/software/bash/manual/ |
| YAML | `/yaml/yaml-spec` | https://github.com/yaml/yaml-spec |
| JSON | `/websites/json` | https://www.json.org/ |
| JSONC (JSON mit Kommentaren) | `/eslint/json` | https://eslint.org/docs/latest/ |

## Bot / Dependency-Management

| Tool | ctx7 Library-ID | GitHub / URL |
|---|---|---|
| Renovate | `/renovatebot/renovate` | https://github.com/renovatebot/renovate |
| Dependabot | `/dependabot/dependabot-core` | https://github.com/dependabot/dependabot-core |

## AI / Agents

| Tool | ctx7 Library-ID | GitHub / URL |
|---|---|---|
| OpenCode | `/anomalyco/opencode` | https://github.com/anomalyco/opencode |
| OpenCode (Website) | `/websites/opencode_ai` | https://opencode.ai/ |
| websearch | (agent-native, keine ctx7-Library) | https://opencode.ai/docs/ |
| webfetch | (agent-native, keine ctx7-Library) | https://opencode.ai/docs/ |

> **Hinweis:** OpenCode-Versionsinfos werden nicht über ctx7 geliefert (ctx7 referenziert nur
> `vscode-a.0.0.12`); die aktuelle Release-Version + Release Notes kommen immer via
> `gh api repos/anomalyco/opencode/releases/latest` (`.tag_name` / `.body`).