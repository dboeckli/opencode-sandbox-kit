# syntax=docker/dockerfile:1
#
# Pinned Mistral Vibe image for the `mistral-vibe-agent` v3 sandbox workload (issue #241).
# Builds on the versioned `shell-docker` template, bakes the kit tooling (JDK,
# Maven, Docker CLI, Compose, kubectl, Helm, Kafka, Node, npm CLIs) and a pinned
# `mistral-vibe` version (PyPI).
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
# ARG BASE_IMAGE uses the shared shell-docker pin (Renovate-managed);
# ARG VIBE_VERSION is the Mistral Vibe pin (Renovate, PyPI mistral-vibe).

ARG BASE_IMAGE=docker/sandbox-templates:shell-docker-0.10.0
FROM ${BASE_IMAGE}

ARG VIBE_VERSION=3.0.4

# The plain shell template does not set an npm global prefix; keep the shared
# kit convention for install-tooling-user.sh.
ENV NPM_CONFIG_PREFIX=/usr/local/share/npm-global
ENV PATH=/usr/local/share/npm-global/bin:${PATH}

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
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc g++ python3-dev \
 && rm -rf /var/lib/apt/lists/*

# Root-level tooling. install-tooling.sh is fail-open by design; the explicit
# verification step below makes the build fail loud.
RUN chmod +x /tmp/kit/*.sh \
 && bash /tmp/kit/install-apt-packages.sh \
 && bash /tmp/kit/install-tooling.sh all

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
RUN shfmt --version \
 && java -version \
 && mvn -v \
 && docker --version \
 && docker compose version \
 && kubectl version --client \
 && helm version --short \
 && helm4 version --short \
 && kafka-topics.sh --version \
 && node --version \
 && [ "$(node --version | sed 's/^v//; s/\..*//')" -ge 24 ] \
 && command -v ctx7 \
 && command -v skills \
 && command -v prettier \
 && command -v renovate \
 && bru --version \
 && command -v mcp-inspector \
 && uv --version

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
