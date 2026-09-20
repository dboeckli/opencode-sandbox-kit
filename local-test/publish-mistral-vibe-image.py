#!/usr/bin/env python3
"""Build and push the Mistral Vibe image locally (docker buildx).

Local counterpart of .github/workflows/publish-mistral-vibe-image.yml. The tag
scheme mirrors the feature-branch CI build (semver prerelease + timestamp) and
additionally sets the moving `local` tag:

    <namespace>/sbx-mistral-vibe:<pin>-<branch-slug>.<YYYYMMDDHHMMSS>
    <namespace>/sbx-mistral-vibe:local

Run via the IntelliJ run config `publish-mistral-vibe-image` (or directly):
    python local-test/publish-mistral-vibe-image.py            # build + push
    python local-test/publish-mistral-vibe-image.py --build-only

Environment overrides: VIBE_IMAGE_NAMESPACE, VIBE_IMAGE_NAME, VIBE_BUILDX_BUILDER.
Requires `docker` (Docker Desktop) with a logged-in Docker Hub session.
"""

import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from shutil import which

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTEXT = os.path.join(ROOT, "mistral-vibe-agent")
DOCKERFILE = os.path.join(CONTEXT, "Dockerfile")
NAMESPACE = os.environ.get("VIBE_IMAGE_NAMESPACE", "domboeckli")
NAME = os.environ.get("VIBE_IMAGE_NAME", "sbx-mistral-vibe")
BUILDER = os.environ.get("VIBE_BUILDX_BUILDER", "sbx-vibe")


def run(cmd):
    print("+ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def pin_version():
    with open(DOCKERFILE, encoding="utf-8") as f:
        m = re.search(r"ARG VIBE_VERSION=([0-9]+(?:\.[0-9]+)+)", f.read())
    if not m:
        sys.exit("VIBE_VERSION pin not found in mistral-vibe-agent/Dockerfile")
    return m.group(1)


def branch_slug():
    try:
        ref = subprocess.check_output(
            ["git", "-C", ROOT, "rev-parse", "--abbrev-ref", "HEAD"],
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        ref = "local"
    slug = re.sub(r"[^a-z0-9_.-]+", "-", ref.lower()).strip("-")
    return slug or "local"


def ensure_builder():
    """Ensure a docker-container buildx builder (needed for provenance/SBOM)."""
    listing = subprocess.run(
        ["docker", "buildx", "ls", "--format", "{{.Name}}"],
        capture_output=True, text=True,
    ).stdout
    if re.search(rf"^{re.escape(BUILDER)}\s*$", listing, re.M):
        run(["docker", "buildx", "use", BUILDER])
    else:
        run(["docker", "buildx", "create", "--name", BUILDER,
             "--driver", "docker-container", "--use", "--bootstrap"])


def main():
    if which("docker") is None:
        sys.exit("docker not found on PATH")
    build_only = "--build-only" in sys.argv[1:]
    version = pin_version()
    slug = branch_slug()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    version_tag = f"{NAMESPACE}/{NAME}:{version}-{slug}.{ts}"
    local_tag = f"{NAMESPACE}/{NAME}:local"
    print(f"Version tag: {version_tag}")
    print(f"Moving tag:  {local_tag}")
    ensure_builder()
    cmd = ["docker", "buildx", "build",
           "--platform", "linux/amd64",
           "--provenance=true", "--sbom=true",
           "-t", version_tag,
           "-t", local_tag]
    if not build_only:
        cmd += ["--push"]
    cmd += [CONTEXT]
    run(cmd)
    print("Built (not pushed)." if build_only else "Pushed.")


if __name__ == "__main__":
    main()
