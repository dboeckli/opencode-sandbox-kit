#!/usr/bin/env bash
# MCP servers + host systems reachability for the TUI sidebar "MCP & Host Systems" box.
# Report in startup-checks token format (name:OK | name:FAIL): line 1 = MCP servers
# (space-separated), then one host system per line. The TUI splits all tokens on
# whitespace and renders each on its own line (vertically stacked).
# Bounded timeouts so the check never hangs; set +e so one failure never aborts.
set +e

# MCP servers reachable via the sbx MCP gateway (IntelliJ MCP, Kubernetes MCP).
# The sandbox holds no kubeconfig (host-side Kubernetes MCP server, issue #40);
# the helper runs one MCP handshake and reports mcp-gateway/mcp-idea/mcp-k8s.
mcp=$(bash "$HOME/.local/bin/mcp-check.sh")

# Host systems (external): Docker Desktop daemon reachable (optional;
# DOCKER_HOST=tcp://host.docker.internal:2375)?
if timeout 5 docker -H tcp://host.docker.internal:2375 info >/dev/null 2>&1; then
  docker_host="docker-host:OK"
else
  docker_host="docker-host:FAIL"
fi

# Output contract: line 1 = MCP servers (space-separated), one host system per
# following line (the TUI renders each whitespace-separated token on its own line).
printf '%s\n%s\n' "$mcp" "$docker_host"
