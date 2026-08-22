#!/usr/bin/env python3
"""local-test-kits.py - automatischer Test der 4 Agent-Szenarien des opencode-sandbox-kit.

Laeuft auf Windows (PowerShell/CMD) und Linux/macOS, sofern `sbx` und ein
Docker-Daemon verfuegbar sind (auf Windows der nativen Docker Desktop, NICHT aus WSL).

Szenarien:
  1. OpenCode + opencode-agent    (sbx create opencode --kit ./opencode-agent/)
  2. Claude   + opencode-agent    (sbx create claude --kit ./opencode-agent/)      — Home (api.anthropic.com)
  3. Claude   + claude-zurich-agent (sbx create claude --kit ./claude-zurich-agent/) — Zurich LiteLLM-Proxy
  4. Mammouth + mammouth-agent    (sbx create mammouth --kit ./mammouth-agent/)

Voraussetzungen:
  - Docker laeuft, `sbx` CLI im PATH
  - Globale Secrets registriert: github, anthropic, mammouth, context7, openrouter, google, stackoverflow, cloudsmith und zurich
    (sbx secret set mammouth / sbx secret set context7 / sbx secret set openrouter / sbx secret set google / sbx secret set stackoverflow / sbx secret set cloudsmith / sbx secret set zurich — seit v0.38 ohne `-g`)

Verwendung:
  python local-test-kits.py                 # alle 4 Kits testen (default: all)
  python local-test-kits.py opencode        # nur OpenCode testen
  python local-test-kits.py claude          # nur Claude testen (Home + Zurich-Szenario)
  python local-test-kits.py claude-zurich   # nur das Zurich-Szenario testen
  python local-test-kits.py mammouth        # nur Mammouth testen
  python local-test-kits.py --help          # alle Optionen anzeigen
  python local-test-kits.py --validate-only # nur Kit-Validierung, keine Sandbox/Sandbox-Szenarien

Optionen:
  {all,opencode,claude,claude-zurich,mammouth}  Zu testendes Kit (default: all)
  -h, --help                      Diese Hilfe anzeigen
  --keep                          Sandboxes nach dem Test behalten
  --ci                            CI-Modus: Fake-API-Keys, kein realer
                                  mammouth-API-Call
  --validate-only                 Nur Kit-Validierung (sbx kit validate),
                                  keine Secrets-/Sandbox-Checks (default: Sandboxes
                                  werden gestartet)
"""

import argparse
import os
import re
import ssl
import subprocess
import sys
import tempfile
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
                "claude-zurich-agent/files/home/stackexchange-api.md")

# sbx CLI: die Offline-Referenz (opencode-agent/files/home/sbx-cli.md) wird aus der
# Release-Binary generiert (local-test/regenerate-sbx-doc.py). Die dokumentierte Version
# steht im Header der Datei; Update-Check vergleicht sie mit dem gepinnten SBX_VERSION aus
# .github/workflows/validate.yml (Source of Truth, Renovate managed).
SBX_DOC_FILE = "opencode-agent/files/home/sbx-cli.md"
SBX_VALIDATE_YML = ".github/workflows/validate.yml"

# Die Install-Skripte liegen als identische Kopien in den files/home/.local/bin-
# Bundles aller drei Kits. `setup.install` konsumiert sie aus dem Sandbox-Home. Alle
# Kopien muessen identisch bleiben (edit target = eine Kopie, andere per cp syncen;
# Renovate aktualisiert alle gemeinsam).
INSTALL_SCRIPT_PAIRS = (
    ("opencode-agent/files/home/.local/bin/install-tooling.sh",
     "mammouth-agent/files/home/.local/bin/install-tooling.sh",
     "claude-zurich-agent/files/home/.local/bin/install-tooling.sh"),
    ("opencode-agent/files/home/.local/bin/install-tooling-user.sh",
     "mammouth-agent/files/home/.local/bin/install-tooling-user.sh",
     "claude-zurich-agent/files/home/.local/bin/install-tooling-user.sh"),
    ("opencode-agent/files/home/.local/bin/regenerate-kubeconfig.py",
     "mammouth-agent/files/home/.local/bin/regenerate-kubeconfig.py",
     "claude-zurich-agent/files/home/.local/bin/regenerate-kubeconfig.py"),
)


def enable_ansi():
    if os.name == "nt":
        os.system("")


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
    proc = subprocess.run(
        ["sbx"] + args,
        capture_output=not stream,
        text=True,
    )
    if stream:
        return proc.returncode, ""
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


