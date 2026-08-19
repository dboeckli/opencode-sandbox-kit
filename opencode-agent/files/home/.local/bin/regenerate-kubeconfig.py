#!/usr/bin/env python3
"""Regenerate ~/.kube/config from the read-only host kubeconfig mount.

Docker Desktop Kubernetes: the sandbox receives the host's raw kubeconfig via a
read-only workspace mount (/c/Users/<user>/.kube). kubectl needs a transformed
copy: server rewritten to host.docker.internal, insecure-skip-tls-verify set
(apiserver cert is only valid for kubernetes.docker.internal/127.0.0.1), client
cert/key kept. Idempotent — only writes when the content changed.

Runs from setup.startup (both kits) as user 1000. Never fails the session:
without the mount or on error the script exits 0, so a sandbox without the
.kube workspace starts normally.

The script lives as identical copies in all three kits (files/home/.local/bin/ of
opencode-agent/spec.yaml, mammouth-agent/spec.yaml and claude-zurich-agent/spec.yaml) —
edit one copy, sync the others; the validate-only check fails on drift.
"""

import glob
import os
import sys

SERVER = "https://host.docker.internal:6443"


def regenerate():
    import yaml

    paths = glob.glob("/c/Users/*/.kube/config")
    if not paths:
        return
    with open(paths[0]) as f:
        cfg = yaml.safe_load(f)
    if not cfg or not cfg.get("users"):
        return
    user = cfg["users"][0]["user"]

    out = {
        "apiVersion": "v1",
        "kind": "Config",
        "clusters": [
            {
                "cluster": {
                    "server": SERVER,
                    "insecure-skip-tls-verify": True,
                },
                "name": "docker-desktop",
            }
        ],
        "contexts": [
            {
                "context": {"cluster": "docker-desktop", "user": "docker-desktop"},
                "name": "docker-desktop",
            }
        ],
        "current-context": "docker-desktop",
        "users": [
            {
                "name": "docker-desktop",
                "user": {
                    "client-certificate-data": user.get("client-certificate-data"),
                    "client-key-data": user.get("client-key-data"),
                },
            }
        ],
    }

    kdir = os.path.expanduser("~/.kube")
    os.makedirs(kdir, exist_ok=True)
    kpath = os.path.join(kdir, "config")
    data = yaml.safe_dump(out, sort_keys=False, default_flow_style=False)
    if os.path.isfile(kpath):
        with open(kpath) as f:
            if f.read() == data:
                return
    with open(kpath, "w") as f:
        f.write(data)


if __name__ == "__main__":
    try:
        regenerate()
    except Exception:
        sys.exit(0)
