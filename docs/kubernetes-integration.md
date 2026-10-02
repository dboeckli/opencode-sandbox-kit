# Kubernetes-Integration (Docker Desktop)

> **Abgelöst (2026-09-30):** Der frühere Ansatz — Host-`.kube` **read-only mounten** und per
> `regenerate-kubeconfig.py` in eine Sandbox-`~/.kube/config` transformieren — ist **ersetzt**.
> Die Sandbox hält jetzt **keine** Kubernetes-Credentials mehr.
>
> **Aktuell:** Kubernetes-Zugriff über einen **host-seitigen MCP-Server**
> (`containers/kubernetes-mcp-server`, stdio, vom sbx MCP-Gateway gestartet) — read-only, ohne
> kubeconfig-Mount und ohne Client-Zertifikat/-Key in der Sandbox.
>
> Anleitung: **[`docs/kubernetes-mcp-server.md`](kubernetes-mcp-server.md)**
> (Issue [#40](https://codeberg.org/dboeckli/opencode-sandbox-kit/issues/40)).

## Kurzfassung

1. **Installieren** (Host, PowerShell): `.\local-scripts\install-kubernetes-mcp-server.ps1`
2. **Konfigurieren** (stdio): `.\local-scripts\configure-kubernetes-mcp-server.ps1`
3. **Registrieren** (sbx startet den Server): `sbx mcp add k8s --command "$env:USERPROFILE\.local\bin\kubernetes-mcp-server.exe" --args "--config,$env:USERPROFILE\.config\kubernetes-mcp-server\config.toml"`
4. **In der Sandbox nutzen:** `sbx run … --static-mcp idea,k8s` (kein `.kube:ro`-Mount)

> Der historische Mount-/Transformations-Ansatz (Issue #38) ist damit obsolet; Details zur
> Migrations-Entscheidung in Issue #40.

> [!WARNING]
> **Produktions-No-Go:** Der MCP-Server läuft read-only, aber ohne `denied_resources` für `Secret`
> (nötig für das `helm`-Toolset — Helm v3 speichert Releases als Secrets). Der Agent kann dadurch
> **Cluster-Secrets inkl. `.data` lesen**. Nur für Entwicklungs-Cluster (Docker Desktop).
> Siehe [`kubernetes-mcp-server.md`](kubernetes-mcp-server.md#sicherheit-kurz).