def _sbx_doc_version():
    path = os.path.join(ROOT, SBX_DOC_FILE)
    if not os.path.isfile(path):
        return None, None
    with open(path, encoding="utf-8") as f:
        head = f.read(600)
    m = re.search(r"v(\d+\.\d+\.\d+)-Release-Binary", head)
    if not m:
        m = re.search(r"\*\*v(\d+\.\d+\.\d+)\*\*", head)
    return (m.group(1), path) if m else (None, path)


def check_sbx_doc_update(installed_ver=""):
    """Vergleicht die im Kit dokumentierte sbx-CLI-Version (sbx-cli.md-Header) mit dem
    gepinnten SBX_VERSION (validate.yml). Schlaegt fehl bei Abweichung — die Doku muss
    den Pin spiegeln und wird per regenerate-sbx-doc.py neu erzeugt (Default liest
    denselben Pin). Kein GitHub-API-Zugriff: Source of Truth ist der lokale Pin.

    Zusaetzlich wird die installierte CLI-Version (sofern ermittelbar) gegen den Pin
    geprueft — eine aeltere installierte sbx erzeugt nur eine Warnung (kein FAIL), da
    dieser Check offline ist und den Host-Stand nicht erzwingen soll."""
    documented, doc_path = _sbx_doc_version()
    if not documented:
        fail("sbx CLI version (nicht in sbx-cli.md gefunden)")
        return
    pin_version = _sbx_pin_version()
    if not pin_version:
        fail("sbx CLI version (SBX_VERSION nicht in validate.yml gefunden)")
        return
    if documented != pin_version:
        fail(
            f"sbx CLI version mismatch (Doku v{documented}, Pin v{pin_version})",
            f"Neuerzeugen: python local-test/regenerate-sbx-doc.py v{pin_version}",
        )
    else:
        pass_(f"sbx CLI version up-to-date (v{documented}, Pin v{pin_version})")

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


