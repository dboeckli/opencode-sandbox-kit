# syntax=docker/dockerfile:1
#
# Pinned Pi Coding Agent image for the `pi-agent` v3 sandbox workload (issue #236).
# Bakes the kit tooling on top of the plain `shell-docker` template, so Pi has full
# tooling parity (JDK, Maven, Docker CLI, Compose, kubectl, Helm, Kafka CLI,
# Node.js, npm CLIs, agent-user tooling) and no runtime installs.
#
# Build/publish (descriptor is the Dockerfile frontend):
#   docker buildx build ./pi-agent -f ./pi-agent/pi-agent.yaml \
#     -t <IMAGE_PREFIX>/sbx-pi-agent:<tag> --push
#
# Local build (single arch):
#   docker buildx build ./pi-agent -f ./pi-agent/pi-agent.yaml \
#     -t <IMAGE_PREFIX>/sbx-pi-agent:local --load
#
# ARG BASE_IMAGE uses the shell-docker pin (same as Mistral Vibe; Renovate-managed);
# ARG PI_VERSION is the Pi pin (Renovate, npm @earendil-works/pi-coding-agent).

ARG BASE_IMAGE=docker/sandbox-templates:shell-docker-0.10.0
FROM ${BASE_IMAGE}

# The plain shell template does not set an npm global prefix.
# Keep the shared kit convention so install-tooling-user.sh finds the CLIs at
# /usr/local/share/npm-global/bin.
ENV NPM_CONFIG_PREFIX=/usr/local/share/npm-global
ENV PATH=/usr/local/share/npm-global/bin:${PATH}

ARG PI_VERSION=1.5.0

# The base image runs as the unprivileged `agent` user; installs need root.
USER root

COPY files/home/.local/bin/install-apt-packages.sh /tmp/kit/install-apt-packages.sh
COPY files/home/.local/bin/install-tooling.sh /tmp/kit/install-tooling.sh
COPY files/home/.local/bin/install-tooling-user.sh /tmp/kit/install-tooling-user.sh

# Root-level tooling. install-tooling.sh is fail-open by design (for the runtime
# `setup.install` in v2 kits); the explicit verification step below makes the
# build fail loud.
RUN chmod +x /tmp/kit/*.sh \
 && bash /tmp/kit/install-apt-packages.sh \
 && bash /tmp/kit/install-tooling.sh all

# npm-global CLIs (install-tooling.sh installed Node 26; npm prefix is /usr/local).
# Same npm CLI set as the other kit images, plus Pi itself. Retry the install:
# the npm registry occasionally serves metadata for a just-published dependency
# before all its versions resolve (transient ETARGET), which fails a single run.
RUN set -e; \
    for attempt in 1 2 3; do \
      if npm_config_bin_links=true npm install -g ctx7 skills prettier renovate @usebruno/cli@4.3.0 \
           @modelcontextprotocol/inspector@2.13.0 \
         && npm_config_bin_links=true npm install -g --ignore-scripts @earendil-works/pi-coding-agent@${PI_VERSION}; then \
        break; \
      fi; \
      if [ "${attempt}" = "3" ]; then exit 1; fi; \
      echo "npm install failed (attempt ${attempt}/3); retrying in 10s..." >&2; \
      sleep 10; \
    done

# Fail-closed verification: abort the build if any tool is missing or wrong.
# Node must satisfy Pi's floor (>= 22.19) — install-tooling.sh installs the
# shared Node pin (26.x), so this also proves tooling parity.
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
 && pi --version \
 && pi --version | grep -F "${PI_VERSION}"

# Global git hook must exist before install-tooling-user.sh sets core.hooksPath.
COPY --chown=agent:agent files/home/.config/git/hooks/commit-msg /home/agent/.config/git/hooks/commit-msg

# Agent-user tooling (skills, git hook, repsy docs) as uid 1000 / `agent`.
RUN runuser -u agent -- env HOME=/home/agent bash /tmp/kit/install-tooling-user.sh

# Pi lazy-downloads `fd` (and `rg`) into ~/.pi/agent/bin on first run when they
# are missing. Bake both so a fresh sandbox is ready without a runtime download.
# Ubuntu's fd package installs the binary as `fdfind`; Pi looks for `fd`.
RUN apt-get update \
 && apt-get install -y --no-install-recommends fd-find ripgrep \
 && ln -sf /usr/bin/fdfind /usr/local/bin/fd \
 && rm -rf /var/lib/apt/lists/* \
 && fd --version \
 && rg --version

# Runtime startup scripts (lifecycle@1 startup in pi-agent.yaml), the Pi agent
# configuration (settings + MCP gateway) and the MCP read-only guard extension.
# Kept after the tooling layers so edits here do not invalidate the heavy build cache.
COPY --chown=agent:agent files/home/.local/bin/pi-startup-ca.sh /home/agent/.local/bin/pi-startup-ca.sh
COPY --chown=agent:agent files/home/.local/bin/pi-startup-maven.sh /home/agent/.local/bin/pi-startup-maven.sh
COPY --chown=agent:agent files/home/.local/bin/mcp-check.sh /home/agent/.local/bin/mcp-check.sh
COPY --chown=agent:agent files/home/.pi/agent/ /home/agent/.pi/agent/
COPY --chown=agent:agent files/home/sbx-cli.md files/home/stackexchange-api.md \
    files/home/stackexchange-api-detail.md /home/agent/
RUN chmod +x /home/agent/.local/bin/pi-startup-*.sh /home/agent/.local/bin/mcp-check.sh

RUN rm -rf /tmp/kit

# Same runtime environment as the other kit images.
ENV JAVA_HOME=/usr/local/java
ENV npm_config_bin_links=false

USER agent

# Launch Pi. The kit descriptor owns the agent lifecycle; this CMD is kept for
# plain `docker run`.
ENTRYPOINT ["pi"]
CMD []
