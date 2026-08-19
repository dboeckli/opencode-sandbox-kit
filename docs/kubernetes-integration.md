# Kubernetes-Integration (Docker Desktop): kubeconfig in der Sandbox

Issue: https://github.com/dboeckli/opencode-sandbox-kit/issues/38

## Ziel

Aus der Sandbox heraus auf den Docker-Desktop-Kubernetes-Cluster des Windows-Hosts zugreifen
(`kubectl get nodes`, `kubectl cluster-info`, ...). Voraussetzung ist die Whitelist
`host.docker.internal:6443` (bzw. `localhost:6443`/`127.0.0.1:6443`) in `permissions.network.allow`
beider Kit-Specs — erst danach ist der kube-apiserver aus der Sandbox erreichbar.

## Kernproblem: Host-kubeconfig ist für die Sandbox nicht direkt lesbar

Die Sandbox sieht nur den **Workspace** (`C:\development\projects\...`, Filesystem-Passthrough).
Die Host-kubeconfig (`%USERPROFILE%\.kube\config`) liegt **außerhalb** des Workspace und ist
für den Agenten auf zwei Wegen blockiert:

- **IntelliJ MCP** (`idea_read_file`): liest nur Dateien innerhalb des Projekts — außerhalb
  liegt `File ... is outside project, library, and SDK roots`.
- **Host-Terminal**: `idea_execute_terminal_command` ist durch die IntelliJ-MCP-Whitelist
  (Deny-by-Default, nur lesende Tools) nicht verfügbar.

### Lösung: `.kube` als zusätzlichen Read-only-Workspace mounten

