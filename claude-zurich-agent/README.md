# claude-zurich-agent — Claude Code gegen den Zurich-LiteLLM-Proxy

Separates Kit (kind: mixin) für Claude Code über den Zurich-LiteLLM-Proxy
`genai-lounge-nx-litellm-uat-emea.zurich.com` (nur im Firmennetz/Wikom-VPN erreichbar).
Der Root-Kit (`opencode-sandbox-kit`) bleibt der **Home-Standard** — Claude Code gegen
`api.anthropic.com`.

## Unterschiede zum Root-Kit

- `ANTHROPIC_BASE_URL` → `https://genai-lounge-nx-litellm-uat-emea.zurich.com`
- Model-Aliasse mit `eu.`-Präfix (LiteLLM-Aliasse des Zurich-Proxys, sonst 403
  `key not allowed to access model`):
  - `ANTHROPIC_MODEL` / `ANTHROPIC_DEFAULT_SONNET_MODEL` = `eu.anthropic.claude-sonnet-4-6`
  - `ANTHROPIC_DEFAULT_OPUS_MODEL` = `eu.anthropic.claude-opus-4-8`
  - `ANTHROPIC_DEFAULT_HAIKU_MODEL` / `CLAUDE_CODE_SUBAGENT_MODEL` = `eu.anthropic.claude-haiku-4-5-20251001-v1:0`
- Service `zurich` (`ZURICH_LITELLM_API_KEY`, `proxyManaged: true`): der Sandbox-Proxy injiziert
  den echten Key bei Requests an `genai-lounge-nx-litellm-uat-emea.zurich.com`
  (Header `Authorization: Bearer` + `x-api-key`)
- Network-Allowlist enthält zusätzlich `genai-lounge-nx-litellm-uat-emea.zurich.com` + `*.zurich.com`

## Verwendung (PowerShell, Docker Desktop nativ)

```powershell
# einmalig: Zurich-LiteLLM-Key registrieren
sbx secret set zurich

# Sandbox starten (z. Bsp. claude-zurich)
sbx run claude --name claude-zurich --kit ./claude-zurich-agent/
```

In der Sandbox ist `ZURICH_LITELLM_API_KEY=proxy-managed` gesetzt (Platzhalter); Claude Code sendet
`proxy-managed` als Key (via `apiKeyHelper`), der Proxy ersetzt den Platzhalter transparent. Der
Anthropic-Key (`sbx secret set anthropic`) ist für dieses Kit nicht nötig.

## Auth-Detail

Auth läuft über den `apiKeyHelper` (`echo proxy-managed`) — funktioniert mit LiteLLM-Proxy. Ein
`ANTHROPIC_AUTH_TOKEN` (Bearer) ist als Alternative möglich, aber nicht nötig.

## Dateien

- `spec.yaml` — Kit-Definition (env, network allow, credentials, setup wie Root-Kit)
- `files/home/.claude/` — Claude-Settings (Modell `eu.anthropic.claude-sonnet-4-6`, IntelliJ-MCP-Whitelist),
  `CLAUDE.md`, `network-policy.md`, Statusline
- `files/home/.config/sandbox-kit/`, `files/home/.local/bin/`, `files/home/stackexchange-api*.md` —
  identische Kopien des Root-Kits (Drift-Check in `local-test/local-test-kits.py --validate-only`)