# syntax=docker/dockerfile:1
#
# Standalone OpenCode 2 workload (issue #266; same base as the other v3 kits,
# issue #254). Bakes the kit tooling + OpenCode 2 config, plugins and guards on
# top of Docker's official `shell-docker-image`.
#
# Base: `docker.io/sbx/shell-docker-image:latest` — the Docker-recommended base for
# custom workloads that need Docker Engine (docs: customize/author/base-images.md).
# Docker rebuilds it nightly (Ubuntu 26.04 + Node/npm, Python, Go, headless JDK,
# Docker CLI + compose + buildx). We do NOT re-install Node/Docker CLI/compose/buildx
# (avoids double installation; versions are verified below). uv is installed by
# install-tooling.sh (pinned >= 0.13.8, incl. uvx; issue #284) because the base uv's
# CPython download index is too old for newer patch pins (e.g. 3.12.16). The JDK is
# installed as Liberica via install-tooling.sh so all kits share the same JDK vendor/build.
#
# OpenCode 2 itself is NOT part of the base: it is installed from npm and pinned to
# the 2.x line via ARG OPENCODE2_VERSION (Renovate-managed, npm `@opencode/cli`).
# The package is a native-binary launcher: its postinstall hardlinks the matching
# platform binary (optionalDependencies) into bin/opencode.exe. npm installs every
# linux/x64 variant (glibc/musl, AVX2/baseline, ~960 MB total), so the unused
# variants are pruned after the fail-closed version check.
#
# Build/publish (descriptor is the Dockerfile frontend):
#   docker buildx build ./opencode2-v3-agent -f ./opencode2-v3-agent/opencode2-v3-agent.yaml \
#     -t <IMAGE_PREFIX>/sbx-opencode2:<tag> --push
#
# Local build:
#   docker buildx build ./opencode2-v3-agent -f ./opencode2-v3-agent/opencode2-v3-agent.yaml \
#     -t <IMAGE_PREFIX>/sbx-opencode2:local --load
#
# ARG OPENCODE2_VERSION must mirror OPENCODE2_VERSION in local-test-kits.py and
# validate.yml/e2e.yml (Renovate-managed; 2.x line).

ARG BASE_IMAGE=docker.io/sbx/shell-docker-image:latest@sha256:cbeb851c8a7deb8ba62c9b87f8186fd102aaaf9cbf05d4591f8461b82a84e8f6
FROM ${BASE_IMAGE}

# OpenCode 2 CLI pin (npm `@opencode/cli`, 2.x). Available to the RUN steps below.
ARG OPENCODE2_VERSION=2.3.0

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
COPY files/home/.local/bin/seed-opencode2-model-favorites.py /usr/local/bin/seed-opencode2-model-favorites.py
COPY files/home/.local/bin/opencode2-entrypoint.sh /usr/local/bin/opencode2-entrypoint
RUN chmod +x /usr/local/bin/seed-opencode2-model-favorites.py /usr/local/bin/opencode2-entrypoint

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

# npm-global CLIs (NPM_CONFIG_PREFIX inherited from the shell base).
# OpenCode 2 is pinned to the 2.x line via `@opencode/cli@${OPENCODE2_VERSION}`.
# Retry: the npm registry occasionally serves metadata for a just-published
# dependency before all its versions resolve (transient ETARGET).
RUN set -e; \
    for attempt in 1 2 3; do \
      if npm_config_bin_links=true npm install -g ctx7 skills prettier renovate @usebruno/cli@4.3.0 \
           @modelcontextprotocol/inspector@2.15.0 "@opencode/cli@${OPENCODE2_VERSION}"; then \
        break; \
      fi; \
      if [ "${attempt}" = "3" ]; then exit 1; fi; \
      echo "npm install failed (attempt ${attempt}/3); retrying in 10s..." >&2; \
      sleep 10; \
    done

# Fail-closed verification. Base-provided tools (Docker CLI, compose) and the
# install-tooling tools (Node, uv, Liberica JDK, Maven, …) are verified here; the build
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
    uv --version; \
    uvx --version; \
    uv python list --all-versions 3.12 | grep -q 'cpython-3.12.16-linux'; \
    command -v ctx7; \
    command -v skills; \
    command -v prettier; \
    command -v renovate; \
    bru --version; \
    command -v mcp-inspector; \
    opencode --version; \
    opencode --version | grep -Fq "${OPENCODE2_VERSION}"

# Agent-user tooling (skills, Claude statusline, repsy docs) as uid 1000 / `agent`.
RUN runuser -u agent -- env HOME=/home/agent bash /tmp/kit/install-tooling-user.sh

# Seed the model-picker favorites at build time (the entrypoint re-runs it).
RUN runuser -u agent -- env HOME=/home/agent python3 /usr/local/bin/seed-opencode2-model-favorites.py

# Prune the unused native-binary variants (npm installs glibc+musl and AVX2+baseline
# for linux/x64, ~960 MB). The postinstall left a regular binary in the CLI package
# (hardlink or copy); verify it first, then drop the platform packages.
RUN set -eux; \
    root="$(npm root -g)"; \
    bin="$root/@opencode/cli/bin/opencode.exe"; \
    [ -f "$bin" ] && [ ! -L "$bin" ] && [ "$(stat -c %s "$bin")" -gt 1000000 ]; \
    opencode --version | grep -Fq "${OPENCODE2_VERSION}"; \
    rm -rf "$root"/@opencode/cli-linux-* "$root"/@opencode/cli/node_modules/@opencode/cli-linux-*; \
    du -sh "$root/@opencode/cli"; \
    opencode --version | grep -Fq "${OPENCODE2_VERSION}"

# Cleanup needs root (the /tmp/kit scripts are root-owned).
USER root
RUN rm -rf /tmp/kit

# Same runtime environment as the other kit images.
ENV JAVA_HOME=/usr/local/java
ENV npm_config_bin_links=false

USER agent

# The wrapper seeds the model-picker favorites, then execs opencode.
ENTRYPOINT ["opencode2-entrypoint"]
CMD []