`sbx run` unterstützt **mehrere Workspaces**; zusätzliche Pfade werden direkt an ihrem
absoluten Host-Pfad gemountet, mit `:ro` als **Read-only-Mount**
([docs.docker.com/ai/sandboxes/usage](https://docs.docker.com/ai/sandboxes/usage/#multiple-workspaces)):

> **Optional:** Der `.kube:ro`-Mount ist nur für den kubectl-Zugriff auf Docker Desktop
> Kubernetes nötig. Ohne ihn startet die Sandbox **normal** — `setup.startup` läuft dann
> als no-op (kein `/c/Users/*/.kube/config`-Glob-Treffer → keine `~/.kube/config`, exit 0),
> kubectl hat lediglich keinen konfigurierten Cluster. Einfacher Start ohne Mount:

```powershell
sbx run opencode --name opencode-sandbox --kit ./opencode-agent/
```

> Mit Kubernetes-Zugriff (Mounts werden nur bei Sandbox-Erstellung gesetzt — beendet die
> laufende Session!):

```powershell
# Recreate:
sbx rm opencode-sandbox --force
sbx run opencode --name opencode-sandbox --kit ./opencode-agent/ "C:\development\projects\opencode-sandbox-kit" "$env:USERPROFILE\.kube:ro"
```

| Aspekt | Detail |
|--------|--------|
| Erster Pfad | Primary Workspace — der Agent startet hier (Projekt) |
| `.kube:ro` | Zusätzlicher Workspace, **read-only** (nur Read-Policy, kein Write auf die Host-kubeconfig) |
| Pfad in der Sandbox | `C:\Users\<user>\.kube` → `/c/Users/<user>/.kube` (gleiche `/c/...`-Konvention wie der Projekt-Workspace) |
| Aktualität | Live — Docker Desktop rotiert Zertifikate → die Sandbox liest sofort den aktuellen Stand, kein Copy/Delete nötig |

> **Warum kein Copy-Ansatz?** Ein Kopieren der Host-kubeconfig in den Workspace (frühere Variante)
> funktioniert zwar, hat aber Nachteile: Temp-Datei mit dem Host-Client-Zertifikat/-Key liegt im
> Workspace (darf nie in Git), wird nach Docker-Desktop-Rotation veraltet, und der Delete-Schritt
> ist manuell. Der Read-only-Mount ist live, immer aktuell und garantiert schreibgeschützt.

## Transformation: Gemountete Host-kubeconfig → Sandbox-kubeconfig

> **Automatisch seit 13.08.2026:** Die Transformation läuft bei jedem Sandbox-Start
> automatisch — `setup.startup` in allen Kits (opencode-agent/spec.yaml, mammouth-agent/spec.yaml,
> claude-zurich-agent/spec.yaml)
> führt `python3 /home/agent/.local/bin/regenerate-kubeconfig.py` als User 1000 aus.
> Das Skript liegt als identische Kopie in `files/home/.local/bin/` aller Kits
> (Drift-Check in `local-test-kits.py --validate-only`). Es ist idempotent (schreibt
> nur bei geändertem Inhalt) und greift nur, wenn der `.kube`-Mount vorhanden ist —
> ohne Mount bleibt `~/.kube/config` unangetastet, der Session-Start schlägt nie fehl.
> Das unten stehende Skript dient als Referenz der Transformation.

Der Read-only-Mount liefert die **rohe** Host-kubeconfig (`server:
https://kubernetes.docker.internal:6443`, Client-Cert-Auth). Für `kubectl` in der Sandbox ist
weiterhin eine transformierte `~/.kube/config` nötig:

| Feld | Host-kubeconfig | Sandbox-kubeconfig | Grund |
|------|-----------------|--------------------|-------|
| `clusters[].cluster.server` | `https://kubernetes.docker.internal:6443` | `https://host.docker.internal:6443` | `kubernetes.docker.internal` löst nur in der Docker-Desktop-VM auf; die Sandbox erreicht den Host nur über `host.docker.internal` (wie IntelliJ MCP auf 64342) |
| `clusters[].cluster.insecure-skip-tls-verify` | — | `true` | Das apiserver-Zertifikat ist nur für `kubernetes.docker.internal`/`127.0.0.1` signiert, nicht für `host.docker.internal`; SANs erweitern = Cluster-Neustart (nicht empfohlen) |
| `users[].user.client-certificate-data` | übernehmen | übernehmen | Docker Desktop nutzt Client-Cert-Auth |
| `users[].user.client-key-data` | übernehmen | übernehmen | dito |
| `clusters[].cluster.certificate-authority-data` | übernehmen | weglassen (nicht benötigt) | `insecure-skip-tls-verify: true` deaktiviert die CA-Prüfung |

Da die Quelle gemountet (und damit live) ist, lässt sich die `~/.kube/config` jederzeit
reproduzieren — z. B. als Skript (Python, `yaml` ist in der Sandbox installiert):

```python
import yaml, os, glob

# Read-only-Mount der Host-kubeconfig. Der Benutzername im Mount-Pfad ist
# benutzerspezifisch → per Glob auflösen (funktioniert für jeden User).
paths = glob.glob('/c/Users/*/.kube/config')
if not paths:
    raise SystemExit('Kubeconfig-Mount nicht gefunden: /c/Users/*/.kube/config')
with open(paths[0]) as f:
    cfg = yaml.safe_load(f)
user = cfg['users'][0]['user']

out = {
    'apiVersion': 'v1',
    'kind': 'Config',
    'clusters': [{
        'cluster': {
            'server': 'https://host.docker.internal:6443',
            'insecure-skip-tls-verify': True,
        },
        'name': 'docker-desktop',
    }],
    'contexts': [{
        'context': {'cluster': 'docker-desktop', 'user': 'docker-desktop'},
        'name': 'docker-desktop',
    }],
    'current-context': 'docker-desktop',
    'users': [{
        'name': 'docker-desktop',
        'user': {
            'client-certificate-data': user['client-certificate-data'],
            'client-key-data': user['client-key-data'],
        },
    }],
}

os.makedirs(os.path.expanduser('~/.kube'), exist_ok=True)
with open(os.path.expanduser('~/.kube/config'), 'w') as f:
    yaml.safe_dump(out, f, sort_keys=False, default_flow_style=False)
```

## Verifikation

```bash
# 1. Mount prüfen (read-only): Datei lesbar, Schreiben blockiert
ls -la /c/Users/*/.kube/
echo test > /c/Users/*/.kube/config   # → Read-only file system

# 2. Erreichbarkeit (Network-Policy greift seit dem Sandbox-Neustart)
curl -sk -m 5 https://host.docker.internal:6443/version     # → Version-JSON, NICHT "Blocked by network policy"

# 3. kubeconfig / API-Zugriff
kubectl cluster-info
kubectl get nodes -o wide          # → docker-desktop Ready v1.34.x
kubectl get namespaces
```

> **Hinweis:** Die Allowlist und die Workspace-Mounts werden nur bei Session-/Sandbox-Start
> geladen — nach einem Edit von `opencode-agent/spec.yaml` bzw. zum Hinzufügen eines Mounts muss die Sandbox
> neu erstellt werden. Siehe `docs/TODO-38-kubernetes-integration.md` für den konkreten Stand.
