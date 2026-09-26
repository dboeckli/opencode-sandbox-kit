#!/usr/bin/env python3
"""Build and push the OpenCode tooling image locally (docker buildx).

Local counterpart of .github/workflows/build-and-publish-opencode-image.yml. The image is the
official `opencode-docker` sandbox template with the kit tooling baked in (issue #137);
the tag is derived from the base template pin (TEMPLATE_VERSION). The tag scheme mirrors
the feature-branch CI build (semver prerelease + timestamp) and additionally sets the
moving `local` tag:

    <namespace>/sbx-opencode-tooling:<basever>-<branch-slug>.<YYYYMMDDHHMMSS>
    <namespace>/sbx-opencode-tooling:local

Run via the IntelliJ run config `build-and-publish-opencode-image` (or directly):
    python local-test/build-and-publish-opencode-image.py            # build + push + load locally (linux/amd64)
    python local-test/build-and-publish-opencode-image.py --build-only
    python local-test/build-and-publish-opencode-image.py --no-load   # push only, don't load into local Docker
    python local-test/build-and-publish-opencode-image.py --platform linux/arm64   # arm64 host only

Besides pushing the attested image to the registry, it loads the image into the
local Docker daemon (a second, cache-backed build without provenance/SBOM, since
the docker exporter cannot carry attestations). The full console output (including
the docker/buildx output) is additionally written to
`target/build-and-publish-opencode-image.log` (gitignored) for later inspection.

`local-test-kits.py opencode` uses the moving `local` tag by default
(`--template docker.io/<namespace>/sbx-opencode-tooling:local`), so a local run after
this script tests exactly this build. CI passes a feature tag via `OPENCODE_IMAGE_TAG`.

Environment overrides: OPENCODE_IMAGE_NAMESPACE, OPENCODE_IMAGE_NAME, OPENCODE_BUILDX_BUILDER.
Requires `docker` (Docker Desktop) with a logged-in Docker Hub session.
"""

import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from shutil import which

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTEXT = os.path.join(ROOT, "opencode-agent")
DOCKERFILE = os.path.join(CONTEXT, "opencode", "Dockerfile")
TARGET = os.path.join(ROOT, "target")
LOG_FILE = os.path.join(TARGET, "build-and-publish-opencode-image.log")
NAMESPACE = os.environ.get("OPENCODE_IMAGE_NAMESPACE", "domboeckli")
NAME = os.environ.get("OPENCODE_IMAGE_NAME", "sbx-opencode-tooling")
BUILDER = os.environ.get("OPENCODE_BUILDX_BUILDER", "sbx-opencode")


class Tee:
    """Write to several streams at once (original stdout/stderr + the log file)."""

    def __init__(self, *streams):
        self._streams = streams

    def write(self, data):
        for stream in self._streams:
            if stream is None or getattr(stream, "closed", False):
                continue
            stream.write(data)
            stream.flush()

    def flush(self):
        for stream in self._streams:
            if stream is None or getattr(stream, "closed", False):
                continue
            stream.flush()

    def isatty(self):
        return False


def run(cmd):
    """Run a command, streaming its combined output through Python (so the Tee captures it)."""
    print("+ " + " ".join(cmd), flush=True)
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        print(line, end="")
    proc.wait()
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd)


def base_version():
    with open(DOCKERFILE, encoding="utf-8") as f:
        m = re.search(
            r"ARG BASE_IMAGE=docker/sandbox-templates:opencode-docker-([0-9]+(?:\.[0-9]+)+)",
            f.read(),
        )
    if not m:
        sys.exit("opencode-docker BASE_IMAGE pin not found in opencode-agent/opencode/Dockerfile")
    return m.group(1)


def branch_slug():
    try:
        ref = subprocess.check_output(
            ["git", "-C", ROOT, "rev-parse", "--abbrev-ref", "HEAD"],
            text=True, encoding="utf-8", errors="replace",
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        ref = "local"
    slug = re.sub(r"[^a-z0-9_.-]+", "-", ref.lower()).strip("-")
    return slug or "local"


def ensure_builder():
    """Ensure a docker-container buildx builder (needed for provenance/SBOM)."""
    listing = subprocess.run(
        ["docker", "buildx", "ls", "--format", "{{.Name}}"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    ).stdout
    if re.search(rf"^{re.escape(BUILDER)}\s*$", listing, re.M):
        run(["docker", "buildx", "use", BUILDER])
    else:
        run(["docker", "buildx", "create", "--name", BUILDER,
             "--driver", "docker-container", "--use", "--bootstrap"])


def main():
    os.makedirs(TARGET, exist_ok=True)
    log_file = open(LOG_FILE, "w", encoding="utf-8", errors="replace", buffering=1)
    orig_stdout, orig_stderr = sys.stdout, sys.stderr
    sys.stdout = Tee(orig_stdout, log_file)
    sys.stderr = Tee(orig_stderr, log_file)
    try:
        print(f"Log: {LOG_FILE}")

        if which("docker") is None:
            sys.exit("docker not found on PATH")
        argv = sys.argv[1:]
        build_only = "--build-only" in argv
        no_load = "--no-load" in argv
        platform = "linux/amd64"
        if "--platform" in argv:
            platform = argv[argv.index("--platform") + 1]
        version = base_version()
        slug = branch_slug()
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        version_tag = f"{NAMESPACE}/{NAME}:{version}-{slug}.{ts}"
        local_tag = f"{NAMESPACE}/{NAME}:local"
        print(f"Version tag: {version_tag}")
        print(f"Moving tag:  {local_tag}")
        print(f"Platform:    {platform}")
        print(f"Dockerfile:  {DOCKERFILE}")
        ensure_builder()

        # Registry build (attested: provenance + SBOM). Explicit -f: the Dockerfile
        # lives in a subfolder (IntelliJ-friendly canonical name), context is the kit dir.
        push_cmd = ["docker", "buildx", "build",
                    "-f", DOCKERFILE,
                    "--platform", platform,
                    "--provenance=true", "--sbom=true",
                    "-t", version_tag,
                    "-t", local_tag]
        if not build_only:
            push_cmd += ["--push"]
        push_cmd += [CONTEXT]
        run(push_cmd)
        print("Built (not pushed)." if build_only else "Pushed to registry.")

        # Also load into the local Docker daemon (docker exporter cannot carry
        # attestations, so this second, cache-backed build omits provenance/SBOM).
        if not build_only and not no_load:
            load_cmd = ["docker", "buildx", "build",
                        "-f", DOCKERFILE,
                        "--platform", platform,
                        "--load",
                        "-t", version_tag,
                        "-t", local_tag,
                        CONTEXT]
            run(load_cmd)
            print(f"Loaded locally: {version_tag} + {local_tag}")

        print(f"Done. Log written to: {LOG_FILE}")
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
        # Restore the real streams before closing the log file: otherwise the
        # interpreter's final sys.stdout flush would hit the closed log file
        # ("Exception ignored while flushing sys.stdout").
        sys.stdout, sys.stderr = orig_stdout, orig_stderr
        log_file.close()


if __name__ == "__main__":
    main()
