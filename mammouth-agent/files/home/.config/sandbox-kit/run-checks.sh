#!/usr/bin/env bash
# Sandbox startup checks - run once per session, output a one-line report.
set +e

report=""

# 1. Context7
if npx ctx7 --help >/dev/null 2>&1; then
  report="$report ctx7:OK"
else
  report="$report ctx7:FAIL"
fi

# 2. IntelliJ MCP server (SSE endpoint reachable)
# Robust: retries each endpoint a few times with a short delay - at session start the
# IntelliJ MCP server may still be starting up, so a single probe fails spuriously.
# host.docker.internal is primary (routes to the Windows host loopback);
# 127.0.0.1/localhost only work in host-network mode (rare).
code=""
for host in host.docker.internal 127.0.0.1 localhost; do
  attempt=1
  while [ "$attempt" -le 3 ]; do
    code=$(curl -s -o /dev/null -w '%{http_code}' -m 4 "http://$host:64342/sse" 2>/dev/null)
    if [ "$code" = "200" ] || [ "$code" = "206" ]; then
      break 2
    fi
    code=""
    attempt=$((attempt + 1))
    [ "$attempt" -le 3 ] && sleep 1
  done
done
if [ "$code" = "200" ] || [ "$code" = "206" ]; then
  report="$report intellij-mcp:OK"
else
  report="$report intellij-mcp:FAIL"
fi

# 3. gh CLI + gh api (authenticated API call)
if gh auth status >/dev/null 2>&1 && gh api user >/dev/null 2>&1; then
  report="$report gh:OK"
else
  report="$report gh:FAIL"
fi

# 4. Java / Maven
if java -version >/dev/null 2>&1 && mvn -version >/dev/null 2>&1; then
  report="$report java/maven:OK"
else
  report="$report java/maven:FAIL"
fi

# 5. Docker CLI (isolated daemon in the microVM)
if docker version >/dev/null 2>&1; then
  report="$report docker:OK"
else
  report="$report docker:FAIL"
fi

# 6. kubectl
if kubectl version --client >/dev/null 2>&1; then
  report="$report kubectl:OK"
else
  report="$report kubectl:FAIL"
fi

# 7. Skills
if skills ls -g >/dev/null 2>&1; then
  report="$report skills:OK"
else
  report="$report skills:FAIL"
fi

# 8. Mammouth Code
if command -v mammouth >/dev/null 2>&1; then
  report="$report mammouth:OK"
else
  report="$report mammouth:FAIL"
fi

echo "[startup-checks]$report"
