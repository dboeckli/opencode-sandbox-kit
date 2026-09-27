#!/usr/bin/env python3
"""Leert den Cloudsmith-Recycle-Bin eines Repos (endgültiges Löschen) — gibt Storage frei.

Soft-gelöschte Packages (über `DELETE /packages/...`) werden von Cloudsmith **7 Tage**
aufbewahrt und zählen in dieser Zeit weiter gegen das Storage-Kontingent. Dieses Skript
listet den Recycle Bin (`/recycle-bin/{owner}/?repository=<repo>`) und löscht die Einträge
per `POST /recycle-bin/{owner}/action/ {"action":"hard_delete", identifiers:[…]}` sofort und
dauerhaft (Batches ≤ 100). Das betrifft ausschließlich bereits gelöschte Packages; die
aktuell getaggten (Live-)Images sind nicht im Recycle Bin.

Dry-Run als Default (nur auflisten).

Umgebungsvariablen:
  OWNER / REPO               Cloudsmith owner + Repo (pflicht)
  CLOUDSMITH_API_KEY         API-Key (pflicht)
  DRY_RUN                    "true" = nur auflisten (Default true)
"""
import json
import os
import sys
from urllib.request import Request, urlopen

API = "https://api.cloudsmith.io/v1"
OWNER = os.environ["OWNER"]
REPO = os.environ["REPO"]
KEY = os.environ["CLOUDSMITH_API_KEY"]
DRY_RUN = os.environ.get("DRY_RUN", "true").lower() == "true"


def api(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"X-Api-Key": KEY}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = Request(f"{API}{path}", method=method, headers=headers, data=data)
    with urlopen(request) as resp:
        raw = resp.read()
        return (json.loads(raw) if raw else None), resp.headers


def list_recycle_bin():
    page, out = 1, []
    while True:
        data, headers = api(
            "GET", f"/recycle-bin/{OWNER}/?repository={REPO}&page={page}&page_size=100"
        )
        if not data:
            break
        out.extend(data)
        pagetotal = int(headers.get("X-Pagination-Pagetotal", "0") or "0")
        if len(data) < 100 or (pagetotal > 0 and page >= pagetotal):
            break
        page += 1
    return out


def main():
    entries = list_recycle_bin()
    size = sum(int(e.get("size") or 0) for e in entries)
    print(f"Recycle Bin {OWNER}/{REPO}: {len(entries)} Packages, {size / 1e9:.1f} GB (pre-dedup)")
    if not entries:
        print("Recycle Bin ist leer.")
        sys.exit(0)
    if DRY_RUN:
        print("Dry-Run aktiv — nichts gelöscht. Run mit DRY_RUN=false wiederholen.")
        sys.exit(0)

    identifiers = [e["slug_perm"] for e in entries if e.get("slug_perm")]
    actioned, failed = 0, 0
    for i in range(0, len(identifiers), 100):
        batch = identifiers[i:i + 100]
        result, _ = api(
            "POST",
            f"/recycle-bin/{OWNER}/action/",
            {"action": "hard_delete", "identifiers": batch, "repository": REPO},
        )
        result = result or {}
        actioned += len(result.get("packages_actioned") or [])
        failed += len(result.get("packages_failed_to_action") or {})
        print(f"Batch {i // 100 + 1}: actioned={len(result.get('packages_actioned') or [])}, "
              f"failed={len(result.get('packages_failed_to_action') or {})}")
    print(f"Fertig. hard_delete actioned={actioned}, failed={failed}")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
