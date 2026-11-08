# syntax=docker/dockerfile:1
#
# Standalone OpenCode v3 workload (issue #242; base migrated to the Docker-provided
# shell images in issue #254). Bakes the kit tooling + OpenCode config, plugins and
# guards on top of Docker's official `shell-docker-image`.
#
# Base: `docker.io/sbx/shell-docker-image:latest` — the Docker-recommended base for
# custom workloads that need Docker Engine (docs: customize/author/base-images.md).
# Docker rebuilds it nightly (Ubuntu 26.04 + Node/npm, Python, Go, headless JDK, uv,
# Docker CLI + compose + buildx). We do NOT re-install Node/Docker CLI/compose/buildx
# (avoids double installation; versions are verified below). The JDK is installed as
# Liberica via install-tooling.sh so all kits share the same JDK vendor/build.
#
# OpenCode itself is NOT part of the base: it is installed from npm and pinned to the
# 1.x line via ARG OPENCODE_VERSION (Renovate-managed). The official installer
# (opencode.ai/v2/install) only serves 1.x up to 1.18.18; the npm package
# `opencode-ai` carries the last 1.x (1.19.5).
#
# Build/publish (descriptor is the Dockerfile frontend):
#   docker buildx build ./opencode-v3-agent -f ./opencode-v3-agent/opencode-v3-agent.yaml \
#     -t <IMAGE_PREFIX>/sbx-opencode:<tag> --push
#
# Local build:
#   docker buildx build ./opencode-v3-agent -f ./opencode-v3-agent/opencode-v3-agent.yaml \
#     -t <IMAGE_PREFIX>/sbx-opencode:local --load
#
# ARG OPENCODE_VERSION must mirror OPENCODE_VERSION in local-test-kits.py and
# validate.yml/e2e.yml (Renovate-managed; 1.x line).

ARG BASE_IMAGE=docker.io/sbx/shell-docker-image:latest@sha256:969457e4d3eb99b913985875dab829e41924e5435255356546ccefea56c5d6ea
FROM ${BASE_IMAGE}

# OpenCode CLI pin (npm `opencode-ai`, 1.x). Available to the RUN steps below.
ARG OPENCODE_VERSION=1.19.5

# The base image runs as the unprivileged `agent` user; installs need root.
USER root

# Kit content: ~/.config/opencode (config, plugins, guards), sandbox-kit scripts,
# git hook, offline docs.
COPY --chown=agent:agent files/home/ /home/agent/

# Root-level installer scripts (executed below from /tmp).
COPY files/home/.local/bin/install-apt-packages.sh /tmp/kit/install-apt-packages.sh
COPY files/home/.local/bin/install-tooling.sh /tmp/kit/install-tooling.sh
COPY files/home/.local/bin/install-tooling-user.sh /tmp/kit/install-tooling-user.sh

# Entrypoint wrapper + model-picker seeder. The favorites file must exist before
# the TUI starts (lifecycle startup runs after the entrypoint -> race).
COPY files/home/.local/bin/seed-opencode-model-favorites.py /usr/local/bin/seed-opencode-model-favorites.py
COPY files/home/.local/bin/opencode-entrypoint.sh /usr/local/bin/opencode-entrypoint
RUN chmod +x /usr/local/bin/seed-opencode-model-favorites.py /usr/local/bin/opencode-entrypoint

# Root-level tooling. The base already ships Node/npm, Docker CLI + compose + buildx
# — those are not re-installed (no double installation). The JDK is installed as
# Liberica (install-tooling.sh jdk) so all kits share the same JDK vendor/build at
# JAVA_HOME=/usr/local/java. `rm -rf /usr/local/java` forces a fresh Liberica install
# even if the base (or a base update) ever provides its own /usr/local/java.
# `node` keeps its idempotency guard: it installs the pinned Node only when the base
# Node is < 24 (npm CLIs such as renovate require >= 24).
RUN rm -rf /usr/local/java \
 && chmod +x /tmp/kit/*.sh \
 && bash /tmp/kit/install-apt-packages.sh \
 && for t in node shfmt jdk maven kubectl helm kafka; do bash /tmp/kit/install-tooling.sh "$t"; done

# npm-global CLIs (NPM_CONFIG_PREFIX inherited from the shell base).
# OpenCode is pinned to the 1.x line via `opencode-ai@${OPENCODE_VERSION}`.
# Retry: the npm registry occasionally serves metadata for a just-published
# dependency before all its versions resolve (transient ETARGET).
RUN set -e; \
    for attempt in 1 2 3; do \
      if npm_config_bin_links=true npm install -g ctx7 skills prettier renovate @usebruno/cli@4.3.0 \
           @modelcontextprotocol/inspector@2.13.0 "opencode-ai@${OPENCODE_VERSION}"; then \
        break; \
      fi; \
      if [ "${attempt}" = "3" ]; then exit 1; fi; \
      echo "npm install failed (attempt ${attempt}/3); retrying in 10s..." >&2; \
      sleep 10; \
    done

# Fail-closed verification. Base-provided tools (Docker CLI, compose) and the
# install-tooling tools (Node, Liberica JDK, Maven, …) are verified here; the build
# fails if a version no longer fits the kit's requirements (issue #254).
RUN set -eux; \
    node --version; \
    [ "$(node --version | sed 's/^v//; s/\..*//')" -ge 24 ]; \
    java -version; \
    [ "$(readlink -f "$(command -v java)")" = "/usr/local/java/bin/java" ]; \
    javac -version; \
    [ "$(readlink -f "$(command -v javac)")" = "/usr/local/java/bin/javac" ]; \
    jar --version; \
    [ "$(readlink -f "$(command -v jar)")" = "/usr/local/java/bin/jar" ]; \
    /usr/local/java/bin/java -version; \
    mvn -v; \
    docker --version; \
    docker compose version; \
    kubectl version --client; \
    helm version --short; \
    helm4 version --short; \
    kafka-topics.sh --version; \
    shfmt --version; \
    command -v ctx7; \
    command -v skills; \
    command -v prettier; \
    command -v renovate; \
    bru --version; \
    command -v mcp-inspector; \
    opencode --version; \
    opencode --version | grep -Fq "${OPENCODE_VERSION}"

# Agent-user tooling (skills, Claude statusline, repsy docs) as uid 1000 / `agent`.
RUN runuser -u agent -- env HOME=/home/agent bash /tmp/kit/install-tooling-user.sh

# Seed the model-picker favorites at build time (the entrypoint re-runs it).
RUN runuser -u agent -- env HOME=/home/agent python3 /usr/local/bin/seed-opencode-model-favorites.py

# Cleanup needs root (the /tmp/kit scripts are root-owned).
USER root
RUN rm -rf /tmp/kit

# Same runtime environment as the other kit images.
ENV JAVA_HOME=/usr/local/java
ENV npm_config_bin_links=false

USER agent

# The wrapper seeds the model-picker favorites, then execs opencode.
ENTRYPOINT ["opencode-entrypoint"]
CMD []
