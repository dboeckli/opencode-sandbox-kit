# syntax=docker/dockerfile:1
#
# Standalone Claude Code v3 workload (issue #242; base migrated to the Docker-provided
# shell image in issue #254). This image bakes the kit tooling + the Claude config,
# managed settings and guards on top of Docker's official `shell-docker-image`; the
# Claude Code CLI itself is installed from npm (`@anthropic-ai/claude-code`, pinned via
# ARG CLAUDE_VERSION). The base already ships Node/npm, Python, Go, uv, tini and the
# Docker CLI + compose + buildx — those are NOT re-installed (versions verified below).
#
# Build/publish (descriptor is the Dockerfile frontend):
#   docker buildx build ./claude-v3-agent -f ./claude-v3-agent/claude-v3-agent.yaml \
#     -t <IMAGE_PREFIX>/sbx-claude:<tag> --push
#
# Local build:
#   docker buildx build ./claude-v3-agent -f ./claude-v3-agent/claude-v3-agent.yaml \
#     -t <IMAGE_PREFIX>/sbx-claude:local --load
#
# ARG BASE_IMAGE is Docker's official custom-workload base (`:latest`, nightly, Issue #254).
# ARG CLAUDE_VERSION is the Claude Code CLI pin (npm `@anthropic-ai/claude-code`, Renovate).

ARG BASE_IMAGE=docker.io/sbx/shell-docker-image:latest@sha256:160a9e3f5cd4bafb39bb9db3a839cb5a468a5a3eff394d8c90fbc1f2635abd00
FROM ${BASE_IMAGE}

ARG CLAUDE_VERSION=2.1.322

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

# Root-level tooling. The base already provides Node/npm, Docker CLI + compose +
# buildx, Python, Go, uv and tini — those are not re-installed. The JDK is installed
# as Liberica (install-tooling.sh jdk) so all kits share the same vendor/build at
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
    fi \
 && java -version \
 && [ "$(readlink -f "$(command -v java)")" = "/usr/local/java/bin/java" ] \
 && javac -version \
 && [ "$(readlink -f "$(command -v javac)")" = "/usr/local/java/bin/javac" ] \
 && jar --version \
 && [ "$(readlink -f "$(command -v jar)")" = "/usr/local/java/bin/jar" ] \
 && shfmt --version

# npm-global CLIs (NPM_CONFIG_PREFIX inherited from the shell base). The Claude Code CLI
# is installed here too (postinstall copies the platform-native binary over the wrapper).
# Retry: the npm registry occasionally serves metadata for a just-published dependency
# before all its versions resolve (transient ETARGET).
RUN set -e; \
    for attempt in 1 2 3; do \
      if npm_config_bin_links=true npm install -g ctx7 skills prettier renovate @usebruno/cli@4.3.0 \
           @modelcontextprotocol/inspector@2.14.0 "@anthropic-ai/claude-code@${CLAUDE_VERSION}"; then \
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
    command -v mcp-inspector; \
    command -v claude; \
    runuser -u agent -- env HOME=/home/agent claude --version; \
    runuser -u agent -- env HOME=/home/agent claude --version | grep -F "${CLAUDE_VERSION}"

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

# tini comes from the base image. The wrapper merges the kit config, then execs the
# Claude Code CLI (no --dangerously-skip-permissions, so `permissions.ask` stays effective).
ENTRYPOINT ["tini", "--"]
CMD ["claude-entrypoint"]
