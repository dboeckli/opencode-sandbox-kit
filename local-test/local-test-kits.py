#!/usr/bin/env python3
"""local-test-kits.py - automatischer Test der 5 Agent-Szenarien des opencode-sandbox-kit.

Laeuft auf Windows (PowerShell/CMD) und Linux/macOS, sofern `sbx` und ein
Docker-Daemon verfuegbar sind (auf Windows der nativen Docker Desktop, NICHT aus WSL).

Szenarien:
  1. OpenCode v3 + opencode-v3-agent   (sbx create ./opencode-v3-agent/ — v3-Workload)
  2. Claude v3   + claude-v3-agent     (sbx create ./claude-v3-agent/ — v3-Workload)
  3. Mammouth    + mammouth-agent      (sbx create ./mammouth-agent/ — Sandbox-Kit, erstes positionales Argument)
  4. Mistral Vibe + mistral-vibe-agent  (sbx create ./mistral-vibe-agent/ — Sandbox-Kit, eigenes gepinntes Image)
  5. Pi          + pi-agent            (sbx create ./pi-agent/ — v3-Workload, Kit-Spec v3)

Voraussetzungen:
  - Docker laeuft, `sbx` CLI im PATH
  - Globale Secrets registriert: github, github-maven, anthropic, mammouth, deepseek, mistral, context7, openrouter, google, stackoverflow, cloudsmith, sonarcloud, codeberg
    (sbx secret set github-maven / sbx secret set mammouth / sbx secret set mistral / sbx secret set context7 / sbx secret set openrouter / sbx secret set google / sbx secret set stackoverflow / sbx secret set cloudsmith / sbx secret set sonarcloud / sbx secret set codeberg — seit v0.38 ohne `-g`)
  - Mammouth-Szenario: v3-Workload; `MAMMOUTH_IMAGE_TAG` (default `local`) referenziert das publizierte Image
  - Mistral-Vibe-Szenario (lokal): das Image `<IMAGE_PREFIX>/sbx-mistral-vibe:local` ist publiziert
    (IntelliJ-Run-Config `build-and-publish-mistral-vibe-image` bzw. `python local-test/build-and-publish-mistral-vibe-image.py`);
    CI/e2e uebergibt stattdessen den Feature-Tag per `VIBE_IMAGE_TAG`
  - Pi-Szenario: v3-Workload, sbx >= v0.45; lokal wird das Kit-Verzeichnis gebaut (oder
    PI_IMAGE_TAG fuer ein publiziertes Image gesetzt)

Verwendung:
  python local-test-kits.py                 # alle 5 Szenarien testen (default: all)
  python local-test-kits.py opencode-v3     # nur OpenCode v3 testen
  python local-test-kits.py claude-v3       # nur Claude v3 testen
  python local-test-kits.py mammouth        # nur Mammouth testen
  python local-test-kits.py mistral-vibe    # nur Mistral Vibe testen
  python local-test-kits.py pi              # nur Pi testen
  python local-test-kits.py --help          # alle Optionen anzeigen
  python local-test-kits.py --validate-only # nur Kit-Validierung, keine Sandbox/Sandbox-Szenarien (v3 via Kit-Builder)

Optionen:
  {all,opencode-v3,claude-v3,mammouth,mistral-vibe,pi}  Zu testendes Kit (default: all)
  -h, --help                      Diese Hilfe anzeigen
  --keep                          Sandboxes nach dem Test behalten
  --ci                            CI-Modus: Fake-API-Keys, kein realer
                                  mammouth-/mistral-API-Call
  --validate-only                 Nur Kit-Validierung (sbx kit validate; v3-Kits
                                  via Kit-Builder), keine Secrets-/Sandbox-Checks
                                  (default: Sandboxes werden gestartet)
  --skip-v3-builder               v3-Kits nur per Offline-Probe pruefen (schnell,
                                  z. B. CI-Szenario-Laeufe)
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
import urllib.error
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
SO_DOC_FILES = ("mammouth-agent/files/home/stackexchange-api.md",
                "mistral-vibe-agent/files/home/stackexchange-api.md",
                "pi-agent/files/home/stackexchange-api.md",
                "opencode-v3-agent/files/home/stackexchange-api.md",
                "claude-v3-agent/files/home/stackexchange-api.md")

# sbx CLI: die Offline-Referenz (sbx-cli.md) wird aus der Release-Binary generiert
# (local-test/regenerate-sbx-doc.py). Die dokumentierte Version steht im Header der Datei;
# Update-Check vergleicht sie mit dem gepinnten SBX_VERSION aus .github/workflows/validate.yml
# (Source of Truth, Renovate managed). Identische Kopien in allen Kit-Bundles.
SBX_DOC_FILES = ("mammouth-agent/files/home/sbx-cli.md",
                 "mistral-vibe-agent/files/home/sbx-cli.md",
                 "pi-agent/files/home/sbx-cli.md",
                 "opencode-v3-agent/files/home/sbx-cli.md",
                 "claude-v3-agent/files/home/sbx-cli.md")
SBX_VALIDATE_YML = ".github/workflows/validate.yml"

# Die Install-Skripte liegen als identische Kopien in den files/home/.local/bin-
# Bundles aller Kits. Mammouth/Pi mcp-check.sh weichen bewusst ab (Agent-Config-Pfade
# ~/.pi/agent/mcp.json + pi-CLI im Deep-Probe-Fallback) und ist daher NICHT gepaart. `setup.install` konsumiert sie aus dem Sandbox-Home. Alle
# Kopien muessen identisch bleiben (edit target = eine Kopie, andere per cp syncen;
# Renovate aktualisiert beide gemeinsam).
INSTALL_SCRIPT_PAIRS = (
    ("opencode-v3-agent/files/home/.local/bin/install-tooling.sh",
     "mammouth-agent/files/home/.local/bin/install-tooling.sh"),
    ("opencode-v3-agent/files/home/.local/bin/install-tooling.sh",
     "mistral-vibe-agent/files/home/.local/bin/install-tooling.sh"),
    ("opencode-v3-agent/files/home/.local/bin/install-tooling-user.sh",
     "mammouth-agent/files/home/.local/bin/install-tooling-user.sh"),
    ("opencode-v3-agent/files/home/.local/bin/install-tooling-user.sh",
     "mistral-vibe-agent/files/home/.local/bin/install-tooling-user.sh"),
    ("opencode-v3-agent/files/home/.local/bin/mcp-check.sh",
     "mistral-vibe-agent/files/home/.local/bin/mcp-check.sh"),
    ("opencode-v3-agent/files/home/.local/bin/install-apt-packages.sh",
     "mammouth-agent/files/home/.local/bin/install-apt-packages.sh"),
    ("opencode-v3-agent/files/home/.local/bin/install-apt-packages.sh",
     "mistral-vibe-agent/files/home/.local/bin/install-apt-packages.sh"),
    ("opencode-v3-agent/files/home/.local/bin/install-tooling.sh",
     "pi-agent/files/home/.local/bin/install-tooling.sh"),
    ("opencode-v3-agent/files/home/.local/bin/install-tooling-user.sh",
     "pi-agent/files/home/.local/bin/install-tooling-user.sh"),
    ("opencode-v3-agent/files/home/.local/bin/install-apt-packages.sh",
     "pi-agent/files/home/.local/bin/install-apt-packages.sh"),
    ("pi-agent/files/home/.local/bin/pi-startup-ca.sh",
     "mammouth-agent/files/home/.local/bin/mammouth-startup-ca.sh"),
    ("pi-agent/files/home/.local/bin/pi-startup-maven.sh",
     "mammouth-agent/files/home/.local/bin/mammouth-startup-maven.sh"),
    ("pi-agent/files/home/.local/bin/pi-startup-ca.sh",
     "mistral-vibe-agent/files/home/.local/bin/vibe-startup-ca.sh"),
    ("pi-agent/files/home/.local/bin/pi-startup-maven.sh",
     "mistral-vibe-agent/files/home/.local/bin/vibe-startup-maven.sh"),
    ("opencode-v3-agent/files/home/.local/bin/install-tooling.sh",
     "opencode-v3-agent/files/home/.local/bin/install-tooling.sh"),
    ("opencode-v3-agent/files/home/.local/bin/install-tooling-user.sh",
     "opencode-v3-agent/files/home/.local/bin/install-tooling-user.sh"),
    ("opencode-v3-agent/files/home/.local/bin/install-apt-packages.sh",
     "opencode-v3-agent/files/home/.local/bin/install-apt-packages.sh"),
    ("opencode-v3-agent/files/home/.local/bin/mcp-check.sh",
     "opencode-v3-agent/files/home/.local/bin/mcp-check.sh"),
    ("pi-agent/files/home/.local/bin/pi-startup-ca.sh",
     "opencode-v3-agent/files/home/.local/bin/opencode-startup-ca.sh"),
    ("pi-agent/files/home/.local/bin/pi-startup-maven.sh",
     "opencode-v3-agent/files/home/.local/bin/opencode-startup-maven.sh"),
    ("opencode-v3-agent/files/home/.local/bin/install-tooling.sh",
     "claude-v3-agent/files/home/.local/bin/install-tooling.sh"),
    ("opencode-v3-agent/files/home/.local/bin/install-tooling-user.sh",
     "claude-v3-agent/files/home/.local/bin/install-tooling-user.sh"),
    ("opencode-v3-agent/files/home/.local/bin/install-apt-packages.sh",
     "claude-v3-agent/files/home/.local/bin/install-apt-packages.sh"),
    ("opencode-v3-agent/files/home/.local/bin/mcp-check.sh",
     "claude-v3-agent/files/home/.local/bin/mcp-check.sh"),
    ("pi-agent/files/home/.local/bin/pi-startup-ca.sh",
     "claude-v3-agent/files/home/.local/bin/claude-startup-ca.sh"),
    ("pi-agent/files/home/.local/bin/pi-startup-maven.sh",
     "claude-v3-agent/files/home/.local/bin/claude-startup-maven.sh"),
)

# Workflow-Dateien mit den CLI-Pin-Variablen (Renovate-managed).
WORKFLOW_FILES = (".github/workflows/validate.yml", ".github/workflows/e2e.yml")

# Claude Code v3 (Issue #254, voll migriert): Basis ist die gemeinsame Custom-Workload-Basis
# `docker.io/sbx/shell-docker-image:latest`; die CLI kommt aus npm (`@anthropic-ai/claude-code`,
# Renovate-managed) statt aus dem frueheren `claude-code-docker`-Template. Drift-Check in
# check_claude_v3_cli_version(); Update-Hinweis gegen die npm-latest-Version.
CLAUDE_VERSION = "2.1.319"
CLAUDE_VERSION_RE = re.compile(r"ARG CLAUDE_VERSION=(?P<v>[0-9]+\.[0-9]+\.[0-9]+)")
CLAUDE_WORKFLOW_VAR = "CLAUDE_VERSION"
CLAUDE_NPM_LATEST_URL = "https://registry.npmjs.org/@anthropic-ai%2Fclaude-code/latest"

# Docker-verwaltete Custom-Workload-Basis (Issue #254): `:latest`, nightly, kein Semver-Pin.
# Alle Custom-Workload-Kits (OpenCode v3 / Claude Code v3 / Mammouth / Mistral Vibe / Pi)
# nutzen sie; Renovate
# trackt die jeweilige CLI-Version, nicht die driftende Basis. Node/npm, Python, Go, uv und
# Docker CLI/compose/buildx kommen aus der Basis (nicht mehr separat installiert).
SHELL_BASE_IMAGE_EXPECTED = "docker.io/sbx/shell-docker-image:latest"

# Eigenstaendiger, im Code erwarteter BASE_IMAGE-Wert (ARG BASE_IMAGE=...) eines Kit-Dockerfiles.
BASE_IMAGE_RE = re.compile(r"ARG BASE_IMAGE=(?P<img>\S+)")

# OpenCode-v3 (Issue #254): Custom-Workload-Basis + OpenCode-CLI-Pin (npm `opencode-ai`,
# bewusst 1.x-Linie). Renovate trackt die CLI-Version (nicht die driftende Basis).
OPENCODE_VERSION = "1.19.5"
OPENCODE_VERSION_RE = re.compile(r"ARG OPENCODE_VERSION=(?P<v>[0-9]+\.[0-9]+\.[0-9]+)")
OPENCODE_BASE_IMAGE_EXPECTED = SHELL_BASE_IMAGE_EXPECTED
OPENCODE_WORKFLOW_VAR = "OPENCODE_VERSION"
OPENCODE_NPM_LATEST_URL = "https://registry.npmjs.org/opencode-ai/latest"

# Mammouth (Issue #137/#240): eigenes Image (mammouth-agent/mammouth-agent.dockerfile, v3) — Basis
# shell-docker-image + Kit-Tooling + Mammouth-CLI. MAMMOUTH_VERSION (CLI-Pin) treibt den Image-Tag;
# ARG BASE_IMAGE muss der gemeinsamen Custom-Workload-Basis entsprechen (Issue #254). Update-Check
# des CLI-Pins gegen das latest GitHub-Release (mammouth-ai/code, Tag v<ver>); warnt (gelb).
MAMMOUTH_DOCKERFILE = "mammouth-agent/mammouth-agent.dockerfile"
MAMMOUTH_DESCRIPTOR = "mammouth-agent/mammouth-agent.yaml"
MAMMOUTH_DESCRIPTOR_VERSION_RE = re.compile(r'default:\s*"(?P<v>[0-9]+(?:\.[0-9]+)+)"')
MAMMOUTH_IMAGE_NAMESPACE = os.environ.get("MAMMOUTH_IMAGE_NAMESPACE", "domboeckli")
MAMMOUTH_IMAGE_NAME = os.environ.get("MAMMOUTH_IMAGE_NAME", "sbx-mammouth")
MAMMOUTH_VERSION_RE = re.compile(r"ARG MAMMOUTH_VERSION=(?P<v>[0-9]+(?:\.[0-9]+)+)")
MAMMOUTH_LATEST_URL = "https://api.github.com/repos/mammouth-ai/code/releases/latest"

# Mistral Vibe: Pin im Dockerfile (ARG VIBE_VERSION) — die spec.yaml referenziert das Image
# mit demselben Tag. Update-Check gegen die latest PyPI-Version (mistral-vibe); warnt (gelb)
# bei neuerer Version. Die Basis ist die gemeinsame Custom-Workload-Basis (Issue #254).
VIBE_DOCKERFILE = "mistral-vibe-agent/mistral-vibe-agent.dockerfile"
VIBE_DESCRIPTOR = "mistral-vibe-agent/mistral-vibe-agent.yaml"
VIBE_IMAGE_NAME = os.environ.get("VIBE_IMAGE_NAME", "sbx-mistral-vibe")
VIBE_VERSION_RE = re.compile(r"ARG VIBE_VERSION=(?P<v>[0-9]+(?:\.[0-9]+)+)")
VIBE_DESCRIPTOR_VERSION_RE = re.compile(r'default:\s*"(?P<v>[0-9]+(?:\.[0-9]+)+)"')
VIBE_PYPI_URL = "https://pypi.org/pypi/mistral-vibe/json"

# Pi Coding Agent (Issue #236): v3-Workload, Descriptor pi-agent/pi-agent.yaml
# (args.version.default) + Dockerfile pi-agent/pi-agent.dockerfile (ARG PI_VERSION).
# Beide Pins muessen gleich sein; das Image backt exakt diese Version. Basis ist die
# gemeinsame Custom-Workload-Basis (Issue #254). Update-Check gegen die latest
# npm-Version (@earendil-works/pi-coding-agent); neueres Release = warn.
PI_DESCRIPTOR = "pi-agent/pi-agent.yaml"
PI_DOCKERFILE = "pi-agent/pi-agent.dockerfile"
PI_IMAGE_NAME = os.environ.get("PI_IMAGE_NAME", "sbx-pi-agent")
PI_DESCRIPTOR_VERSION_RE = re.compile(r'default:\s*"(?P<v>[0-9]+(?:\.[0-9]+)+)"')
PI_DOCKERFILE_VERSION_RE = re.compile(r"ARG PI_VERSION=(?P<v>[0-9]+(?:\.[0-9]+)+)")
PI_NPM_URL = "https://registry.npmjs.org/@earendil-works%2Fpi-coding-agent/latest"

# Lokaler Docker-MCP-Server (Issue #165): Pin im Doku-Command (`uvx mcp-server-docker==<v>`,
# docs/mcp/docker-mcp-server.md) und im README; Update-Check gegen die latest PyPI-Version
# (mcp-server-docker), warnt (gelb), Drift zwischen den Dateien = fail.
# Reiner Host-Server (nicht Teil des Sandbox-Images).
DOCKER_MCP_DOC = "docs/mcp/docker-mcp-server.md"
DOCKER_MCP_FILES = (DOCKER_MCP_DOC, "README.md")
DOCKER_MCP_PIN_RE = re.compile(r"mcp-server-docker==(?P<v>[0-9]+(?:\.[0-9]+)+)")
DOCKER_MCP_PYPI_URL = "https://pypi.org/pypi/mcp-server-docker/json"

# Bruno CLI (Issue #257 im spring-6-gateway-Repo): Pin `@usebruno/cli@<v>` in allen drei
# Kit-Specs (setup.install) und in den Tooling-Images (Dockerfile). Der Validate-Check
# prueft die Gleichheit aller Vorkommen und warnt (gelb) bei einer neueren npm-Version —
# der Bump kommt via Renovate-Custom-Manager (.github/renovate.json).
BRUNO_PIN_FILES = [
    "mammouth-agent/mammouth-agent.dockerfile",
    "pi-agent/pi-agent.dockerfile",
    "opencode-v3-agent/opencode-v3-agent.dockerfile",
    "claude-v3-agent/claude-v3-agent.dockerfile",
]
BRUNO_PIN_RE = re.compile(r"@usebruno/cli@(?P<v>[0-9]+(?:\.[0-9]+)+)")
BRUNO_NPM_URL = "https://registry.npmjs.org/@usebruno/cli/latest"

# MCP Inspector CLI (Issue #231): Pin `@modelcontextprotocol/inspector@<v>` in denselben
# Dateien wie der Bruno-Pin (vier Kit-Specs + Tooling-Image-Dockerfiles). Nur die CLI ist
# nutzbar (Web/TUI brauchen Browser bzw. Ports). Drift = fail, neueres npm-Release = warn;
# der Bump kommt via Renovate-Custom-Manager (.github/renovate.json).
INSPECTOR_PIN_FILES = [
    "mammouth-agent/mammouth-agent.dockerfile",
    "pi-agent/pi-agent.dockerfile",
    "opencode-v3-agent/opencode-v3-agent.dockerfile",
    "claude-v3-agent/claude-v3-agent.dockerfile",
]
INSPECTOR_PIN_RE = re.compile(r"@modelcontextprotocol/inspector@(?P<v>[0-9]+(?:\.[0-9]+)+)")
INSPECTOR_NPM_URL = "https://registry.npmjs.org/@modelcontextprotocol/inspector/latest"

# Apache Kafka-Distribution: install-tooling.sh laedt den Tarball von dlcdn
# (haelt nur die aktuellen Releases) mit Fallback auf archive.apache.org (alle
# Releases). Der Validate-Check stellt sicher, dass KAFKA_VER als Tarball
# existiert (dlcdn ODER archive) — faengt einen Renovate-Bump auf eine in Maven
# Central verfuegbare, aber noch nicht als Distro veroeffentlichte Version ab,
# bevor der Image-Build bricht (fail-closed Verify: kafka-topics.sh fehlt -> exit 127).
KAFKA_INSTALL_SCRIPT = "opencode-v3-agent/files/home/.local/bin/install-tooling.sh"
KAFKA_VER_RE = re.compile(r'KAFKA_VER="(?P<v>[0-9]+\.[0-9]+\.[0-9]+)"')
KAFKA_SCALA_VER_RE = re.compile(r'KAFKA_SCALA_VER="(?P<v>[0-9]+\.[0-9]+)"')
KAFKA_CDN_URL = "https://dlcdn.apache.org/kafka/{ver}/kafka_{scala}-{ver}.tgz"
KAFKA_ARCHIVE_URL = "https://archive.apache.org/dist/kafka/{ver}/kafka_{scala}-{ver}.tgz"

OPENCODE_V3_DOCKERFILE = "opencode-v3-agent/opencode-v3-agent.dockerfile"
OPENCODE_V3_DESCRIPTOR = "opencode-v3-agent/opencode-v3-agent.yaml"
OPENCODE_V3_IMAGE_NAME = os.environ.get("OPENCODE_V3_IMAGE_NAME", "sbx-opencode")
CLAUDE_V3_DOCKERFILE = "claude-v3-agent/claude-v3-agent.dockerfile"
CLAUDE_V3_DESCRIPTOR = "claude-v3-agent/claude-v3-agent.yaml"
CLAUDE_V3_IMAGE_NAME = os.environ.get("CLAUDE_V3_IMAGE_NAME", "sbx-claude")
# Zentraler Registry-Umschalter: vollstaendiger Image-Prefix (Registry + Namespace [+ Repo])
# ohne Image-Namen. Default Docker Hub (wie die CI, Repo-Variable `IMAGE_PREFIX`); Cloudsmith
# ist der Ausweich-Registry. Umschalten per Env `IMAGE_PREFIX` (auch in den IntelliJ-Run-Configs
# gesetzt):
#   Docker Hub (Default): docker.io/domboeckli
#   Cloudsmith:           docker.cloudsmith.io/dboeckli/sbx
# Der Image-Name wird jeweils angehaengt: "<IMAGE_PREFIX>/sbx-<name>:<tag>".
DEFAULT_IMAGE_PREFIX = "docker.io/domboeckli"
IMAGE_PREFIX = os.environ.get("IMAGE_PREFIX") or DEFAULT_IMAGE_PREFIX

# Secrets je Szenario: Globale Dienst-Secrets, die das jeweilige Szenario in der Sandbox
# benötigt (Kit-deklarierte Services aus den v3-Deskriptoren credentials[].service).
# Fehlermeldungen nennen das betroffene Kit.
SCENARIO_KIT = {
    "mammouth": "mammouth-agent",
    "mistral-vibe": "mistral-vibe-agent",
    "pi": "pi-agent",
    "opencode-v3": "opencode-v3-agent",
    "claude-v3": "claude-v3-agent",
}
SCENARIO_SECRETS = {
    "mammouth": ("github", "github-maven", "mammouth", "zai", "mistral", "context7", "stackoverflow", "cloudsmith", "sonarcloud", "codeberg"),
    "mistral-vibe": ("github", "github-maven", "mistral", "zai", "context7", "stackoverflow", "cloudsmith", "sonarcloud", "codeberg"),
    "pi": ("github", "github-maven", "deepseek", "zai", "mistral", "openrouter", "google", "context7", "stackoverflow", "cloudsmith", "sonarcloud", "codeberg"),
    "opencode-v3": ("github", "github-maven", "deepseek", "context7", "openrouter", "google", "zai", "mistral", "stackoverflow", "cloudsmith", "sonarcloud", "codeberg"),
    "claude-v3": ("github", "github-maven", "anthropic", "context7", "mistral", "zai", "stackoverflow", "cloudsmith", "sonarcloud", "codeberg"),
}
# Reihenfolge der Checks (Ausgabe stabil halten)
SECRET_ORDER = ("github", "github-maven", "anthropic", "mammouth", "deepseek", "mistral", "zai", "context7", "openrouter",
                "google", "stackoverflow", "cloudsmith", "sonarcloud", "codeberg")


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


def run_sbx_stdout(args):
    """`sbx` starten und stdout/stderr getrennt zurueckgeben.

    `run_sbx()` mischt beide Streams fuer Diagnose-Ausgaben. Seit sbx v0.48 gehen
    Warnungen/Hinweise nach stderr und Ergebnisse nach stdout — strukturierte
    Ausgabe (`--json`, `-q`) darf deshalb nur aus stdout geparst werden.
    """
    if which("sbx") is None:
        print(_color("31", "sbx CLI nicht gefunden (PATH?)"))
        sys.exit(1)
    proc = subprocess.run(
        ["sbx"] + args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, (proc.stdout or "").strip(), (proc.stderr or "").strip()


def run_sbx_json(args):
    """`sbx ... --json` ausfuehren und das geparste Dokument zurueckgeben.

    `None` bedeutet: Aufruf fehlgeschlagen oder Ausgabe ist kein JSON (aeltere
    sbx-Version, Sign-in-Fehler, ...). Aufrufer fallen dann auf den Parser fuer
    die menschlich lesbare Ausgabe zurueck.
    """
    code, out, _err = run_sbx_stdout(list(args) + ["--json"])
    if code != 0 or not out:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


def sbx_names(args):
    """Namen aus `sbx ... -q` als Set, oder `None` wenn der Aufruf scheitert.

    `-q` gibt nur Namen aus (ein Name pro Zeile oder leerzeichengetrennt) und ist
    damit unabhaengig vom Tabellen-Layout. `-q` und `--json` schliessen sich aus.
    """
    code, out, _err = run_sbx_stdout(list(args) + ["-q"])
    if code != 0:
        return None
    return set(out.split())


def exec_sandbox(name, cmd):
    return run_sbx(["exec", name, "bash", "-c", cmd])


def _policy_entry_line(entry):
    if not isinstance(entry, dict):
        return str(entry)
    parts = []
    for key in ("host", "count", "proxy_type", "rule", "reason", "first_seen", "last_seen"):
        value = entry.get(key)
        if value in (None, "", 0, []):
            continue
        parts.append(f"{key}={value}")
    return " ".join(parts) or json.dumps(entry, ensure_ascii=False)


def blocked_requests(name):
    # Seit sbx v0.48: {updated_at, allowed: [...], blocked: [...]}
    data = run_sbx_json(["policy", "log", name])
    if isinstance(data, dict) and isinstance(data.get("blocked"), list):
        blocked = data["blocked"]
        if not blocked:
            info(f"  sbx policy log {name}: keine Blocked requests")
            return 0
        info(f"  sbx policy log {name} (Blocked requests, {len(blocked)}):")
        for entry in blocked:
            print("         " + _policy_entry_line(entry))
        return 0
    # Fallback: menschlich lesbare Tabelle (sbx < v0.48)
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
    info(f"  sbx policy log {name} (vollstaendig):")
    data = run_sbx_json(["policy", "log", name])
    if data is not None:
        for line in json.dumps(data, indent=2, ensure_ascii=False).splitlines():
            print("         " + line)
        return
    code, out = run_sbx(["policy", "log", name])
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
    alle Kit-Kopien mit dem gepinnten SBX_VERSION (validate.yml) und stellt sicher, dass
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


def _http_status(url):
    """HTTP-Statuscode eines HEAD-Requests (TLS-Fallback). None bei Netzwerkfehler.
    Liefert auch 4xx/5xx (HTTPError.code) zurueck, damit Aufrufer 404 vs. OK unterscheiden."""
    def _head(ctx):
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            return resp.status

    try:
        try:
            return _head(ssl.create_default_context())
        except urllib.error.HTTPError as e:
            return e.code
        except Exception:
            try:
                return _head(ssl._create_unverified_context())
            except urllib.error.HTTPError as e:
                return e.code
    except Exception:
        return None


def _version_key(v):
    return tuple(int(x) for x in v.split("."))


def _version_newer(a, b):
    """True, wenn a > b (semver-artig, Teilkomponenten-Vergleich bis max Tiefe)."""
    ka, kb = _version_key(a), _version_key(b)
    for x, y in zip(ka, kb):
        if x != y:
            return x > y
    return len(ka) > len(kb)



def _dockerfile_base_image(rel_path):
    """BASE_IMAGE-Wert (ARG BASE_IMAGE=...) eines Kit-Dockerfiles."""
    path = os.path.join(ROOT, rel_path)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        m = BASE_IMAGE_RE.search(f.read())
    return m.group("img") if m else None


def _dockerfile_base_version(rel_path, regex):
    """Basis-Template-Version aus der `ARG BASE_IMAGE=...`-Zeile eines Tooling-Dockerfiles."""
    path = os.path.join(ROOT, rel_path)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        m = regex.search(f.read())
    return m.group("v") if m else None


KIT_KIND_RE = re.compile(r"^kind:\s*(?P<v>\S+)", re.M)


def _kit_kind(kit_dir):
    """`kind` (mixin|sandbox|workload) eines Kits.
    Sandbox- und v3-Workload-Kits definieren den Agenten selbst und werden bei
    `sbx create`/`sbx run` als erstes positionales Argument uebergeben; `--kit` ist
    fuer sie deprecated (sbx >= 0.42, gilt nur fuer Mixin-Kits).
    v2: <kit>/spec.yaml; v3: <kit>/<basename>.yaml (Descriptor)."""
    path = os.path.join(kit_dir, "spec.yaml")
    if not os.path.isfile(path):
        path = os.path.join(kit_dir, os.path.basename(os.path.normpath(kit_dir)) + ".yaml")
    if not os.path.isfile(path):
        return "mixin"
    with open(path, encoding="utf-8") as f:
        m = KIT_KIND_RE.search(f.read())
    return m.group("v") if m else "mixin"


def _mammouth_cli_pin_version():
    """Mammouth-CLI-Pin aus dem Dockerfile (ARG MAMMOUTH_VERSION) — treibt den Image-Tag."""
    return _dockerfile_base_version(MAMMOUTH_DOCKERFILE, MAMMOUTH_VERSION_RE)



def check_workflow_job_references():
    """e2e.yml-Integritaet: jede `needs`-Referenz muss als Job im selben Workflow existieren und
    jedes lokale `uses: ./.github/workflows/*.yml` muss eine vorhandene Datei sein. Haette den
    CI-Parse-Fehler 'needs: build-and-publish-claude-v3-image ohne Job-Definition' gefunden
    (regex-basiert, keine PyYAML-Abhaengigkeit)."""
    path = os.path.join(ROOT, ".github/workflows/e2e.yml")
    if not os.path.isfile(path):
        fail("workflow references (e2e.yml fehlt)")
        return
    with open(path, encoding="utf-8") as f:
        text = f.read()
    # Top-Level-Job-Keys: zwei Leerzeichen Einzug unter `jobs:` (Superset inkl. on/env-Keys ist ok —
    # entscheidend ist, dass jede needs-Referenz im Set vorkommt).
    jobs = set(re.findall(r"(?m)^  ([a-zA-Z0-9_-]+):\s*(?:#.*)?$", text))
    missing_jobs = set()
    for m in re.finditer(r"(?m)^\s*needs:\s*\[([^\]]+)\]", text):
        for ref in m.group(1).split(","):
            ref = ref.strip()
            if ref and ref not in jobs:
                missing_jobs.add(ref)
    for m in re.finditer(r"(?m)^\s*needs:\s*([a-zA-Z0-9_-]+)\s*$", text):
        if m.group(1) not in jobs:
            missing_jobs.add(m.group(1))
    missing_files = []
    for m in re.finditer(r"(?m)^\s*uses:\s*(\./\.github/[^\s]+)\s*$", text):
        rel = m.group(1)[2:]
        if not os.path.isfile(os.path.join(ROOT, rel)):
            missing_files.append(rel)
    if missing_jobs or missing_files:
        detail = []
        if missing_jobs:
            detail.append("needs ohne Job-Definition: " + ", ".join(sorted(missing_jobs)))
        if missing_files:
            detail.append("uses ohne Workflow-Datei: " + ", ".join(sorted(missing_files)))
        fail("workflow references (e2e.yml)", "; ".join(detail))
        return
    pass_(f"workflow references (e2e.yml: needs/uses aufgeloest, {len(jobs)} Top-Level-Keys)")



def _docker_template_node_major(image):
    """Node-Major-Version aus einem Basis-Template-Image (best-effort via `docker run`).
    None, wenn Docker/Image fehlt oder node nicht ausfuehrbar ist (Check wird uebersprungen)."""
    if which("docker") is None:
        return None
    try:
        insp = subprocess.run(["docker", "image", "inspect", image],
                              capture_output=True, text=True, timeout=60)
        if insp.returncode != 0:
            pull = subprocess.run(["docker", "pull", image],
                                  capture_output=True, text=True, timeout=900)
            if pull.returncode != 0:
                return None
        run = subprocess.run(["docker", "run", "--rm", "--entrypoint", "node", image, "--version"],
                             capture_output=True, text=True, timeout=120)
        if run.returncode != 0:
            return None
        m = re.search(r"v(\d+)\.", (run.stdout or "") + (run.stderr or ""))
        return int(m.group(1)) if m else None
    except Exception:
        return None


def check_template_node_baseline():
    """Warn-Check (Issue #138): liefert die Basis bereits Node >= 24, kann der
    `install-tooling.sh node`-Step (Node-24-Tarball) + der `nodejs.org`-Allowlist-Eintrag entfallen —
    die npm-CLIs (renovate >=43) laufen dann auf dem vom Basis-Image gelieferten Node. Prueft die
    gemeinsame Docker-verwaltete Custom-Workload-Basis `docker.io/sbx/shell-docker-image:latest`
    (OpenCode v3/Claude v3/Mammouth/Vibe/Pi, Issue #254). Best-effort ueber Docker (Image-Pull,
    gecacht); wird uebersprungen, wenn Docker oder das Image nicht verfuegbar ist."""
    images = {"shell-docker-image": SHELL_BASE_IMAGE_EXPECTED}
    if which("docker") is None:
        print("  " + _color("33", "[SKIP] template node baseline — docker nicht im PATH"))
        return
    versions = {name: _docker_template_node_major(image) for name, image in images.items()}
    unknown = [f for f, m in versions.items() if m is None]
    if unknown:
        print("  " + _color("33", f"[SKIP] template node baseline — Image/node nicht verfuegbar: {', '.join(unknown)}"))
        return
    summary = ", ".join(f"{f}: v{m}" for f, m in versions.items())
    if all(m >= 24 for m in versions.values()):
        warn(
            f"template node baseline >= 24 ({summary})",
            "install-tooling.sh node-Step + nodejs.org-Allowlist entfernen (spec.yaml install-Step, "
            "Dockerfile node-Verifikation, renovate.json NODE_VER-customManager, Docs) — "
            "Basis-Template liefert Node 24 nativ",
        )
    else:
        pass_(f"template node baseline < 24 ({summary}) — install-tooling.sh node weiterhin noetig")


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
    descriptor_pin = _pi_pin_from(MAMMOUTH_DESCRIPTOR, MAMMOUTH_DESCRIPTOR_VERSION_RE)
    if not descriptor_pin:
        fail(f"mammouth CLI version (args.version.default nicht in {MAMMOUTH_DESCRIPTOR} gefunden)")
        return
    if descriptor_pin != pin:
        fail(
            f"mammouth CLI version (Descriptor-Pin v{descriptor_pin} != Dockerfile-Pin v{pin})",
            f"args.version.default in {MAMMOUTH_DESCRIPTOR} und ARG MAMMOUTH_VERSION in {MAMMOUTH_DOCKERFILE} angleichen",
        )
        return
    base = _dockerfile_base_image(MAMMOUTH_DOCKERFILE)
    if base != SHELL_BASE_IMAGE_EXPECTED:
        fail(
            f"mammouth base image ({base or 'BASE_IMAGE fehlt'} != {SHELL_BASE_IMAGE_EXPECTED})",
            f"ARG BASE_IMAGE in {MAMMOUTH_DOCKERFILE} auf {SHELL_BASE_IMAGE_EXPECTED} setzen "
            "(gemeinsame Custom-Workload-Basis, Issue #254)",
        )
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


def _vibe_descriptor_pin():
    path = os.path.join(ROOT, VIBE_DESCRIPTOR)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        m = VIBE_DESCRIPTOR_VERSION_RE.search(f.read())
    return m.group("v") if m else None


def check_vibe_cli_update():
    """Vergleicht den Vibe-Pin (ARG VIBE_VERSION im Dockerfile — das Image installiert
    exakt diese Version) mit der latest PyPI-Version (mistral-vibe) und prueft, dass die
    spec.yaml dasselbe Image-Tag referenziert und die Basis die gemeinsame
    Custom-Workload-Basis ist (Issue #254). Warnt (gelb) bei neuerer PyPI-Version."""
    pin = _vibe_dockerfile_pin()
    if not pin:
        fail("mistral-vibe version (VIBE_VERSION nicht in mistral-vibe-agent/mistral-vibe-agent.dockerfile gefunden)")
        return
    descriptor_pin = _vibe_descriptor_pin()
    if not descriptor_pin:
        fail(f"mistral-vibe version (args.version.default nicht in {VIBE_DESCRIPTOR} gefunden)")
        return
    if descriptor_pin != pin:
        fail(
            f"mistral-vibe version (Descriptor-Pin v{descriptor_pin} != Dockerfile-Pin v{pin})",
            f"args.version.default in {VIBE_DESCRIPTOR} und ARG VIBE_VERSION in {VIBE_DOCKERFILE} angleichen",
        )
        return
    base = _dockerfile_base_image(VIBE_DOCKERFILE)
    if base != SHELL_BASE_IMAGE_EXPECTED:
        fail(
            f"mistral-vibe base image ({base or 'BASE_IMAGE fehlt'} != {SHELL_BASE_IMAGE_EXPECTED})",
            f"ARG BASE_IMAGE in {VIBE_DOCKERFILE} auf {SHELL_BASE_IMAGE_EXPECTED} setzen "
            "(gemeinsame Custom-Workload-Basis, Issue #254)",
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
            f"Optional: ARG VIBE_VERSION in {VIBE_DOCKERFILE} + args.version.default in {VIBE_DESCRIPTOR} auf "
            f"v{latest} heben, Image neu publizieren (build-and-publish-mistral-vibe-image.yml)",
        )
    else:
        pass_(f"mistral-vibe version up-to-date (Pin v{pin}, PyPI latest v{latest})")


def _opencode_v3_cli_version():
    """OpenCode-CLI-Pin (ARG OPENCODE_VERSION) aus dem OpenCode-v3-Dockerfile."""
    return _dockerfile_base_version(OPENCODE_V3_DOCKERFILE, OPENCODE_VERSION_RE)


def _opencode_v3_base_image():
    """BASE_IMAGE-Wert (ARG BASE_IMAGE=...) aus dem OpenCode-v3-Dockerfile."""
    return _dockerfile_base_image(OPENCODE_V3_DOCKERFILE)


def _workflow_env_version(env_name, files):
    """Wert einer `NAME: X.Y.Z`-Workflow-Variable aus den uebergebenen YAML-Dateien."""
    regex = re.compile(re.escape(env_name) + r":\s*(?P<v>[0-9]+\.[0-9]+\.[0-9]+)")
    for rel in files:
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as f:
            m = regex.search(f.read())
        if m:
            return m.group("v")
    return None


def check_opencode_v3_cli_version():
    """Prueft den OpenCode-CLI-Pin (1.x) des OpenCode-v3-Workloads:
    - BASE_IMAGE ist die von Docker empfohlene Custom-Workload-Basis
      (`docker.io/sbx/shell-docker-image:latest`, Issue #254)
    - ARG OPENCODE_VERSION == OPENCODE_VERSION-Konstante dieses Scripts
    - OPENCODE_VERSION in validate.yml/e2e.yml == Konstante
    - Update-Hinweis, falls npm (`opencode-ai`) eine neuere stabile 1.x-Version hat."""
    cur = _opencode_v3_cli_version()
    if not cur:
        fail(f"opencode-v3 CLI (ARG OPENCODE_VERSION nicht in {OPENCODE_V3_DOCKERFILE} gefunden)")
        return
    base = _opencode_v3_base_image()
    if base != OPENCODE_BASE_IMAGE_EXPECTED:
        fail(
            f"opencode-v3 base image ({base or 'BASE_IMAGE fehlt'} != {OPENCODE_BASE_IMAGE_EXPECTED})",
            f"ARG BASE_IMAGE in {OPENCODE_V3_DOCKERFILE} auf {OPENCODE_BASE_IMAGE_EXPECTED} setzen "
            "(Docker-empfohlene Custom-Workload-Basis, Issue #254)",
        )
        return
    if cur != OPENCODE_VERSION:
        fail(
            f"opencode-v3 CLI (Dockerfile-Pin {cur} != OPENCODE_VERSION {OPENCODE_VERSION})",
            f"ARG OPENCODE_VERSION in {OPENCODE_V3_DOCKERFILE} auf {OPENCODE_VERSION} setzen",
        )
        return
    wf = _workflow_env_version(OPENCODE_WORKFLOW_VAR, WORKFLOW_FILES)
    if wf is None:
        fail(f"opencode-v3 CLI ({OPENCODE_WORKFLOW_VAR} nicht in validate.yml/e2e.yml gefunden)")
        return
    if wf != cur:
        fail(
            f"opencode-v3 CLI ({OPENCODE_WORKFLOW_VAR} {wf} != OPENCODE_VERSION {cur})",
            f"{OPENCODE_WORKFLOW_VAR} in .github/workflows/validate.yml + e2e.yml auf {cur} setzen",
        )
        return
    try:
        data = json.loads(_http_get(OPENCODE_NPM_LATEST_URL))
        latest = str(data.get("version", ""))
    except Exception as e:
        warn(f"opencode-v3 CLI update check skipped (npm latest nicht abrufbar: {e})")
        pass_(f"opencode-v3 CLI pin up-to-date ({cur}, npm latest unbekannt)")
        return
    latest_major = latest.split(".")[0] if latest else ""
    if latest_major == "1" and _version_newer(latest, cur):
        warn(
            f"opencode-v3 CLI update available (Pin {cur}, npm latest 1.x {latest})",
            f"Optional: OPENCODE_VERSION in {OPENCODE_V3_DOCKERFILE} + local-test-kits.py + "
            f"validate.yml/e2e.yml auf {latest} heben (Renovate, 1.x-Linie)",
        )
    else:
        pass_(f"opencode-v3 CLI pin up-to-date ({cur}; npm latest {latest or 'n/a'}, bewusst 1.x)")


def _claude_v3_cli_version():
    """Claude-Code-CLI-Pin (ARG CLAUDE_VERSION) aus dem Claude-v3-Dockerfile."""
    return _dockerfile_base_version(CLAUDE_V3_DOCKERFILE, CLAUDE_VERSION_RE)


def check_claude_v3_cli_version():
    """Prueft den Claude-Code-CLI-Pin (Issue #254, voll migriert):
    - BASE_IMAGE ist die gemeinsame Docker-verwaltete Custom-Workload-Basis
    - ARG CLAUDE_VERSION == CLAUDE_VERSION-Konstante dieses Scripts
    - CLAUDE_VERSION in validate.yml/e2e.yml == Konstante
    - Update-Hinweis, falls npm (`@anthropic-ai/claude-code`) eine neuere Version hat."""
    cur = _claude_v3_cli_version()
    if not cur:
        fail(f"claude-v3 CLI (ARG CLAUDE_VERSION nicht in {CLAUDE_V3_DOCKERFILE} gefunden)")
        return
    base = _dockerfile_base_image(CLAUDE_V3_DOCKERFILE)
    if base != SHELL_BASE_IMAGE_EXPECTED:
        fail(
            f"claude-v3 base image ({base or 'BASE_IMAGE fehlt'} != {SHELL_BASE_IMAGE_EXPECTED})",
            f"ARG BASE_IMAGE in {CLAUDE_V3_DOCKERFILE} auf {SHELL_BASE_IMAGE_EXPECTED} setzen "
            "(gemeinsame Custom-Workload-Basis, Issue #254)",
        )
        return
    if cur != CLAUDE_VERSION:
        fail(
            f"claude-v3 CLI (Dockerfile-Pin {cur} != CLAUDE_VERSION {CLAUDE_VERSION})",
            f"ARG CLAUDE_VERSION in {CLAUDE_V3_DOCKERFILE} auf {CLAUDE_VERSION} setzen",
        )
        return
    wf = _workflow_env_version(CLAUDE_WORKFLOW_VAR, WORKFLOW_FILES)
    if wf is None:
        fail(f"claude-v3 CLI ({CLAUDE_WORKFLOW_VAR} nicht in validate.yml/e2e.yml gefunden)")
        return
    if wf != cur:
        fail(
            f"claude-v3 CLI ({CLAUDE_WORKFLOW_VAR} {wf} != CLAUDE_VERSION {cur})",
            f"{CLAUDE_WORKFLOW_VAR} in .github/workflows/validate.yml + e2e.yml auf {cur} setzen",
        )
        return
    try:
        data = json.loads(_http_get(CLAUDE_NPM_LATEST_URL))
        latest = str(data.get("version", ""))
    except Exception as e:
        warn(f"claude-v3 CLI update check skipped (npm latest nicht abrufbar: {e})")
        pass_(f"claude-v3 CLI pin up-to-date ({cur}, npm latest unbekannt)")
        return
    if latest and _version_newer(latest, cur):
        warn(
            f"claude-v3 CLI update available (Pin {cur}, npm latest {latest})",
            f"Optional: CLAUDE_VERSION in {CLAUDE_V3_DOCKERFILE} + local-test-kits.py + "
            f"validate.yml/e2e.yml auf {latest} heben (Renovate)",
        )
    else:
        pass_(f"claude-v3 CLI pin up-to-date ({cur}; npm latest {latest or 'n/a'})")


def _pi_pin_from(rel, regex):
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        m = regex.search(f.read())
    return m.group("v") if m else None


def check_pi_cli_update():
    """Vergleicht den Pi-Pin (Descriptor args.version.default) mit dem Dockerfile-Pin
    (ARG PI_VERSION), prueft die gemeinsame Custom-Workload-Basis (Issue #254) und
    warnt (gelb) bei einer neueren npm-Version (@earendil-works/pi-coding-agent)."""
    pin = _pi_pin_from(PI_DESCRIPTOR, PI_DESCRIPTOR_VERSION_RE)
    if not pin:
        fail("pi version (args.version.default nicht in pi-agent/pi-agent.yaml gefunden)")
        return
    dockerfile_pin = _pi_pin_from(PI_DOCKERFILE, PI_DOCKERFILE_VERSION_RE)
    if not dockerfile_pin:
        fail("pi version (ARG PI_VERSION nicht in pi-agent/pi-agent.dockerfile gefunden)")
        return
    if dockerfile_pin != pin:
        fail(
            f"pi version (Dockerfile-Pin v{dockerfile_pin} != Descriptor-Pin v{pin})",
            f"ARG PI_VERSION in {PI_DOCKERFILE} und args.version.default in {PI_DESCRIPTOR} angleichen",
        )
        return
    base = _dockerfile_base_image(PI_DOCKERFILE)
    if base != SHELL_BASE_IMAGE_EXPECTED:
        fail(
            f"pi base image ({base or 'BASE_IMAGE fehlt'} != {SHELL_BASE_IMAGE_EXPECTED})",
            f"ARG BASE_IMAGE in {PI_DOCKERFILE} auf {SHELL_BASE_IMAGE_EXPECTED} setzen "
            "(gemeinsame Custom-Workload-Basis, Issue #254)",
        )
        return
    try:
        data = json.loads(_http_get(PI_NPM_URL))
        latest = str(data["version"])
    except Exception as e:
        fail("pi version (npm latest nicht abrufbar)", str(e))
        return
    if _version_newer(latest, pin):
        warn(
            f"pi update available (Pin v{pin}, npm latest v{latest})",
            f"Optional: args.version.default in {PI_DESCRIPTOR} + ARG PI_VERSION in {PI_DOCKERFILE} "
            f"auf v{latest} heben, Image neu publizieren (build-and-publish-pi-image.yml)",
        )
    else:
        pass_(f"pi version up-to-date (Pin v{pin}, npm latest v{latest})")


def check_pi_mcp_guard():
    """Fuehrt die Unit-Tests der Pi-MCP-Guard-Policy aus (Node type-stripping).
    Die Policy spiegelt die OpenCode-Whitelist; der Test haelt Allow-/Deny-Listen
    und den Run-Config-Guard synchron. Uebersprungen, wenn Node fehlt."""
    if which("node") is None:
        print("  " + _color("33", "[SKIP] pi mcp guard policy — node nicht im PATH"))
        return
    proc = subprocess.run(
        ["node", "--test", "pi-agent/test/mcp-guard-policy.test.ts"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if proc.returncode == 0:
        pass_("pi mcp guard policy tests (node --test)")
    else:
        fail("pi mcp guard policy tests (node --test)", (proc.stdout or "")[-500:] + (proc.stderr or "")[-500:])


def _docker_mcp_pins():
    """Liest den `mcp-server-docker==<v>`-Pin aus allen Doku-/README-Dateien."""
    pins = {}
    for rel in DOCKER_MCP_FILES:
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            return None, f"{rel} fehlt"
        with open(path, encoding="utf-8") as f:
            m = DOCKER_MCP_PIN_RE.search(f.read())
        if not m:
            return None, f"Pin `mcp-server-docker==<v>` nicht in {rel} gefunden"
        pins[rel] = m.group("v")
    return pins, None


def check_docker_mcp_update():
    """Prueft den Pin des lokalen Docker-MCP-Servers (`uvx mcp-server-docker==<v>`,
    docs/mcp/docker-mcp-server.md + README.md) auf Gleichheit und vergleicht ihn mit der
    latest PyPI-Version. Drift zwischen den Dateien = fail; neueres Release = warn (gelb).
    Der Server laeuft host-seitig (nicht Teil des Sandbox-Images)."""
    pins, err = _docker_mcp_pins()
    if err:
        fail(f"mcp-server-docker version ({err})")
        return
    unique = sorted(set(pins.values()))
    if len(unique) != 1:
        detail = ", ".join(f"{rel}={v}" for rel, v in pins.items())
        fail(
            f"mcp-server-docker pin drift ({detail})",
            "alle Vorkommen (docs/mcp/docker-mcp-server.md + README.md) auf dieselbe Version setzen",
        )
        return
    pin = unique[0]
    try:
        data = json.loads(_http_get(DOCKER_MCP_PYPI_URL))
        latest = str(data["info"]["version"])
    except Exception as e:
        fail("mcp-server-docker version (PyPI latest nicht abrufbar)", str(e))
        return
    if _version_newer(latest, pin):
        warn(
            f"mcp-server-docker update available (Pin v{pin}, PyPI latest v{latest})",
            f"Pin in {DOCKER_MCP_DOC} + README.md auf v{latest} heben; auf dem Host neu registrieren "
            f"(`sbx mcp rm docker` + `sbx mcp add docker --command \"uvx\" "
            f"--args \"mcp-server-docker=={latest}\"`)",
        )
    else:
        pass_(f"mcp-server-docker version up-to-date (Pin v{pin}, PyPI latest v{latest})")


def check_bruno_cli_update():
    """Prueft den Bruno-CLI-Pin (`@usebruno/cli@<v>`) in allen Kit-Specs und
    Tooling-Images auf Gleichheit und vergleicht ihn mit der latest npm-Version.
    Drift zwischen den Dateien = fail; neueres npm-Release = warn (Renovate-Bump)."""
    pins = {}
    for rel in BRUNO_PIN_FILES:
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            fail(f"bruno CLI pin ({rel} fehlt)")
            return
        with open(path, encoding="utf-8") as f:
            m = BRUNO_PIN_RE.search(f.read())
        if not m:
            fail(f"bruno CLI pin (@usebruno/cli@<version> nicht in {rel} gefunden)")
            return
        pins[rel] = m.group("v")
    unique = sorted(set(pins.values()))
    if len(unique) != 1:
        detail = ", ".join(f"{rel}={v}" for rel, v in pins.items())
        fail(
            f"bruno CLI pin drift ({detail})",
            "alle Vorkommen (Specs + Dockerfiles) auf dieselbe @usebruno/cli-Version setzen",
        )
        return
    pin = unique[0]
    try:
        data = json.loads(_http_get(BRUNO_NPM_URL))
        latest = str(data["version"])
    except Exception as e:
        fail("bruno CLI version (npm latest nicht abrufbar)", str(e))
        return
    if _version_newer(latest, pin):
        warn(
            f"bruno CLI update available (Pin v{pin}, npm latest v{latest})",
            "Optional: @usebruno/cli-Pin in den Specs + Dockerfiles auf "
            f"v{latest} heben (Renovate-Custom-Manager uebernimmt den Bump)",
        )
    else:
        pass_(f"bruno CLI version up-to-date (Pin v{pin}, npm latest v{latest})")


def check_inspector_cli_update():
    """Prueft den MCP-Inspector-Pin (`@modelcontextprotocol/inspector@<v>`) in allen
    Kit-Specs und Tooling-Images auf Gleichheit und vergleicht ihn mit der latest
    npm-Version. Drift = fail; neueres npm-Release = warn (Renovate-Bump)."""
    pins = {}
    for rel in INSPECTOR_PIN_FILES:
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            fail(f"mcp-inspector pin ({rel} fehlt)")
            return
        with open(path, encoding="utf-8") as f:
            m = INSPECTOR_PIN_RE.search(f.read())
        if not m:
            fail(f"mcp-inspector pin (@modelcontextprotocol/inspector@<version> nicht in {rel} gefunden)")
            return
        pins[rel] = m.group("v")
    unique = sorted(set(pins.values()))
    if len(unique) != 1:
        detail = ", ".join(f"{rel}={v}" for rel, v in pins.items())
        fail(
            f"mcp-inspector pin drift ({detail})",
            "alle Vorkommen (Specs + Dockerfiles) auf dieselbe @modelcontextprotocol/inspector-Version setzen",
        )
        return
    pin = unique[0]
    try:
        data = json.loads(_http_get(INSPECTOR_NPM_URL))
        latest = str(data["version"])
    except Exception as e:
        fail("mcp-inspector version (npm latest nicht abrufbar)", str(e))
        return
    if _version_newer(latest, pin):
        warn(
            f"mcp-inspector update available (Pin v{pin}, npm latest v{latest})",
            "Optional: @modelcontextprotocol/inspector-Pin in den Specs + Dockerfiles auf "
            f"v{latest} heben (Renovate-Custom-Manager uebernimmt den Bump)",
        )
    else:
        pass_(f"mcp-inspector version up-to-date (Pin v{pin}, npm latest v{latest})")


def _kafka_pin():
    """(KAFKA_VER, KAFKA_SCALA_VER) aus install-tooling.sh, oder (None, None)."""
    path = os.path.join(ROOT, KAFKA_INSTALL_SCRIPT)
    if not os.path.isfile(path):
        return None, None
    with open(path, encoding="utf-8") as f:
        content = f.read()
    mv = KAFKA_VER_RE.search(content)
    ms = KAFKA_SCALA_VER_RE.search(content)
    if not mv or not ms:
        return None, None
    return mv.group("v"), ms.group("v")


def check_kafka_distro_availability():
    """KAFKA_VER (install-tooling.sh) muss als Binary-Tarball existieren — auf dlcdn
    (aktuelle Releases) ODER archive.apache.org (aeltere, von dlcdn entfernte).
    Faengt einen Renovate-Bump auf eine Maven-verfuegbare, aber noch nicht
    veroeffentlichte Distro ab, bevor der Image-Build bricht."""
    ver, scala = _kafka_pin()
    if not ver or not scala:
        fail("kafka distro (KAFKA_VER/KAFKA_SCALA_VER nicht in "
             f"{KAFKA_INSTALL_SCRIPT} gefunden)")
        return
    cdn_status = _http_status(KAFKA_CDN_URL.format(ver=ver, scala=scala))
    arch_status = _http_status(KAFKA_ARCHIVE_URL.format(ver=ver, scala=scala))
    if cdn_status == 200:
        pass_(f"kafka distro v{ver} available (dlcdn; archive HTTP {arch_status})")
    elif arch_status == 200:
        warn(
            f"kafka distro v{ver} not on dlcdn (HTTP {cdn_status}) — nur im Apache-Archiv",
            "install-tooling.sh faellt auf archive.apache.org zurueck; sobald die Version "
            "aus beiden Quellen verschwindet, bricht der Image-Build",
        )
    else:
        fail(
            f"kafka distro v{ver} not available "
            f"(dlcdn HTTP {cdn_status}, archive HTTP {arch_status})",
            "KAFKA_VER auf eine veroeffentlichte Distro setzen "
            "(https://dlcdn.apache.org/kafka/)",
        )


def main():
    enable_ansi()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("agent", nargs="?", choices=["all", "opencode-v3", "claude-v3", "mammouth", "mistral-vibe", "pi"],
                        default="all", help="Zu testendes Kit (default: all)")
    parser.add_argument("--keep", action="store_true", help="Sandboxes nach dem Test behalten")
    parser.add_argument("--ci", action="store_true",
                        help="CI-Modus: Fake-API-Keys, kein realer mammouth-/mistral-API-Call")
    parser.add_argument("--validate-only", action="store_true",
                        help="Nur Kit-Validierung, keine Sandbox-Szenarien (default: Sandboxes werden gestartet); v3-Kits werden ueber den Kit-Builder validiert")
    parser.add_argument("--workspace", default=None,
                        help="Workspace-Pfad fuer die Sandbox-Szenarien "
                             "(default: $WORKSPACE_DIR oder Repo-Root)")
    parser.add_argument("--skip-v3-builder", action="store_true",
                        help="v3-Kits nur per Offline-Probe pruefen statt ueber den Kit-Builder "
                             "(schnell; fuer CI-Szenario-Laeufe, volle Validierung via --validate-only)")
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
    # v3-Quellkits können nicht ueber den `--offline`-Ladepfad validiert werden
    # ("no kit builder configured"). Der Kit-Builder (Sandbox `sbx-kit-builder`)
    # baut das Artefakt und validiert es — genau das passiert im Publish-Build.
    # Default: echte Artefakt-Validierung ueber den Kit-Builder (auch im Voll-Lauf).
    # `--skip-v3-builder` schaltet auf den schnellen Offline-Probe zurueck (z. B. in
    # CI-Szenario-Laeufen, wo sonst pro Matrix-Job alle Kits erneut gebaut wuerden).
    validate_v3_via_builder = not args.skip_v3_builder
    builder_hints = ("no kit builder configured", "failed to create kit builder",
                     "failed to start kit builder", "kit builder sandbox",
                     "sandboxd", "cannot connect to the docker daemon",
                     "is the docker daemon running", "/dev/kvm", "kvm",
                     "not signed in to docker")

    def validate_kit(label, kit_dir, v3):
        info("  --> validate: " + kit_dir)
        cmd = ["kit", "validate"]
        if v3 and not validate_v3_via_builder:
            cmd.append("--offline")
        cmd.append(kit_dir)
        code, out = run_sbx(cmd, stream=True)
        if code == 0:
            pass_(f"sbx kit validate ({label})")
            return
        if v3:
            low = out.lower()
            if not validate_v3_via_builder and "no kit builder configured" in low:
                print("  " + _color("33", f"[SKIP] sbx kit validate ({label}) — Offline-Probe "
                                          "(--skip-v3-builder); volle Validierung via Kit-Builder "
                                          "(`--validate-only` bzw. ohne --skip-v3-builder)"))
                return
            if any(hint in low for hint in builder_hints):
                last = out.strip().splitlines()[-1] if out.strip() else "unknown"
                warn(
                    f"sbx kit validate ({label}) — Kit-Builder nicht verfügbar ({last})",
                    "v3-Quellkit wird per buildx-Kit-Frontend im Publish/e2e gebaut; "
                    "für die echte Artefakt-Validierung `sbx kit validate ./<kit>/` "
                    "(ohne --offline, Kit-Builder-Sandbox) auf einem Host mit Docker/KVM ausführen",
                )
                return
        fail(f"sbx kit validate ({label})")

    # Kit-Validierung: `--validate-only` und `all` validieren alle Kits (repo-weites
    # Gate fuer shared Tooling/Pins). Bei einem einzelnen Szenario nur dessen Kit
    # bauen — sonst wird fuer `local-test-kits.py opencode-v3` unnoetig jedes andere
    # Kit-Artefakt neu gebaut.
    kit_specs = [
        ("opencode-v3-agent", "opencode-v3"),
        ("claude-v3-agent", "claude-v3"),
        ("mammouth-agent", "mammouth"),
        ("mistral-vibe-agent", "mistral-vibe"),
        ("pi-agent", "pi"),
    ]
    if args.validate_only or agent == "all":
        validate_specs = kit_specs
    else:
        validate_specs = [spec for spec in kit_specs if spec[1] == agent]
    if validate_v3_via_builder:
        info("  (v3-Kits: Validierung ueber den Kit-Builder `sbx-kit-builder`; der erste Lauf baut die Artefakte und dauert laenger)")
    for kit_name, _ in validate_specs:
        validate_kit(kit_name, os.path.join(ROOT, kit_name), v3=True)

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
        info("==> e2e.yml Workflow-Referenzen (needs/uses)")
        check_workflow_job_references()
        print()
        info("==> OpenCode-v3 Base/CLI-Check (shell-docker-image + OPENCODE_VERSION, 1.x)")
        check_opencode_v3_cli_version()
        print()
        info("==> Claude-v3 Base/CLI-Check (shell-docker-image + CLAUDE_VERSION, npm @anthropic-ai/claude-code)")
        check_claude_v3_cli_version()
        print()
        info("==> Sandbox-Template Node-Baseline-Check (Node >= 24 macht install-tooling.sh node ueberfluessig)")
        check_template_node_baseline()
        print()
        info("==> Mammouth-CLI Version Update-Check (GitHub Release)")
        check_mammouth_cli_update()
        print()
        info("==> Mistral-Vibe Version Update-Check (PyPI + Image-Tag + Custom-Workload-Basis)")
        check_vibe_cli_update()
        print()
        info("==> Pi Version Update-Check (npm + Descriptor/Dockerfile-Pin + Custom-Workload-Basis)")
        check_pi_cli_update()
        print()
        info("==> Pi MCP-Guard Policy (Unit-Tests)")
        check_pi_mcp_guard()
        print()
        info("==> Docker-MCP-Server Version Update-Check (PyPI)")
        check_docker_mcp_update()
        print()
        info("==> Bruno-CLI Version Update-Check (npm + Pin-Drift)")
        check_bruno_cli_update()
        print()
        info("==> MCP-Inspector Version Update-Check (npm + Pin-Drift)")
        check_inspector_cli_update()
        print()
        info("==> Apache-Kafka-Distro Verfuegbarkeit (Tarball auf dlcdn ODER archive.apache.org)")
        check_kafka_distro_availability()
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
    # Seit sbx v0.48: `-q` liefert nur die Namen (layout-unabhaengig). Die
    # Tabellen-Ausgabe oben bleibt reine Diagnose; geprueft wird gegen das Set.
    # Fallback auf die Tabelle, falls `-q` nicht verfuegbar ist (aeltere Version).
    global_secrets = sbx_names(["secret", "ls", "-g"])

    # Nur Secrets prüfen, die ein ausgewähltes Szenario (Kit) tatsächlich benötigt —
    # Fehlermeldungen nennen das betroffene Kit/Szenario.
    if agent == "all":
        selected = set(SCENARIO_SECRETS)
    else:
        selected = {agent}
    for sname in SECRET_ORDER:
        if not any(sname in SCENARIO_SECRETS[sc] for sc in selected):
            continue
        if global_secrets is not None:
            ok = sname in global_secrets
        else:
            ok = re.search(
                rf"^\(global\)\s+service\s+{re.escape(sname)}\s+\(stored\)$", secret_out, re.M
            ) is not None
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
        '"npm:npm --version" "kafka:kafka-topics.sh --version" "bruno:bru --version" '
        '"mcp-inspector:command -v mcp-inspector" "pi:pi --version" "opencode:opencode --version" "claude:claude --version"; do '
        'name="${t%%:*}"; cmd="${t#*:}"; if $cmd >/dev/null 2>&1; then echo "TOOL-OK:$name"; '
        'else echo "TOOL-FAIL:$name"; fi; done'
    )

    scenarios = [
        {
            "name": "kit-test-opencode-v3",
            "agent": "opencode-v3",
            "kit": os.path.join(ROOT, "opencode-v3-agent"),
            "model": "deepseek/deepseek-flash",
            "config_label": "opencode-v3 config (default model, gateway, guard, CLI)",
            "config": 'test -f ~/.config/opencode/opencode.jsonc && grep -q "deepseek/deepseek-flash" ~/.config/opencode/opencode.jsonc && grep -q "mcp-gateway_analyze_calls" ~/.config/opencode/opencode.jsonc && test -f ~/.config/opencode/plugins/intellij-run-config-guard.js && opencode --version >/dev/null 2>&1 && echo CONFIG-OK || { echo "MODEL=$(grep -c deepseek/deepseek-flash ~/.config/opencode/opencode.jsonc 2>/dev/null || echo 0)"; echo "GW=$(grep -c mcp-gateway_analyze_calls ~/.config/opencode/opencode.jsonc 2>/dev/null || echo 0)"; echo "GUARD=$(test -f ~/.config/opencode/plugins/intellij-run-config-guard.js && echo 1 || echo 0)"; echo "CLI=$(opencode --version 2>/dev/null || echo MISSING)"; exit 1; }',
        },
        {
            "name": "kit-test-claude-v3",
            "agent": "claude-v3",
            "kit": os.path.join(ROOT, "claude-v3-agent"),
            "model": "claude-sonnet-4-6",
            "config_label": "claude-v3 config (default model, gateway, guard, managed settings, CLI)",
            "config": 'test -f ~/.claude/settings.json && grep -q "claude-sonnet-4-6" ~/.claude/settings.json && grep -q "mcp__mcp-gateway__" ~/.claude/settings.json && grep -q "mcp-gateway" ~/.claude.json && grep -q "intellij-run-config-guard.sh" /etc/claude-code/managed-settings.json && claude --version >/dev/null 2>&1 && echo CONFIG-OK || { echo "MODEL=$(grep -c claude-sonnet-4-6 ~/.claude/settings.json 2>/dev/null || echo 0)"; echo "GW=$(grep -c mcp-gateway ~/.claude.json 2>/dev/null || echo 0)"; echo "GUARD=$(grep -c intellij-run-config-guard.sh /etc/claude-code/managed-settings.json 2>/dev/null || echo 0)"; echo "CLI=$(claude --version 2>/dev/null || echo MISSING)"; exit 1; }',
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
        {
            "name": "kit-test-pi",
            "agent": "pi",
            "kit": os.path.join(ROOT, "pi-agent"),
            "model": "deepseek/deepseek-flash",
            "config_label": "pi config (default model + mcp-gateway + read-only guard)",
            "config": (
                'test -f ~/.pi/agent/settings.json '
                '&& grep -q "\\"defaultProvider\\": \\"deepseek\\"" ~/.pi/agent/settings.json '
                '&& grep -q "\\"defaultModel\\": \\"deepseek-flash\\"" ~/.pi/agent/settings.json '
                '&& grep -q "mcp-gateway.docker.internal" ~/.pi/agent/mcp.json '
                '&& test -f ~/.pi/agent/extensions/mcp-guard.ts '
                '&& test -f ~/.pi/agent/lib/mcp-guard-policy.ts '
                '&& pi --version >/dev/null 2>&1 '
                '&& [ "${DEEPSEEK_API_KEY:-}" = "proxy-managed" ] '
                '&& ! (pi --help 2>&1 | grep -q "Failed to load extension") '
                '&& echo CONFIG-OK '
                '|| { echo "SETTINGS=$(cat ~/.pi/agent/settings.json 2>/dev/null || echo MISSING)"; '
                'echo "GATEWAY=$(grep -c mcp-gateway.docker.internal ~/.pi/agent/mcp.json 2>/dev/null || echo 0)"; '
                'echo "GUARD=$(test -f ~/.pi/agent/extensions/mcp-guard.ts && test -f ~/.pi/agent/lib/mcp-guard-policy.ts && echo 1 || echo 0)"; '
                'echo "DEEPSEEK=${DEEPSEEK_API_KEY:-<unset>}"; '
                'echo "PI=$(pi --version 2>/dev/null || echo MISSING)"; '
                'pi --help 2>&1 | grep -i "extension" | head -3; exit 1; }'
            ),
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
        # v3-Workloads/Sandbox-Kits unter IMAGE_PREFIX (Default Docker Hub
        # `docker.io/domboeckli`, per `IMAGE_PREFIX`-Env umschaltbar):
        #   - opencode-v3: <IMAGE_PREFIX>/sbx-opencode:<tag>  (OPENCODE_V3_IMAGE_TAG, default `local`)
        #   - claude-v3:   <IMAGE_PREFIX>/sbx-claude:<tag>    (CLAUDE_V3_IMAGE_TAG, default `local`)
        #   - mammouth:    <IMAGE_PREFIX>/sbx-mammouth:<tag>  (MAMMOUTH_IMAGE_TAG, default `local`)
        #   - mistral-vibe: <IMAGE_PREFIX>/sbx-mistral-vibe:<tag> (VIBE_IMAGE_TAG, default `local`)
        # Pi: lokal das Kit-Verzeichnis (sbx baut es), in CI das publizierte Image (PI_IMAGE_TAG).
        kit_target = s["kit"]
        if s["agent"] == "pi":
            pi_tag = os.environ.get("PI_IMAGE_TAG")
            if pi_tag:
                kit_target = f"{IMAGE_PREFIX}/{PI_IMAGE_NAME}:{pi_tag}"
                info(f"Pi-Image (publiziert): {kit_target}")
            else:
                info("Pi-Image: lokales v3-Workload-Verzeichnis (sbx baut beim Erzeugen)")
        if s["agent"] == "opencode-v3":
            # Lokal default `local`; explizit leer (Branch/PR) -> lokales Verzeichnis.
            oc_raw = os.environ.get("OPENCODE_V3_IMAGE_TAG")
            oc_tag = "local" if oc_raw is None else oc_raw
            if oc_tag:
                kit_target = f"{IMAGE_PREFIX}/{OPENCODE_V3_IMAGE_NAME}:{oc_tag}"
                info(f"OpenCode-v3-Image (publiziert): {kit_target}")
            else:
                info("OpenCode-v3-Image: lokales v3-Workload-Verzeichnis (sbx baut beim Erzeugen)")
        if s["agent"] == "claude-v3":
            # Lokal default `local`; explizit leer (Branch/PR) -> lokales Verzeichnis.
            cc_raw = os.environ.get("CLAUDE_V3_IMAGE_TAG")
            cc_tag = "local" if cc_raw is None else cc_raw
            if cc_tag:
                kit_target = f"{IMAGE_PREFIX}/{CLAUDE_V3_IMAGE_NAME}:{cc_tag}"
                info(f"Claude-v3-Image (publiziert): {kit_target}")
            else:
                info("Claude-v3-Image: lokales v3-Workload-Verzeichnis (sbx baut beim Erzeugen)")
        if s["agent"] == "mammouth":
            # Lokal default `local` (per build-and-publish-mammouth-image); CI/e2e
            # uebergibt den Master-Tag per MAMMOUTH_IMAGE_TAG. Explizit leer
            # (Branch/PR) -> lokales v3-Workload-Verzeichnis, damit der Branch-Stand
            # getestet wird und kein v2-Master-Image als v3-Kit gepullt wird.
            mam_raw = os.environ.get("MAMMOUTH_IMAGE_TAG")
            mam_tag = "local" if mam_raw is None else mam_raw
            if mam_tag:
                kit_target = f"{IMAGE_PREFIX}/{MAMMOUTH_IMAGE_NAME}:{mam_tag}"
                info(f"Mammouth-Image (publiziert): {kit_target}")
            else:
                info("Mammouth-Image: lokales v3-Workload-Verzeichnis (sbx baut beim Erzeugen)")
        if _kit_kind(s["kit"]) in ("sandbox", "workload"):
            # Sandbox-/Workload-Kit definiert den Agenten selbst → Kit als erstes
            # positionales Argument; kein Agent-Name, kein --kit (deprecated fuer Sandbox-Kits).
            create_cmd = ["create", "--name", s["name"], kit_target, ws]
        else:
            create_cmd = ["create", "--name", s["name"], s["agent"], ws, "--kit", kit_target]
        # Mistral Vibe (v3): publiziertes Image per Ref; lokal default `local`
        # (build-and-publish-mistral-vibe-image), CI/e2e uebergibt den Master-Tag.
        # Explizit leer (Branch/PR) -> lokales Workload-Verzeichnis (Branch-Stand).
        if s["agent"] == "mistral-vibe":
            vibe_raw = os.environ.get("VIBE_IMAGE_TAG")
            vibe_tag = "local" if vibe_raw is None else vibe_raw
            if vibe_tag:
                kit_target = f"{IMAGE_PREFIX}/{VIBE_IMAGE_NAME}:{vibe_tag}"
                info(f"Mistral-Vibe-Image (publiziert): {kit_target}")
            else:
                info("Mistral-Vibe-Image: lokales v3-Workload-Verzeichnis (sbx baut beim Erzeugen)")
        # Host-Shared-Skills-Store NICHT mounten: die Sandbox bleibt ausserhalb der
        # geteilten Trust-Boundary; die Kit-Skills kommen aus dboeckli/ai-agent-skills
        # (install-tooling-user.sh), nicht vom Host.
        create_cmd += ["--skills=off"]
        # IntelliJ MCP via sbx MCP Gateway (Issue #57): `--static-mcp idea` nur setzen, wenn der Server auf dem
        # Host registriert ist — sonst schlägt `sbx create` fehl (jeder static-mcp-Name muss registriert sein).
        # CI hat kein `idea` registriert → Sandbox ohne static-mcp; der Config-Check prüft dann nur die Whitelist,
        # der Gateway-Weg wird lokal mit registriertem `idea` getestet.
        # Seit sbx v0.48: `-q` liefert nur die Namen (layout-unabhaengig);
        # Fallback auf die Tabelle, falls `-q` nicht verfuegbar ist (aeltere Version).
        mcp_names = sbx_names(["mcp", "ls"])
        if mcp_names is not None:
            has_idea = "idea" in mcp_names
        else:
            c_mcp, out_mcp = run_sbx(["mcp", "ls"])
            has_idea = c_mcp == 0 and re.search(r"^\s*idea\s+", out_mcp, re.M) is not None
        if has_idea:
            create_cmd += ["--static-mcp", "idea"]
            info("  IntelliJ MCP: idea registriert → --static-mcp idea")
        else:
            print("  " + _color("33", "  [SKIP] --static-mcp idea — 'idea' nicht auf dem Host registriert "
                                      "(sbx mcp add idea --url http://localhost:64615/stream --skip-ssrf-check)"))
        info("  setup.install laeuft jetzt (npm-CLIs, apt, JDK, Maven, Docker CLI, Compose, "
             "kubectl, Helm 4, Kafka, Skills). Mit vorgebackenem Image (opencode) in Sekunden; "
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
        # Pi ist nur im Pi-Image vorhanden; die anderen Agenten-Images bringen es nicht mit.
        required_tools = ["ctx7", "gh", "java", "javac", "mvn", "docker", "kubectl", "jq", "node", "npm", "kafka"]
        if s["agent"] == "pi":
            required_tools.append("pi")
        if s["agent"] == "opencode-v3":
            required_tools.append("opencode")
        if s["agent"] == "claude-v3":
            required_tools.append("claude")
        for t in required_tools:
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

        # Node muss >= 24 sein (npm CLIs wie renovate >=43 fordern ^24.11) — der basis-Template-Node
        # ist 22, install-tooling.sh node hebt auf 24 an. `node --version` allein würde ein fehlgeschlagenes
        # Upgrade (Fallback auf Node 22) nicht erkennen, daher explizit die Major-Version prüfen.
        c2, node_out = exec_sandbox(s["name"], "node --version")
        node_m = re.match(r"v(\d+)\.", node_out.strip())
        if c2 == 0 and node_m and int(node_m.group(1)) >= 24:
            pass_(f"tool: node >= 24 ({node_out.strip()})")
        else:
            sfail("tool: node >= 24 (npm CLIs wie renovate >=43 fordern Node ^24.11)", node_out)
            c3, logtail = exec_sandbox(s["name"], "tail -n 40 /var/log/sbx-kit-install.log 2>/dev/null")
            if c3 == 0 and logtail:
                print("         " + _color("31", "--- install log tail (node) ---"))
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

        # Issue #163: IntelliJ MCP is only reachable through the sbx MCP gateway
        # (mcp-idea). The sandbox must NOT be able to reach the host port directly,
        # otherwise any sandbox process could bypass the mcp-gateway permission
        # whitelist and the run-config guard via curl.
        c2, out = exec_sandbox(s["name"], "MCP_CHECK_DEEP=1 bash ~/.local/bin/mcp-check.sh")
        if c2 == 0 and "mcp-idea:OK" in out:
            pass_("intellij-mcp via sbx MCP gateway (mcp-idea)")
        elif ci:
            print("  " + _color("33", "[SKIP] intellij-mcp via sbx MCP gateway (mcp-idea) — expected: "
                                     "IntelliJ MCP muss auf dem Host laufen (nicht im CI)"))
        else:
            sfail("intellij-mcp via sbx MCP gateway (mcp-idea)",
                 "Gateway/IntelliJ nicht erreichbar — sbx mcp add idea + --static-mcp idea pruefen; "
                 f"status={out.strip()}")

        direct_cmd = (
            'blocked=1; '
            'for port in 64615 64342; do '
            'for host in host.docker.internal 127.0.0.1 localhost; do '
            'code=$(curl -s -o /dev/null -w "%{http_code}" -m 3 "http://$host:$port/sse" 2>/dev/null); '
            '[ "$code" = "200" ] || [ "$code" = "206" ] && blocked=0; '
            'done; done; '
            'echo "DIRECT-BLOCKED=$blocked"'
        )
        c2, out = exec_sandbox(s["name"], direct_cmd)
        if c2 == 0 and "DIRECT-BLOCKED=1" in out:
            pass_("intellij-mcp direct host port blocked (proxy 403, issue #163)")
        else:
            sfail("intellij-mcp direct host port blocked (proxy 403, issue #163)",
                 f"host.docker.internal:64615/64342 direkt erreichbar; {out.strip()}")

        skills_cmd = (
            "for sk in camel-matrix cc-best-practices project-references skill-best-practices "
            "using-superpowers systematic-debugging verification-before-completion; do "
            "skills ls -g | grep -q \"$sk\" || echo \"MISSING:$sk\"; done; echo SKILLS-DONE"
        )
        c2, out = exec_sandbox(s["name"], skills_cmd)
        if c2 == 0 and "MISSING" not in out:
            pass_("skills installed (dboeckli bundle + superpowers)")
        else:
            sfail("skills installed (dboeckli bundle + superpowers)", out)

        ctx7_env_cmd = 'echo "CONTEXT7_API_KEY=${CONTEXT7_API_KEY:-<unset>}"'
        c2, out = exec_sandbox(s["name"], ctx7_env_cmd)
        if c2 == 0 and "CONTEXT7_API_KEY=proxy-managed" in out:
            pass_("context7 proxy env wiring (CONTEXT7_API_KEY=proxy-managed)")
        else:
            sfail("context7 proxy env wiring (CONTEXT7_API_KEY=proxy-managed)", out)

        openrouter_env_cmd = 'echo "OPENROUTER_API_KEY=${OPENROUTER_API_KEY:-<unset>}"'
        c2, out = exec_sandbox(s["name"], openrouter_env_cmd)
        if s["agent"] in ("opencode-v3", "pi"):
            if c2 == 0 and "OPENROUTER_API_KEY=proxy-managed" in out:
                pass_("openrouter proxy env wiring (OPENROUTER_API_KEY=proxy-managed)")
            else:
                sfail("openrouter proxy env wiring (OPENROUTER_API_KEY=proxy-managed)", out)
        else:
            if c2 == 0 and "OPENROUTER_API_KEY=<unset>" in out:
                pass_("openrouter not wired (only opencode-v3/pi declare openrouter)")
            else:
                sfail("openrouter not wired (only opencode-v3/pi declare openrouter)", out)

        # Built-in google service: the opencode template injects the placeholder
        # under GOOGLE_GENERATIVE_AI_API_KEY (the env name the AI SDK's google
        # provider reads by default) — assert that for the opencode template,
        # while claude/mammouth must have it unset.
        google_env_cmd = 'echo "GOOGLE_GENERATIVE_AI_API_KEY=${GOOGLE_GENERATIVE_AI_API_KEY:-<unset>}"'
        if s["agent"] == "pi":
            gemini_env_cmd = 'echo "GEMINI_API_KEY=${GEMINI_API_KEY:-<unset>}"'
            c2, out = exec_sandbox(s["name"], gemini_env_cmd)
            if c2 == 0 and "GEMINI_API_KEY=proxy-managed" in out:
                pass_("google proxy env wiring (GEMINI_API_KEY=proxy-managed)")
            else:
                sfail("google proxy env wiring (GEMINI_API_KEY=proxy-managed)", out)
        else:
            c2, out = exec_sandbox(s["name"], google_env_cmd)
        if s["agent"] == "opencode-v3":
            if c2 == 0 and "GOOGLE_GENERATIVE_AI_API_KEY=proxy-managed" in out:
                pass_("google proxy env wiring (GOOGLE_GENERATIVE_AI_API_KEY=proxy-managed)")
            else:
                sfail("google proxy env wiring (GOOGLE_GENERATIVE_AI_API_KEY=proxy-managed)", out)
        elif s["agent"] not in ("pi",):
            if c2 == 0 and "GOOGLE_GENERATIVE_AI_API_KEY=<unset>" in out:
                pass_("google not wired (only opencode-v3 declares google)")
            else:
                sfail("google not wired (only opencode-v3 declares google)", out)

        # Kit-deklarierter zai-Service: von opencode-v3/claude-v3, mammouth-agent
        # und mistral-vibe-agent deklariert.
        # (mistral-vibe hat eigene zai-Checks im Kit-spezifischen Block.)
        if s["agent"] != "mistral-vibe":
            zai_env_cmd = 'echo "ZAI_API_KEY=${ZAI_API_KEY:-<unset>}"'
            c2, out = exec_sandbox(s["name"], zai_env_cmd)
            if c2 == 0 and "ZAI_API_KEY=proxy-managed" in out:
                pass_("zai proxy env wiring (ZAI_API_KEY=proxy-managed)")
            else:
                sfail("zai proxy env wiring (ZAI_API_KEY=proxy-managed)", out)

        # Kit-deklarierter mistral-Service: opencode-v3/claude-v3 und mammouth-agent;
        # das mistral-vibe-Kit prueft es im eigenen Block.
        if s["agent"] != "mistral-vibe":
            mistral_env_cmd = 'echo "MISTRAL_API_KEY=${MISTRAL_API_KEY:-<unset>}"'
            c2, out = exec_sandbox(s["name"], mistral_env_cmd)
            if c2 == 0 and "MISTRAL_API_KEY=proxy-managed" in out:
                pass_("mistral proxy env wiring (MISTRAL_API_KEY=proxy-managed)")
            else:
                sfail("mistral proxy env wiring (MISTRAL_API_KEY=proxy-managed)", out)

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
                # Der Abgleich ist nur aussagekraeftig, wenn das getestete Image aus diesem
                # Checkout stammt (Tag == Pin [Release-Build] oder `local` [lokal gebaut]). Bei
                # Tag `latest` (CI-Branch-Push) ist es das publizierte Master-Image: ein
                # Renovate-Pin-Bump waere sonst ein Fehlalarm (Image-Tag != Pin, aber das neue
                # Image wird auf dem Branch gar nicht gebaut/gepusht).
                mam_tag = os.environ.get("MAMMOUTH_IMAGE_TAG") or "local"
                mammouth_ver_cmd = "mammouth --version 2>/dev/null | grep -oE '[0-9]+(\\.[0-9]+)+' | head -1"
                c2, out = exec_sandbox(s["name"], mammouth_ver_cmd)
                installed = out.strip().splitlines()[0].strip() if c2 == 0 and out.strip() else ""
                pin = _mammouth_cli_pin_version()
                if mam_tag == "latest":
                    print("  " + _color("33", "[SKIP] mammouth CLI version installed — Image-Tag "
                                              "'latest' (publiziertes Master-Image, nicht aus diesem "
                                              "Checkout); Pin-Abgleich nicht aussagekraeftig"))
                elif installed and pin and installed == pin:
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
                # Nur aussagekraeftig, wenn das getestete Image aus diesem Checkout stammt
                # (Tag == Pin [Release-Build] oder `local` [lokal gebaut]). Bei Tag `latest`
                # (CI-Branch-Push) ist es das publizierte Master-Image; ein Renovate-Pin-Bump
                # waere sonst ein Fehlalarm.
                vibe_raw = os.environ.get("VIBE_IMAGE_TAG")
                vibe_tag = "local" if vibe_raw is None else vibe_raw
                vibe_ver_cmd = "vibe --version 2>/dev/null | grep -oE '[0-9]+(\\.[0-9]+)+' | head -1"
                c2, out = exec_sandbox(s["name"], vibe_ver_cmd)
                installed = out.strip().splitlines()[0].strip() if c2 == 0 and out.strip() else ""
                pin = _vibe_dockerfile_pin()
                if vibe_tag in ("", "latest"):
                    print("  " + _color("33", "[SKIP] mistral-vibe version installed — Image-Tag "
                                              "'latest' (publiziertes Master-Image, nicht aus diesem "
                                              "Checkout); Pin-Abgleich nicht aussagekraeftig"))
                elif installed and pin and installed == pin:
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

                # Z.AI (GLM-5.3-Flash Default + GLM-5.3 + GLM-4.7-Flash): Sentinel + Credential-Aufloesung.
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

        # Issue #139: der Gateway-Handshake allein beweist nur, dass die Infrastruktur
        # erreichbar ist — in JEDER Sandbox muss der Agent den Client selbst verdrahten
        # haben (sbx injiziert nur fuer unterstuetzte Agenten): mcp-client:OK (Config)
        # und mcp-tools:OK (echter Handshake ueber den Agent-Client, Deep-Modus;
        # Fallback auf mcp-client, wenn die CLI kein `mcp list` kennt, z.B. Vibe).
        c2, out = exec_sandbox(s["name"], "MCP_CHECK_DEEP=1 bash ~/.local/bin/mcp-check.sh")
        mcp_tokens = {k: v for k, v in re.findall(r"([A-Za-z0-9_/-]+):(OK|FAIL)", out)}
        for token, label in (("mcp-client", "gateway declared in agent config"),
                             ("mcp-tools", "agent MCP client connects to the gateway")):
            if mcp_tokens.get(token) == "OK":
                pass_(f"MCP client wiring ({label})")
            else:
                sfail(f"MCP client wiring ({label})", f"status={mcp_tokens.get(token)}; {out.strip()}")

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
