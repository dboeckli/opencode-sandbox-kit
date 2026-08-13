# SessionStart-Hook / statusLine: Warum `managed-settings.json`?

## Problem

Das `claude-code-docker`-Template überschreibt `~/.claude/settings.json` beim Start jeder
Session — u.a. mit `apiKeyHelper`, `defaultMode: bypassPermissions` und einem Default-Modell
(Opus 5). Eigene Settings (Modell, MCP-Server, Permissions) müssen daher nach jedem
Template-Overwrite erneut angewendet werden.

## Race Condition

Für die meisten Kit-Felder reicht der `setup.startup`-Hook-Merge (Python, `settings.kit.json`
in `~/.claude/settings.json` mergen, siehe `spec.yaml:157-180`). **Hooks und `statusLine`
reichen damit nicht**: Der Merge ist asynchron zum Session-Start, die Hooks würden erst ab der
nächsten Session greifen bzw. teils gar nicht — unzuverlässig und nicht Template-sicher.

## Lösung

Hooks + `statusLine` gehören in die **`managed-settings.json`** unter `/etc/claude-code/`:

- Höchste Precedence — wird vom Template nicht überschrieben.
- Wird bei `setup.install` geschrieben (`spec.yaml:122-156`) und existiert bereits beim ersten
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
        "matcher": "mcp__idea__execute_run_configuration",
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

- `files/home/.claude/settings.json` und `settings.kit.json` tragen bewusst **keine**
  `hooks`/`statusLine` mehr — nur der Setup-Hook schreibt sie nach `/etc/claude-code/`.
- **SessionStart-Hook**: `~/.config/sandbox-kit/run-checks-hook.sh` — führt die
  Sandbox-Checks aus und übergibt den Report als System-Message.
- **PreToolUse-Guard**: `~/.config/sandbox-kit/intellij-run-config-guard.sh` — erlaubt
  `idea_execute_run_configuration` nur für `local-test-kits-validate-only`.
- **statusLine**: `bash ~/.claude/statusline.sh` — zeigt Modell, Kontext-Tokens, Kosten,
  geänderte Zeilen und Session-Dauer.

Damit wird doppeltes Feuern vermieden: Weil user-`settings.json` und `settings.kit.json`
keine `hooks`/`statusLine` enthalten, gibt es nur die eine Definition in
`managed-settings.json`.
