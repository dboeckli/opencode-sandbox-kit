#!/usr/bin/env python3
"""IntelliJ MCP repair: ermittelt den aktuellen Port des JetBrains-MCP-Servers und
erneuert die sbx-Gateway-Registrierung (rm + add) inklusive Verifikation.

Hintergrund: Der MCP-Port ist dynamisch (JetBrains YouTrack IJPL-248682; beobachtet
64342 und 64615) und kann nach jedem Start/Update von IntelliJ wechseln. Dieses
Script macht die Neuregistrierung reproduzierbar, ohne den Port manuell in
Settings -> Tools -> MCP Server nachzuschlagen.

Ausfuehrung: auf dem Windows-Host (sbx CLI ist dort installiert), nicht in der Sandbox.
Optionaler Parameter: Port, um die automatische Ermittlung zu uebergehen.
"""

import csv
import re
import shutil
import socket
import subprocess
import sys
from io import StringIO

FALLBACK_PORTS = [64615, 64342]
PROCESS_NAMES = ("idea64.exe", "idea.exe")


def fail(msg):
    print(f"FEHLER: {msg}", file=sys.stderr)
    sys.exit(1)


def _run(args, capture=False):
    return subprocess.run(
        args,
        capture_output=capture,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def find_idea_pids():
    """PIDs der laufenden IntelliJ-Prozesse ueber tasklist ermitteln."""
    out = _run(["tasklist", "/NH", "/FO", "CSV"], capture=True).stdout
    pids = set()
    for row in csv.reader(StringIO(out)):
        if len(row) >= 2 and row[0].strip().lower() in PROCESS_NAMES and row[1].isdigit():
            pids.add(int(row[1]))
    return pids


def listening_ports(pids):
    """Lokale Ports der LISTENING-TCP-Sockets der uebergebenen PIDs (netstat)."""
    out = _run(["netstat", "-ano", "-p", "tcp"], capture=True).stdout
    ports = set()
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[0].upper() == "TCP" and parts[3].upper() == "LISTENING":
            try:
                pid = int(parts[4])
            except ValueError:
                continue
            if pid in pids:
                port_str = parts[1].rsplit(":", 1)[-1]
                if port_str.isdigit():
                    ports.add(int(port_str))
    return sorted(ports)


def is_mcp_port(port, timeout=2):
    """Probe GET /sse auf 127.0.0.1:<port>; True wenn der Server mit 200/206 antwortet."""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout) as sock:
            sock.sendall(b"GET /sse HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n")
            sock.settimeout(timeout)
            data = sock.recv(4096)
        status = data.split(b"\r\n", 1)[0].decode("latin1", "replace")
        return bool(re.search(r"\s(200|206)\s", status))
    except (OSError, socket.timeout):
        return False


def run_sbx(args):
    print(">>> sbx " + " ".join(args))
    return _run(["sbx"] + args).returncode


def main():
    print("")
    print("============================================================")
    print(" IntelliJ MCP repair (Port ermitteln + Registrierung neu)")
    print("============================================================")

    if not shutil.which("sbx"):
        fail("sbx nicht gefunden. Diese Run-Config gehoert auf den Windows-Host (sbx installiert).")

    port = 0
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])

    if port == 0:
        pids = find_idea_pids()
        print(f"Idea-Prozesse (PIDs): {sorted(pids) if pids else 'keine gefunden'}")
        candidates = listening_ports(pids) + FALLBACK_PORTS
        for candidate in candidates:
            if is_mcp_port(candidate):
                port = candidate
                break

    if not port:
        fail("Kein IntelliJ-MCP-Port gefunden.\n"
             "  1) IntelliJ IDEA muss laufen und das Projekt geoeffnet sein (MCP-Server aktiv).\n"
             "  2) Aktuellen Port pruefen: Settings -> Tools -> MCP Server -> 'Copy Config'.")
    print(f"Aktueller IntelliJ-MCP-Port: {port}")

    # Alte Registrierung entfernen; Fehler ist ok (idea evtl. noch nicht registriert).
    run_sbx(["mcp", "rm", "idea"])

    url = f"http://localhost:{port}/stream"
    rc = run_sbx(["mcp", "add", "idea", "--url", url, "--skip-ssrf-check"])
    if rc != 0:
        fail(f"sbx mcp add fehlgeschlagen (exit {rc}).")

    print("\n>>> sbx mcp inspect idea    (erwartet: URL http://localhost:<port>/stream)")
    inspect = _run(["sbx", "mcp", "inspect", "idea"], capture=True)
    sys.stdout.write(inspect.stdout)
    if f":{port}/stream" not in inspect.stdout:
        print(f"WARNUNG: Registrierte URL enthaelt nicht den ermittelten Port {port}.", file=sys.stderr)

    print("\n>>> sbx mcp ls               (erwartet: idea   remote   ready)")
    listing = _run(["sbx", "mcp", "ls"], capture=True)
    sys.stdout.write(listing.stdout)
    if re.search(r"idea.*remote.*ready", listing.stdout):
        print(f"\nOK: idea ist unter http://localhost:{port}/stream registriert und ready.")
    else:
        print("\nHinweis: idea wurde nicht als 'remote ready' gefunden - Status oben pruefen.", file=sys.stderr)

    print("\nFertig. Falls eine laufende Sandbox noch den alten Port nutzt:")
    print("  sbx mcp load idea --sandbox <name>")


if __name__ == "__main__":
    main()
