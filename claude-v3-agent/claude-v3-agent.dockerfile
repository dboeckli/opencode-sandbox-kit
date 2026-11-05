# syntax=docker/dockerfile:1
#
# Standalone Claude Code v3 workload (issue #242). The v1/v2 `opencode-agent/`
# mixin stays untouched; this image bakes the kit tooling + the Claude config,
# managed settings and guards on top of the versioned `claude-code-docker`
# template (the Claude Code CLI itself comes from the template).
#
# Build/publish (descriptor is the Dockerfile frontend):
#   docker buildx build ./claude-v3-agent -f ./claude-v3-agent/claude-v3-agent.yaml \
#     -t <IMAGE_PREFIX>/sbx-claude:<tag> --push
#
# Local build:
#   docker buildx build ./claude-v3-agent -f ./claude-v3-agent/claude-v3-agent.yaml \
#     -t <IMAGE_PREFIX>/sbx-claude:local --load
#
# ARG BASE_IMAGE must mirror TEMPLATE_VERSION_CLAUDE (Renovate-managed).

ARG BASE_IMAGE=docker/sandbox-templates:claude-code-docker-0.10.0
FROM ${BASE_IMAGE}

# The base image runs as the unprivileged `agent` user; installs need root.
USER root

# Kit content: ~/.claude (settings, permission whitelist, docs), ~/.claude.json
# (MCP gateway), sandbox-kit scripts, git hook, offline docs.
COPY --chown=agent:agent files/home/ /home/agent/

# Root-level installer scripts (executed below from /tmp).
COPY files/home/.local/bin/install-apt-packages.sh /tmp/kit/install-apt-packages.sh
COPY files/home/.local/bin/install-tooling.sh /tmp/kit/install-tooling.sh
COPY files/home/.local/bin/install-tooling-user.sh /tmp/kit/install-tooling-user.sh

# Runtime config merge + entrypoint wrapper (re-applies kit settings and the
# MCP gateway before Claude Code starts; see claude-config.py).
COPY files/home/.local/bin/claude-config.py /usr/local/bin/claude-config.py
COPY files/home/.local/bin/claude-entrypoint.sh /usr/local/bin/claude-entrypoint
RUN chmod +x /usr/local/bin/claude-config.py /usr/local/bin/claude-entrypoint

# Root-level tooling. install-tooling.sh is fail-open by design; the explicit
# verification step below makes the build fail loud.
RUN chmod +x /tmp/kit/*.sh \
 && bash /tmp/kit/install-apt-packages.sh \
 && bash /tmp/kit/install-tooling.sh all

# npm-global CLIs (NPM_CONFIG_PREFIX inherited from the claude-code base).
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
 && command -v claude \
 && runuser -u agent -- env HOME=/home/agent claude --version

# Agent-user tooling (skills, Claude statusline, repsy docs) as uid 1000 / `agent`.
RUN runuser -u agent -- env HOME=/home/agent bash /tmp/kit/install-tooling-user.sh

# Highest-precedence managed settings (statusLine + PreToolUse/SessionStart hooks);
# the template does not overwrite /etc/claude-code. Needs root.
RUN bash /home/agent/.local/bin/write-managed-settings.sh

# Cleanup needs root (the /tmp/kit scripts are root-owned).
RUN rm -rf /tmp/kit

# Same runtime environment as the other kit images.
ENV JAVA_HOME=/usr/local/java
ENV ANTHROPIC_DEFAULT_SONNET_MODEL=claude-sonnet-4-6
ENV ANTHROPIC_MODEL=claude-sonnet-4-6
ENV npm_config_bin_links=false

USER agent

# tini is inherited from the base image. The wrapper merges the kit config,
# then execs the Claude Code CLI (without the template's
# --dangerously-skip-permissions, so `permissions.ask` stays effective).
ENTRYPOINT ["tini", "--"]
CMD ["claude-entrypoint"]
