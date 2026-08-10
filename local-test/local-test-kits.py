#!/usr/bin/env python3
"""local-test-kits.py - automatischer Test der 3 Agent-Szenarien des opencode-sandbox-kit.

Laeuft auf Windows (PowerShell/CMD) und Linux/macOS, sofern `sbx` und ein
Docker-Daemon verfuegbar sind (auf Windows der nativen Docker Desktop, NICHT aus WSL).

Szenarien:
  1. OpenCode + Mixin-Kit      (sbx create opencode --kit .)
  2. Claude   + Mixin-Kit      (sbx create claude --kit .)
  3. Mammouth + mammouth-agent (sbx create mammouth --kit ./mammouth-agent/)

Voraussetzungen:
  - Docker laeuft, `sbx` CLI im PATH
  - Globale Secrets registriert: github, anthropic, mammouth, context7 und openrouter
    (sbx secret set mammouth / sbx secret set context7 / sbx secret set openrouter — seit v0.38 ohne `-g`)

Verwendung:
  python local-test-kits.py                 # alle 3 Kits testen (default: all)
  python local-test-kits.py opencode        # nur OpenCode testen
  python local-test-kits.py claude          # nur Claude testen
  python local-test-kits.py mammouth        # nur Mammouth testen
  python local-test-kits.py --help          # alle Optionen anzeigen
  python local-test-kits.py --validate-only # nur Kit-Validierung, keine Sandbox/Sandbox-Szenarien

Optionen:
  {all,opencode,claude,mammouth}  Zu testendes Kit (default: all)
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
import subprocess
import sys
import tempfile
import time
from shutil import which

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
passed = []
failed = []


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


def main():
    enable_ansi()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("agent", nargs="?", choices=["all", "opencode", "claude", "mammouth"],
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
    info(f"  --> validate: {ROOT}")
    code, _ = run_sbx(["kit", "validate", ROOT], stream=True)
    pass_("sbx kit validate (mixin)") if code == 0 else fail("sbx kit validate (mixin)")
    info(f"  --> validate: {os.path.join(ROOT, 'mammouth-agent')}")
    code, _ = run_sbx(["kit", "validate", os.path.join(ROOT, "mammouth-agent")], stream=True)
    pass_("sbx kit validate (mammouth-agent)") if code == 0 else fail("sbx kit validate (mammouth-agent)")

    if args.validate_only:
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
    for sname in ("github", "anthropic", "mammouth", "context7", "openrouter"):
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
            "kit": ROOT,
            "model": "opencode/deepseek-v4-flash-free",
            "config": 'grep -q "opencode/deepseek-v4-flash-free" ~/.config/opencode/opencode.jsonc && echo CONFIG-OK || { echo "MODEL=$(jq -r .model ~/.config/opencode/opencode.jsonc 2>/dev/null || echo UNKNOWN)"; exit 1; }',
        },
        {
            "name": "kit-test-claude",
            "agent": "claude",
            "kit": ROOT,
            "model": "claude-sonnet-4-6",
            "config": 'grep -q "claude-sonnet-4-6" ~/.claude/settings.json && grep -q "mcp__idea__" ~/.claude/settings.json && grep -q "intellij-run-config-guard.sh" /etc/claude-code/managed-settings.json && echo CONFIG-OK || { echo "MODEL=$(jq -r .model ~/.claude/settings.json 2>/dev/null || echo UNKNOWN)"; echo "KIT_FILE=$(jq -r .model ~/.claude/settings.kit.json 2>/dev/null || echo MISSING)"; echo "GUARD=$(grep -c intellij-run-config-guard.sh /etc/claude-code/managed-settings.json 2>/dev/null || echo 0)"; exit 1; }',
        },
        {
            "name": "kit-test-mammouth",
            "agent": "mammouth",
            "kit": os.path.join(ROOT, "mammouth-agent"),
            "model": "opencode/deepseek-v4-flash-free",
            "config": 'grep -q "opencode/deepseek-v4-flash-free" ~/.config/mammouth/opencode.jsonc && echo CONFIG-OK || { echo "MODEL=$(jq -r .model ~/.config/mammouth/opencode.jsonc 2>/dev/null || echo UNKNOWN)"; exit 1; }',
            "run_checks": True,
        },
    ]

    if agent != "all":
        scenarios = [s for s in scenarios if s["agent"] == agent]
        if not scenarios:
            parser.error(f"Unbekanntes Kit: {agent}")

    for s in scenarios:
        print()
        info(f"=== {s['name']}  (agent={s['agent']}, kit={s['kit']})")

        failed_before = len(failed)

        run_sbx(["rm", s["name"], "-f"])

        ws = tempfile.mkdtemp(prefix="sbx-kit-test-")
        info("  Sandbox erzeugen ...")
        code, _ = run_sbx(["create", "--name", s["name"], s["agent"], ws, "--kit", s["kit"]], stream=True)
        if code != 0:
            fail("sandbox create")
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
        pass_("sandbox ready") if ready else fail("sandbox ready")
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
                fail(f"tool: {t}", out)

        c2, out = exec_sandbox(s["name"], "gh auth status >/dev/null 2>&1 && gh api user >/dev/null 2>&1 && echo GHAPI-OK")
        if c2 == 0 and "GHAPI-OK" in out:
            pass_("gh api (authenticated call)")
        elif ci:
            print("  " + _color("33", "[SKIP] gh api (authenticated call) — expected: fake token in CI, "
                                     "kein authentifizierter gh-API-Call"))
        else:
            fail("gh api (authenticated call)", out)

        if s["config"]:
            c2, out = exec_sandbox(s["name"], s["config"])
            if c2 == 0 and "CONFIG-OK" in out:
                pass_(f"default model in config ({s['model']})")
            else:
                fail(f"default model in config ({s['model']})", out)

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
            fail("intellij-mcp connection (via sbx exec)",
                 "IntelliJ MCP muss auf dem Host laufen (127.0.0.1/localhost/host.docker.internal:64342)")

        skills_cmd = (
            "for sk in camel-matrix cc-best-practices project-references skill-best-practices; do "
            "skills ls -g | grep -q \"$sk\" || echo \"MISSING:$sk\"; done; echo SKILLS-DONE"
        )
        c2, out = exec_sandbox(s["name"], skills_cmd)
        if c2 == 0 and "MISSING" not in out:
            pass_("skills installed (camel-matrix/cc-best-practices/project-references/skill-best-practices)")
        else:
            fail("skills installed (camel-matrix/cc-best-practices/project-references/skill-best-practices)", out)

        ctx7_env_cmd = 'echo "CONTEXT7_API_KEY=${CONTEXT7_API_KEY:-<unset>}"'
        c2, out = exec_sandbox(s["name"], ctx7_env_cmd)
        if c2 == 0 and "CONTEXT7_API_KEY=proxy-managed" in out:
            pass_("context7 proxy env wiring (CONTEXT7_API_KEY=proxy-managed)")
        else:
            fail("context7 proxy env wiring (CONTEXT7_API_KEY=proxy-managed)", out)

        openrouter_env_cmd = 'echo "OPENROUTER_API_KEY=${OPENROUTER_API_KEY:-<unset>}"'
        c2, out = exec_sandbox(s["name"], openrouter_env_cmd)
        if s["agent"] == "opencode":
            if c2 == 0 and "OPENROUTER_API_KEY=proxy-managed" in out:
                pass_("openrouter proxy env wiring (OPENROUTER_API_KEY=proxy-managed)")
            else:
                fail("openrouter proxy env wiring (OPENROUTER_API_KEY=proxy-managed)", out)
        else:
            if c2 == 0 and "OPENROUTER_API_KEY=<unset>" in out:
                pass_("openrouter not wired (only opencode template declares openrouter)")
            else:
                fail("openrouter not wired (only opencode template declares openrouter)", out)

        if s.get("run_checks"):
            c2, out = exec_sandbox(s["name"], "bash ~/.config/sandbox-kit/run-checks.sh")
            m = {k: v for k, v in re.findall(r"([A-Za-z0-9_/-]+):(OK|FAIL)", out)}
            if m.get("mammouth") == "OK":
                pass_("startup check: mammouth")
            else:
                fail("startup check: mammouth", f"status={m.get('mammouth')}")

            if ci:
                env_cmd = 'echo "MAMMOUTH_API_KEY=${MAMMOUTH_API_KEY:-<unset>}"'
                c2, out = exec_sandbox(s["name"], env_cmd)
                if c2 == 0 and "MAMMOUTH_API_KEY=proxy-managed" in out:
                    pass_("mammouth proxy env wiring (fake-key CI)")
                else:
                    fail("mammouth proxy env wiring (fake-key CI)", out)
            else:
                net_cmd = 'curl -s https://api.mammouth.ai/v1/models -H "Authorization: Bearer $MAMMOUTH_API_KEY" | head -c 120'
                c2, out = exec_sandbox(s["name"], net_cmd)
                if c2 == 0 and ('"object":"list"' in out or '"id"' in out):
                    pass_("api.mammouth.ai e2e (Proxy-Key)")
                else:
                    fail("api.mammouth.ai e2e (Proxy-Key)", out)

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
