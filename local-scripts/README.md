# local-scripts

Host-seitige Setup-/Utility-Skripte (**PowerShell, Windows**). Sie laufen **auf dem Windows-Host** —
nicht in der Sandbox und nicht in der CI.

Abgrenzung zu den anderen Skript-Orten:

| Ort | Läuft wo | Zweck |
|-----|----------|-------|
| `local-test/` | Host | lokale Tests/Validierung (Python, `--validate-only`, Image-Builds) |
| `local-scripts/` | Host | lokales Setup/Utility (PowerShell) |
| `*/files/home/.local/bin/` | Sandbox | Tooling/Agent-Config *in* der Sandbox |
| `.github/workflows/scripts/` | CI | Pipeline-Helfer |

## Skripte

| Skript | Zweck |
|--------|-------|
| `install-kubernetes-mcp-server.ps1` | [`containers/kubernetes-mcp-server`](https://github.com/containers/kubernetes-mcp-server) als native Windows-Binary installieren (Issue [#40](https://codeberg.org/dboeckli/opencode-sandbox-kit/issues/40)) |
| `configure-kubernetes-mcp-server.ps1` | `config.toml` im **stdio-Modus** schreiben (read-only, Toolsets core/config/helm, Host-kubeconfig, `log_file=stderr`), für `sbx mcp add --command`; setzt eine bestehende Installation voraus |

## Nutzung

```powershell
# aktuelle Release-Version installieren (Default: %USERPROFILE%\.local\bin, PATH wird gesetzt)
.\local-scripts\install-kubernetes-mcp-server.ps1

# bestimmte Version
.\local-scripts\install-kubernetes-mcp-server.ps1 -Version v0.0.67

# ohne PATH-Eintrag
.\local-scripts\install-kubernetes-mcp-server.ps1 -AddToPath:$false

# config.toml schreiben (nach der Installation; scheitert ohne Installation)
.\local-scripts\configure-kubernetes-mcp-server.ps1
```

Voraussetzungen: Windows, PowerShell 5.1+, Internetzugang (GitHub Releases).
Konfiguration und Start des Servers: siehe [`docs/kubernetes-mcp-server.md`](../docs/kubernetes-mcp-server.md).
