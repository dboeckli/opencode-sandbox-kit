# Fix: SessionStart Hook — vollständige Diagnose und Fixes

## Symptome

| Umgebung | statusLine | Startup-Checks |
|----------|-----------|---------------|
| Ubuntu-WSL | ✅ angezeigt | ❌ nicht ausgeführt |
| PowerShell (Windows) | ❌ nicht angezeigt | ❌ nicht ausgeführt |

---

## Problem 1 — Race Condition (betrifft PowerShell: beides kaputt)

**Ursache:** `setup.startup` (der settings.json-Merge) wird **80ms nach** dem Claude-Code-Start
abgeschlossen. Claude Code liest `settings.json` beim Start — bevor das Merge fertig ist.
Ergebnis: kein `statusLine`, keine Hooks konfiguriert.

```
Session start (session file written): 2026-08-08T08:24:00.171
settings.json merge write:            2026-08-08T08:24:00.251
                                                         ↑ 80ms zu spät
```

In Ubuntu-WSL ist der Start langsamer (WSL-Overhead), das Merge gewinnt das Rennen.
In PowerShell (nativer Windows-Docker) startet Claude Code schneller → Race Condition.

**Fix 1a — setup.startup auf Python umstellen** (`spec.yaml`):

`jq` braucht ~80ms Prozess-Startup. Python inline ist deutlich schneller:

```yaml
startup:
  - command:
      - python3
      - -c
      - |
        import json, os
        sf = os.path.expanduser('~/.claude/settings.json')
        kf = os.path.expanduser('~/.claude/settings.kit.json')
        if not (os.path.exists(sf) and os.path.exists(kf)):
            exit(0)
        with open(sf) as f: base = json.load(f)
        with open(kf) as f: kit = json.load(f)
        def merge(b, o):
            r = dict(b)
            for k, v in o.items():
                if k in r and isinstance(r[k], dict) and isinstance(v, dict):
                    r[k] = merge(r[k], v)
                else:
                    r[k] = v
            return r
        with open(sf, 'w') as f:
            json.dump(merge(base, kit), f, indent=2)
    user: "1000"
```

Zusätzlicher Vorteil: korrekte Array-Behandlung (Overlay gewinnt für Arrays statt
`null` wie bei `jq -s '.[0] * .[1]'`).

**Fix 1b — settings.json vorausfüllen** (`files/home/.claude/settings.json`):

Template-Felder bereits in der deployed `settings.json` vorausfüllen, damit Claude Code
die vollständigen Settings liest — auch wenn das Merge noch nicht fertig ist:

```json
{
  "apiKeyHelper": "echo proxy-managed",
  "alwaysThinkingEnabled": true,
  "themeId": 1,
  "defaultMode": "bypassPermissions",
  "bypassPermissionsModeAccepted": true,
  "skipDangerousModePermissionPrompt": true,
  "model": "claude-sonnet-4-6",
  "statusLine": { ... },
  ...
}
```

Wenn das Template `settings.json` zusammenführt (additiv), überleben die Kit-Felder.
Wenn das Template überschreibt, stellt `setup.startup` sie wieder her (Safety-Net).

---

## Problem 2 — Falsches Hook-Output-Format (betrifft Ubuntu: Checks nicht angezeigt)

**Ursache:** Das committete Skript gab noch `systemMessage` aus — dieses Feld wird
von Claude Code bei `SessionStart` nicht als Kontext injiziert:

```bash
# vorher (committed HEAD, falsch):
printf '{"continue": true, "suppressOutput": false, "systemMessage": %s}\n' "$escaped"
```

Das korrekte Format für `SessionStart`-Hooks laut Claude Code Doku ist
`hookSpecificOutput.additionalContext`:

```bash
# nachher (Fix):
printf '{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": %s}}\n' "$escaped"
```

**Fix 2** — bereits im Working Tree, wird mit diesem Commit übernommen.

---

## Problem 3 — jq-Array-Merge-Bug (latentes Problem)

`jq -s '.[0] * .[1]'` multipliziert Arrays anstatt sie zu überschreiben. Falls das
Template jemals `hooks`-Keys in `settings.json` schreibt, werden die Hook-Arrays zu `null`.

Der Python-Merge (Fix 1a) löst dieses Problem: Nicht-Dict-Werte (inkl. Arrays) werden
durch den Overlay-Wert ersetzt.

---

## Quelle

Claude Code Hook-Dokumentation (via Context7 `/anthropics/claude-code`):
- `SessionStart`-Hooks verwenden `hookSpecificOutput.additionalContext`
- Race-Condition-Diagnose: Session-Timestamp vs. `settings.json`-mtime (80ms Diff)

---

## Fix 4 — Robuste Lösung: managed-settings.json (Stand 2026-08-08)

**Ursache des verbleibenden Problems:** Fix 1a/1b adressieren die Race nur oberflächlich.
Claude Code liest `~/.claude/settings.json` **beim Start**; der Kit-`setup.startup`-Merge (Python oder jq)
läuft **parallel zum Entrypoint** — selbst ein schneller Merge kommt zu spät. Wird die user-`settings.json`
vom Template **überschrieben** statt gemergt, sind `hooks`/`statusLine` beim Start gar nicht registriert.

**Fix:** Hooks + statusLine in **`managed-settings.json`** unter **`/etc/claude-code/`** verlagern:

- Höchste Precedence im Settings-Hierarchy (managed > user > project > project-local)
- Liegt **außerhalb** von `~/.claude` → das Template überschreibt sie **nicht**
- `setup.install` schreibt sie einmalig beim Sandbox-Creation (vor jedem Claude-Code-Start)
- `SessionStart`-Hook (`run-checks-hook.sh`) + `PreToolUse`-Hook (Run-Config-Guard) + `statusLine`
  sind damit beim Session-Start **garantiert** vorhanden

Umgesetzt:
- `spec.yaml` → `setup.install`: schreibt `/etc/claude-code/managed-settings.json`
  (statusLine + PreToolUse-Guard + SessionStart-Checks)
- `files/home/.claude/settings.json` + `settings.kit.json`: **enthalten keine** `hooks`/`statusLine` mehr
  (sonst doppeltes Hook-Feuern); behalten `model`, `mcpServers`, `permissions`

> **Hinweis:** `managed-settings.json` ist enterprise-enforced — Settings dort lassen sich von der
> user-`settings.json` nicht überschreiben. `allowManagedHooksOnly` bewusst **nicht** gesetzt (Default:
> false), damit weiterhin User-/Plugin-Hooks laufen.
