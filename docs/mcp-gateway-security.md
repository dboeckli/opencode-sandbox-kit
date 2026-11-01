# MCP-Gateway: Trust-Boundary und lokale Mitigationen

**Stand:** 2026-11-01 · Issues: [#163](https://codeberg.org/dboeckli/opencode-sandbox-kit/issues/163),
[#229](https://codeberg.org/dboeckli/opencode-sandbox-kit/issues/229) ·
Upstream: [docker/sbx-releases#585](https://github.com/docker/sbx-releases/issues/585)

## Kernaussage

Der sbx MCP-Gateway (`mcp-gateway.docker.internal/mcp`) ist der **einzige** Weg der Sandbox zu den
Host-MCP-Servern (IntelliJ, Kubernetes, Docker). Er ist aber **keine Sandbox-Grenze**:

- Die `mcp-gateway_*`-Permission-Whitelist und der Run-Config-Guard werden **agent-seitig** erzwungen
  (OpenCode/Mammouth `permission`, Claude `permissions` + PreToolUse-Hook, Vibe `pre_tool`-Hook).
- Der Gateway akzeptiert den Sentinel `Authorization: Bearer proxy-managed` von **jedem** Sandbox-Prozess
  und führt die Tools **aller** registrierten Server aus — auch `ask`/`deny`-Tools.
- Ein bash-fähiger Agent (oder prompt-injected Code) kann die Whitelist daher per `curl` **oder**
  `mcp-inspector --cli` (im Kit enthalten, Issue [#231](https://codeberg.org/dboeckli/opencode-sandbox-kit/issues/231))
  umgehen.

Die Whitelist ist eine **Agent-Guardrail** (Schutz vor Fehlbedienung/Fehlentscheidungen des Agenten),
keine Sicherheitsgrenze gegen beliebigen Code in der Sandbox.

## Zwei Pfade (und was #163 geschlossen hat)

```
#163 (direkter Pfad, geschlossen):
  Sandbox-Prozess ──curl──▶ host.docker.internal:64615 ──▶ IntelliJ
  (nur erreichbar, weil 64615/64342 in permissions.network.allow standen)

Vorgesehener Pfad (offen, kein lokales Policy-Enforcement):
  Agent/Gastprozess ──MCP──▶ mcp-gateway.docker.internal/mcp
                              └─ host-seitig ─▶ IntelliJ / K8s / Docker
```

Nachweis (lokale Sandbox): `initialize` + `tools/list` → 112 Tools inkl. `execute_terminal_command`,
`pods_exec`, `resources_delete`, `helm_install`, `run_container`, `build_image`; `tools/call`
`pods_list` liefert echte Cluster-Daten.

## Was Docker bereits kann (aber lokal nicht aktiviert)

Docker beschreibt **MCP-Policies** (Cedar), die host-seitig im Gateway **vor** der Tool-Ausführung
durchgesetzt werden:

| Aktion | Steuert |
|--------|---------|
| `register` | `sbx mcp add` (Server-Registrierung) |
| `invokeTool` | Tool-Aufrufe |
| `invokePrimordial` | Gateway-Meta-Tools (`mcp-exec`, `code-mode`, `mcp-add`, OAuth-Helper) |
| `readResource` / `getPrompt` | Resource-Reads / Prompts |

Default-deny, `forbid` schlägt `permit`. **Aber:** MCP-Policies sind Teil der
**Organization-Governance** (separates, kostenpflichtiges Abo). Ist keine Org-Policy aktiv, wertet der
Gateway Cedar **nicht** aus und erlaubt MCP-Aktivität. Laut Doku gibt es *kein* lokales Preset-Äquivalent
zu Netzwerk-Policy. Siehe Upstream [#585](https://github.com/docker/sbx-releases/issues/585).

## Lokale Mitigationen (was dieses Kit empfiehlt)

Die folgenden Maßnahmen reduzieren den Blast-Radius, solange es kein lokales Gateway-Policy-Enforcement gibt:

1. **Minimal laden:** `--static-mcp` nur mit den tatsächlich benötigten Servern. Für fremde/untrusted
   Prompts insbesondere **kein** Docker-MCP laden.
2. **Kubernetes-MCP einschränken:** `read_only = true` und Toolsets auf `core,config` reduzieren, wenn
   keine Schreib-/Helm-Operationen gebraucht werden. Für Produktions-Cluster `denied_resources` für
   `Secret` aktivieren (Helm-Tools entfallen dann) — siehe
   [kubernetes-mcp-server.md](kubernetes-mcp-server.md#sicherheit-kurz).
3. **Docker-MCP nur auf Dev-Hosts:** Der Server ist host-root-äquivalent (`container run -v /:/host`).
   Nur registrieren, wenn Host-Docker-Zugriff wirklich nötig ist — siehe
   [docker-mcp-server.md](docker-mcp-server.md).
4. **Prompt-Injection als Code behandeln:** Sobald ein Agent Shell + Netzwerk hat, sind gehostete
   MCP-Server erreichbar. Untrusted Inhalte (Web, Issues, Logs, Repos) nicht mit privilegierten
   MCP-Servern kombinieren.
5. **Audit nutzen:** `sbx policy log <sandbox>`; Upstream
   [#424](https://github.com/docker/sbx-releases/issues/424) (Policy-Audit-Stream) und
   [#733](https://github.com/docker/sbx-releases/issues/733) (Security-Posture-Inspection) beobachten.

## Upstream-Status

- [docker/sbx-releases#585](https://github.com/docker/sbx-releases/issues/585) — „Supported local way to
  disable host MCP access while retaining agent OAuth": fordert eine lokale, host-seitige Restriktion, die
  auch für **ordinary guest processes** gilt (nicht nur für die Agent-Tool-Liste). Offen, keine
  Maintainer-Antwort.
- [#612](https://github.com/docker/sbx-releases/issues/612) — MCP-Connectoren default aktiv.
- Gewünschte Weiterentwicklung: lokales MCP-Policy-Preset (`sbx policy allow|deny mcp …`), local
  default-deny am Gateway, Tool-Whitelist bei der Registrierung (`--tools`), host-seitig und
  unabhängig von der Agent-Config wirksam.

## Verwandte Kit-Issues

- [#163](https://codeberg.org/dboeckli/opencode-sandbox-kit/issues/163) — direkter IntelliJ-Host-Port
  (geschlossen: Allowlist-Einträge entfernt).
- [#229](https://codeberg.org/dboeckli/opencode-sandbox-kit/issues/229) — Gateway selbst per `curl`
  erreichbar (dieses Dokument).
- [#231](https://codeberg.org/dboeckli/opencode-sandbox-kit/issues/231) — MCP-Inspector-CLI im Kit:
  zweiter direkter JSON-RPC-Client am Gateway (gleiche Restrisiko-Klasse wie `curl`).
