<!-- sandbox-kit: hard rules (always loaded) -->

## Harte Regeln (immer befolgen)

1. **Diff-Review:** Nach Änderungen **nur** `target/review/changes.patch` erzeugen (`mkdir -p target/review && git diff <base> > target/review/changes.patch`) und diese Datei in IntelliJ öffnen (`mcp-gateway_open_file_in_editor`) — keine Einzeldateien öffnen.
2. **Feature Branch:** Vor jeder Änderung einen Branch `feature/<kurzer-text>` anlegen (mit Issue: `feature/<nummer>-<max-4-wörter>`); nie direkt auf `master`/`main` committen oder pushen.
3. **Kein Auto-Commit/-Push:** `git commit`, `git push` und PR-Erstellung nur nach expliziter Zustimmung des Users; vor einem Push den Diff freigeben lassen.

Vollständige Sandbox-/Kit-Regeln (Umgebung, Netzwerk-Policy, MCP-Whitelist, Auth, Tooling) stehen in `/usr/share/sandbox/kit/mistral-vibe-agent/context.md` — bei nichttrivialen Aufgaben vorher lesen.

## IntelliJ MCP: Projektpfad

`projectPath`/Projektparameter immer im **Windows-Format** übergeben (`C:/development/projects/<projekt>`) — Linux-Pfade (`/c/development/...`) lehnt der IntelliJ MCP ab. Der Fehlertext nennt die offenen Projekte; von dort übernehmen.