def main():
    enable_ansi()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("agent", nargs="?", choices=["all", "opencode", "claude", "claude-zurich", "mammouth"],
                        default="all", help="Zu testendes Kit (default: all)")
    parser.add_argument("--keep", action="store_true", help="Sandboxes nach dem Test behalten")
    parser.add_argument("--ci", action="store_true",
                        help="CI-Modus: Fake-API-Keys, kein realer mammouth-API-Call")
    parser.add_argument("--validate-only", action="store_true",
                        help="Nur Kit-Validierung, keine Sandbox-Szenarien (default: Sandboxes werden gestartet)")
    args = parser.parse_args()
    ci = args.ci
    agent = args.agent

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
    info(f"  --> validate: {os.path.join(ROOT, 'claude-zurich-agent')}")
    code, _ = run_sbx(["kit", "validate", os.path.join(ROOT, "claude-zurich-agent")], stream=True)
    pass_("sbx kit validate (claude-zurich-agent)") if code == 0 else fail("sbx kit validate (claude-zurich-agent)")

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
    for sname in ("github", "anthropic", "mammouth", "context7", "openrouter", "google", "stackoverflow", "cloudsmith", "zurich"):
        ok = re.search(rf"^\(global\)\s+service\s+{sname}\s+\(stored\)$", secret_out, re.M)
        pass_(f"secret: {sname}") if ok else fail(f"secret: {sname}")

    tools_cmd = (
        'for t in "ctx7:ctx7 --version" "gh:gh auth status" "java:java -version" '
        '"javac:javac -version" "mvn:mvn -version" "docker:docker version" '
        '"kubectl:kubectl version --client" "jq:jq --version" "node:node --version" '
        '"npm:npm --version"; do '
        'name="${t%%:*}"; cmd="${t#*:}"; if $cmd >/dev/null 2>&1; then echo "TOOL-OK:$name"; '
        'else echo "TOOL-FAIL:$name"; fi; done'
    )

    scenarios = [
        {
            "name": "kit-test-opencode",
            "agent": "opencode",
            "kit": os.path.join(ROOT, "opencode-agent"),
            "model": "deepseek/deepseek-v4-flash",
            "config": 'grep -q "deepseek/deepseek-v4-flash" ~/.config/opencode/opencode.jsonc && echo CONFIG-OK || { echo "MODEL=$(jq -r .model ~/.config/opencode/opencode.jsonc 2>/dev/null || echo UNKNOWN)"; exit 1; }',
        },
        {
            "name": "kit-test-claude",
            "agent": "claude",
            "kit": os.path.join(ROOT, "opencode-agent"),
            "model": "claude-sonnet-4-6",
            "config": 'grep -q "claude-sonnet-4-6" ~/.claude/settings.json && grep -q "mcp__idea__" ~/.claude/settings.json && grep -q "intellij-run-config-guard.sh" /etc/claude-code/managed-settings.json && echo CONFIG-OK || { echo "MODEL=$(jq -r .model ~/.claude/settings.json 2>/dev/null || echo UNKNOWN)"; echo "KIT_FILE=$(jq -r .model ~/.claude/settings.kit.json 2>/dev/null || echo MISSING)"; echo "GUARD=$(grep -c intellij-run-config-guard.sh /etc/claude-code/managed-settings.json 2>/dev/null || echo 0)"; exit 1; }',
        },
        {
            "name": "kit-test-claude-zurich",
            "agent": "claude",
            "tags": ["claude", "claude-zurich"],
            "kit": os.path.join(ROOT, "claude-zurich-agent"),
            "model": "eu.anthropic.claude-sonnet-4-6",
            "config": 'grep -q "eu.anthropic.claude-sonnet-4-6" ~/.claude/settings.json && grep -q "mcp__idea__" ~/.claude/settings.json && grep -q "intellij-run-config-guard.sh" /etc/claude-code/managed-settings.json && echo "ANTHROPIC_BASE_URL=${ANTHROPIC_BASE_URL}" && echo "ANTHROPIC_MODEL=${ANTHROPIC_MODEL}" && [ "${ANTHROPIC_BASE_URL}" = "https://genai-lounge-nx-litellm-uat-emea.zurich.com" ] && echo CONFIG-OK || { echo "MODEL=$(jq -r .model ~/.claude/settings.json 2>/dev/null || echo UNKNOWN)"; echo "KIT_FILE=$(jq -r .model ~/.claude/settings.kit.json 2>/dev/null || echo MISSING)"; echo "GUARD=$(grep -c intellij-run-config-guard.sh /etc/claude-code/managed-settings.json 2>/dev/null || echo 0)"; echo "BASE_URL=${ANTHROPIC_BASE_URL:-<unset>}"; exit 1; }',
        },
        {
            "name": "kit-test-mammouth",
            "agent": "mammouth",
            "kit": os.path.join(ROOT, "mammouth-agent"),
            "model": "deepseek/deepseek-v4-flash",
            "config": 'grep -q "deepseek/deepseek-v4-flash" ~/.config/mammouth/opencode.jsonc && echo CONFIG-OK || { echo "MODEL=$(jq -r .model ~/.config/mammouth/opencode.jsonc 2>/dev/null || echo UNKNOWN)"; exit 1; }',
            "run_checks": True,
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

        ws = tempfile.mkdtemp(prefix="sbx-kit-test-")
        info("  Sandbox erzeugen ...")
        code, _ = run_sbx(["create", "--name", s["name"], s["agent"], ws, "--kit", s["kit"]], stream=True)
        if code != 0:
            sfail("sandbox create")
            blocked_requests(s["name"])
            run_sbx(["rm", s["name"], "-f"])
            continue

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
        for t in ("ctx7", "gh", "java", "javac", "mvn", "docker", "kubectl", "jq", "node", "npm"):
            if t in ok_tools:
                pass_(f"tool: {t}")
            else:
                sfail(f"tool: {t}", out)

        c2, out = exec_sandbox(s["name"], "gh auth status >/dev/null 2>&1 && gh api user >/dev/null 2>&1 && echo GHAPI-OK")
        if c2 == 0 and "GHAPI-OK" in out:
            pass_("gh api (authenticated call)")
        elif ci:
            print("  " + _color("33", "[SKIP] gh api (authenticated call) — expected: fake token in CI, "
                                     "kein authentifizierter gh-API-Call"))
        else:
            sfail("gh api (authenticated call)", out)

        if s["config"]:
            c2, out = exec_sandbox(s["name"], s["config"])
            if c2 == 0 and "CONFIG-OK" in out:
                pass_(f"default model in config ({s['model']})")
            else:
                sfail(f"default model in config ({s['model']})", out)

        mcp_cmd = (
            'code=""; '
            'for host in host.docker.internal 127.0.0.1 localhost; do '
            'code=$(curl -s -o /dev/null -w "%{http_code}" -m 3 "http://$host:64342/sse" 2>/dev/null); '
            '[ "$code" = "200" ] || [ "$code" = "206" ] && break; code=""; done; '
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
                 "IntelliJ MCP muss auf dem Host laufen (127.0.0.1/localhost/host.docker.internal:64342)")

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


        if s.get("run_checks"):
            c2, out = exec_sandbox(s["name"], "bash ~/.config/sandbox-kit/run-checks.sh")
            m = {k: v for k, v in re.findall(r"([A-Za-z0-9_/-]+):(OK|FAIL)", out)}
            if m.get("mammouth") == "OK":
                pass_("startup check: mammouth")
            else:
                sfail("startup check: mammouth", f"status={m.get('mammouth')}")

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
