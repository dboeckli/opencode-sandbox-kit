# SessionStart-Hook / statusLine: Warum `managed-settings.json`?

## Problem

Das `claude-code-docker`-Template überschreibt `~/.claude/settings.json` beim Start jeder
Session — u.a. mit `apiKeyHelper`, `defaultMode: bypassPermissions` und einem Default-Modell
(Opus 5). Eigene Settings (Modell, MCP-Server, Permissions) müssen daher nach jedem
Template-Overwrite erneut angewendet werden. Der Merge setzt u.a. `defaultMode: default` — das Kit
nutzt nicht mehr `bypassPermissions`, damit `permissions.ask` (K8s-Schreib-/Exec-Tools) greift.

## Race Condition

Für die meisten Kit-Felder reicht der Settings-Merge (`settings.kit.json`
in `~/.claude/settings.json` mergen; im claude-v3-Agent-Kit macht das der `claude-entrypoint`
**vor** dem CLI-Start, im v2-Mixin war es ein `setup.startup`-Hook). **Hooks und `statusLine`
reichen damit nicht**: Der Merge ist asynchron zum Session-Start, die Hooks würden erst ab der
nächsten Session greifen bzw. teils gar nicht — unzuverlässig und nicht Template-sicher.

## Lösung

Hooks + `statusLine` gehören in die **`managed-settings.json`** unter `/etc/claude-code/`:

- Höchste Precedence — wird vom Template nicht überschrieben.
- Wird beim Image-Build geschrieben (`write-managed-settings.sh` im claude-v3-Agent-Kit) und existiert bereits beim ersten
  Session-Start, bevor der Template-Overwrite stattfinden kann.

```json
{
  "statusLine": {
    "type": "command",
    "command": "bash ~/.claude/statusline.sh"
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__mcp-gateway__execute_run_configuration",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.config/sandbox-kit/intellij-run-config-guard.sh"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.config/sandbox-kit/run-checks-hook.sh"
          }
        ]
      }
    ]
  }
}
```

## Konsequenzen

- `claude-v3-agent/files/home/.claude/settings.json` und `settings.kit.json` tragen bewusst **keine**
  `hooks`/`statusLine` mehr — sie liegen ausschließlich in der `/etc/claude-code/managed-settings.json`.
- **SessionStart-Hook**: `~/.config/sandbox-kit/run-checks-hook.sh` — führt die
  Sandbox-Checks aus und übergibt den Report als System-Message.
- **PreToolUse-Guard**: `~/.config/sandbox-kit/intellij-run-config-guard.sh` — erlaubt
  `mcp__mcp-gateway__execute_run_configuration` nur für `local-test-kits-validate-only`.
- **statusLine**: `bash ~/.claude/statusline.sh` — zeigt Modell, Kontext-Tokens, Kosten,
  geänderte Zeilen und Session-Dauer.

Damit wird doppeltes Feuern vermieden: Weil user-`settings.json` und `settings.kit.json`
keine `hooks`/`statusLine` enthalten, gibt es nur die eine Definition in
`managed-settings.json`.
