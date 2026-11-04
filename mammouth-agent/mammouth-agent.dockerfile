# syntax=docker/dockerfile:1
#
# Pinned Mammouth Code image for the `mammouth-agent` v3 sandbox workload (issue #240).
# Mammouth is an OpenCode fork; the image builds on the plain `shell-docker`
# template (no OpenCode CLI in the image) and bakes the kit tooling + Mammouth CLI.
#
# Build/publish (descriptor is the Dockerfile frontend):
#   docker buildx build ./mammouth-agent -f ./mammouth-agent/mammouth-agent.yaml \
#     -t <IMAGE_PREFIX>/sbx-mammouth:<tag> --push
#
# Local build:
#   docker buildx build ./mammouth-agent -f ./mammouth-agent/mammouth-agent.yaml \
#     -t <IMAGE_PREFIX>/sbx-mammouth:local --load
#
# ARG BASE_IMAGE uses the shell-docker pin (same as Mistral Vibe; Renovate-managed);
# ARG MAMMOUTH_VERSION is the Mammouth CLI pin (Renovate, mammouth-ai/code).

ARG BASE_IMAGE=docker/sandbox-templates:shell-docker-0.10.0
FROM ${BASE_IMAGE}

# The plain shell template does not set an npm global prefix (opencode-docker did).
# Keep the shared kit convention for install-tooling-user.sh.
ENV NPM_CONFIG_PREFIX=/usr/local/share/npm-global
ENV PATH=/usr/local/share/npm-global/bin:${PATH}

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

# Base utilities the Mammouth installer/tooling expect on the plain shell image.
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates xz-utils unzip \
 && rm -rf /var/lib/apt/lists/*

# Root-level tooling. install-tooling.sh is fail-open by design; the explicit
# verification step below makes the build fail loud.
RUN chmod +x /tmp/kit/*.sh \
 && bash /tmp/kit/install-apt-packages.sh \
 && bash /tmp/kit/install-tooling.sh all

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
 && command -v mcp-inspector

# Mammouth Code CLI (install.sh, pinned): run as the `agent` user so the binaries
# land in ~/.mammouth, then symlink into PATH for the `mammouth` entrypoint.
RUN runuser -u agent -- env HOME=/home/agent VERSION="${MAMMOUTH_VERSION}" \
      bash -c 'curl -fsSL https://code.mammouth.ai/install.sh | VERSION="$VERSION" bash' \
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
