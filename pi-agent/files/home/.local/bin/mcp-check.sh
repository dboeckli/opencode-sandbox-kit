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
#   mcp-client:OK    the agent config declares the gateway (url = MCP_URL)
#   mcp-tools:OK     (deep) the agent's own MCP client reports the gateway CONNECTED;
#                    falls back to mcp-client when no supported CLI exists
# Any missing step -> that token is FAIL.
#
# mcp-client/mcp-tools close the blind spot from issue #139: the handshake above only
# proves that the gateway + upstream servers answer *from the sandbox*, not that the
# agent registered a client and loaded its tools. sbx injects the entry for supported
# agents (OpenCode, Claude); Mammouth/Vibe get it from their kit config. `mcp-client`
# is the cheap config check (also used by the 10s TUI box); `mcp-tools` additionally
# runs `<agent> mcp list`, which performs a real handshake through the agent's own
# client (startup report only — spawning an agent process every 10s is wasteful).
#
# Bounded timeouts, never hangs. `mcp-gateway.docker.internal` is not in NO_PROXY,
# so curl routes through the sandbox HTTP proxy (the only network egress) — do not
# disable the proxy. A *cold* agent CLI bootstraps its config-dir plugin dependencies
# on the first run (bun/npm install through the proxy; ~60s for mammouth, ~10s once
# warm), so the deep probe budgets the whole run instead of a short per-attempt kill.
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
# `client_clis` records the agent CLI(s) whose OWN config declares the gateway: the deep
# probe must only ask those. Another agent CLI that happens to be installed (e.g.
# `opencode` in the mammouth image) has no gateway config and would answer "No MCP
# servers configured" — a false failure if it were probed instead.
client_clis=""
for cfg in "$HOME/.config/opencode/opencode.json" "$HOME/.config/opencode/opencode.jsonc" \
           "$HOME/.config/mammouth/opencode.jsonc" "$HOME/.vibe/config.toml" \
           "$HOME/.pi/agent/mcp.json" "$HOME/.claude.json"; do
  [ -f "$cfg" ] || continue
  if grep -Eq 'url"?[[:space:]]*[:=][[:space:]]*"http://mcp-gateway\.docker\.internal/mcp' "$cfg" 2>/dev/null; then
    client="mcp-client:OK"
    rel="${cfg#"$HOME"/}"
    case "$rel" in
      .config/mammouth/*) cand="mammouth" ;;
      .config/opencode/*) cand="opencode" ;;
      .vibe/*)            cand="vibe" ;;
      .pi/*)              cand="pi" ;;
      .claude.json)       cand="claude" ;;
      *)                  cand="" ;;
    esac
    if [ -n "$cand" ]; then
      case " $client_clis " in
        *" $cand "*) ;;
        *) client_clis="$client_clis $cand" ;;
      esac
    fi
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

if [ "${MCP_CHECK_DEEP:-0}" = "1" ]; then
  # Deep probe: `<agent> mcp list` connects through the agent's own MCP client and
  # prints "mcp-gateway ... connected" on success (mammouth/opencode; claude uses a
  # similar line). No such CLI support (e.g. Mistral Vibe) -> fall back to the config
  # result. Only the CLI(s) whose config declares the gateway above are probed.
  #
  # A cold CLI bootstraps its plugin dependencies on first run (mammouth ~60s); a short
  # per-attempt timeout would kill that, and the old fallthrough then probed a different
  # installed CLI (opencode -> "No MCP servers configured") as a false failure. Budget
  # the whole probe and distinguish a timeout (transient, retry, definitive result) from
  # an unsupported `mcp list` subcommand (skip, fall back to the config check).
  tools="mcp-tools:FAIL"
  probed=0
  [ -z "$client_clis" ] && client_clis="pi mammouth opencode claude vibe"
  deep_deadline=$(( $(date +%s) + 180 ))
  for cli in $client_clis; do
    command -v "$cli" >/dev/null 2>&1 || continue
    attempt=1
    had_mcp_list=0
    last_rc=124
    while [ "$attempt" -le 3 ]; do
      remaining=$(( deep_deadline - $(date +%s) ))
      [ "$remaining" -lt 10 ] && break
      per_attempt=120
      [ "$remaining" -lt "$per_attempt" ] && per_attempt=$remaining
      mcp_list_out=$(timeout "$per_attempt" "$cli" mcp list 2>&1)
      last_rc=$?
      if [ "$last_rc" -eq 0 ]; then
        had_mcp_list=1
        if printf '%s\n' "$mcp_list_out" | grep -Eqi 'mcp-gateway.*connected|connected.*mcp-gateway'; then
          tools="mcp-tools:OK"
          break
        fi
      elif [ "$last_rc" -ne 124 ]; then
        # Non-zero and not a timeout -> the CLI has no `mcp list` subcommand (e.g.
        # Vibe): skip it and fall back to the config result, not a failure.
        break
      fi
      attempt=$((attempt + 1))
      [ "$attempt" -le 3 ] && sleep 3
    done
    if [ "$tools" = "mcp-tools:OK" ]; then
      probed=1
      break
    fi
    # A timed-out CLI (rc 124) or one that answered but never reported the gateway
    # connected is this image's configured agent: record the definitive result and
    # stop, so an unconfigured CLI cannot mask it.
    if [ "$had_mcp_list" = "1" ] || [ "$last_rc" -eq 124 ]; then
      probed=1
      # Diagnostics go to stderr (not part of the one-line report) so a failure in CI
      # shows what the agent client actually printed.
      printf 'mcp-tools diagnostic (%s): rc=%s %s\n' \
        "$cli" "$last_rc" "$(printf '%s' "$mcp_list_out" | tr '\n' ' ' | cut -c1-300)" >&2
      break
    fi
  done
  [ "$probed" = "0" ] && tools="mcp-tools:${client#mcp-client:}"
  echo "$gateway $idea $k8s $docker $client $tools"
else
  echo "$gateway $idea $k8s $docker $client"
fi
