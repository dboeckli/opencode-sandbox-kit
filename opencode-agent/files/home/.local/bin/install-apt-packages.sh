#!/usr/bin/env bash
set -euo pipefail

# apt package installation (root). Referenced by `setup.install` in all three kit specs
# (single source of truth for the inline apt step they previously duplicated). Retries
# while the template's own apt-get (001-startup-opencode) holds the dpkg/apt lock, so the
# sandbox build does not fail on a transient lock condition.
#
# Bundled via files/home/.local/bin/ (all kits), executed by setup.install as root. Must
# stay identical in all kits — edit one copy, then `cp` it to the others
# (`mammouth-agent/files/home/.local/bin/`, `claude-zurich-agent/files/home/.local/bin/`).
# Drift is caught by local-test-kits.py (--validate-only, INSTALL_SCRIPT_PAIRS).

for i in $(seq 1 24); do
  if apt-get update && apt-get install -y jq python3 python3-pip python3-yaml; then
    exit 0
  fi
  echo "apt-get fehlgeschlagen (Versuch ${i}/24) - Lock/Netzwerk? warte 10s ..." >&2
  sleep 10
done
echo "FEHLER: apt-Installation nach 24 Versuchen fehlgeschlagen" >&2
exit 1
