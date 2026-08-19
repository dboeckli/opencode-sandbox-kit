#!/usr/bin/env python3
"""regenerate-sbx-doc.py - sbx CLI-Offline-Referenz aus der Release-Binary neu erzeugen.

Die sbx CLI ist NICHT in Context7 (nur /docker/docs mit Teil-Abdeckung). Die einzige
vollstaendige, versionstreue Quelle sind die `--help`-Outputs der Binary selbst. Dieses
Skript laedt die Release-Binary aus `docker/sbx-releases`, sammelt `sbx --help` + die
`--help` aller Subcommands, erzeugt `opencode-agent/files/home/sbx-cli.md` und syncet die
Kopien in alle drei Kit-Bundles (opencode-agent/, mammouth-agent/, claude-zurich-agent/).

Nach einem sbx-Version-Bump (Renovate/Validate-Check meldet Drift) einmal ausfuehren:

  python local-test/regenerate-sbx-doc.py            # neueste Release
  python local-test/regenerate-sbx-doc.py v0.39.0    # bestimmte Version

Anforderungen: python3, `gh` (oder direkter GitHub-Zugriff via urllib als Fallback).
"""

import os
import platform
import re
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from shutil import which

REPO = "docker/sbx-releases"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SBX_DOC_RELS = ("opencode-agent/files/home/sbx-cli.md",
                "mammouth-agent/files/home/sbx-cli.md",
                "claude-zurich-agent/files/home/sbx-cli.md")


def _red(msg):
    return f"\033[31m{msg}\033[0m"


def _green(msg):
    return f"\033[32m{msg}\033[0m"


def latest_tag():
    """Latest Release-Tag via GitHub API (public)."""
    url = f"https://api.github.com/repos/{REPO}/releases/latest"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            import json
            tag = json.loads(resp.read()).get("tag_name") or ""
    except Exception:
        tag = ""
    tag = tag.strip()
    if not tag:
        sys.exit(_red(f"Latest-Tag nicht abrufbar: {url}"))
    return tag


def asset_name():
    system = platform.system()
    machine = platform.machine().lower()
    if system == "Linux":
        arch = "arm64" if machine in ("aarch64", "arm64") else \
               ("amd64" if machine in ("x86_64", "amd64") else None)
        return f"DockerSandboxes-linux-{arch}.tar.gz" if arch else None
    if system == "Darwin":
        if machine in ("arm64", "aarch64"):
            return "DockerSandboxes-darwin-arm64.tar.gz"
        if machine in ("x86_64", "amd64"):
            return "DockerSandboxes-darwin.tar.gz"
    return None


def run(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out


def download(tag, asset, dest_dir):
    url = f"https://github.com/{REPO}/releases/download/{tag}/{asset}"
    dest = os.path.join(dest_dir, asset)
    if which("gh"):
        code, out = run(["gh", "release", "download", "-R", REPO, tag,
                         "--pattern", asset, "--dir", dest_dir])
        if code != 0:
            print(_red(f"gh release download fehlgeschlagen: {out.strip()}"))
            print(_red(f"Fallback: direkter Download von {url}"))
            manifest = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
            print(manifest.stdout or manifest.stderr)
        else:
            return dest
    print(f"  download {url}")
    with urllib.request.urlopen(url, timeout=180) as resp, open(dest, "wb") as f:
        f.write(resp.read())
    return dest


def find_binary(tarball_path):
    with tarfile.open(tarball_path) as tf:
        names = tf.getnames()
        binary = next((n for n in names if n.endswith("/sbx") and not n.endswith(".sbx")), None)
        if not binary:
            sys.exit(_red(f"sbx-Binary nicht im Tarball gefunden ({tarball_path})"))
        base = os.path.dirname(tarball_path)
        tf.extract(binary, base)
        extracted = os.path.join(base, binary)
        dest = os.path.join(base, "sbx")
        if extracted != dest:
            os.replace(extracted, dest)
    return dest


def collect_help(binary):
    if not os.access(binary, os.X_OK):
        os.chmod(binary, 0o755)
    code, main = run([binary, "--help"])
    if code != 0:
        code, main = run([binary, "help"])
    if code != 0:
        sys.exit(_red(f"sbx --help schlug fehl: {main}"))
    commands = []
    in_cmds = False
    for line in main.splitlines():
        if line.strip() == "Available Commands:":
            in_cmds = True
            continue
        if in_cmds:
            if line.strip() == "" or line.strip().startswith(("Flags:", "Use ")):
                in_cmds = False
                continue
            m = re.match(r"^\s{2}([a-z][\w-]*)\s+", line)
            if m:
                commands.append(m.group(1))
    sections = [("sbx --help", main)]
    for cmd in commands:
        _, body = run([binary, cmd, "--help"])
        sections.append((f"sbx {cmd} --help", body))
    return sections


def render(version, sections):
    hdr = (
        f"# sbx CLI Reference (offline)\n\n"
        f"Kompakte Offline-Referenz der **Docker Sandboxes CLI (`sbx`)** — generiert aus den authentischen\n"
        f"`--help`-Outputs der **{version}**-Release-Binary (`docker/sbx-releases`). Includiert NICHT das\n"
        f"interaktive TUI; aktualisieren durch Neugenerierung aus der Binary (`sbx <cmd> --help`).\n"
        f"Detaillierte Hintergrunddoku (Kits, Policy, Proxy, Troubleshooting): `npx ctx7 docs /docker/docs <query>`\n"
        f"(nur teilweise abgedeckt — die CLI selbst ist NICHT in Context7). Kit-Grammatik v2:\n"
        f"`https://github.com/docker/sbx-kits-contrib/blob/main/spec/SPEC-v2.md`.\n"
    )
    out = [hdr]
    for title, body in sections:
        body = re.sub(r"\n{3,}", "\n\n", body.strip())
        out.append(f"## {title}\n```\n{body}\n```\n")
    return "\n".join(out)


def main():
    ver = sys.argv[1] if len(sys.argv) > 1 else latest_tag()
    ver = ver if ver.startswith("v") else f"v{ver}"
    asset = asset_name()
    if not asset:
        sys.exit(_red(f"Nicht unterstützte Plattform: {platform.system()} {platform.machine()} "
                      "- Windows nutzt einen MSI-Installer (kein Tarball)."))
    print(f"sbx CLI Doku neu erzeugen (Version {ver})")
    print(f"  asset: {asset}")
    with tempfile.TemporaryDirectory(prefix="sbx-doc-") as tmp:
        tarball = download(ver, asset, tmp)
        binary = find_binary(tarball)
        print(f"  binary: {binary}")
        print("  sammle --help-Outputs...")
        sections = collect_help(binary)
        print(f"  {len(sections)} Sektionen gesammelt")
        text = render(ver, sections)
        first = os.path.join(ROOT, SBX_DOC_RELS[0])
        with open(first, "w", encoding="utf-8") as f:
            f.write(text)
        for rel in SBX_DOC_RELS[1:]:
            dst = os.path.join(ROOT, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "w", encoding="utf-8") as f:
                f.write(text)
        # Konsistenz pruefen
        blobs = []
        for rel in SBX_DOC_RELS:
            with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
                blobs.append(f.read())
        if len(set(blobs)) != 1:
            sys.exit(_red("FEHLER: Kopien von sbx-cli.md sind nicht identisch"))
        print(_green(f"OK: sbx-cli.md {ver} regeneriert und auf {len(SBX_DOC_RELS)} Kopien gesynct"))


if __name__ == "__main__":
    main()