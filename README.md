# opencode-sandbox-kit

Docker Sandbox Kit (mixin) for OpenCode development with ctx7 and IntelliJ MCP.

```
┌─────────────────────────────────────────────────────────────────┐
│                         WINDOWS HOST                            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    IntelliJ IDEA                          │   │
│  │  ◀── Projekt öffnen, Code anzeigen, Refactoring etc.     │   │
│  │                                                           │   │
│  │  MCP Server läuft auf http://127.0.0.1:64342/sse         │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │ Port 64342                               │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Docker Desktop (WSL)                         │   │
│  │                                                           │   │
│  │  host.docker.internal → Windows-Host                      │   │
│  │                                                           │   │
│  │  ┌────────────────────────────────────────────────────┐   │   │
│  │  │           SANDBOX (Container/VM)                    │   │   │
│  │  │                                                    │   │   │
│  │  │  ┌──────────────────────────────────────────────┐  │   │   │
│  │  │  │    opencode (CLI Agent)                       │  │   │   │
│  │  │  │                                               │  │   │   │
│  │  │  │  MCP Client ───► host.docker.internal:        │  │   │   │
│  │  │  │                 64342/sse                     ──┼──┼───┼───▶
│  │  │  │                                               │  │   │   │
│  │  │  │  liest/schreibt                               │  │   │   │
│  │  │  │  /workspace/ → Projekt-Code                   │  │   │   │
│  │  │  └──────────────────────────────────────────────┘  │   │   │
│  │  └────────────────────────────────────────────────────┘   │   │
│  │                                                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  📁 C:\development\projects\ ← geteilt via /mnt/c              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Usage (PowerShell on Windows)

```powershell
sbx run opencode --name opencode-sandbox --kit .
```

The sandbox runs inside Docker Desktop. IntelliJ MCP is reached via `host.docker.internal:64342`.

Optional — Context7 API-Key für höheres Rate-Limit:

```powershell
sbx exec opencode-sandbox bash -c "echo 'export CONTEXT7_API_KEY=your-key' >> /etc/sandbox-persistent.sh"
```

## Troubleshooting

### KVM Permission Denied (WSL2)

On WSL2, the sandbox VM (`nerdbox`) needs access to `/dev/kvm`. If you see:
```
failed to create VM: sailor: Hypervisor error: KVM error: Permission denied
```

```console
# Add user to groups
sudo usermod -aG kvm $USER
sudo usermod -aG sgx $USER

# Fix /dev/kvm group ownership
sudo chgrp kvm /dev/kvm

# Restart the sandbox daemon to pick up group changes
sbx daemon stop
sbx daemon start --detach
```

### Remove a sandbox

```powershell
sbx rm opencode-sandbox --force
```

### IntelliJ MCP connection failed (WSL2 / Docker)

Der IntelliJ MCP-Forwarder läuft auf Windows unter `127.0.0.1:64342`.

**Via `host.docker.internal` (funktioniert mit Docker Desktop unter Windows):**  
Im Sandbox-Kit ist die MCP-URL auf `host.docker.internal:64342` konfiguriert. Docker Desktop löst diese Adresse automatisch auf den Windows-Host auf. Funktioniert auch ohne WSL `networkingMode=mirrored`.

**Alternativ — WSL `networkingMode=mirrored`:**  
Falls `host.docker.internal` nicht verfügbar sein sollte (z. B. Docker Engine ohne Docker Desktop), kann in der `.wslconfig` `networkingMode=mirrored` gesetzt werden. Dann wird `127.0.0.1` aus dem Container direkt an Windows durchgereicht. Die URL in `opencode.jsonc` müsste dann wieder auf `127.0.0.1` geändert werden.

Stelle zudem sicher, dass Port 64342 in der Windows-Firewall freigegeben ist.

## References

- [Docker Sandbox Kits](https://docs.docker.com/ai/sandboxes/customize/kits/)
- [Kit Spec Reference](https://docs.docker.com/ai/sandboxes/customize/kit-reference/)
