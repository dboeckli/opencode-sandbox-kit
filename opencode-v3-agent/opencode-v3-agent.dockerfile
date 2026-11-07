# syntax=docker/dockerfile:1
#
# Standalone OpenCode v3 workload (issue #242). The v1/v2 `opencode-agent/`
# mixin stays untouched; this image bakes the kit tooling + the OpenCode config,
# plugins and guards on top of the versioned `opencode-docker` template.
#
# Build/publish (descriptor is the Dockerfile frontend):
#   docker buildx build ./opencode-v3-agent -f ./opencode-v3-agent/opencode-v3-agent.yaml \
#     -t <IMAGE_PREFIX>/sbx-opencode:<tag> --push
#
# Local build:
#   docker buildx build ./opencode-v3-agent -f ./opencode-v3-agent/opencode-v3-agent.yaml \
#     -t <IMAGE_PREFIX>/sbx-opencode:local --load
#
# ARG BASE_IMAGE must mirror TEMPLATE_VERSION_OPENCODE (Renovate-managed).
# The OpenCode CLI itself comes from the template (currently 1.19.5).

ARG BASE_IMAGE=docker/sandbox-templates:opencode-docker-0.11.0
FROM ${BASE_IMAGE}

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

# Root-level tooling. install-tooling.sh is fail-open by design; the explicit
# verification step below makes the build fail loud.
RUN chmod +x /tmp/kit/*.sh \
 && bash /tmp/kit/install-apt-packages.sh \
 && bash /tmp/kit/install-tooling.sh all

# npm-global CLIs (NPM_CONFIG_PREFIX inherited from the opencode base).
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
 && command -v mcp-inspector \
 && opencode --version

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
