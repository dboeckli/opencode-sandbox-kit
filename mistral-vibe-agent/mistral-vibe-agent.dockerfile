# syntax=docker/dockerfile:1
#
# Pinned Mistral Vibe image for the `mistral-vibe-agent` v3 sandbox workload (issue #241;
# base migrated to the Docker-provided shell image in issue #254).
# Builds on Docker's official `shell-docker-image`, bakes the kit tooling (Liberica JDK,
# Maven, kubectl, Helm, Kafka, Node, npm CLIs) and a pinned `mistral-vibe` version (PyPI).
# The base already ships Node/npm, Python and the Docker CLI + compose + buildx —
# those are NOT re-installed (no double installation; versions are verified below).
# uv is installed by install-tooling.sh (pinned >= 0.13.8, incl. uvx; issue #284)
# because the base uv's CPython download index is too old for newer patch pins.
#
# Build/publish (descriptor is the Dockerfile frontend):
#   docker buildx build ./mistral-vibe-agent -f ./mistral-vibe-agent/mistral-vibe-agent.yaml \
#     -t <IMAGE_PREFIX>/sbx-mistral-vibe:<tag> --push
#
# Local build:
#   docker buildx build ./mistral-vibe-agent -f ./mistral-vibe-agent/mistral-vibe-agent.yaml \
#     -t <IMAGE_PREFIX>/sbx-mistral-vibe:local --load
#
# CI builds linux/amd64 + linux/arm64 on native runners (`uv tool install` does
# not run under QEMU arm64 emulation) and merges with `imagetools create`.
#
# ARG BASE_IMAGE is Docker's official custom-workload base (`:latest`, nightly) —
# Node/npm, Python and the Docker CLI/compose/buildx come from it (Issue #254).
# ARG VIBE_VERSION is the Mistral Vibe pin (Renovate, PyPI mistral-vibe).

ARG BASE_IMAGE=docker.io/sbx/shell-docker-image:latest@sha256:78bbd3aa71057e907f70a81c23456ab5476c8b6ec66c7d2bb356181fa3f94a1f
FROM ${BASE_IMAGE}

ARG VIBE_VERSION=3.1.2

USER root

# Kit content: ~/.vibe config/hooks/guard, sandbox-kit scripts, offline docs.
COPY --chown=agent:agent files/home/ /home/agent/

# Root-level installer scripts (executed below from /tmp).
COPY files/home/.local/bin/install-apt-packages.sh /tmp/kit/install-apt-packages.sh
COPY files/home/.local/bin/install-tooling.sh /tmp/kit/install-tooling.sh
COPY files/home/.local/bin/install-tooling-user.sh /tmp/kit/install-tooling-user.sh

# Build tools for source builds of native dependencies: `miniaudio` (a transitive
# mistral-vibe dependency) ships no arm64 wheel for Python 3.14, so uv compiles it
# from source — needs a C/C++ compiler and the Python dev headers (pyconfig.h).
# The base image already ships gcc/g++, but not the Python dev headers.
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3-dev \
 && rm -rf /var/lib/apt/lists/*

# Root-level tooling. The base already provides Node/npm, Docker CLI + compose +
# buildx and Python — those are not re-installed (uv is installed here, Issue #284).
# The JDK is installed as
# Liberica (install-tooling.sh jdk) so all kits share the same vendor/build at
# JAVA_HOME=/usr/local/java. `rm -rf /usr/local/java` forces a fresh Liberica install
# even if the base ever provides its own /usr/local/java. install-tooling.sh is
# fail-open by design; the explicit verification step below makes the build fail loud.
RUN rm -rf /usr/local/java \
 && chmod +x /tmp/kit/*.sh \
 && bash /tmp/kit/install-apt-packages.sh \
 && for t in node shfmt uv jdk maven kubectl helm kafka; do bash /tmp/kit/install-tooling.sh "$t"; done \
 && if grep -q 'FAILED' /var/log/sbx-kit-install.log 2>/dev/null; then \
      echo "ERROR: tooling install failed (transient download?) -- see /var/log/sbx-kit-install.log:"; \
      grep -B1 -A8 'FAILED' /var/log/sbx-kit-install.log; \
      exit 1; \
    fi \
 && java -version \
 && [ "$(readlink -f "$(command -v java)")" = "/usr/local/java/bin/java" ] \
 && javac -version \
 && [ "$(readlink -f "$(command -v javac)")" = "/usr/local/java/bin/javac" ] \
 && jar --version \
 && [ "$(readlink -f "$(command -v jar)")" = "/usr/local/java/bin/jar" ] \
 && shfmt --version

# npm-global CLIs (install-tooling.sh installed Node 26). Retry: the npm registry
# occasionally serves metadata for a just-published dependency before all its
# versions resolve (transient ETARGET).
RUN set -e; \
    for attempt in 1 2 3; do \
      if npm_config_bin_links=true npm install -g ctx7 skills prettier renovate @usebruno/cli@4.3.0 \
           @modelcontextprotocol/inspector@2.14.0; then \
        break; \
      fi; \
      if [ "${attempt}" = "3" ]; then exit 1; fi; \
      echo "npm install failed (attempt ${attempt}/3); retrying in 10s..." >&2; \
      sleep 10; \
    done

# Fail-closed verification: abort the build if any tool is missing or wrong.
# Base-provided tools (Docker CLI, compose) and the install-tooling tools (Node, uv,
# Liberica JDK, Maven, …) are verified here; the build fails if a version no longer
# fits the kit's requirements (Issue #254).
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
    uv --version; \
    uvx --version; \
    uv python list --all-versions 3.12 | grep -q 'cpython-3.12.16-linux'

# Install Vibe as the non-root agent user. The socks extra is installed explicitly
# so the agent works through the sandbox proxy (some releases don't pull it in).
USER agent
RUN uv tool install "mistral-vibe==${VIBE_VERSION}" --with "httpx[socks]" \
 && vibe --version | grep -F "${VIBE_VERSION}"

# Agent-user tooling (skills, Claude statusline, repsy docs) as uid 1000 / `agent`.
RUN bash /tmp/kit/install-tooling-user.sh

# Cleanup needs root (the /tmp/kit scripts are root-owned).
USER root
RUN rm -rf /tmp/kit
USER agent

# Same runtime environment as the other kit images; pin the start model via ENV
# (wins over config.toml; `/model` still switches per session).
ENV JAVA_HOME=/usr/local/java
ENV npm_config_bin_links=false
ENV VIBE_ACTIVE_MODEL=glm-flash

# Launch Vibe in auto-approve mode (the pre_tool guard enforces the read-only
# MCP whitelist).
ENTRYPOINT ["vibe", "--agent", "auto-approve"]
CMD []
