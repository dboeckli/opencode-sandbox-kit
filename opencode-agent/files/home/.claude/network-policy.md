# Sandbox Network policy (allow-list)

The sandbox uses a **deny-by-default** network policy (authoritative source: `spec.yaml` → `permissions.network.allow`).
Only the hosts below are reachable. Any request to a host not on this list is blocked by the host proxy
(HTTP 403) and never leaves the sandbox — the attempt only wastes time and tokens.

Before making an outbound request (`curl`, `npm`, `git clone`, `websearch`, `webfetch`, ...), check
this list. Prefer whitelisted endpoints: `npx ctx7 docs` for library docs, `gh` / `api.github.com`
for GitHub, `npm` against `registry.npmjs.org`, `docker pull` against `docker.io`.

- **Agent APIs**: `opencode.ai`, `*.opencode.ai`, `api.deepseek.com`, `*.deepseek.com` (DeepSeek), `anthropic.com`, `api.anthropic.com`, `*.anthropic.com`, `mammouth.ai`, `*.mammouth.ai`, `api.mammouth.ai`, `code.mammouth.ai`, `model-explorer.mammouth.ai`, `openrouter.ai`, `*.openrouter.ai`, `generativelanguage.googleapis.com` (Google Gemini)
- **GitHub**: `github.com`, `api.github.com`, `*.github.com`, `githubusercontent.com`, `objects.githubusercontent.com`, `*.githubusercontent.com`
- **Docs / Context7**: `context7.com`, `*.context7.com`, `models.dev`
- **JetBrains Help**: `jetbrains.com`, `www.jetbrains.com` (IntelliJ HTTP-Client Feature-Doku, z. B. `www.jetbrains.com/help/idea/http-response-handler-examples.html`)
- **Package registries**: `registry.npmjs.org`, `dlcdn.apache.org`, `camel.apache.org`, `*.camel.apache.org`, `maven.org`, `repo1.maven.org`, `*.maven.org`, `spring.io`, `repo.spring.io`, `*.spring.io`
- **Docker / Kubernetes**: `docker.io`, `*.docker.io`, `docker.com`, `*.docker.com`, `download.docker.com`, `dl.k8s.io`, `get.helm.sh`
- **Zusätzliche Container-Registries**: `docker.elastic.co` (Elasticsearch/Kibana/Filebeat/APM), `docker-auth.elastic.co` (Elastic Token-Auth), `cr.jaegertracing.io` (Jaeger), `ghcr.io` (GitHub Packages)
- **Private Maven- & Helm-Repos**: `repo.repsy.io` (Maven + Helm-OCI + Docker), `jitpack.io`, `artifacts.cibseven.org`, `packages.scm-manager.org`
- **Cloudsmith**: `api.cloudsmith.io` (Artifact-Hosting API), `upload.cloudsmith.io` (Package-Upload), `docker.cloudsmith.io` (Helm-OCI-Registry für rest-mvc-Subcharts); API-Doku via Context7 (`npx ctx7 docs /cloudsmith-io/cloudsmith-api <query>`, z. B. FilesApi/Upload)
- **Cloudflare R2**: `**/*.r2.cloudflarestorage.com` (Object Storage; Multi-Level-Wildcard — Blob-Host ist z. B. `docker-registry-production.<hash>.r2.cloudflarestorage.com`)
- **Liberica JDK**: `api.bell-sw.com` (Renovate Versions-API)
- **Ubuntu apt (http, Port 80)**: `archive.ubuntu.com`, `security.ubuntu.com`, `ports.ubuntu.com` (arm64)
- **MongoDB**: `repo.mongodb.org` (apt im Helm-Test-Pod)
- **Skills CLI**: `add-skill.vercel.sh`
- **Web search (last resort)**: `*.exa.ai`
- **Stack Overflow API**: `api.stackexchange.com` (Fallback-Quelle bei spezifischen Fehlermeldungen)
- **IntelliJ MCP (Windows host)**: `localhost:64342`, `127.0.0.1:64342`, `host.docker.internal:64342`
- **Docker Desktop Kubernetes (Windows host)**: `localhost:6443`, `127.0.0.1:6443`, `host.docker.internal:6443` (kube-apiserver)
- **Docker Desktop Docker Engine (Windows host)**: `localhost:2375`, `127.0.0.1:2375`, `host.docker.internal:2375` (Daemon-API via TCP; `export DOCKER_HOST=tcp://host.docker.internal:2375`)
- **Elastic REST-APIs (ELK-Stack, Docker Compose im Host-Docker)**: `localhost:9200`, `127.0.0.1:9200`, `host.docker.internal:9200` (Elasticsearch REST-API), `localhost:5601`, `127.0.0.1:5601`, `host.docker.internal:5601` (Kibana UI + REST-API), `localhost:8200`, `127.0.0.1:8200`, `host.docker.internal:8200` (APM Server OTLP-HTTP-Intake)
- **Elastic REST-APIs (Docker Desktop Kubernetes, NodePort → localhost)**: `localhost:30920`, `127.0.0.1:30920` (Elasticsearch), `localhost:30561`, `127.0.0.1:30561` (Kibana), `localhost:30820`, `127.0.0.1:30820` (APM Server)

Not reachable (blocked): telemetry, and any other host not on this list.