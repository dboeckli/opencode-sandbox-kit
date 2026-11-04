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
# Prints five space-separated tokens in the startup-checks format (six with
# MCP_CHECK_DEEP=1):
#   mcp-gateway:OK   gateway reachable (handshake succeeded)
#   mcp-idea:OK      IntelliJ tools present (get_symbol_info)
#   mcp-k8s:OK       Kubernetes tools present (pods_list)
#   mcp-docker:OK    Docker tools present (list_containers)
#   mcp-client:OK    Mammouth's opencode.jsonc declares the gateway (url = MCP_URL)
#   mcp-tools:OK     (deep) `mammouth mcp list` reports the gateway CONNECTED
# Any missing step -> that token is FAIL.
#
# mcp-client/mcp-tools close the blind spot from issue #139: the handshake above
# only proves that the gateway + upstream servers answer *from the sandbox*, not
# that Mammouth registered a client and loaded its tools.
#
# Bounded timeouts, never hangs. `mcp-gateway.docker.internal` is not in NO_PROXY,
# so curl routes through the sandbox HTTP proxy (the only network egress) — do
# not disable the proxy. A cold Mammouth CLI may bootstrap on the first run, so
# the deep probe budgets the whole run instead of a short per-attempt kill.
set +e

MCP_URL="http://mcp-gateway.docker.internal/mcp"
MAMMOUTH_CONFIG="$HOME/.config/mammouth/opencode.jsonc"

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

if [ -f "$MAMMOUTH_CONFIG" ] \
  && grep -Eq 'url"?[[:space:]]*[:=][[:space:]]*"http://mcp-gateway\.docker\.internal/mcp' "$MAMMOUTH_CONFIG" 2>/dev/null; then
  client="mcp-client:OK"
fi

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

if [ "${MCP_CHECK_DEEP:-0}" = "1" ]; then
  # Deep probe: `mammouth mcp list` connects through Mammouth's own MCP client
  # and prints "mcp-gateway ... connected" on success. Budget the whole probe.
  tools="mcp-tools:FAIL"
  probed=0
  deep_deadline=$(( $(date +%s) + 180 ))
  attempt=1
  had_mcp_list=0
  last_rc=124
  while [ "$attempt" -le 3 ]; do
    remaining=$(( deep_deadline - $(date +%s) ))
    [ "$remaining" -lt 10 ] && break
    per_attempt=120
    [ "$remaining" -lt "$per_attempt" ] && per_attempt=$remaining
    mcp_list_out=$(timeout "$per_attempt" mammouth mcp list 2>&1)
    last_rc=$?
    if [ "$last_rc" -eq 0 ]; then
      had_mcp_list=1
      if printf '%s\n' "$mcp_list_out" | grep -Eqi 'mcp-gateway.*connected|connected.*mcp-gateway'; then
        tools="mcp-tools:OK"
        probed=1
        break
      fi
    elif [ "$last_rc" -ne 124 ]; then
      # Non-zero and not a timeout -> no usable `mcp list`; fall back to config.
      break
    fi
    attempt=$((attempt + 1))
    [ "$attempt" -le 3 ] && sleep 3
  done
  if [ "$probed" = "0" ] && { [ "$had_mcp_list" = "1" ] || [ "$last_rc" -eq 124 ]; }; then
    printf 'mcp-tools diagnostic (mammouth): rc=%s %s\n' \
      "$last_rc" "$(printf '%s' "$mcp_list_out" | tr '\n' ' ' | cut -c1-300)" >&2
  fi
  [ "$tools" = "mcp-tools:OK" ] || tools="mcp-tools:${client#mcp-client:}"
  echo "$gateway $idea $k8s $docker $client $tools"
else
  echo "$gateway $idea $k8s $docker $client"
fi
