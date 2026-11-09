#!/usr/bin/env python3
"""Free disk space from Docker buildx on the host (Windows/PowerShell).

Removes the obsolete pre-v3 buildx builders and prunes the build cache of the
active kit builders:

    python local-test/docker-buildx-cleanup.py                    # remove obsolete + prune active
    python local-test/docker-buildx-cleanup.py --dry-run          # only print the commands
    python local-test/docker-buildx-cleanup.py --no-rm            # prune only
    python local-test/docker-buildx-cleanup.py --no-prune         # remove obsolete only
    python local-test/docker-buildx-cleanup.py --stop-active      # also stop active builders (free RAM)
    python local-test/docker-buildx-cleanup.py --remove-active    # remove active builders (free RAM)

Why per builder: `docker buildx prune -af` without `--builder` prunes only the
*current* builder, but each kit builds with its own builder (see BUILDER in
local-test/build-and-publish-*-image.py). The obsolete `sbx-opencode`/`sbx-claude`
builders predate the v3 migration and are superseded by `sbx-opencode-v3`/
`sbx-claude-v3`; removing them also drops their build cache (builder state).

`--stop-active` stops the running BuildKit containers of the active builders
(frees RAM in the Docker Desktop VM, keeps builder config and cache).
`--remove-active` removes them entirely (also drops their cache volume; the
build-and-publish scripts recreate a builder on the next build). The two flags
are mutually exclusive, and `--remove-active` skips pruning because the cache is
deleted anyway.

`-a` (prune) includes internal/frontend images, so rebuilds are slower until the
cache is warm again. After pruning, compact the WSL2 VHDX to return the freed
space to C: (see docs/docker-disk-cleanup.md, section 3).

The console output (including the docker/buildx output) is additionally written
to `target/docker-buildx-cleanup.log` (gitignored) for later inspection.

Requires `docker` (Docker Desktop) on PATH. Run this on the host (PowerShell) -
the sandbox has an isolated Docker daemon that would prune the wrong cache.
"""

import os
import subprocess
import sys
from shutil import which

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, "target")
LOG_FILE = os.path.join(TARGET, "docker-buildx-cleanup.log")

# Pre-v3 builders (superseded by the *-v3 variants) - safe to remove.
OLD_BUILDERS = ("sbx-opencode", "sbx-claude")

# Builders currently used by local-test/build-and-publish-*-image.py.
ACTIVE_BUILDERS = (
    "sbx-opencode-v3",
    "sbx-claude-v3",
    "sbx-mammouth",
    "sbx-pi",
    "sbx-vibe",
)


class Tee:
    """Write to several streams at once (console + log file)."""

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


def run(cmd, dry_run):
    """Stream a command's combined output; return True on success."""
    print("+ " + " ".join(cmd), flush=True)
    if dry_run:
        return True
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
    return proc.returncode == 0


def existing_builders():
    """Return the set of known buildx builder names."""
    result = subprocess.run(
        ["docker", "buildx", "ls", "--format", "{{.Name}}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        sys.exit("docker buildx ls failed:\n" + (result.stderr or result.stdout))
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def main():
    os.makedirs(TARGET, exist_ok=True)
    log_file = open(LOG_FILE, "w", encoding="utf-8", errors="replace", buffering=1)
    orig_stdout, orig_stderr = sys.stdout, sys.stderr
    sys.stdout = Tee(orig_stdout, log_file)
    sys.stderr = Tee(orig_stderr, log_file)
    try:
        print(f"Log: {LOG_FILE}")
        cleanup()
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
        # Restore the real streams before closing the log file (otherwise the
        # interpreter's final sys.stdout flush would hit the closed log file).
        sys.stdout, sys.stderr = orig_stdout, orig_stderr
        log_file.close()


def cleanup():
    argv = sys.argv[1:]
    dry_run = "--dry-run" in argv
    do_rm = "--no-rm" not in argv
    stop_active = "--stop-active" in argv
    remove_active = "--remove-active" in argv
    # Removing the active builders drops their cache anyway, so skip the (then
    # pointless) prune pass.
    do_prune = "--no-prune" not in argv and not remove_active

    if stop_active and remove_active:
        sys.exit("--stop-active and --remove-active are mutually exclusive")

    if which("docker") is None:
        sys.exit("docker not found on PATH (run on the Windows host, not in the sandbox)")

    if dry_run:
        print("DRY RUN - no commands are executed\n")

    existing = existing_builders()
    failed = []

    if do_rm:
        print("== Remove obsolete builders ==")
        for builder in OLD_BUILDERS:
            if builder in existing:
                if not run(["docker", "buildx", "rm", builder], dry_run):
                    failed.append(f"buildx rm {builder}")
            else:
                print(f"skip {builder}: not present")
        if not dry_run:
            existing = existing_builders()

    if do_prune:
        print("\n== Prune build cache (active builders) ==")
        for builder in ACTIVE_BUILDERS:
            if builder in existing:
                if not run(
                    ["docker", "buildx", "prune", "--builder", builder, "-af"],
                    dry_run,
                ):
                    failed.append(f"buildx prune --builder {builder}")
            else:
                print(f"skip {builder}: not present")

    if remove_active:
        print("\n== Remove active builders (free RAM; recreated on next build) ==")
        for builder in ACTIVE_BUILDERS:
            if builder in existing:
                if not run(["docker", "buildx", "rm", builder], dry_run):
                    failed.append(f"buildx rm {builder}")
            else:
                print(f"skip {builder}: not present")
    elif stop_active:
        print("\n== Stop active builders (free RAM; config + cache kept) ==")
        for builder in ACTIVE_BUILDERS:
            if builder in existing:
                if not run(["docker", "buildx", "stop", builder], dry_run):
                    failed.append(f"buildx stop {builder}")
            else:
                print(f"skip {builder}: not present")

    if failed:
        sys.exit("\nFailed: " + ", ".join(failed))

    print("\nDone." + (" (dry run)" if dry_run else ""))
    if not dry_run and do_prune:
        print(
            "Tip: compact the WSL2 VHDX to return space to C: "
            "(docs/docker-disk-cleanup.md, section 3)."
        )


if __name__ == "__main__":
    main()
