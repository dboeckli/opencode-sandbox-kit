# Kubernetes-Integration (Docker Desktop): Whitelisting `host.docker.internal:6443`

Issue: https://github.com/dboeckli/opencode-sandbox-kit/issues/38
Branch: `feature/38-kubernetes-integration-docker-desktop-whitelisting`

## Status: Whitelist + Read-only-Mount + automatische kubeconfig-Regenerierung fertig

> **Verifikation (13.08.2026, Sandbox `opencode-sandbox` mit `.kube:ro`-Mount):**
> Mount `/c/Users/dboec/.kube` als read-only (`Read-only file system` beim Schreibtest) ✓
> `curl -sk https://host.docker.internal:6443/version` → `v1.34.1` (Whitelist greift) ✓
> `kubectl cluster-info` → control plane läuft; `kubectl get nodes` → `docker-desktop Ready v1.34.1`;
> Namespace-Liste abrufbar ✓
> `sbx kit validate` (mixin + mammouth-agent): 5 Checks PASS, exit 0 ✓
>
> **Benutzerunabhängig gemacht:** Das Generierungs-Skript in `docs/kubernetes-integration.md` löst
> den Mount-Pfad per Glob (`/c/Users/*/.kube/config`) auf statt den Usernamen hartzukodieren —
> funktioniert für jeden Windows-User. Der Start-Befehl nutzt weiterhin `"$env:USERPROFILE\.kube:ro"`.
>
> **Automatik ergänzt:** Die kubeconfig-Transformation läuft jetzt **automatisch bei jedem
> Sandbox-Start** — `setup.startup`-Hook in beiden Kits führt `files/home/.local/bin/
> regenerate-kubeconfig.py` aus (idempotent, no-op ohne Mount, Drift-gesynct via
> `local-test-kits.py --validate-only`). Verifiziert: Config löschen → Skript erzeugt sie neu →
> `kubectl get nodes` → `docker-desktop Ready v1.34.1`.

## Was bereits gemacht wurde

1. **Whitelist ergänzt** in `permissions.network.allow` (beide Kits):
   - `spec.yaml` + `mammouth-agent/spec.yaml`: `localhost:6443`, `127.0.0.1:6443`, `host.docker.internal:6443`
2. **Docs synchron gehalten** (3 Dateien, identisch):
   - `files/home/.claude/network-policy.md`
   - `files/home/.config/opencode/network-policy.md`
   - `mammouth-agent/files/home/.config/mammouth/network-policy.md`
   - Eintrag: `localhost:6443`, `127.0.0.1:6443`, `host.docker.internal:6443` (kube-apiserver)
3. **Wichtige Erkenntnis (Fehler beim Test):** Der Proxy normalisiert `host.docker.internal`
   für das Policy-Matching zu `localhost`. Nur `host.docker.internal:6443` zu whitelisten
   reicht NICHT — `curl -sk https://host.docker.internal:6443/version` liefert
   `Blocked by network policy: domain localhost:6443`. Daher alle drei Hostnamen
   whitelisten (gleiches Muster wie IntelliJ MCP auf 64342).
4. **Host-Verifikation (PowerShell):** apiserver erreichbar — `curl.exe -sk
   https://localhost:6443/version` → k8s v1.34.1; `kubectl config view --minify` →
   `https://kubernetes.docker.internal:6443`.

## Als Nächstes zu tun

1. **Sandbox neu starten** (bestätigt, dass Whitelist + Mount + `setup.startup`-Automatik
   auch nach einem frischen Session-Start greifen — `~/.kube/config` sollte ohne manuellen
   Schritt existieren):
   ```powershell
   sbx rm opencode-sandbox --force
   sbx run opencode --name opencode-sandbox --kit . "C:\development\projects\opencode-sandbox-kit" "$env:USERPROFILE\.kube:ro"
   ```
   Danach in der Sandbox: `kubectl get nodes` → `docker-desktop Ready`.
   Ein Start **ohne** Mount funktioniert ebenfalls (`sbx run opencode --name opencode-sandbox
   --kit .`) — die Automatik ist dann ein no-op, kubectl hat nur keinen Cluster.
2. **PR-Message prüfen** und Branch `feature/38-kubernetes-integration-docker-desktop-whitelisting` committen.
