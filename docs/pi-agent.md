# Pi Coding Agent Kit (Kit-Spec v3)

Pi (`@earendil-works/pi-coding-agent`) läuft als eigenständiger **v3-Sandbox-Workload** unter
`pi-agent/`. Das Kit hat dasselbe Tooling wie die anderen Kits und verdrahtet den sbx MCP
Gateway direkt über Pis eingebautes MCP (`~/.pi/agent/mcp.json`) — kein `pi-mcp-adapter` nötig.

## Voraussetzungen

- `sbx` **≥ v0.45** (Repo-Pin v0.50.1) — v3-Format.
- Docker Desktop mit `docker login` (Publish) bzw. lokaler Docker-Daemon (Build).
- Host-MCP registriert: `sbx mcp add idea --url http://localhost:64615/stream --skip-ssrf-check`
  (optional `k8s`, `docker`); Sandbox mit `--static-mcp idea,k8s,docker` erzeugen.
- Secrets: `sbx secret set deepseek` (Default-Modell), optional `zai`, `mistral`, `openrouter`,
  `google`, `context7`, `stackoverflow`, `cloudsmith`, `github-maven`, `sonarcloud`, `codeberg`.

## Aufbau

```
pi-agent/
├── pi-agent.yaml          # v3 descriptor (kind: workload, args.version, capabilities)
├── pi-agent.dockerfile    # Image: Kit-Tooling + Pi, ENTRYPOINT [pi]
├── context.md             # Sandbox-AGENTS.md (agent-context@1, contentFile)
└── files/home/
    ├── .local/bin/        # install-*.sh (Kopien), pi-startup-*.sh, mcp-check.sh
    ├── .config/git/hooks/ # commit-msg (AI-Attribution entfernen)
    ├── .pi/agent/         # settings.json, mcp.json, extensions/mcp-guard.ts, lib/mcp-guard-policy.ts
    ├── sbx-cli.md, stackexchange-api*.md
```

v3-Besonderheiten gegenüber den v2-Kits:

- Kein `sandbox:`-Block: Image, Entrypoint und ENV stehen im Dockerfile.
- Kein `setup.install`: Tooling wird beim Image-Build gebacken; Runtime-Initialisierung
  (Proxy-CA, Maven-Settings) läuft über `com.docker.sandbox/lifecycle@1` `startup`.
- Kein `files/home`-Auto-Mount: alle Dateien werden per `COPY` ins Image gelegt.
- Publish per `docker buildx build ./pi-agent -f ./pi-agent/pi-agent.yaml` (nicht `sbx kit push`,
  das ist v1/v2).
- Keine Komposition mit v1/v2-Kits; `--template`/`--kit-arg imageTag` entfallen.

## Tooling-Parität

Das Image nutzt dieselben Skripte und Versionen wie die anderen Kits:

- Node 26.13.0, shfmt 3.14.1, Liberica JDK 25.0.5+11, Maven 3.10.0, Docker CLI 27.5.1,
  Compose 5.7.0, kubectl (stable), Helm 4.3.1, Kafka 4.4.0
- apt: `jq`, `python3`, `python3-pip`, `python3-yaml`, `libatomic1`
- `fd` + `ripgrep` (Pi lädt sie sonst beim ersten Start nach `~/.pi/agent/bin`)
- Node 26 (via `install-tooling.sh node`; die shell-docker-Basis bringt Node 22 mit)
- npm: `ctx7`, `skills`, `prettier`, `renovate`, `@usebruno/cli`, `@modelcontextprotocol/inspector`,
  `@earendil-works/pi-coding-agent`
- Agent-User: git-`commit-msg`-Hook, Superpowers + dboeckli-Skills (`~/.agents/skills`, Pi erkennt
  das nativ), Repsy-Docs-Clone (`~/docs/repsy-docs`)
- Fail-closed-Verify im Build (alle Tools + `pi --version` == Pin)

Die Skript-Kopien werden von `python local-test/local-test-kits.py --validate-only` auf Drift
geprüft (`INSTALL_SCRIPT_PAIRS`).

## Agent-Konfiguration

`~/.pi/agent/settings.json`:

```json
{
  "defaultProvider": "deepseek",
  "defaultModel": "deepseek-flash",
  "defaultThinkingLevel": "medium"
}
```

