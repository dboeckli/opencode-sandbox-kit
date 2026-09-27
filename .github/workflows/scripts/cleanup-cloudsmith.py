#!/usr/bin/env python3
"""Löscht alte Cloudsmith-Feature-Branch-Image-Snapshots aus `sbx`.

Cloudsmith-Docker-Modell: pro Image gibt es ein **getaggtes Index-Package** (Multi-Arch)
mit `tags.version = ['<basever>-<branch-slug>.<YYYYMMDDHHMMSS>', '<branch-slug>']` sowie
**untagged** Kind-Manifeste (amd64/arm64/Attestations), die vom Index referenziert werden.

Dieses Script löscht ausschließlich Packages, deren `tags.version` einen
Feature-Snapshot-Tag enthält (`<basever>-<slug>.<14-stelliger Timestamp>`).
Master-Images (`<basever>` + `latest`) matchen nicht und bleiben erhalten.
Untagged Kind-Manifeste werden NICHT einzeln gelöscht (sie sind vom Index referenziert;
Cloudsmith räumt unreferenzierte Manifeste selbst auf). Zusätzlich nur älter als MAX_AGE_DAYS.

Dry-Run als Default.

Umgebungsvariablen:
  OWNER / REPO               Cloudsmith owner + Repo (pflicht)
  CLOUDSMITH_API_KEY         API-Key (pflicht)
  PACKAGE                    Nur Packages, deren Name diesen String enthält (optional)
  MAX_AGE_DAYS               Mindestalter in Tagen (Default 1)
  DRY_RUN                    "true" = nur auflisten (Default true)
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen

API = "https://api.cloudsmith.io/v1"
OWNER = os.environ["OWNER"]
REPO = os.environ["REPO"]
PACKAGE = os.environ.get("PACKAGE", "")
KEY = os.environ["CLOUDSMITH_API_KEY"]
MAX_AGE_DAYS = int(os.environ.get("MAX_AGE_DAYS", "1"))
DRY_RUN = os.environ.get("DRY_RUN", "true").lower() == "true"
# Feature-Branch-Snapshot: <basever>-<branch-slug>.<YYYYMMDDHHMMSS>
# (Master-Tags sind <basever> bzw. "latest" -> kein Match).
FEATURE_RE = re.compile(r"-\S*\.[0-9]{14}$")


def req(method, path):
    request = Request(f"{API}{path}", method=method, headers={"X-Api-Key": KEY})
    with urlopen(request) as resp:
        body = resp.read()
        return (json.loads(body) if body else None), resp.headers


def version_tags(pkg):
    return (pkg.get("tags", {}) or {}).get("version") or []


def feature_versions(pkg):
    return [v for v in version_tags(pkg) if FEATURE_RE.search(v)]


def age_days(uploaded_at):
    if not uploaded_at:
        return 0
    created = datetime.fromisoformat(uploaded_at.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - created).days


def main():
    page, deleted, listed = 1, 0, 0
    while True:
        data, headers = req(
            "GET",
            f"/packages/{OWNER}/{REPO}/?page={page}&page_size=100&sort=-date",
        )
        if not data:
            break

        for pkg in data:
            name = pkg.get("name", "")
            if PACKAGE and PACKAGE not in name:
                continue

            candidates = feature_versions(pkg)
            if not candidates:
                continue

            age = age_days(pkg.get("uploaded_at") or "")
            if age < MAX_AGE_DAYS:
                continue

            listed += 1
            ident = pkg.get("identifier_perm") or pkg.get("slug_perm")
            action = "[DRY-RUN] würde löschen" if DRY_RUN else "Lösche"
            print(f"{action} {name}: {candidates} (Alter {age}d, id={ident})")
            if not DRY_RUN:
                req("DELETE", f"/packages/{OWNER}/{REPO}/{ident}/")
                deleted += 1

        pagetotal = int(headers.get("X-Pagination-Pagetotal", "0") or "0")
        if not data or len(data) < 100 or (pagetotal > 0 and page >= pagetotal):
            break
        page += 1

    print(f"Fertig. gelöscht={deleted}, qualifiziert={listed}")
    if DRY_RUN:
        print("Dry-Run aktiv — nichts gelöscht. Run mit DRY_RUN=false wiederholen.")
    sys.exit(0 if deleted == listed else 1)


if __name__ == "__main__":
    main()
