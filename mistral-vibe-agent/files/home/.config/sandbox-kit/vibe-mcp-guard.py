#!/usr/bin/env python3
"""Vibe pre_tool guard for the IntelliJ MCP tools delivered via the sbx MCP gateway.

Deny-by-default: only the read-only IntelliJ MCP tools used by the kit are
allowed (mirrors the OpenCode/Mammouth permission whitelist). The gateway
meta-tools (`mcp-gateway_code-mode`, `mcp-gateway_mcp-exec`, `mcp-gateway_mcp-find`,
`mcp-gateway_mcp-add`, `mcp-gateway_mcp-config-set`) and every write/execute tool
are denied.

`mcp-gateway_execute_run_configuration` is allowed only for the
`local-test-kits-validate-only` run configuration (same restriction as the
OpenCode plugin / Claude PreToolUse hook in the mixin kit).

Runs as a Vibe pre_tool hook (see ~/.vibe/hooks.toml): reads the JSON invocation
on stdin and prints a deny decision as JSON on stdout (nothing = pass through).
"""

import fnmatch
import json
import sys

PREFIX = "mcp-gateway_"

# Read-only IntelliJ MCP tools (tool name after the `mcp-gateway_` prefix).
ALLOW = (
    "get_*",
    "list_*",
    "search_*",
    "read*",
    "generate_*",
    "xdebug_get_*",
    "xdebug_list_*",
    "analyze_calls",
    "git_status",
    "lint_files",
    "fetch_query_result",
    "preview_table_data",
    "test_database_connection",
    "introspect_schema",
    "run_inspection_kts",
    "validate_inspection_kts",
    "build_project",
    "open_file_in_editor",
)

RUN_CONFIG_TOOL = PREFIX + "execute_run_configuration"
RUN_CONFIG_ALLOWED = "local-test-kits-validate-only"


def _is_allowed(tool):
    if not tool.startswith(PREFIX):
        return True
    name = tool[len(PREFIX):]
    if name == "execute_run_configuration":
        return False  # checked separately against the configuration name
    return any(fnmatch.fnmatchcase(name, pattern) for pattern in ALLOW)


def _deny(reason):
    json.dump({"decision": "deny", "reason": reason}, sys.stdout)
    sys.stdout.write("\n")


def main():
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0

    tool = payload.get("tool_name") or ""
    if _is_allowed(tool):
        return 0

    if tool == RUN_CONFIG_TOOL:
        config = (payload.get("tool_input") or {}).get("configurationName")
        if config == RUN_CONFIG_ALLOWED:
            return 0
        _deny(
            "IntelliJ run configuration %r is not allowed; only %r may be executed."
            % (config, RUN_CONFIG_ALLOWED)
        )
        return 0

    _deny(
        "IntelliJ MCP tool %r is not on the read-only allow-list "
        "(write/execute tools and gateway meta-tools are blocked)." % tool
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
