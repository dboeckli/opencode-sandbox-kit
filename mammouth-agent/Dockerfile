# syntax=docker/dockerfile:1
#
# Pinned Mammouth Code image for the `mammouth-agent` sandbox kit (issue #137).
#
# Bakes the kit tooling AND the Mammouth CLI on top of the official `opencode-docker`
# template (Mammouth is an OpenCode fork), so `setup.install` no longer downloads
# tooling or the agent at sandbox creation time. Mirrors the Mistral Vibe agent kit
# (agent baked into the image), but reuses the opencode-docker base.
#
# Build/publish: .github/workflows/build-and-publish-mammouth-image.yml (multi-arch amd64+arm64).
#
# Run (local dev):
#   sbx run ./mammouth-agent/ --kit-arg imageTag=local --skills=off --static-mcp idea .
#
# ARG BASE_IMAGE must mirror TEMPLATE_VERSION (Renovate-managed); ARG MAMMOUTH_VERSION
# is the Mammouth CLI pin (Renovate, mammouth-ai/code) and drives the image tag.

ARG BASE_IMAGE=docker/sandbox-templates:opencode-docker-0.7.0
FROM ${BASE_IMAGE}

# The base image runs as the unprivileged `agent` user; installs need root.
USER root

COPY files/home/.local/bin/install-apt-packages.sh /tmp/kit/install-apt-packages.sh
COPY files/home/.local/bin/install-tooling.sh /tmp/kit/install-tooling.sh
COPY files/home/.local/bin/install-tooling-user.sh /tmp/kit/install-tooling-user.sh

# Root-level tooling. install-tooling.sh is fail-open by design (for the runtime
# `setup.install`); the explicit verification step below makes the build fail loud.
RUN chmod +x /tmp/kit/*.sh \
 && bash /tmp/kit/install-apt-packages.sh \
 && bash /tmp/kit/install-tooling.sh all

# npm-global CLIs (NPM_CONFIG_PREFIX=/usr/local/share/npm-global inherited from the base).
RUN npm_config_bin_links=true npm install -g ctx7 skills prettier renovate

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
 && command -v ctx7 \
 && command -v skills \
 && command -v prettier \
 && command -v renovate

# Mammouth Code CLI (install.sh, pinned): run as the `agent` user so the binaries land
# in ~/.mammouth, then symlink into PATH for the `mammouth` entrypoint.
ARG MAMMOUTH_VERSION=1.18.31.1
RUN runuser -u agent -- env HOME=/home/agent VERSION="${MAMMOUTH_VERSION}" \
      bash -c 'curl -fsSL https://code.mammouth.ai/install.sh | VERSION="$VERSION" bash' \
 && test -x /home/agent/.mammouth/bin/mammouth \
 && ln -sf /home/agent/.mammouth/bin/mammouth /usr/local/bin/mammouth

# Agent-user tooling (skills, Claude statusline, repsy docs) as uid 1000 / `agent`.
RUN runuser -u agent -- env HOME=/home/agent bash /tmp/kit/install-tooling-user.sh

RUN rm -rf /tmp/kit

# Restore the base image's default user (Entrypoint/CMD are inherited from the base;
# the kit sets `sandbox.entrypoint: [mammouth]`).
USER agent