`~/.pi/agent/mcp.json` (eingebautes MCP):

```json
{
  "mcpServers": {
    "mcp-gateway": {
      "url": "http://mcp-gateway.docker.internal/mcp",
      "headers": { "Authorization": "Bearer proxy-managed" }
    }
  }
}
```

`~/.pi/agent/extensions/mcp-guard.ts` blockt im `tool_call`-Hook alle `mcp__mcp_gateway__*`-Tools außer
der Read-only-Whitelist; `mcp__mcp_gateway__execute_run_configuration` ist nur
für `local-test-kits-validate-only` erlaubt.

## Credentials

Alle Provider-Keys laufen über `proxyManaged`-Sentinel (`proxy-managed`); der sbx-Proxy ersetzt
ihn bei Requests an die jeweilige API-Domain. Pi liest die Env-Namen:

| Provider | Env | Secret |
|---|---|---|
| DeepSeek (Default) | `DEEPSEEK_API_KEY` | `sbx secret set deepseek` |
| Z.AI (GLM) | `ZAI_API_KEY` | `sbx secret set zai` |
| Mistral | `MISTRAL_API_KEY` | `sbx secret set mistral` |
| OpenRouter | `OPENROUTER_API_KEY` | `sbx secret set openrouter` |
| Google Gemini | `GEMINI_API_KEY` | `sbx secret set google` |
| Context7 | `CONTEXT7_API_KEY` | `sbx secret set context7` |
| Stack Overflow | `STACKOVERFLOW_API_KEY` | `sbx secret set stackoverflow` |
| Cloudsmith | `CLOUDSMITH_API_KEY` | `sbx secret set cloudsmith` |
| GitHub Packages Maven | `GITHUB_MAVEN_TOKEN` | `sbx secret set github-maven` |
| SonarCloud | `SONAR_TOKEN` | `sbx secret set sonarcloud` |
| Codeberg | `CODEBERG_TOKEN` | `sbx secret set codeberg` |

## Starten

```powershell
# Lokal aus dem Verzeichnis (sbx baut das Kit)
sbx run ./pi-agent/ `
    --skills=off `
    --static-mcp idea,k8s,docker `
    . `
    "C:\development\maven-repo:ro"

# Publiziertes Image
sbx run docker.io/domboeckli/sbx-pi-agent:local `
    --skills=off `
    --static-mcp idea,k8s,docker
```

## Build & Publish

```powershell
# Lokal bauen/laden (Tag <pi-version>-<slug>.<ts> + local)
python local-test\build-and-publish-pi-image.py
python local-test\build-and-publish-pi-image.py --build-only

# CI: .github/workflows/build-and-publish-pi-image.yml (multi-arch, workflow_dispatch)
```

Tags: master `<pi-version>` + `latest`; Branch/PR `<pi-version>-<slug>.<ts>` + `<slug>`;
lokal `local`.

## Tests

```powershell
python local-test\local-test-kits.py --validate-only   # Kit + Pins + Drift
python local-test\local-test-kits.py pi                # Sandbox-Szenario
```

Der Validate-Lauf prüft den Pi-Pin (Descriptor == Dockerfile-ARG), das Basis-Template, die
MCP-Guard-Unit-Tests und warnt bei neuerer npm-Version. `sbx kit validate` kann ein **v3-Quellkit**
mit `--offline` nicht prüfen (`no kit builder configured`) — die Descriptor-/Dockerfile-Validierung
übernimmt das buildx-Kit-Frontend im Publish-Workflow bzw. das e2e-Szenario (`sbx run ./pi-agent/`).
Das e2e-Szenario prüft zudem Config, Credential-Wiring und MCP-Gateway (den Guard deckt der Unit-Test ab).

## Troubleshooting

- **`sbx` < v0.45**: v3-Workload wird nicht unterstützt — sbx aktualisieren.
- **Kein `mcp-*` in Pi**: Sandbox ohne `--static-mcp` erzeugt (Gateway nicht registriert);
  Sandbox neu erstellen.
- **`/mcp` zeigt keine Tools**: Host-Server registrieren (`sbx mcp add idea …`) und
  `--static-mcp idea,k8s,docker` setzen.
- **Tool fehlt im Image**: Build-Log prüfen; der Fail-closed-Verify bricht den Build ab.
