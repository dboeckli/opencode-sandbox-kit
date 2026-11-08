# syntax=docker/dockerfile:1
#
# Pinned Mammouth Code image for the `mammouth-agent` v3 sandbox workload (issue #240;
# base migrated to the Docker-provided shell image in issue #254).
# Mammouth is an OpenCode fork; the image builds on Docker's official
# `shell-docker-image` (no OpenCode CLI in the image) and bakes the kit tooling + Mammouth CLI.
# The base already ships Node/npm, Python, Go, uv and the Docker CLI + compose + buildx —
# those are NOT re-installed (no double installation; versions are verified below). The JDK
# is installed as Liberica via install-tooling.sh so all kits share the same vendor/build.
#
# Build/publish (descriptor is the Dockerfile frontend):
#   docker buildx build ./mammouth-agent -f ./mammouth-agent/mammouth-agent.yaml \
#     -t <IMAGE_PREFIX>/sbx-mammouth:<tag> --push
#
# Local build:
#   docker buildx build ./mammouth-agent -f ./mammouth-agent/mammouth-agent.yaml \
#     -t <IMAGE_PREFIX>/sbx-mammouth:local --load
#
# ARG BASE_IMAGE is Docker's official custom-workload base (`:latest`, nightly) —
# Node/npm, Docker CLI/compose/buildx, Python, Go and uv come from it (Issue #254).
# ARG MAMMOUTH_VERSION is the Mammouth CLI pin (Renovate, mammouth-ai/code).

ARG BASE_IMAGE=docker.io/sbx/shell-docker-image:latest@sha256:969457e4d3eb99b913985875dab829e41924e5435255356546ccefea56c5d6ea
FROM ${BASE_IMAGE}

ARG MAMMOUTH_VERSION=1.18.31.2

# The base image runs as the unprivileged `agent` user; installs need root.
USER root

# Kit content: config (mammouth/, sandbox-kit/, git hooks), scripts, offline docs.
COPY --chown=agent:agent files/home/ /home/agent/

# Root-level installer scripts (executed below from /tmp).
COPY files/home/.local/bin/install-apt-packages.sh /tmp/kit/install-apt-packages.sh
COPY files/home/.local/bin/install-tooling.sh /tmp/kit/install-tooling.sh
COPY files/home/.local/bin/install-tooling-user.sh /tmp/kit/install-tooling-user.sh

# Entrypoint wrapper + model-picker seeder. The favorites file must exist before
# Mammouth starts (the TUI reads it at startup), so the entrypoint seeds it.
COPY files/home/.local/bin/seed-mammouth-model-favorites.py /usr/local/bin/seed-mammouth-model-favorites.py
COPY files/home/.local/bin/mammouth-entrypoint.sh /usr/local/bin/mammouth-entrypoint
RUN chmod +x /usr/local/bin/seed-mammouth-model-favorites.py /usr/local/bin/mammouth-entrypoint

# Base utilities (curl, ca-certificates, xz-utils, unzip) already ship in the
# shell-docker-image base — no extra apt layer needed.

# Root-level tooling. The base already provides Node/npm, Docker CLI + compose +
# buildx, Python, Go and uv — those are not re-installed. The JDK is installed as
# Liberica (install-tooling.sh jdk) so all kits share the same vendor/build at
# JAVA_HOME=/usr/local/java. `rm -rf /usr/local/java` forces a fresh Liberica install
# even if the base ever provides its own /usr/local/java. install-tooling.sh is
# fail-open by design; the explicit verification step below makes the build fail loud.
RUN rm -rf /usr/local/java \
 && chmod +x /tmp/kit/*.sh \
 && bash /tmp/kit/install-apt-packages.sh \
 && for t in node shfmt jdk maven kubectl helm kafka; do bash /tmp/kit/install-tooling.sh "$t"; done \
 && if grep -q 'FAILED' /var/log/sbx-kit-install.log 2>/dev/null; then \
      echo "ERROR: tooling install failed (transient download?) -- see /var/log/sbx-kit-install.log:"; \
      grep -B1 -A8 'FAILED' /var/log/sbx-kit-install.log; \
      exit 1; \
    fi

# npm-global CLIs (install-tooling.sh installed Node 26; npm prefix is /usr/local/share/npm-global).
# Retry: the npm registry occasionally serves metadata for a just-published
# dependency before all its versions resolve (transient ETARGET).
RUN set -e; \
    for attempt in 1 2 3; do \
      if npm_config_bin_links=true npm install -g ctx7 skills prettier renovate @usebruno/cli@4.3.0 \
           @modelcontextprotocol/inspector@2.13.0; then \
        break; \
      fi; \
      if [ "${attempt}" = "3" ]; then exit 1; fi; \
      echo "npm install failed (attempt ${attempt}/3); retrying in 10s..." >&2; \
      sleep 10; \
    done

# Fail-closed verification: abort the build if any tool is missing or wrong.
# Base-provided tools (Docker CLI, compose) and the install-tooling tools (Node,
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
    command -v mcp-inspector

# Mammouth Code CLI (install.sh, pinned): run as the `agent` user so the binaries
# land in ~/.mammouth, then symlink into PATH for the `mammouth` entrypoint.
# Retry the whole install: the script downloads the release asset from GitHub,
# which occasionally returns transient 5xx (503/504) and has no retry of its own.
RUN set -e; \
    for attempt in 1 2 3 4 5; do \
      if runuser -u agent -- env HOME=/home/agent VERSION="${MAMMOUTH_VERSION}" \
           bash -c 'curl -fsSL https://code.mammouth.ai/install.sh | VERSION="$VERSION" bash'; then \
        break; \
      fi; \
      if [ "${attempt}" = "5" ]; then exit 1; fi; \
      echo "mammouth install failed (attempt ${attempt}/5); retrying in 15s..." >&2; \
      sleep 15; \
    done \
 && test -x /home/agent/.mammouth/bin/mammouth \
 && ln -sf /home/agent/.mammouth/bin/mammouth /usr/local/bin/mammouth \
 && mammouth --version | grep -F "${MAMMOUTH_VERSION}"

# Seed the model-picker favorites at build time so the state file already exists
# on the very first start (the entrypoint re-runs the seed anyway).
RUN runuser -u agent -- env HOME=/home/agent python3 /usr/local/bin/seed-mammouth-model-favorites.py

# Agent-user tooling (skills, Claude statusline, repsy docs) as uid 1000 / `agent`.
RUN runuser -u agent -- env HOME=/home/agent bash /tmp/kit/install-tooling-user.sh

RUN rm -rf /tmp/kit

# Same runtime environment as the other kit images.
ENV JAVA_HOME=/usr/local/java
ENV npm_config_bin_links=false

USER agent

# The wrapper seeds the model-picker favorites, then execs mammouth.
ENTRYPOINT ["mammouth-entrypoint"]
CMD []
