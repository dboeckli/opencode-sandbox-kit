#!/usr/bin/env python3
"""Löscht Feature-Branch-Image-Snapshots (+ deren verwaiste Manifeste) aus `dboeckli/sbx`.

Cloudsmith-Docker-Modell: pro Image existieren
  - getaggte Packages (Multi-Arch-Index + Per-Arch-Index) und
  - **untagged** Kind-Manifeste (Plattform-Manifeste + Attestations), die von einem Index
    per Digest referenziert werden.

Deshalb werden untagged Manifeste **nicht blind** gelöscht (das würde Live-Images wie
`<basever>`/`latest` zerstören). Stattdessen:
  1. Feature-getaggte Packages (Muster `<basever>-<slug>.<YYYYMMDDHHMMSS>` bzw. SLUG) werden gelöscht.
  2. Danach werden untagged Manifeste gelöscht, die von **keinem** verbleibenden getaggten
     Index mehr referenziert werden (= echte Orphans). Die Referenzen werden anonym vom
     Registry-Endpoint (`docker.cloudsmith.io`) gelesen.
  Fail-safe: Lässt sich auch nur ein Referenz-Manifest nicht lesen, wird die Orphan-Löschung
  übersprungen (nur die getaggten Feature-Packages werden gelöscht).

Modi:
  - SLUG gesetzt (z. B. bei PR-Merge): nur Images dieses Branch-Slugs.
  - SLUG leer (Nightly/Master-Push): Feature-Snapshots `<basever>-<slug>.<ts>` aelter als MAX_AGE_DAYS.

Umgebungsvariablen:
  OWNER / REPO               Cloudsmith owner + Repo (pflicht)
  CLOUDSMITH_API_KEY         API-Key (pflicht)
  PACKAGE                    Nur Packages, deren Name diesen String enthält (optional)
  SLUG                       Branch-Slug; gesetzt = nur diesen Branch loeschen (optional)
  MAX_AGE_DAYS               Mindestalter in Tagen (Default 1)
  DRY_RUN                    "true" = nur auflisten (Default true)
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from urllib.parse import quote
from urllib.request import Request, urlopen

API = "https://api.cloudsmith.io/v1"
REGISTRY = "https://docker.cloudsmith.io"
OWNER = os.environ["OWNER"]
REPO = os.environ["REPO"]
PACKAGE = os.environ.get("PACKAGE", "")
KEY = os.environ["CLOUDSMITH_API_KEY"]
MAX_AGE_DAYS = int(os.environ.get("MAX_AGE_DAYS", "1"))
DRY_RUN = os.environ.get("DRY_RUN", "true").lower() == "true"
# Branch-Slug wie in den build-and-publish-Workflows (lowercase, non-alnum -> '-').
SLUG = re.sub(r"[^a-z0-9_.-]+", "-", os.environ.get("SLUG", "").strip().lower()).strip("-")
# Feature-Branch-Snapshot: <basever>-<branch-slug>.<YYYYMMDDHHMMSS>
# (Master-Tags sind <basever> bzw. "latest" -> kein Match).
FEATURE_RE = re.compile(r"-\S*\.[0-9]{14}$")
ACCEPT = ", ".join((
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.oci.image.manifest.v1+json",
    "application/vnd.docker.distribution.manifest.v2+json",
))

_tokens = {}


def api(method, path):
    request = Request(f"{API}{path}", method=method, headers={"X-Api-Key": KEY})
    with urlopen(request) as resp:
        body = resp.read()
        return (json.loads(body) if body else None), resp.headers


def _registry_token(image):
    """Anonymes Pull-Token fuer ein Image (public OSS-Repo)."""
    if image in _tokens:
        return _tokens[image]
    scope = quote(f"repository:{OWNER}/{REPO}/{image}:pull", safe="")
    with urlopen(f"{REGISTRY}/login?service=docker.cloudsmith.io&scope={scope}") as resp:
        token = json.loads(resp.read()).get("token") or ""
    _tokens[image] = token
    return token


def child_digests(image, tag):
    """Kind-Digests des Index-Manifests <image>:<tag> (leer, wenn kein Index).

    Wirft bei Fehlern (Aufrufer behandelt das fail-safe)."""
    request = Request(
        f"{REGISTRY}/v2/{OWNER}/{REPO}/{image}/manifests/{tag}",
        headers={"Authorization": f"Bearer {_registry_token(image)}", "Accept": ACCEPT},
    )
    with urlopen(request) as resp:
        manifest = json.loads(resp.read())
    media_type = manifest.get("mediaType", "")
    if "index" in media_type or "manifest.list" in media_type:
        return [m["digest"] for m in manifest.get("manifests", []) if m.get("digest")]
    return []


def version_tags(pkg):
    return (pkg.get("tags", {}) or {}).get("version") or []


def feature_versions(pkg):
    """Kandidaten-Tags fuer dieses Package (SLUG-Modus oder Nightly-Feature-Muster)."""
    tags = version_tags(pkg)
    if SLUG:
        slug_re = re.compile(rf"-{re.escape(SLUG)}\.[0-9]{{14}}$")
        return [t for t in tags if t == SLUG or slug_re.search(t)]
    return [t for t in tags if FEATURE_RE.search(t)]


def matches_name(pkg):
    return not PACKAGE or PACKAGE in pkg.get("name", "")


def age_days(uploaded_at):
    if not uploaded_at:
        return 0
    created = datetime.fromisoformat(uploaded_at.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - created).days


def fetch_all_packages():
    page, out = 1, []
    while True:
        data, headers = api("GET", f"/packages/{OWNER}/{REPO}/?page={page}&page_size=100&sort=-date")
        if not data:
            break
        out.extend(data)
        pagetotal = int(headers.get("X-Pagination-Pagetotal", "0") or "0")
        if len(data) < 100 or (pagetotal > 0 and page >= pagetotal):
            break
        page += 1
    return out


def delete(ident, label, name):
    action = "[DRY-RUN] würde löschen" if DRY_RUN else "Lösche"
    print(f"{action} {name}: {label} (id={ident})")
    if not DRY_RUN:
        api("DELETE", f"/packages/{OWNER}/{REPO}/{ident}/")


def main():
    pkgs = fetch_all_packages()
    tagged = [p for p in pkgs if version_tags(p)]
    untagged = [p for p in pkgs if not version_tags(p)]
    print(f"Packages: {len(pkgs)} (tagged={len(tagged)}, untagged={len(untagged)})")

    # 1) Feature-getaggte Packages zum Loeschen bestimmen
    to_delete_tagged, keep_tagged = [], []
    for p in tagged:
        if not matches_name(p):
            continue
        cands = feature_versions(p)
        if cands and age_days(p.get("uploaded_at") or "") >= MAX_AGE_DAYS:
            to_delete_tagged.append((p, cands))
        else:
            keep_tagged.append(p)

    # 2) Referenzierte Kind-Digests der verbleibenden getaggten Indizes einsammeln (fail-safe)
    referenced, ref_ok = set(), True
    for p in keep_tagged:
        for tag in version_tags(p):
            try:
                referenced.update(child_digests(p["name"], tag))
            except Exception as e:  # noqa: BLE001
                ref_ok = False
                print(f"WARN: Referenzen von {p['name']}:{tag} nicht lesbar ({e}) — Orphan-Loeschung wird uebersprungen")

    # 3) Untagged Orphans: nicht mehr referenziert + Alter + Name
    to_delete_untagged = []
    if ref_ok:
        for p in untagged:
            if not matches_name(p):
                continue
            if p.get("version") in referenced:
                continue
            if age_days(p.get("uploaded_at") or "") < MAX_AGE_DAYS:
                continue
            to_delete_untagged.append(p)

    # 4) Loeschen
    for p, cands in to_delete_tagged:
        delete(p.get("identifier_perm") or p.get("slug_perm"), cands, p["name"])
    if ref_ok:
        for p in to_delete_untagged:
            delete(p.get("identifier_perm") or p.get("slug_perm"),
                   f"untagged orphan {str(p.get('version'))[:16]}", p["name"])

    deleted = (0 if DRY_RUN else len(to_delete_tagged) + len(to_delete_untagged))
    print(f"Fertig. tagged={len(to_delete_tagged)}, untagged-orphans={len(to_delete_untagged)}, "
          f"referenced={len(referenced)}{'' if ref_ok else ' (Referenzen unvollstaendig!)'}")
    if DRY_RUN:
        print("Dry-Run aktiv — nichts gelöscht. Run mit DRY_RUN=false wiederholen.")
    sys.exit(0)


if __name__ == "__main__":
    main()
