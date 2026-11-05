#!/usr/bin/env python3
"""Ensure the Claude Code config is complete before the CLI starts.

The base template overwrites ``~/.claude/settings.json`` at session start; a
lifecycle startup hook would run after the agent has already read it. This
script is invoked by ``claude-entrypoint`` *before* ``claude`` starts and:

* registers the sbx MCP gateway in ``~/.claude.json`` (idempotent; other MCP
  servers and existing state are preserved), and
* re-applies the kit defaults from ``~/.claude/settings.kit.json`` on top of
  the (possibly template-reset) ``~/.claude/settings.json``.

Defaulted values from ``settings.kit.json`` are merged in; arrays are replaced
(so the kit's permission lists win). Missing/unreadable files are ignored.
"""

import json
import os
import tempfile

HOME = os.path.expanduser("~")
CLAUDE_JSON = os.path.join(HOME, ".claude.json")
SETTINGS = os.path.join(HOME, ".claude", "settings.json")
SETTINGS_KIT = os.path.join(HOME, ".claude", "settings.kit.json")

GATEWAY = {
    "type": "http",
    "url": "http://mcp-gateway.docker.internal/mcp",
    "headers": {"Authorization": "Bearer proxy-managed"},
}


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def write(path, data):
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def merge(base, override):
    result = dict(base)
    for key, value in override.items():
        if isinstance(result.get(key), dict) and isinstance(value, dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = value
    return result


def main():
    claude = load(CLAUDE_JSON)
    servers = claude.get("mcpServers")
    if not isinstance(servers, dict):
        servers = {}
    servers["mcp-gateway"] = GATEWAY
    claude["mcpServers"] = servers
    claude.setdefault("hasCompletedOnboarding", True)
    write(CLAUDE_JSON, claude)

    kit = load(SETTINGS_KIT)
    if kit:
        write(SETTINGS, merge(load(SETTINGS), kit))


if __name__ == "__main__":
    main()
