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
code=$(curl -s -o /dev/null -w '%{http_code}' -m 3 http://host.docker.internal:64342/sse 2>/dev/null)
if [ "$code" = "200" ] || [ "$code" = "206" ]; then
  report="$report intellij-mcp:OK"
else
  report="$report intellij-mcp:FAIL"
fi

# 3. gh CLI
if gh auth status >/dev/null 2>&1; then
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

echo "[startup-checks]$report"
