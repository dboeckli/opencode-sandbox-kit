#!/usr/bin/env bash
# Claude Code PreToolUse guard for the IntelliJ MCP tool `idea_execute_run_configuration`.
# permits only the whitelisted run configuration. Everything else is denied.
#
# The `permissions` allow/deny arrays cannot express per-argument constraints for
# MCP tools (they always match the whole tool), so the configurationName is only
# inspectable here, in the PreToolUse hook payload (`tool_input.configurationName`).
set -uo pipefail

input=$(cat 2>/dev/null || true)
tool_name=$(printf '%s' "$input" | jq -r '.tool_name // empty' 2>/dev/null)

if [ "$tool_name" != "mcp__idea__execute_run_configuration" ]; then
  # Not the guarded tool: let the normal permission flow decide (exit code 0 = pass).
  exit 0
fi

config=$(printf '%s' "$input" | jq -r '.tool_input.configurationName // empty' 2>/dev/null)

if [ "$config" = "local-test-kits-validate-only" ]; then
  # Allowed: exit 0 (pass) lets Claude Code's configured permission rule (ask) apply.
  exit 0
fi

# Deny: print the decision JSON to stderr and exit 2 (block).
{
  printf '{"hookSpecificOutput": {"permissionDecision": "deny"}, '
  printf '"systemMessage": "Run configuration %s is not allowed. Allowed: local-test-kits-validate-only"}' \
    "$(printf '%s' "$config" | jq -Rsa . 2>/dev/null)"
} >&2
exit 2