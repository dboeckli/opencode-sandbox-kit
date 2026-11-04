#!/usr/bin/env bash
set -euo pipefail

# Import the sandbox proxy CA into the JDK cacerts (root).
# Same behavior as the opencode-agent `setup.startup` step: Java/Maven must
# trust the proxy TLS interception so proxy-managed credentials can be
# injected into Maven builds. Idempotent (delete + import on every start).

if [ -n "${PROXY_CA_CERT_B64:-}" ]; then
	echo "${PROXY_CA_CERT_B64}" | base64 -d > /tmp/proxy-ca.crt 2>/dev/null || true
fi
CA=/tmp/proxy-ca.crt
[ -s "${CA}" ] || CA=/usr/local/share/ca-certificates/proxy-ca.crt
KS="${JAVA_HOME:-/usr/local/java}/lib/security/cacerts"
ok=0
for _ in $(seq 1 300); do
	if [ -f "${CA}" ] && [ -f "${KS}" ] && command -v keytool >/dev/null 2>&1; then
		keytool -delete -alias proxy-ca -keystore "${KS}" -storepass changeit >/dev/null 2>&1 || true
		if keytool -importcert -noprompt -alias proxy-ca -file "${CA}" -keystore "${KS}" -storepass changeit >/dev/null 2>&1; then
			echo "proxy-ca in JDK cacerts importiert (Quelle: ${CA})"
			ok=1
		else
			echo "FEHLER: proxy-ca Import in JDK cacerts fehlgeschlagen"
		fi
		break
	fi
	sleep 1
done
[ "${ok}" = 1 ] || echo "proxy-ca Import nach 300s uebersprungen (KS=$([ -f "${KS}" ] && echo da || echo fehlt), CA=$([ -f "${CA}" ] && echo da || echo fehlt))"
