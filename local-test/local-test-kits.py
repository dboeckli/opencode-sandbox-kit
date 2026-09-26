#!/usr/bin/env python3
"""local-test-kits.py - automatischer Test der 4 Agent-Szenarien des opencode-sandbox-kit.

Laeuft auf Windows (PowerShell/CMD) und Linux/macOS, sofern `sbx` und ein
Docker-Daemon verfuegbar sind (auf Windows der nativen Docker Desktop, NICHT aus WSL).

Szenarien:
  1. OpenCode     + opencode-agent      (sbx create opencode --kit ./opencode-agent/)
  2. Claude       + opencode-agent      (sbx create claude --kit ./opencode-agent/)   — Home (api.anthropic.com)
  3. Mammouth     + mammouth-agent      (sbx create ./mammouth-agent/ — Sandbox-Kit, erstes positionales Argument)
  4. Mistral Vibe + mistral-vibe-agent  (sbx create ./mistral-vibe-agent/ — Sandbox-Kit, eigenes gepinntes Image)

Voraussetzungen:
  - Docker laeuft, `sbx` CLI im PATH
  - Globale Secrets registriert: github, github-maven, anthropic, mammouth, mistral, context7, openrouter, google, stackoverflow, cloudsmith, sonarcloud
    (sbx secret set github-maven / sbx secret set mammouth / sbx secret set mistral / sbx secret set context7 / sbx secret set openrouter / sbx secret set google / sbx secret set stackoverflow / sbx secret set cloudsmith / sbx secret set sonarcloud — seit v0.38 ohne `-g`)
  - Mistral-Vibe-Szenario (lokal): das Image `domboeckli/sbx-mistral-vibe:local` ist publiziert
    (IntelliJ-Run-Config `build-and-publish-mistral-vibe-image` bzw. `python local-test/build-and-publish-mistral-vibe-image.py`);
    CI/e2e uebergibt stattdessen den Feature-Tag per `VIBE_IMAGE_TAG`

Verwendung:
  python local-test-kits.py                 # alle 4 Szenarien testen (default: all)
  python local-test-kits.py opencode        # nur OpenCode testen
  python local-test-kits.py claude          # nur Claude testen (Home-Szenario)
  python local-test-kits.py mammouth        # nur Mammouth testen
  python local-test-kits.py mistral-vibe    # nur Mistral Vibe testen
  python local-test-kits.py --help          # alle Optionen anzeigen
  python local-test-kits.py --validate-only # nur Kit-Validierung, keine Sandbox/Sandbox-Szenarien

Optionen:
  {all,opencode,claude,mammouth,mistral-vibe}  Zu testendes Kit (default: all)
  -h, --help                      Diese Hilfe anzeigen
  --keep                          Sandboxes nach dem Test behalten
  --ci                            CI-Modus: Fake-API-Keys, kein realer
                                  mammouth-/mistral-API-Call
  --validate-only                 Nur Kit-Validierung (sbx kit validate),
                                  keine Secrets-/Sandbox-Checks (default: Sandboxes
                                  werden gestartet)
  --workspace <pfad>              Workspace der Sandbox-Szenarien
                                  (default: $WORKSPACE_DIR oder Repo-Root)
"""

import argparse
import json
import os
import re
import ssl
import subprocess
import sys
import time
import urllib.request
from shutil import which

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
passed = []
failed = []

# Stack Exchange API: Update-Check über den offiziellen Change-Log.
# Er listet Versionen neueste-zuerst ("Version 2.3" zuerst). Die dokumentierte
# Version steht in den offline-Doku-Dateien des Kits (Basis-URL api.stackexchange.com/<v>).
SO_CHANGE_LOG_URL = "https://api.stackexchange.com/docs/change-log"
SO_CHANGE_LOG_RE = re.compile(r"<h[12][^>]*>\s*Version\s+(\d+\.\d+)\s*</h[12]>")
SO_DOC_FILES = ("opencode-agent/files/home/stackexchange-api.md",
                "mammouth-agent/files/home/stackexchange-api.md",
                "mistral-vibe-agent/files/home/stackexchange-api.md")

# sbx CLI: die Offline-Referenz (sbx-cli.md) wird aus der Release-Binary generiert
# (local-test/regenerate-sbx-doc.py). Die dokumentierte Version steht im Header der Datei;
# Update-Check vergleicht sie mit dem gepinnten SBX_VERSION aus .github/workflows/validate.yml
# (Source of Truth, Renovate managed). Identische Kopien in allen drei Kit-Bundles.
SBX_DOC_FILES = ("opencode-agent/files/home/sbx-cli.md",
                 "mammouth-agent/files/home/sbx-cli.md",
                 "mistral-vibe-agent/files/home/sbx-cli.md")
SBX_VALIDATE_YML = ".github/workflows/validate.yml"

# Die Install-Skripte liegen als identische Kopien in den files/home/.local/bin-
# Bundles beider Kits. `setup.install` konsumiert sie aus dem Sandbox-Home. Alle
# Kopien muessen identisch bleiben (edit target = eine Kopie, andere per cp syncen;
# Renovate aktualisiert beide gemeinsam).
INSTALL_SCRIPT_PAIRS = (
    ("opencode-agent/files/home/.local/bin/install-tooling.sh",
     "mammouth-agent/files/home/.local/bin/install-tooling.sh"),
    ("opencode-agent/files/home/.local/bin/install-tooling.sh",
     "mistral-vibe-agent/files/home/.local/bin/install-tooling.sh"),
    ("opencode-agent/files/home/.local/bin/install-tooling-user.sh",
     "mammouth-agent/files/home/.local/bin/install-tooling-user.sh"),
    ("opencode-agent/files/home/.local/bin/install-tooling-user.sh",
     "mistral-vibe-agent/files/home/.local/bin/install-tooling-user.sh"),
    ("opencode-agent/files/home/.local/bin/regenerate-kubeconfig.py",
     "mammouth-agent/files/home/.local/bin/regenerate-kubeconfig.py"),
    ("opencode-agent/files/home/.local/bin/regenerate-kubeconfig.py",
     "mistral-vibe-agent/files/home/.local/bin/regenerate-kubeconfig.py"),
    ("opencode-agent/files/home/.local/bin/install-apt-packages.sh",
     "mammouth-agent/files/home/.local/bin/install-apt-packages.sh"),
    ("opencode-agent/files/home/.local/bin/install-apt-packages.sh",
     "mistral-vibe-agent/files/home/.local/bin/install-apt-packages.sh"),
)

# Sandbox-Template-Version (beide Kits, eine Version fuer beide Template-Familien):
#   - Expliziter Pin der lokalen Tests (dieses Script): TEMPLATE_VERSION-Konstante, Renovate-managed.
#   - Muss identisch sein mit `TEMPLATE_VERSION` in .github/workflows/validate.yml + e2e.yml und dem
#     Mammouth-spec-Image (mammouth-agent/spec.yaml) — Drift-Check in check_template_update().
#   - opencode-docker (OpenCode + Mammouth) / claude-code-docker (Claude Home, Mixin-Kit).
# Update-Check gegen die Docker-Hub-Tags (hub.docker.com); warnt (gelb) bei neuerem Tag.
TEMPLATE_VERSION = "0.7.0"
TEMPLATE_CFG_FILES = (".github/workflows/validate.yml", ".github/workflows/e2e.yml")
TEMPLATE_VERSION_RE = re.compile(r"TEMPLATE_VERSION:\s*([0-9]+\.[0-9]+\.[0-9]+)")
TEMPLATE_TAG_RE = re.compile(r"^(?P<fam>opencode-docker|claude-code-docker)-(?P<v>[0-9]+\.[0-9]+\.[0-9]+)$")
DOCKER_HUB_TEMPLATES_URL = "https://hub.docker.com/v2/repositories/docker/sandbox-templates/tags?page_size=100"
# Template-Familie je Agent. Mammouth (kind:sandbox) fehlt bewusst: dort pinnt das spec-Image.
AGENT_TEMPLATES = {"opencode": "opencode-docker", "claude": "claude-code-docker"}

# Mammouth (Issue #137): eigenes Image (mammouth-agent/Dockerfile) — Basis opencode-docker + Kit-Tooling
# + Mammouth-CLI. MAMMOUTH_VERSION (CLI-Pin) treibt den Image-Tag; ARG BASE_IMAGE muss TEMPLATE_VERSION
# spiegeln. Update-Check des CLI-Pins gegen das latest GitHub-Release (mammouth-ai/code, Tag v<ver>);
# warnt (gelb) bei neuerem Release.
MAMMOUTH_DOCKERFILE = "mammouth-agent/Dockerfile"
MAMMOUTH_IMAGE_NAMESPACE = os.environ.get("MAMMOUTH_IMAGE_NAMESPACE", "domboeckli")
MAMMOUTH_IMAGE_NAME = os.environ.get("MAMMOUTH_IMAGE_NAME", "sbx-mammouth")
MAMMOUTH_VERSION_RE = re.compile(r"ARG MAMMOUTH_VERSION=(?P<v>[0-9]+(?:\.[0-9]+)+)")
MAMMOUTH_BASE_IMAGE_RE = re.compile(
    r"ARG BASE_IMAGE=docker/sandbox-templates:opencode-docker-(?P<v>[0-9]+\.[0-9]+\.[0-9]+)"
)
MAMMOUTH_LATEST_URL = "https://api.github.com/repos/mammouth-ai/code/releases/latest"

