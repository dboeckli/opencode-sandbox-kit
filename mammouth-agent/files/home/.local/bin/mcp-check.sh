#!/usr/bin/env bash
# MCP server reachability for the sandbox sidebar box "MCP & Host Systems".
#
# The sandbox reaches all MCP servers through the sbx MCP gateway
# (mcp-gateway.docker.internal): the host-side IntelliJ MCP server, the
# Kubernetes MCP server (containers/kubernetes-mcp-server, issue #40) and — when
# registered via `--static-mcp idea,k8s,docker` — the local Docker MCP server
# (mcp-server-docker, issue #165). A single MCP handshake
# (initialize -> notifications/initialized -> tools/list) reveals which servers
# are registered and reachable.
#
# Prints five space-separated tokens in the startup-checks format:
#   mcp-gateway:OK   gateway reachable (handshake succeeded)
#   mcp-idea:OK      IntelliJ tools present (get_symbol_info)
#   mcp-k8s:OK       Kubernetes tools present (pods_list)
#   mcp-docker:OK    Docker tools present (list_containers)
#   mcp-client:OK    the agent config declares the gateway (url = MCP_URL)
# Any missing step -> that token is FAIL.
#
# mcp-client closes the blind spot from issue #139: the handshake above only proves
# that the gateway + upstream servers answer *from the sandbox*, not that the agent
# registered a client. sbx injects the entry for supported agents (OpenCode, Claude);
# Mammouth/Vibe get it from their kit config. Without it, no mcp-gateway_* tools
# reach the agent even though every probe here is OK.
#
# Bounded timeouts, never hangs. `mcp-gateway.docker.internal` is not in NO_PROXY,
# so curl routes through the sandbox HTTP proxy (the only network egress) — do not
# disable the proxy.
set +e

MCP_URL="http://mcp-gateway.docker.internal/mcp"

mcp_hdr=$(mktemp)
curl -s -D "$mcp_hdr" -m 3 -o /dev/null -X POST "$MCP_URL" \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -H 'Authorization: Bearer proxy-managed' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"sandbox-kit-check","version":"1"}}}' 2>/dev/null
mcp_sid=$(awk 'tolower($1)=="mcp-session-id:"{print $2}' "$mcp_hdr" 2>/dev/null | tr -d '\r')
rm -f "$mcp_hdr"

gateway="mcp-gateway:FAIL"
idea="mcp-idea:FAIL"
k8s="mcp-k8s:FAIL"
docker="mcp-docker:FAIL"
client="mcp-client:FAIL"

# Agent-side wiring: does any agent config declare the gateway URL? JSON agents store
# "url": "http://…", Vibe's TOML stores url = "http://…". Dependency-free (grep, no jq).
for cfg in "$HOME/.config/opencode/opencode.json" "$HOME/.config/opencode/opencode.jsonc" \
           "$HOME/.config/mammouth/opencode.jsonc" "$HOME/.vibe/config.toml" "$HOME/.claude.json"; do
  [ -f "$cfg" ] || continue
  if grep -Eq 'url"?[[:space:]]*[:=][[:space:]]*"http://mcp-gateway\.docker\.internal/mcp' "$cfg" 2>/dev/null; then
    client="mcp-client:OK"
    break
  fi
done

if [ -n "$mcp_sid" ]; then
  gateway="mcp-gateway:OK"
  curl -s -m 3 -o /dev/null -X POST "$MCP_URL" \
    -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
    -H 'Authorization: Bearer proxy-managed' -H "mcp-session-id: $mcp_sid" \
    -d '{"jsonrpc":"2.0","method":"notifications/initialized"}' 2>/dev/null
  mcp_tools=$(curl -s -m 3 -X POST "$MCP_URL" \
    -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
    -H 'Authorization: Bearer proxy-managed' -H "mcp-session-id: $mcp_sid" \
    -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' 2>/dev/null)
  curl -s -m 2 -o /dev/null -X DELETE "$MCP_URL" -H "mcp-session-id: $mcp_sid" 2>/dev/null
  case "$mcp_tools" in
    *'"name":"get_symbol_info"'*) idea="mcp-idea:OK" ;;
  esac
  case "$mcp_tools" in
    *'"name":"pods_list"'*) k8s="mcp-k8s:OK" ;;
  esac
  case "$mcp_tools" in
    *'"name":"list_containers"'*) docker="mcp-docker:OK" ;;
  esac
fi

echo "$gateway $idea $k8s $docker $client"
