# syntax=docker/dockerfile:1
#
# Custom sandbox template for the Claude Code scenario of the `opencode-agent`
# mixin kit (issue #137).
#
# Same tooling bake as `opencode-agent/opencode/Dockerfile`, but based on the official
# `claude-code-docker` template (agent `claude`, default user `agent`,
# NPM_CONFIG_PREFIX=/usr/local/share/npm-global). This file must stay identical
# to `opencode-agent/opencode/Dockerfile` except for the `ARG BASE_IMAGE` line — checked
# by `local-test/local-test-kits.py --validate-only`.
#
# Build/publish: .github/workflows/publish-claude-image.yml (multi-arch amd64+arm64,
# native runners + imagetools merge, provenance/SBOM).
#
# Run:
#   sbx run --template docker.io/domboeckli/sbx-claude-tooling:<tag> claude `
#       --kit ./opencode-agent/ --skills=off --static-mcp idea .
#
# ARG BASE_IMAGE must mirror TEMPLATE_VERSION (Renovate-managed, see .github/renovate.json).

ARG BASE_IMAGE=docker/sandbox-templates:claude-code-docker-0.7.0
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

# Agent-user tooling (skills, Claude statusline, repsy docs) as uid 1000 / `agent`.
RUN runuser -u agent -- env HOME=/home/agent bash /tmp/kit/install-tooling-user.sh

RUN rm -rf /tmp/kit

# Restore the base image's default user (Entrypoint/CMD are inherited from the base).
USER agent