# Mistral Vibe: Pin im Dockerfile (ARG VIBE_VERSION) — die spec.yaml referenziert das Image
# mit demselben Tag. Update-Check gegen die latest PyPI-Version (mistral-vibe); warnt (gelb)
# bei neuerer Version. Das Basis-Image pinnt die shell-Template-Version
# (docker/sandbox-templates:shell-docker-<TEMPLATE_VERSION>), die mit TEMPLATE_VERSION uebereinstimmen muss.
VIBE_DOCKERFILE = "mistral-vibe-agent/Dockerfile"
VIBE_SPEC_FILE = "mistral-vibe-agent/spec.yaml"
VIBE_VERSION_RE = re.compile(r"ARG VIBE_VERSION=(?P<v>[0-9]+(?:\.[0-9]+)+)")
VIBE_IMAGE_TAG_RE = re.compile(r"default:\s*\"(?P<v>[0-9]+(?:\.[0-9]+)+)\"")
VIBE_BASE_IMAGE_RE = re.compile(r"ARG BASE_IMAGE=docker/sandbox-templates:shell-docker-(?P<v>[0-9]+\.[0-9]+\.[0-9]+)")
VIBE_PYPI_URL = "https://pypi.org/pypi/mistral-vibe/json"

# Tooling-Images (Issue #137): eigene Custom-Template-Builds des opencode-agent-Mixin-Kits
# mit vorgebackenem Tooling — opencode-agent/opencode/Dockerfile (Basis opencode-docker) und
# opencode-agent/claude/Dockerfile (Basis claude-code-docker). Die opencode-/claude-Szenarien
# nutzen sie statt der offiziellen Templates. Die beiden Dockerfiles muessen identisch sein
# ausser der ARG BASE_IMAGE-Zeile (Drift-Check in check_image_dockerfiles_sync()).
# Tag: CI/e2e uebergibt den Feature-Tag per `OPENCODE_IMAGE_TAG` / `CLAUDE_IMAGE_TAG`; lokal
# default `local` (zuletzt per local-test/build-and-publish-<agent>-image.py gebaut/gepusht).
OPENCODE_DOCKERFILE = "opencode-agent/opencode/Dockerfile"
CLAUDE_DOCKERFILE = "opencode-agent/claude/Dockerfile"
OPENCODE_IMAGE_NAMESPACE = os.environ.get("OPENCODE_IMAGE_NAMESPACE", "domboeckli")
OPENCODE_IMAGE_NAME = os.environ.get("OPENCODE_IMAGE_NAME", "sbx-opencode-tooling")
CLAUDE_IMAGE_NAMESPACE = os.environ.get("CLAUDE_IMAGE_NAMESPACE", "domboeckli")
CLAUDE_IMAGE_NAME = os.environ.get("CLAUDE_IMAGE_NAME", "sbx-claude-tooling")
OPENCODE_BASE_IMAGE_RE = re.compile(
    r"ARG BASE_IMAGE=docker/sandbox-templates:opencode-docker-(?P<v>[0-9]+\.[0-9]+\.[0-9]+)"
)
CLAUDE_BASE_IMAGE_RE = re.compile(
    r"ARG BASE_IMAGE=docker/sandbox-templates:claude-code-docker-(?P<v>[0-9]+\.[0-9]+\.[0-9]+)"
)

# Secrets je Szenario: Globale Dienst-Secrets, die das jeweilige Szenario in der Sandbox
# benötigt (Kit-deklarierte Services aus den Specs credentials[].service + Template-Built-ins
# wie github/anthropic). openrouter/google verdrahtet nur das opencode-Template.
# Fehlermeldungen nennen das betroffene Kit.
SCENARIO_KIT = {
    "opencode": "opencode-agent",
    "claude": "opencode-agent",  # Claude-Home-Szenario (claude-code-docker-Template + opencode-agent-Kit)
    "mammouth": "mammouth-agent",
    "mistral-vibe": "mistral-vibe-agent",
}
SCENARIO_SECRETS = {
    "opencode": ("github", "github-maven", "context7", "openrouter", "google", "zai", "stackoverflow", "cloudsmith", "sonarcloud"),
    "claude": ("github", "github-maven", "anthropic", "context7", "stackoverflow", "cloudsmith", "sonarcloud"),
    "mammouth": ("github", "github-maven", "mammouth", "context7", "stackoverflow", "cloudsmith", "sonarcloud"),
    "mistral-vibe": ("github", "github-maven", "mistral", "zai", "context7", "stackoverflow", "cloudsmith", "sonarcloud"),
}
# Reihenfolge der Checks (Ausgabe stabil halten)
SECRET_ORDER = ("github", "github-maven", "anthropic", "mammouth", "mistral", "zai", "context7", "openrouter", "google",
                "stackoverflow", "cloudsmith", "sonarcloud")


def enable_ansi():
    """ANSI-Farben + UTF-8 fuer die Konsole aktivieren.

    Der `sbx`-Output enthaelt UTF-8-Box-Zeichen (──, ✓, →, …); ohne UTF-8
    dekodiert/schreibt die Windows-Konsole sie als cp1252 -> Mojibake.
    """
    if os.name == "nt":
        os.system("")                        # ANSI/VT-Verarbeitung aktivieren
        os.system("chcp 65001 >nul 2>&1")    # Konsole auf UTF-8
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def _color(code, text):
    return f"\033[{code}m{text}\033[0m"


def info(msg):
    print(_color("36", msg))


def pass_(msg):
    passed.append(msg)
    print("  " + _color("32", "[PASS] " + msg))


def fail(msg, detail=""):
    failed.append(msg)
    print("  " + _color("31", "[FAIL] " + msg))
    if detail:
        print("         " + _color("31", detail))


def warn(msg, detail=""):
    print("  " + _color("33", "[WARN] " + msg))
    if detail:
        print("         " + _color("33", detail))


