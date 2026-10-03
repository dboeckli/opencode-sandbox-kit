#!/usr/bin/env bash
# MCP servers reachability for the TUI sidebar "MCP & Host Systems" box.
# Report in startup-checks token format (name:OK | name:FAIL): MCP servers,
# space-separated. The TUI splits all tokens on whitespace and renders each on
# its own line (vertically stacked).
# Bounded timeouts so the check never hangs; set +e so one failure never aborts.
set +e

# MCP servers reachable via the sbx MCP gateway (IntelliJ MCP, Kubernetes MCP,
# Docker MCP). The sandbox holds no kubeconfig (host-side Kubernetes MCP server,
# issue #40) and no host-Docker port (local Docker MCP server, issue #165); the
# helper runs one MCP handshake and reports
# mcp-gateway/mcp-idea/mcp-k8s/mcp-docker.
printf '%s\n' "$(bash "$HOME/.local/bin/mcp-check.sh")"
