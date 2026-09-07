# IntelliJ MCP Server: dynamischer Port (IDEA 2026.2.x)

**Stand:** 2026-09-07 · Recherche-Quelle: JetBrains YouTrack + JetBrains-Help-Doku
(`https://www.jetbrains.com/help/idea/mcp-server.html`) + JetBrains Marketplace
(`/plugin/26071-mcp-server`, xmlId `com.intellij.mcpServer`).

## Problem / Beobachtung

Nach dem Update auf **IntelliJ IDEA 2026.2.2** lauscht der MCP-Server nicht mehr auf dem
bisherigen Port `64342`, sondern auf einem anderen Port (beobachtet: `64615`, zusätzlich
`64616`). Ein Neustart von IDEA oder des Rechners kann den Port erneut ändern — damit geht
die MCP-Verbindung (Gateway-Registrierung + Sandbox-Allowlist + Health-Check sind auf einen
festen Port verdrahtet) jeweils verloren.

## Offizielle Bestätigung (YouTrack)

**IJPL-248682** — „External MCP clients fail to connect to SSE endpoint (localhost:64342/sse)
after updating WebStorm 2024.3.5 → 2026.1.3" (identisches Szenario). Antwort JetBrains-Support
(petar.milunovic):

> „The MCP server is disabled by default and **selects its port dynamically**. After an update,
> it may end up disabled or bound to a different port than `64342`."

→ Der Port ist also **dynamisch**; die IDE zeigt den aktuellen Port in
**Settings → Tools → MCP Server** (Client-Config „Copy Config"). Er ist nirgends offiziell
dokumentiert (Help-Doku und Plugin-Changelog nennen keinen Port).

## Relevante YouTrack-Issues

| Issue | Status | Bedeutung |
|-------|--------|-----------|
| **IJPL-207839** | Open (Feature) | **„Configurable MCP Server Port Per Project"** — würde unser Problem dauerhaft lösen (fester/konfigurierbarer Port). **Beobachten!** |
| IJPL-242883 | Fixed (2026.2) | „Allow overriding MCP server availability and port via system property for eval purposes" — Override-Property existiert, Name aber nicht öffentlich dokumentiert |
| IJPL-204081 | Open | „MCP Server: two IDE instances cannot expose MCP port" (Port-Kollision) |
| IJPL-232015 | Open | „MCP Server: enabling from Settings doesn't persist resolved port" |
| IJPL-242651 | Open | Hinweis auf dynamische Ports; mcp-proxy scannt einen Standardbereich |

## Konsequenz für das Kit

- Der Port darf **nicht als feste Konstante** behandelt werden. Aktuell unterstützt das Kit
  `64342` (Legacy) und `64615` (IDEA 2026.2.2) in Allowlist und Health-Check — das ist ein
  pragmatischer Zwischenstand, aber **keine Dauerlösung**.
- **Nach jedem Neustart von IDEA / Rechner:** Port in *Settings → Tools → MCP Server* ablesen
  und ggf. anpassen:
  1. Host-Registrierung: `sbx mcp rm idea` + `sbx mcp add idea --url http://localhost:<port>/stream --skip-ssrf-check`
  2. Sandbox-Allowlist: neuen Port ergänzen (Spec + Sandbox neu erzeugen bzw. `sbx`-Freigabe)
  3. Health-Check: erwartet wieder `intellij-mcp:OK`
- Sobald **IJPL-207839** (konfigurierbarer Port) verfügbar ist: festen Port setzen → Kit kann
  dauerhaft darauf zeigen; die dynamische-Port-Arbeit entfällt.

## Symptome (Erkennung)

- Startup-Check meldet `intellij-mcp:FAIL`.
- Sandbox-Probe auf den alten Port liefert `HTTP 500` (Gateway-Dial → *connection refused*),
  auf einen neuen, nicht-allowlisteten Port `HTTP 403`.
- Auf dem Host ist der Listener aber vorhanden: `Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -ge 64000 }`