def run_sbx(args, stream=False):
    if which("sbx") is None:
        print(_color("31", "sbx CLI nicht gefunden (PATH?)"))
        sys.exit(1)
    if stream:
        # Live-Ausgabe UND mitschneiden (z. B. um Binding-Warnungen zu erkennen).
        proc = subprocess.Popen(
            ["sbx"] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        lines = []
        for line in proc.stdout:
            print(line, end="")
            lines.append(line)
        proc.wait()
        return proc.returncode, "".join(lines)
    proc = subprocess.run(
        ["sbx"] + args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out.strip()


def exec_sandbox(name, cmd):
    return run_sbx(["exec", name, "bash", "-c", cmd])


def blocked_requests(name):
    code, out = run_sbx(["policy", "log", name])
    if code != 0:
        info(f"  sbx policy log {name}:")
        print("         " + (out or "(Fehler beim Aufruf)"))
        return code
    lines = out.splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == "Blocked requests:")
    except StopIteration:
        info(f"  sbx policy log {name}: keine Blocked requests")
        return code
    try:
        end = next(i for i, l in enumerate(lines) if l.strip() == "Allowed requests:")
    except StopIteration:
        end = len(lines)
    blocked = [l for l in lines[start + 2:end] if l.strip()]
    if not blocked:
        info(f"  sbx policy log {name}: keine Blocked requests")
        return code
    info(f"  sbx policy log {name} (Blocked requests):")
    print("         " + "\n         ".join(lines[start:start + 2] + blocked))
    return code


def dump_policy_log(name):
    """Kompletten `sbx policy log` ausgeben (Diagnose bei Proxy-/Injection-Fehlern).

    Anders als blocked_requests() wird nicht nur der Blocked-Abschnitt gezeigt:
    fuer die Credential-Injection sind die PROXY-Spalte (forward vs.
    transparent/forward-bypass) und die Injection-Entscheidung relevant.
    """
    code, out = run_sbx(["policy", "log", name])
    info(f"  sbx policy log {name} (vollstaendig):")
    if code != 0 or not out.strip():
        print("         " + (out or "(kein Output / Fehler beim Aufruf)"))
        return
    for line in out.splitlines():
        print("         " + line)


def _so_doc_version():
    for rel in SO_DOC_FILES:
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as f:
            m = re.search(r"api\.stackexchange\.com/(\d+\.\d+)", f.read())
        if m:
            return m.group(1), path
    return None, None


def check_stackoverflow_api_update():
    """Vergleicht die im Kit dokumentierte Stack Exchange API-Version mit dem
    offiziellen Change-Log. Schlaegt fehl, wenn der Change-Log eine neuere
    Version ausweist (Doku-Dateien muessen aktualisiert werden)."""
    documented, doc_path = _so_doc_version()
    if not documented:
        fail("stackoverflow API version (nicht in Doku-Datei gefunden)")
        return
    try:
        try:
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(SO_CHANGE_LOG_URL, timeout=30, context=ctx) as resp:
                html = resp.read().decode("utf-8", "replace")
        except Exception:
            ctx = ssl._create_unverified_context()
            with urllib.request.urlopen(SO_CHANGE_LOG_URL, timeout=30, context=ctx) as resp:
                html = resp.read().decode("utf-8", "replace")
    except Exception as e:
        fail("stackoverflow API version (Change-Log nicht abrufbar)", str(e))
        return
    versions = SO_CHANGE_LOG_RE.findall(html)
    if not versions:
        fail("stackoverflow API version (keine Versionen im Change-Log)", html[:200])
        return
    newest = versions[0]

    def key(v):
        return tuple(int(x) for x in v.split("."))

    if key(newest) > key(documented):
        fail(
            f"stackoverflow API update available (dokumentiert {documented}, Change-Log {newest})",
            f"Aktualisiere {os.path.relpath(doc_path, ROOT)} (Endpoint-Referenz + api_revision)",
        )
    else:
        pass_(f"stackoverflow API version up-to-date (v{documented})")


def _sbx_doc_version(rel=None):
    path = os.path.join(ROOT, rel or SBX_DOC_FILES[0])
    if not os.path.isfile(path):
        return None, None
    with open(path, encoding="utf-8") as f:
        head = f.read(600)
    m = re.search(r"v(\d+\.\d+\.\d+)-Release-Binary", head)
    if not m:
        m = re.search(r"\*\*v(\d+\.\d+\.\d+)\*\*", head)
    return (m.group(1), path) if m else (None, path)


def check_sbx_doc_update(installed_ver=""):
    """Vergleicht die im Kit dokumentierte sbx-CLI-Version (sbx-cli.md-Header) in allen
    drei Kit-Kopien mit dem gepinnten SBX_VERSION (validate.yml) und stellt sicher, dass
    die Kopien identisch sind. Schlaegt fehl bei Abweichung — die Doku muss den Pin
    spiegeln und wird per regenerate-sbx-doc.py neu erzeugt (Default liest denselben Pin).
    Kein GitHub-API-Zugriff: Source of Truth ist der lokale Pin.

    Zusaetzlich wird die installierte CLI-Version (sofern ermittelbar) gegen den Pin
    geprueft — eine aeltere installierte sbx erzeugt nur eine Warnung (kein FAIL), da
    dieser Check offline ist und den Host-Stand nicht erzwingen soll."""
    pin_version = _sbx_pin_version()
    if not pin_version:
        fail("sbx CLI version (SBX_VERSION nicht in validate.yml gefunden)")
        return
    blobs = {}
    ok = True
    for rel in SBX_DOC_FILES:
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            fail(f"sbx CLI doc copy missing: {rel}", "cp der regenerierten sbx-cli.md")
            ok = False
            continue
        documented, _ = _sbx_doc_version(rel)
        if not documented:
            fail(f"sbx CLI version (nicht in {rel} gefunden)")
            ok = False
            continue
        with open(path, encoding="utf-8") as f:
            blobs[rel] = f.read()
        if documented != pin_version:
            fail(
                f"sbx CLI version mismatch ({rel}: v{documented}, Pin v{pin_version})",
                f"Neuerzeugen: python local-test/regenerate-sbx-doc.py v{pin_version}",
            )
            ok = False
    if len(blobs) == len(SBX_DOC_FILES) and len(set(blobs.values())) > 1:
        fail(
            "sbx CLI doc drift (Kopien nicht identisch)",
            "python local-test/regenerate-sbx-doc.py (syncet alle Kopien)",
        )
        ok = False
    if ok:
        pass_(f"sbx CLI version up-to-date (v{pin_version}, {len(SBX_DOC_FILES)} Kopien)")

    inst = re.search(r"v?(\d+)\.(\d+)\.(\d+)", installed_ver or "")
    if inst and tuple(int(x) for x in inst.groups()) < tuple(int(x) for x in pin_version.split(".")):
        warn(
            f"sbx CLI outdated (installiert v{'.'.join(inst.groups())}, Pin v{pin_version})",
            "Updaten: winget upgrade -h Docker.sbx",
        )


def _sbx_pin_version():
    path = os.path.join(ROOT, SBX_VALIDATE_YML)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        content = f.read()
    m = re.search(r"SBX_VERSION:\s*v(\d+\.\d+\.\d+)", content)
    return m.group(1) if m else None


def check_install_scripts_sync():
    """Dokumentierte Reihenfolge: files/home/ wird VOR setup.install in die Sandbox
    kopiert → die Install-Skripte werden aus den files/home-Kopien ausgefuehrt.
    Diese Pruefung stellt sicher, dass die Kopien in allen Kits identisch sind (die
    Dateien sind das Editiertarget, kein separates Kanonik-Verzeichnis)."""
    for file_a, file_b, *rest in INSTALL_SCRIPT_PAIRS:
        src = os.path.join(ROOT, file_a)
        for rel in (file_b, *rest):
            dst = os.path.join(ROOT, rel)
            if not os.path.isfile(src):
                fail(f"install script missing: {file_a}")
                continue
            if not os.path.isfile(dst):
                fail(f"install script copy missing: {rel}",
                     f"Kopiere die Datei nach {rel}")
                continue
            with open(src, encoding="utf-8") as f:
                a = f.read()
            with open(dst, encoding="utf-8") as f:
                b = f.read()
            if a != b:
                fail(
                    f"install script drift: {rel} != {file_a}",
                    "Edit all files identically (or copy one to the other)",
                )
            else:
                pass_(f"install script synced ({file_a})")


def _http_get(url):
    """Text eines HTTP-GET mit TLS-Fallback abrufen (kein API-Key noetig)."""
    try:
        try:
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(url, timeout=30, context=ctx) as resp:
                return resp.read().decode("utf-8", "replace")
        except Exception:
            ctx = ssl._create_unverified_context()
            with urllib.request.urlopen(url, timeout=30, context=ctx) as resp:
                return resp.read().decode("utf-8", "replace")
    except Exception as e:
        raise RuntimeError(str(e))


def _version_key(v):
    return tuple(int(x) for x in v.split("."))


def _version_newer(a, b):
    """True, wenn a > b (semver-artig, Teilkomponenten-Vergleich bis max Tiefe)."""
    ka, kb = _version_key(a), _version_key(b)
    for x, y in zip(ka, kb):
        if x != y:
            return x > y
    return len(ka) > len(kb)


def _template_workflow_version():
    """`TEMPLATE_VERSION` aus validate.yml/e2e.yml (Renovate-managed) — muss mit der
    TEMPLATE_VERSION-Konstante dieses Scripts uebereinstimmen (Drift-Check)."""
    for rel in TEMPLATE_CFG_FILES:
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as f:
            content = f.read()
        m = TEMPLATE_VERSION_RE.search(content)
        if m:
            return m.group(1)
    return None


def _mammouth_base_image_version():
    """opencode-docker-Basis-Tag im Mammouth-Dockerfile (Mirror der TEMPLATE_VERSION-Konstante)."""
    return _dockerfile_base_version(MAMMOUTH_DOCKERFILE, MAMMOUTH_BASE_IMAGE_RE)


def _dockerfile_base_version(rel_path, regex):
    """Basis-Template-Version aus der `ARG BASE_IMAGE=...`-Zeile eines Tooling-Dockerfiles."""
    path = os.path.join(ROOT, rel_path)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        m = regex.search(f.read())
    return m.group("v") if m else None


def _opencode_base_image_version():
    """opencode-docker-Basis-Tag im OpenCode-Tooling-Dockerfile (Mirror der TEMPLATE_VERSION-Konstante)."""
    return _dockerfile_base_version(OPENCODE_DOCKERFILE, OPENCODE_BASE_IMAGE_RE)


def _claude_base_image_version():
    """claude-code-docker-Basis-Tag im Claude-Tooling-Dockerfile (Mirror der TEMPLATE_VERSION-Konstante)."""
    return _dockerfile_base_version(CLAUDE_DOCKERFILE, CLAUDE_BASE_IMAGE_RE)


def _template_image(agent):
    """Template-Image fuer einen Agent.
    - opencode: eigenes Tooling-Image (Issue #137), Tag per `OPENCODE_IMAGE_TAG` (default `local`).
    - claude: eigenes Tooling-Image (Issue #137), Tag per `CLAUDE_IMAGE_TAG` (default `local`).
    None bei kind:sandbox (Mammouth pinnt im spec-Image)."""
    if agent == "opencode":
        tag = os.environ.get("OPENCODE_IMAGE_TAG") or "local"
        return f"docker.io/{OPENCODE_IMAGE_NAMESPACE}/{OPENCODE_IMAGE_NAME}:{tag}"
    if agent == "claude":
        tag = os.environ.get("CLAUDE_IMAGE_TAG") or "local"
        return f"docker.io/{CLAUDE_IMAGE_NAMESPACE}/{CLAUDE_IMAGE_NAME}:{tag}"
    fam = AGENT_TEMPLATES.get(agent)
    if not fam:
        return None
    return f"docker/sandbox-templates:{fam}-{TEMPLATE_VERSION}"


KIT_KIND_RE = re.compile(r"^kind:\s*(?P<v>\S+)", re.M)


def _kit_kind(kit_dir):
    """`kind` (mixin|sandbox) aus der spec.yaml eines Kits.
    Sandbox-Kits werden bei `sbx create`/`sbx run` als erstes positionales Argument
    uebergeben; `--kit` ist fuer Sandbox-Kits deprecated (sbx >= 0.42, gilt nur fuer Mixin-Kits)."""
    path = os.path.join(kit_dir, "spec.yaml")
    if not os.path.isfile(path):
        return "mixin"
    with open(path, encoding="utf-8") as f:
        m = KIT_KIND_RE.search(f.read())
    return m.group("v") if m else "mixin"


def _mammouth_cli_pin_version():
    """Mammouth-CLI-Pin aus dem Dockerfile (ARG MAMMOUTH_VERSION) — treibt den Image-Tag."""
    return _dockerfile_base_version(MAMMOUTH_DOCKERFILE, MAMMOUTH_VERSION_RE)


def _template_latest_per_family():
    """Neueste Versions-Tags pro Familie (opencode-docker / claude-code-docker)
    von der Docker-Hub-API, inkl. Pagination."""
    tags = []
    url = DOCKER_HUB_TEMPLATES_URL
    for _ in range(10):
        body = _http_get(url)
        data = json.loads(body)
        tags.extend(data.get("results", []))
        nxt = data.get("next")
        if not nxt:
            break
        url = nxt
    latest = {}
    for t in tags:
        m = TEMPLATE_TAG_RE.match(t.get("name", ""))
        if not m:
            continue
        fam, v = m.group("fam"), m.group("v")
        if fam not in latest or _version_newer(v, latest[fam]):
            latest[fam] = v
    return latest


def check_image_dockerfiles_sync():
    """opencode-agent/opencode/Dockerfile und opencode-agent/claude/Dockerfile muessen funktional
    identisch sein (gemeinsame Tooling-Schritte) — Unterschied nur in der ARG BASE_IMAGE-Zeile
    und den Kopf-Kommentaren. Kommentar-/Leerzeilen werden ignoriert."""
    base = os.path.join(ROOT, OPENCODE_DOCKERFILE)
    other = os.path.join(ROOT, CLAUDE_DOCKERFILE)
    if not os.path.isfile(base) or not os.path.isfile(other):
        fail("image dockerfiles (opencode-agent/{opencode,claude}/Dockerfile fehlt)")
        return

    def normalize(path):
        out = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                if s.startswith("ARG BASE_IMAGE="):
                    s = "ARG BASE_IMAGE=<base>"
                out.append(s)
        return "\n".join(out)

    if normalize(base) != normalize(other):
        fail(
            "image dockerfiles drift (opencode-agent/opencode/Dockerfile != opencode-agent/claude/Dockerfile)",
            "Beide Dateien funktional identisch halten — nur ARG BASE_IMAGE + Kopf-Kommentare duerfen abweichen",
        )
    else:
        pass_("image dockerfiles in sync (opencode-agent/opencode/Dockerfile == opencode-agent/claude/Dockerfile, ausser ARG BASE_IMAGE)")


def check_template_update():
    """Vergleicht den expliziten Template-Pin der lokalen Tests (TEMPLATE_VERSION-Konstante dieses
    Scripts — gilt fuer beide Kits: opencode-docker fuer OpenCode+Mammouth, claude-code-docker
    fuer Claude Home) mit .github/workflows/validate.yml/e2e.yml, dem Mammouth-spec-Image und
    den Docker-Hub-Tags von docker/sandbox-templates. Warnt (gelb), wenn ein neuerer Versions-Tag
    (opencode-docker ODER claude-code-docker) existiert als der Pin — der Check soll bei einem Update
    nur hinweisen, nicht fehlschlagen. Fehlschlag nur bei echten Fehlern: Pin nicht gefunden, Tags
    nicht abrufbar, Drift (Konstante != validate.yml/e2e.yml bzw. Mammouth-Dockerfile-Base), oder ein
    Pin-Tag ist nicht auf Docker Hub publiziert."""
    pin = TEMPLATE_VERSION
    wf_ver = _template_workflow_version()
    if wf_ver is None:
        fail("template version (TEMPLATE_VERSION nicht in validate.yml/e2e.yml gefunden)")
        return
    if wf_ver != pin:
        fail(
            f"template version (TEMPLATE_VERSION-Konstante v{pin} != validate.yml/e2e.yml v{wf_ver})",
            f"TEMPLATE_VERSION in .github/workflows/validate.yml + e2e.yml auf v{pin} setzen"
            f" (Pin der lokalen Tests ist die Konstante in {os.path.relpath(__file__, ROOT)})",
        )
        return
    mam_ver = _mammouth_base_image_version()
    if not mam_ver:
        fail("template version (mammouth-agent/Dockerfile BASE_IMAGE nicht gepinnt)",
             f"ARG BASE_IMAGE in {MAMMOUTH_DOCKERFILE} auf docker/sandbox-templates:opencode-docker-{pin} setzen")
        return
    if mam_ver != pin:
        fail(
            f"template version (Mammouth Dockerfile BASE_IMAGE v{mam_ver} != Pin v{pin})",
            f"ARG BASE_IMAGE in {MAMMOUTH_DOCKERFILE} auf docker/sandbox-templates:opencode-docker-{pin} anheben"
            f" (Pin: TEMPLATE_VERSION-Konstante in local-test-kits.py + validate.yml/e2e.yml)",
        )
        return
    oc_ver = _opencode_base_image_version()
    if not oc_ver:
        fail("template version (opencode-agent/opencode/Dockerfile BASE_IMAGE nicht gepinnt)",
             f"ARG BASE_IMAGE in {OPENCODE_DOCKERFILE} auf docker/sandbox-templates:opencode-docker-{pin} setzen")
        return
    if oc_ver != pin:
        fail(
            f"template version (opencode Dockerfile BASE_IMAGE v{oc_ver} != Pin v{pin})",
            f"ARG BASE_IMAGE in {OPENCODE_DOCKERFILE} auf docker/sandbox-templates:opencode-docker-{pin} anheben"
            f" (Pin: TEMPLATE_VERSION-Konstante in local-test-kits.py + validate.yml/e2e.yml)",
        )
        return
    cc_ver = _claude_base_image_version()
    if not cc_ver:
        fail("template version (opencode-agent/claude/Dockerfile BASE_IMAGE nicht gepinnt)",
             f"ARG BASE_IMAGE in {CLAUDE_DOCKERFILE} auf docker/sandbox-templates:claude-code-docker-{pin} setzen")
        return
    if cc_ver != pin:
        fail(
            f"template version (claude Dockerfile BASE_IMAGE v{cc_ver} != Pin v{pin})",
            f"ARG BASE_IMAGE in {CLAUDE_DOCKERFILE} auf docker/sandbox-templates:claude-code-docker-{pin} anheben"
            f" (Pin: TEMPLATE_VERSION-Konstante in local-test-kits.py + validate.yml/e2e.yml)",
        )
        return
    try:
        latest = _template_latest_per_family()
    except Exception as e:
        fail("template version (Docker-Hub-Tags nicht abrufbar)", str(e))
        return
    updates = []
    problems = []
    for fam in ("opencode-docker", "claude-code-docker"):
        latest_ver = latest.get(fam)
        if not latest_ver:
            problems.append(f"{fam}: kein Versions-Tag auf Docker Hub")
        elif _version_newer(latest_ver, pin):
            updates.append(f"{fam}: neuerer Tag v{latest_ver} > Pin v{pin}")
        elif latest_ver != pin:
            problems.append(f"{fam}: Pin-Tag {fam}-{pin} nicht publiziert (letzter Tag v{latest_ver})")
    if updates:
        warn(
            f"template version update available (Pin v{pin}, Docker Hub: {'; '.join(updates)})",
            f"Optional: TEMPLATE_VERSION-Konstante in local-test-kits.py + .github/workflows/*.yml erhoehen"
            f" (Renovate), Mammouth-spec-Image + Start-Commands/README/AGENTS --template-Pins synchronisieren",
        )
    for p in problems:
        fail(f"template version (Pin v{pin}, Docker Hub: {p})")
    if not updates and not problems:
        pass_(f"template version up-to-date (Pin v{pin}: opencode-docker + claude-code-docker)")


def check_mammouth_cli_update():
    """Vergleicht die gepinnte Mammouth-CLI-Version (ARG MAMMOUTH_VERSION im Dockerfile —
    das Image backt exakt diese Version) mit der latest GitHub-Release-Version (mammouth-ai/code).
    Warnt (gelb), wenn ein neueres Release existiert — der
    Check soll bei einem Update nur hinweisen, nicht fehlschlagen. Fehlschlag nur bei
    echten Fehlern (Pin nicht gefunden, Release nicht abrufbar)."""
    pin = _mammouth_cli_pin_version()
    if not pin:
        fail(f"mammouth CLI version (Pin nicht als ARG MAMMOUTH_VERSION in {MAMMOUTH_DOCKERFILE} gefunden)")
        return
    try:
        body = _http_get(MAMMOUTH_LATEST_URL)
        data = json.loads(body)
        latest = str(data.get("tag_name", "")).lstrip("v")
    except Exception as e:
        fail("mammouth CLI version (GitHub latest Release nicht abrufbar)", str(e))
        return
    if not latest:
        fail("mammouth CLI version (kein tag_name im GitHub latest Release)")
        return
    if _version_newer(latest, pin):
        warn(
            f"mammouth CLI update available (Pin v{pin}, latest v{latest})",
            f"Optional: ARG MAMMOUTH_VERSION={latest} in {MAMMOUTH_DOCKERFILE} setzen "
            f"(gebackene Version im Image = Pin)",
        )
    else:
        pass_(f"mammouth CLI version up-to-date (Pin v{pin}, latest v{latest})")


def _vibe_dockerfile_pin():
    path = os.path.join(ROOT, VIBE_DOCKERFILE)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        m = VIBE_VERSION_RE.search(f.read())
    return m.group("v") if m else None


def _vibe_spec_image_tag():
    path = os.path.join(ROOT, VIBE_SPEC_FILE)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        m = VIBE_IMAGE_TAG_RE.search(f.read())
    return m.group("v") if m else None


def _vibe_base_image_version():
    path = os.path.join(ROOT, VIBE_DOCKERFILE)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        m = VIBE_BASE_IMAGE_RE.search(f.read())
    return m.group("v") if m else None


def check_vibe_cli_update():
    """Vergleicht den Vibe-Pin (ARG VIBE_VERSION im Dockerfile — das Image installiert
    exakt diese Version) mit der latest PyPI-Version (mistral-vibe) und prueft, dass die
    spec.yaml dasselbe Image-Tag referenziert sowie das shell-Basis-Image der
    TEMPLATE_VERSION entspricht. Warnt (gelb) bei neuerer PyPI-Version."""
    pin = _vibe_dockerfile_pin()
    if not pin:
        fail("mistral-vibe version (VIBE_VERSION nicht in mistral-vibe-agent/Dockerfile gefunden)")
        return
    image_tag = _vibe_spec_image_tag()
    if not image_tag:
        fail("mistral-vibe version (Image-Tag nicht in mistral-vibe-agent/spec.yaml gefunden)")
        return
    if image_tag != pin:
        fail(
            f"mistral-vibe version (spec-Image-Tag v{image_tag} != Dockerfile-Pin v{pin})",
            f"image in {VIBE_SPEC_FILE} auf domboeckli/sbx-mistral-vibe:{pin} setzen",
        )
        return
    base = _vibe_base_image_version()
    if base is None:
        fail("mistral-vibe base image (shell-Basis-Image nicht in mistral-vibe-agent/Dockerfile gefunden)")
        return
    if base != TEMPLATE_VERSION:
        fail(
            f"mistral-vibe base image (shell-{base} != TEMPLATE_VERSION v{TEMPLATE_VERSION})",
            f"ARG BASE_IMAGE in {VIBE_DOCKERFILE} auf docker/sandbox-templates:shell-docker-{TEMPLATE_VERSION} setzen",
        )
        return
    try:
        data = json.loads(_http_get(VIBE_PYPI_URL))
        latest = str(data["info"]["version"])
    except Exception as e:
        fail("mistral-vibe version (PyPI latest nicht abrufbar)", str(e))
        return
    if _version_newer(latest, pin):
        warn(
            f"mistral-vibe update available (Pin v{pin}, PyPI latest v{latest})",
            f"Optional: ARG VIBE_VERSION in {VIBE_DOCKERFILE} + image-Tag in {VIBE_SPEC_FILE} auf "
            f"v{latest} heben, Image neu publizieren (build-and-publish-mistral-vibe-image.yml)",
        )
    else:
        pass_(f"mistral-vibe version up-to-date (Pin v{pin}, PyPI latest v{latest})")


def main():
    enable_ansi()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("agent", nargs="?", choices=["all", "opencode", "claude", "mammouth", "mistral-vibe"],
                        default="all", help="Zu testendes Kit (default: all)")
    parser.add_argument("--keep", action="store_true", help="Sandboxes nach dem Test behalten")
    parser.add_argument("--ci", action="store_true",
                        help="CI-Modus: Fake-API-Keys, kein realer mammouth-/mistral-API-Call")
    parser.add_argument("--validate-only", action="store_true",
                        help="Nur Kit-Validierung, keine Sandbox-Szenarien (default: Sandboxes werden gestartet)")
    parser.add_argument("--workspace", default=None,
                        help="Workspace-Pfad fuer die Sandbox-Szenarien "
                             "(default: $WORKSPACE_DIR oder Repo-Root)")
    args = parser.parse_args()
    ci = args.ci
    agent = args.agent
    # Default = Repo-Root (nicht cwd): so mountet das Szenario unabhaengig vom
    # Aufrufverzeichnis das Kit-Repo. `--workspace`/`$WORKSPACE_DIR` uebersteuern.
    workspace = os.path.abspath(
        args.workspace or os.environ.get("WORKSPACE_DIR") or ROOT)
    if not os.path.isdir(workspace):
        sys.exit(f"Workspace nicht gefunden: {workspace}")

    print()
    _, sbx_ver = run_sbx(["version"])
    if not sbx_ver:
        _, sbx_ver = run_sbx(["--version"])
    info(f"sbx version: {sbx_ver or 'UNKNOWN'}")

    print()
    info("==> Kit-Validierung")
    info("  --> validate: " + os.path.join(ROOT, "opencode-agent"))
    code, _ = run_sbx(["kit", "validate", os.path.join(ROOT, "opencode-agent")], stream=True)
    pass_("sbx kit validate (opencode-agent)") if code == 0 else fail("sbx kit validate (opencode-agent)")
    info("  --> validate: " + os.path.join(ROOT, "mammouth-agent"))
    code, _ = run_sbx(["kit", "validate", os.path.join(ROOT, "mammouth-agent")], stream=True)
    pass_("sbx kit validate (mammouth-agent)") if code == 0 else fail("sbx kit validate (mammouth-agent)")
    info("  --> validate: " + os.path.join(ROOT, "mistral-vibe-agent"))
    code, _ = run_sbx(["kit", "validate", os.path.join(ROOT, "mistral-vibe-agent")], stream=True)
    pass_("sbx kit validate (mistral-vibe-agent)") if code == 0 else fail("sbx kit validate (mistral-vibe-agent)")

    if args.validate_only:
        print()
        info("==> Stack Exchange API Update-Check")
        check_stackoverflow_api_update()
        print()
        info("==> sbx CLI Update-Check (Offline-Referenz)")
        info(f"  installierte sbx-CLI: {sbx_ver or 'UNBEKANNT'}")
        check_sbx_doc_update(sbx_ver)
        print()
        info("==> Install-Skripte (Single Source of Truth) sync check")
        check_install_scripts_sync()
        print()
        info("==> Tooling-Image Dockerfiles sync check")
        check_image_dockerfiles_sync()
        print()
        info("==> Sandbox-Template-Version Update-Check (Docker Hub)")
        check_template_update()
        print()
        info("==> Mammouth-CLI Version Update-Check (GitHub Release)")
        check_mammouth_cli_update()
        print()
        info("==> Mistral-Vibe Version Update-Check (PyPI + Image-Tag + Basis-Template)")
        check_vibe_cli_update()
        print()
        if not failed:
            print(_color("32", f"VALIDIERUNG OK ({len(passed)} Checks)"))
            sys.exit(0)
        print(_color("31", f"VALIDIERUNG FEHLGESCHLAGEN: {len(failed)} Check(s)"))
        for f in failed:
            print("  - " + _color("31", f))
        sys.exit(1)

    print()
    info("==> Secrets (global)")
    _, secret_out = run_sbx(["secret", "ls"])
    for line in secret_out.splitlines():
        print("      " + line)

    # Nur Secrets prüfen, die ein ausgewähltes Szenario (Kit) tatsächlich benötigt —
    # Fehlermeldungen nennen das betroffene Kit/Szenario.
    if agent == "all":
        selected = set(SCENARIO_SECRETS)
    elif agent == "claude":
        selected = {"claude"}
    else:
        selected = {agent}
    for sname in SECRET_ORDER:
        if not any(sname in SCENARIO_SECRETS[sc] for sc in selected):
            continue
        ok = re.search(rf"^\(global\)\s+service\s+{sname}\s+\(stored\)$", secret_out, re.M)
        if ok:
            pass_(f"secret: {sname}")
        else:
            needers = sorted(sc for sc in selected if sname in SCENARIO_SECRETS[sc])
            kits = " / ".join(f"{sc} (Kit: {SCENARIO_KIT[sc]})" for sc in needers)
            fail(f"secret: {sname} — fehlt, benötigt von {kits}")

    tools_cmd = (
        'for t in "ctx7:ctx7 --version" "gh:gh auth status" "java:java -version" '
        '"javac:javac -version" "mvn:mvn -version" "docker:docker version" '
        '"kubectl:kubectl version --client" "jq:jq --version" "node:node --version" '
        '"npm:npm --version" "kafka:kafka-topics.sh --version"; do '
        'name="${t%%:*}"; cmd="${t#*:}"; if $cmd >/dev/null 2>&1; then echo "TOOL-OK:$name"; '
        'else echo "TOOL-FAIL:$name"; fi; done'
    )

    scenarios = [
        {
            "name": "kit-test-opencode",
            "agent": "opencode",
            "kit": os.path.join(ROOT, "opencode-agent"),
            "model": "deepseek/deepseek-flash",
            "config": 'grep -q "deepseek/deepseek-flash" ~/.config/opencode/opencode.jsonc && grep -q "mcp-gateway_analyze_calls" ~/.config/opencode/opencode.jsonc && ! grep -q "host.docker.internal:64342" ~/.config/opencode/opencode.jsonc && echo CONFIG-OK || { echo "MODEL=$(jq -r .model ~/.config/opencode/opencode.jsonc 2>/dev/null || echo UNKNOWN)"; echo "GW=$(grep -c mcp-gateway_analyze_calls ~/.config/opencode/opencode.jsonc 2>/dev/null || echo 0)"; echo "DIRECT=$(grep -c host.docker.internal:64342 ~/.config/opencode/opencode.jsonc 2>/dev/null || echo 0)"; exit 1; }',
        },
        {
            "name": "kit-test-claude",
            "agent": "claude",
            "kit": os.path.join(ROOT, "opencode-agent"),
            "model": "claude-sonnet-4-6",
            "config": 'grep -q "claude-sonnet-4-6" ~/.claude/settings.json && grep -q "mcp__mcp-gateway__" ~/.claude/settings.json && grep -q "intellij-run-config-guard.sh" /etc/claude-code/managed-settings.json && echo CONFIG-OK || { echo "MODEL=$(jq -r .model ~/.claude/settings.json 2>/dev/null || echo UNKNOWN)"; echo "KIT_FILE=$(jq -r .model ~/.claude/settings.kit.json 2>/dev/null || echo MISSING)"; echo "GUARD=$(grep -c intellij-run-config-guard.sh /etc/claude-code/managed-settings.json 2>/dev/null || echo 0)"; exit 1; }',
        },
        {
            "name": "kit-test-mammouth",
            "agent": "mammouth",
            "kit": os.path.join(ROOT, "mammouth-agent"),
            "model": "deepseek/deepseek-flash",
            "config": 'grep -q "deepseek/deepseek-flash" ~/.config/mammouth/opencode.jsonc && grep -q "mcp-gateway_analyze_calls" ~/.config/mammouth/opencode.jsonc && ! grep -q "host.docker.internal:64342" ~/.config/mammouth/opencode.jsonc && echo CONFIG-OK || { echo "MODEL=$(jq -r .model ~/.config/mammouth/opencode.jsonc 2>/dev/null || echo UNKNOWN)"; echo "GW=$(grep -c mcp-gateway_analyze_calls ~/.config/mammouth/opencode.jsonc 2>/dev/null || echo 0)"; echo "DIRECT=$(grep -c host.docker.internal:64342 ~/.config/mammouth/opencode.jsonc 2>/dev/null || echo 0)"; exit 1; }',
            "run_checks": True,
            "checks_tool": "mammouth",
        },
        {
            "name": "kit-test-mistral-vibe",
            "agent": "mistral-vibe",
            "kit": os.path.join(ROOT, "mistral-vibe-agent"),
            "model": "mistral-vibe",
            "config_label": "vibe config (mcp-gateway + read-only guard)",
            "config": 'test -f ~/.vibe/config.toml && grep -q "mcp-gateway.docker.internal" ~/.vibe/config.toml && grep -q "Bearer proxy-managed" ~/.vibe/config.toml && grep -q "mcp-gateway-readonly-guard" ~/.vibe/hooks.toml && test -f ~/.config/sandbox-kit/vibe-mcp-guard.py && echo CONFIG-OK || { echo "CONFIG=$(grep -c mcp-gateway.docker.internal ~/.vibe/config.toml 2>/dev/null || echo 0)"; echo "HOOKS=$(grep -c mcp-gateway-readonly-guard ~/.vibe/hooks.toml 2>/dev/null || echo 0)"; echo "GUARD=$(test -f ~/.config/sandbox-kit/vibe-mcp-guard.py && echo 1 || echo 0)"; exit 1; }',
            "run_checks": True,
            "checks_tool": "vibe",
        },
    ]

    if agent != "all":
        scenarios = [s for s in scenarios if s["agent"] == agent or agent in s.get("tags", [])]
        if not scenarios:
            parser.error(f"Unbekanntes Kit: {agent}")

    for s in scenarios:
        print()
        info(f"=== {s['name']}  (agent={s['agent']}, kit={s['kit']})")

        def sfail(msg, detail=""):
            fail(f"[{s['name']}] {msg}", detail)

        failed_before = len(failed)

        run_sbx(["rm", s["name"], "-f"])

        ws = workspace
        info(f"  Sandbox erzeugen (Workspace: {ws}) ...")
        # Tooling-Images (Issue #137, Tooling vorgebacken):
        #   - opencode: docker.io/domboeckli/sbx-opencode-tooling:<tag> (OPENCODE_IMAGE_TAG, default `local`)
        #   - claude:   docker.io/domboeckli/sbx-claude-tooling:<tag>   (CLAUDE_IMAGE_TAG, default `local`)
        #   - mammouth: docker.io/domboeckli/sbx-mammouth:<tag>         (MAMMOUTH_IMAGE_TAG, default `local`)
        #   - mistral-vibe: docker.io/domboeckli/sbx-mistral-vibe:<tag> (VIBE_IMAGE_TAG, default `local`)
        #     alle via `--template` (Mixin) bzw. `--kit-arg imageTag` (sandbox-Kits).
        template_fam = AGENT_TEMPLATES.get(s["agent"])
        template_image = _template_image(s["agent"]) if template_fam else None
        if template_fam and not template_image:
            sfail("template pin (TEMPLATE_VERSION-Konstante fehlt)")
            continue
        if _kit_kind(s["kit"]) == "sandbox":
            # Sandbox-Kit (kind:sandbox) definiert den Agenten selbst → Kit als erstes
            # positionales Argument; kein Agent-Name, kein --kit (deprecated fuer Sandbox-Kits).
            create_cmd = ["create", "--name", s["name"], s["kit"], ws]
        else:
            create_cmd = ["create", "--name", s["name"], s["agent"], ws, "--kit", s["kit"]]
        # Mistral-Vibe-Image-Tag per --kit-arg an das Kit uebergeben:
        #   - lokal (Host): `local` = zuletzt lokal gebauter/pushter Stand
        #     (IntelliJ-Run-Config `build-and-publish-mistral-vibe-image`).
        #   - CI/e2e: VIBE_IMAGE_TAG = Feature-Tag (`<pin>-<branch>.<timestamp>`),
        #     damit der e2e genau diesen Branch-Build testet.
        if s["agent"] == "mistral-vibe":
            vibe_tag = os.environ.get("VIBE_IMAGE_TAG") or "local"
            create_cmd += ["--kit-arg", f"imageTag={vibe_tag}"]
            info(f"  Vibe-Image-Tag (--kit-arg imageTag): {vibe_tag}")
        if s["agent"] == "mammouth":
            mam_tag = os.environ.get("MAMMOUTH_IMAGE_TAG") or "local"
            create_cmd += ["--kit-arg", f"imageTag={mam_tag}"]
            info(f"  Mammouth-Image-Tag (--kit-arg imageTag): {mam_tag}")
        # Host-Shared-Skills-Store NICHT mounten: die Sandbox bleibt ausserhalb der
        # geteilten Trust-Boundary; die Kit-Skills kommen aus dboeckli/ai-agent-skills
        # (install-tooling-user.sh), nicht vom Host.
        if template_image:
            create_cmd += ["--template", template_image]
            info(f"  Template gepinnt: {template_image}")
        create_cmd += ["--skills=off"]
        # IntelliJ MCP via sbx MCP Gateway (Issue #57): `--static-mcp idea` nur setzen, wenn der Server auf dem
        # Host registriert ist — sonst schlägt `sbx create` fehl (jeder static-mcp-Name muss registriert sein).
        # CI hat kein `idea` registriert → Sandbox ohne static-mcp; der Config-Check prüft dann nur die Whitelist,
        # der Gateway-Weg wird lokal mit registriertem `idea` getestet.
        c_mcp, out_mcp = run_sbx(["mcp", "ls"])
        if c_mcp == 0 and re.search(r"^\s*idea\s+", out_mcp, re.M):
            create_cmd += ["--static-mcp", "idea"]
            info("  IntelliJ MCP: idea registriert → --static-mcp idea")
        else:
            print("  " + _color("33", "  [SKIP] --static-mcp idea — 'idea' nicht auf dem Host registriert "
                                      "(sbx mcp add idea --url http://localhost:64615/stream --skip-ssrf-check)"))
        info("  setup.install laeuft jetzt (npm-CLIs, apt, JDK, Maven, Docker CLI, Compose, "
             "kubectl, Helm v3/v4, Kafka, Skills). Mit vorgebackenem Image (opencode) in Sekunden; "
             "sonst mehrere Minuten ohne Zwischenausgabe (sbx buffert die Install-Ausgabe bei "
             "gepipetem stdout).")
        code, create_out = run_sbx(create_cmd, stream=True)
        if code != 0:
            sfail("sandbox create")
            blocked_requests(s["name"])
            run_sbx(["rm", s["name"], "-f"])
            continue
        if "no binding authorizes" in create_out:
            sfail(
                "credential binding ('no binding authorizes this service')",
                "Kit-deklarierte Services brauchen ein Credential-Binding in "
                "~/.config/sbx/credentials.yaml (siehe .github/workflows/e2e.yml); "
                "sonst wird der echte Key nicht injiziert (nur der Sentinel gesetzt).",
            )

        ready = False
        for _ in range(30):
            c2, _ = exec_sandbox(s["name"], "echo ok")
            if c2 == 0:
                ready = True
                break
            time.sleep(10)
        pass_("sandbox ready") if ready else sfail("sandbox ready")
        if not ready:
            blocked_requests(s["name"])
            run_sbx(["rm", s["name"], "-f"])
            continue

        c2, out = exec_sandbox(s["name"], tools_cmd)
        ok_tools = set(re.findall(r"TOOL-OK:(\w+)", out))
        missing_tools = []
        for t in ("ctx7", "gh", "java", "javac", "mvn", "docker", "kubectl", "jq", "node", "npm", "kafka"):
            if t in ok_tools:
                pass_(f"tool: {t}")
            else:
                missing_tools.append(t)
                sfail(f"tool: {t}", out)
        if missing_tools:
            # Fail-open (install-tooling.sh): die Sandbox startet trotz Tool-Fehler —
            # Ursache steht im Install-Log (=== <tool> FAILED (exit N) === + Tool-Output).
            c3, logtail = exec_sandbox(s["name"], "tail -n 60 /var/log/sbx-kit-install.log 2>/dev/null")
            if c3 == 0 and logtail:
                print("         " + _color("31", "--- install log tail (fehlende Tools) ---"))
                for line in logtail.splitlines():
                    print("         " + _color("33", line))

        c2, out = exec_sandbox(s["name"], "gh auth status >/dev/null 2>&1 && gh api user >/dev/null 2>&1 && echo GHAPI-OK")
        if c2 == 0 and "GHAPI-OK" in out:
            pass_("gh api (authenticated call)")
        elif ci:
            print("  " + _color("33", "[SKIP] gh api (authenticated call) — expected: fake token in CI, "
                                     "kein authentifizierter gh-API-Call"))
        else:
            sfail("gh api (authenticated call)", out)

        if s["config"]:
            config_label = s.get("config_label", f"default model in config ({s['model']})")
            c2, out = exec_sandbox(s["name"], s["config"])
            if c2 == 0 and "CONFIG-OK" in out:
                pass_(config_label)
            else:
                sfail(config_label, out)

        mcp_cmd = (
            'code=""; '
            'for port in 64615 64342; do '
            'for host in host.docker.internal 127.0.0.1 localhost; do '
            'code=$(curl -s -o /dev/null -w "%{http_code}" -m 3 "http://$host:$port/sse" 2>/dev/null); '
            '[ "$code" = "200" ] || [ "$code" = "206" ] && break 2; code=""; '
            'done; done; '
            'if [ "$code" = "200" ] || [ "$code" = "206" ]; then echo MCP-OK; else echo MCP-FAIL; fi'
        )
        c2, out = exec_sandbox(s["name"], mcp_cmd)
        if c2 == 0 and "MCP-OK" in out:
            pass_("intellij-mcp connection (via sbx exec)")
        elif ci:
            print("  " + _color("33", "[SKIP] intellij-mcp connection (via sbx exec) — expected: "
                                     "IntelliJ MCP muss auf dem Host laufen (nicht im CI)"))
        else:
            sfail("intellij-mcp connection (via sbx exec)",
                 "IntelliJ MCP muss auf dem Host laufen (127.0.0.1/localhost/host.docker.internal:64615 "
                 "(IDEA 2026.2.2) bzw. Legacy :64342)")

        skills_cmd = (
            "for sk in camel-matrix cc-best-practices project-references skill-best-practices; do "
            "skills ls -g | grep -q \"$sk\" || echo \"MISSING:$sk\"; done; echo SKILLS-DONE"
        )
        c2, out = exec_sandbox(s["name"], skills_cmd)
        if c2 == 0 and "MISSING" not in out:
            pass_("skills installed (camel-matrix/cc-best-practices/project-references/skill-best-practices)")
        else:
            sfail("skills installed (camel-matrix/cc-best-practices/project-references/skill-best-practices)", out)

        ctx7_env_cmd = 'echo "CONTEXT7_API_KEY=${CONTEXT7_API_KEY:-<unset>}"'
        c2, out = exec_sandbox(s["name"], ctx7_env_cmd)
        if c2 == 0 and "CONTEXT7_API_KEY=proxy-managed" in out:
            pass_("context7 proxy env wiring (CONTEXT7_API_KEY=proxy-managed)")
        else:
            sfail("context7 proxy env wiring (CONTEXT7_API_KEY=proxy-managed)", out)

        openrouter_env_cmd = 'echo "OPENROUTER_API_KEY=${OPENROUTER_API_KEY:-<unset>}"'
        c2, out = exec_sandbox(s["name"], openrouter_env_cmd)
        if s["agent"] == "opencode":
            if c2 == 0 and "OPENROUTER_API_KEY=proxy-managed" in out:
                pass_("openrouter proxy env wiring (OPENROUTER_API_KEY=proxy-managed)")
            else:
                sfail("openrouter proxy env wiring (OPENROUTER_API_KEY=proxy-managed)", out)
        else:
            if c2 == 0 and "OPENROUTER_API_KEY=<unset>" in out:
                pass_("openrouter not wired (only opencode template declares openrouter)")
            else:
                sfail("openrouter not wired (only opencode template declares openrouter)", out)

        # Built-in google service: the opencode template injects the placeholder
        # under GOOGLE_GENERATIVE_AI_API_KEY (the env name the AI SDK's google
        # provider reads by default) — assert that for the opencode template,
        # while claude/mammouth must have it unset.
        google_env_cmd = 'echo "GOOGLE_GENERATIVE_AI_API_KEY=${GOOGLE_GENERATIVE_AI_API_KEY:-<unset>}"'
        c2, out = exec_sandbox(s["name"], google_env_cmd)
        if s["agent"] == "opencode":
            if c2 == 0 and "GOOGLE_GENERATIVE_AI_API_KEY=proxy-managed" in out:
                pass_("google proxy env wiring (GOOGLE_GENERATIVE_AI_API_KEY=proxy-managed)")
            else:
                sfail("google proxy env wiring (GOOGLE_GENERATIVE_AI_API_KEY=proxy-managed)", out)
        else:
            if c2 == 0 and "GOOGLE_GENERATIVE_AI_API_KEY=<unset>" in out:
                pass_("google not wired (only opencode template declares google)")
            else:
                sfail("google not wired (only opencode template declares google)", out)

        # Kit-deklarierter zai-Service: vom opencode-agent-Kit (OpenCode + Claude)
        # und vom mistral-vibe-agent-Kit deklariert; mammouth nicht.
        # (mistral-vibe hat eigene zai-Checks im Kit-spezifischen Block.)
        if s["agent"] != "mistral-vibe":
            zai_env_cmd = 'echo "ZAI_API_KEY=${ZAI_API_KEY:-<unset>}"'
            c2, out = exec_sandbox(s["name"], zai_env_cmd)
            if s["agent"] in ("opencode", "claude"):
                if c2 == 0 and "ZAI_API_KEY=proxy-managed" in out:
                    pass_("zai proxy env wiring (ZAI_API_KEY=proxy-managed)")
                else:
                    sfail("zai proxy env wiring (ZAI_API_KEY=proxy-managed)", out)
            else:
                if c2 == 0 and "ZAI_API_KEY=<unset>" in out:
                    pass_("zai not wired (only opencode-agent/mistral-vibe-agent declare zai)")
                else:
                    sfail("zai not wired (only opencode-agent/mistral-vibe-agent declare zai)", out)

        # Kit-deklarierter stackoverflow-Service (beide Kits) → Platzhalter in allen 3 Szenarien
        stackoverflow_env_cmd = 'echo "STACKOVERFLOW_API_KEY=${STACKOVERFLOW_API_KEY:-<unset>}"'
        c2, out = exec_sandbox(s["name"], stackoverflow_env_cmd)
        if c2 == 0 and "STACKOVERFLOW_API_KEY=proxy-managed" in out:
            pass_("stackoverflow proxy env wiring (STACKOVERFLOW_API_KEY=proxy-managed)")
        else:
            sfail("stackoverflow proxy env wiring (STACKOVERFLOW_API_KEY=proxy-managed)", out)

        # Offline API-Doku aus files/home/ → ~/stackexchange-api.md + -detail.md
        stackoverflow_doc_cmd = 'test -f ~/stackexchange-api.md -a -f ~/stackexchange-api-detail.md && echo "stackexchange api docs present"'
        c2, out = exec_sandbox(s["name"], stackoverflow_doc_cmd)
        if c2 == 0 and "stackexchange api docs present" in out:
            pass_("stackoverflow offline docs (~/stackexchange-api.md + -detail.md)")
        else:
            sfail("stackoverflow offline docs (~/stackexchange-api.md + -detail.md)", out)

        # Kit-deklarierter cloudsmith-Service (beide Kits) → Platzhalter in allen 3 Szenarien
        cloudsmith_env_cmd = 'echo "CLOUDSMITH_API_KEY=${CLOUDSMITH_API_KEY:-<unset>}"'
        c2, out = exec_sandbox(s["name"], cloudsmith_env_cmd)
        if c2 == 0 and "CLOUDSMITH_API_KEY=proxy-managed" in out:
            pass_("cloudsmith proxy env wiring (CLOUDSMITH_API_KEY=proxy-managed)")
        else:
            sfail("cloudsmith proxy env wiring (CLOUDSMITH_API_KEY=proxy-managed)", out)

        # Kit-deklarierter sonarcloud-Service (alle 3 Kits) → Platzhalter in allen Szenarien
        sonar_env_cmd = 'echo "SONAR_TOKEN=${SONAR_TOKEN:-<unset>}"'
        c2, out = exec_sandbox(s["name"], sonar_env_cmd)
        if c2 == 0 and "SONAR_TOKEN=proxy-managed" in out:
            pass_("sonarcloud proxy env wiring (SONAR_TOKEN=proxy-managed)")
        else:
            sfail("sonarcloud proxy env wiring (SONAR_TOKEN=proxy-managed)", out)

        # SonarCloud-Erreichbarkeit (Web-API): 200 (Token gültig) oder 401 (kein/ungültiger
        # Token) = erreichbar; 403 (Netzwerk-Policy blockt) oder 000 (Timeout) = FAIL.
        # CI nutzt einen fake Key → nur Sentinel-Wiring, kein Netz-Call.
        if not ci:
            sonar_net_cmd = ('curl -s -o /dev/null -w "HTTP:%{http_code}" '
                             'https://sonarcloud.io/api/authentication/validate '
                             '-H "Authorization: Bearer $SONAR_TOKEN"')
            c2, out = exec_sandbox(s["name"], sonar_net_cmd)
            if c2 == 0 and ("HTTP:200" in out or "HTTP:401" in out):
                pass_("sonarcloud reachable (Web-API, HTTP 200/401)")
            else:
                sfail("sonarcloud reachable (Web-API, HTTP 200/401)", out)
        else:
            print("  " + _color("33", "[SKIP] sonarcloud reachability (Web-API) — CI (fake key)"))

        # Kit-deklarierter github-maven-Service (beide Kits) → settings.xml mit
        # <proxies> (Routing durch gateway.docker.internal:3128) + github-Server mit
        # ${env.GITHUB_MAVEN_TOKEN} + Sentinel-Env-Variable + Proxy-CA in JDK-cacerts.
        # Der Proxy injiziert den PAT als 'Authorization: Bearer' (scheme:basic wird nicht unterstützt);
        # Maven muss durch den Proxy routen (<proxies>), damit die Injection greift.
        maven_cmd = (
            'test -f ~/.m2/settings.xml && grep -q "<id>github</id>" ~/.m2/settings.xml '
            '&& grep -q "gateway.docker.internal" ~/.m2/settings.xml '
            '&& grep -q "\\${env.GITHUB_MAVEN_TOKEN}" ~/.m2/settings.xml '
            '&& keytool -list -keystore "$JAVA_HOME/lib/security/cacerts" -storepass changeit 2>/dev/null | grep -q proxy-ca '
            '&& echo "GITHUB_MAVEN_TOKEN=${GITHUB_MAVEN_TOKEN:-<unset>}"'
        )
        c2, out = exec_sandbox(s["name"], maven_cmd)
        if c2 == 0 and "GITHUB_MAVEN_TOKEN=proxy-managed" in out:
            pass_("github-maven maven wiring (settings.xml proxies+server, proxy-ca in cacerts, GITHUB_MAVEN_TOKEN=proxy-managed)")
        else:
            sfail("github-maven maven wiring (settings.xml proxies+server, proxy-ca in cacerts, GITHUB_MAVEN_TOKEN=proxy-managed)", out)

        if s.get("run_checks"):
            checks_tool = s.get("checks_tool", "mammouth")
            c2, out = exec_sandbox(s["name"], "bash ~/.config/sandbox-kit/run-checks.sh")
            m = {k: v for k, v in re.findall(r"([A-Za-z0-9_/-]+):(OK|FAIL)", out)}
            if m.get(checks_tool) == "OK":
                pass_(f"startup check: {checks_tool}")
            else:
                sfail(f"startup check: {checks_tool}", f"status={m.get(checks_tool)}")

            if s["agent"] == "mammouth":
                # Installierte Mammouth-CLI-Version gegen den Pin im Dockerfile (ARG MAMMOUTH_VERSION)
                # pruefen — das Image backt exakt diese Version.
                mammouth_ver_cmd = "mammouth --version 2>/dev/null | grep -oE '[0-9]+(\\.[0-9]+)+' | head -1"
                c2, out = exec_sandbox(s["name"], mammouth_ver_cmd)
                installed = out.strip().splitlines()[0].strip() if c2 == 0 and out.strip() else ""
                pin = _mammouth_cli_pin_version()
                if installed and pin and installed == pin:
                    pass_(f"mammouth CLI version installed (v{installed} == Pin v{pin})")
                elif installed and pin and _version_newer(installed, pin):
                    sfail(f"mammouth CLI version installed (v{installed} > Pin v{pin}, Pin nicht angewendet?)",
                          f"ARG MAMMOUTH_VERSION in {MAMMOUTH_DOCKERFILE} pruefen (Pin {pin}); Image neu bauen")
                elif installed and pin:
                    sfail(f"mammouth CLI version installed (v{installed} != Pin v{pin})",
                          f"ARG MAMMOUTH_VERSION in {MAMMOUTH_DOCKERFILE} erhoehen oder Image neu bauen")
                else:
                    sfail("mammouth CLI version installed (nicht ermittelbar)", f"out={out!r}")

                if ci:
                    env_cmd = 'echo "MAMMOUTH_API_KEY=${MAMMOUTH_API_KEY:-<unset>}"'
                    c2, out = exec_sandbox(s["name"], env_cmd)
                    if c2 == 0 and "MAMMOUTH_API_KEY=proxy-managed" in out:
                        pass_("mammouth proxy env wiring (fake-key CI)")
                    else:
                        sfail("mammouth proxy env wiring (fake-key CI)", out)
                else:
                    net_cmd = 'curl -s https://api.mammouth.ai/v1/models -H "Authorization: Bearer $MAMMOUTH_API_KEY" | head -c 120'
                    c2, out = exec_sandbox(s["name"], net_cmd)
                    if c2 == 0 and ('"object":"list"' in out or '"id"' in out):
                        pass_("api.mammouth.ai e2e (Proxy-Key)")
                    else:
                        sfail("api.mammouth.ai e2e (Proxy-Key)", out)

            elif s["agent"] == "mistral-vibe":
                # Installierte Vibe-Version gegen den Dockerfile-Pin pruefen — das Image
                # bakt exakt diese Version (ARG VIBE_VERSION).
                vibe_ver_cmd = "vibe --version 2>/dev/null | grep -oE '[0-9]+(\\.[0-9]+)+' | head -1"
                c2, out = exec_sandbox(s["name"], vibe_ver_cmd)
                installed = out.strip().splitlines()[0].strip() if c2 == 0 and out.strip() else ""
                pin = _vibe_dockerfile_pin()
                if installed and pin and installed == pin:
                    pass_(f"mistral-vibe version installed (v{installed} == Pin v{pin})")
                elif installed and pin and _version_newer(installed, pin):
                    sfail(f"mistral-vibe version installed (v{installed} > Pin v{pin}, Pin nicht angewendet?)",
                          f"ARG VIBE_VERSION in {VIBE_DOCKERFILE} pruefen; Image neu publizieren")
                elif installed and pin:
                    sfail(f"mistral-vibe version installed (v{installed} != Pin v{pin})",
                          f"Pin in {VIBE_DOCKERFILE} erhoehen oder Image neu bauen")
                else:
                    sfail("mistral-vibe version installed (nicht ermittelbar)", f"out={out!r}")

                # proxyManaged: true -> Runtime setzt MISTRAL_API_KEY auf den Sentinel.
                # (Ohne proxyManaged ist die Variable unset; Vibe braucht sie, um
                # ueberhaupt zu authentifizieren.)
                env_cmd = 'echo "MISTRAL_API_KEY=${MISTRAL_API_KEY:-<unset>}"'
                c2, out = exec_sandbox(s["name"], env_cmd)
                if c2 == 0 and "MISTRAL_API_KEY=proxy-managed" in out:
                    pass_("mistral proxy env wiring (MISTRAL_API_KEY=proxy-managed)")
                else:
                    sfail("mistral proxy env wiring (MISTRAL_API_KEY=proxy-managed)", out)

                # Runtime-Contract (spec-v2 §9.5): SBX_CRED_<SERVICE>_MODE zeigt, wie die
                # Credential aufgeloest wurde (apikey/oauth/none). 'none' => Binding/Secret
                # fehlt -> der Proxy injiziert nichts (Vibe: 401 'Invalid API key').
                cred_cmd = 'echo "SBX_CRED_MISTRAL_MODE=${SBX_CRED_MISTRAL_MODE:-<unset>}"'
                c2, out = exec_sandbox(s["name"], cred_cmd)
                if c2 == 0 and "SBX_CRED_MISTRAL_MODE=apikey" in out:
                    pass_("mistral credential resolved (SBX_CRED_MISTRAL_MODE=apikey)")
                else:
                    sfail("mistral credential resolved (SBX_CRED_MISTRAL_MODE=apikey)",
                          out + " — mistral-Secret/Binding pruefen (~/.config/sbx/credentials.yaml bzw. "
                                "%APPDATA%\\sbx\\credentials.yaml: mistral.apiKey.domains=[api.mistral.ai])")

                # Wie mammouth: lokal den echten Proxy-Key-Pfad testen (nicht nur die
                # Sentinel-Verdrahtung). Ein 401 'Invalid API key' bedeutet, dass der
                # Proxy den Sentinel nicht ersetzt hat — dann `sbx policy log` (PROXY-
                # Spalte: forward vs. transparent/forward-bypass) ausgeben.
                if ci:
                    print("  " + _color("33", "[SKIP] api.mistral.ai e2e (Proxy-Key) — fake key in CI, "
                                             "nur Sentinel-Wiring geprueft"))
                else:
                    net_cmd = ('curl -s -o /tmp/mistral-models.json -w "HTTP:%{http_code}" '
                               'https://api.mistral.ai/v1/models -H "Authorization: Bearer $MISTRAL_API_KEY"; '
                               'echo; head -c 200 /tmp/mistral-models.json')
                    c2, out = exec_sandbox(s["name"], net_cmd)
                    if c2 == 0 and "HTTP:200" in out and '"id"' in out:
                        pass_("api.mistral.ai e2e (Proxy-Key)")
                    else:
                        sfail("api.mistral.ai e2e (Proxy-Key)", out)
                        dump_policy_log(s["name"])

                # Z.AI (GLM-5.3-Flash, Default-Modell): Sentinel + Credential-Aufloesung.
                # Kein Real-API-Call (eigenes Z.AI-Guthaben) — nur Verdrahtung.
                zai_env_cmd = 'echo "ZAI_API_KEY=${ZAI_API_KEY:-<unset>}"'
                c2, out = exec_sandbox(s["name"], zai_env_cmd)
                if c2 == 0 and "ZAI_API_KEY=proxy-managed" in out:
                    pass_("zai proxy env wiring (ZAI_API_KEY=proxy-managed)")
                else:
                    sfail("zai proxy env wiring (ZAI_API_KEY=proxy-managed)", out)

                zai_cred_cmd = 'echo "SBX_CRED_ZAI_MODE=${SBX_CRED_ZAI_MODE:-<unset>}"'
                c2, out = exec_sandbox(s["name"], zai_cred_cmd)
                if c2 == 0 and "SBX_CRED_ZAI_MODE=apikey" in out:
                    pass_("zai credential resolved (SBX_CRED_ZAI_MODE=apikey)")
                else:
                    sfail("zai credential resolved (SBX_CRED_ZAI_MODE=apikey)",
                          out + " — zai-Secret/Binding pruefen (credentials.yaml: zai.apiKey.domains=[api.z.ai])")

        if not args.keep:
            if len(failed) > failed_before:
                blocked_requests(s["name"])
            info("  Sandbox entfernen ...")
            run_sbx(["rm", s["name"], "-f"])

    print()
    if not failed:
        print(_color("32", f"ALLE TESTS BESTANDEN ({len(passed)} Checks)"))
        sys.exit(0)
    print(_color("31", f"FEHLGESCHLAGEN: {len(failed)} Check(s)"))
    for f in failed:
        print("  - " + _color("31", f))
    sys.exit(1)


if __name__ == "__main__":
    main()
