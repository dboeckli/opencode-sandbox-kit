#!/usr/bin/env bash
set -euo pipefail

# Write ~/.m2/settings.xml (agent user) with:
#   - sandbox proxy routing (gateway.docker.internal:3128) so the proxy can
#     MITM and inject the Bearer PAT on maven.pkg.github.com
#   - the github-maven server (password references the proxy-managed sentinel
#     ${env.GITHUB_MAVEN_TOKEN}; the token never lands in the filesystem)
#   - an active host-cache profile when a read-only host Maven repository is
#     mounted (/c/Users/*/.m2/repository, /c/*/maven-repo, /c/*/m2-repository)
# Same behavior as the opencode-agent `setup.startup` step.

path="${HOME}/.m2/settings.xml"
mkdir -p "$(dirname "${path}")"

host_repo=""
for pat in '/c/Users/*/.m2/repository' '/c/*/maven-repo' '/c/*/m2-repository'; do
	# shellcheck disable=SC2086 # intentional glob expansion
	for candidate in ${pat}; do
		if [ -d "${candidate}" ]; then
			host_repo="${candidate}"
			break 2
		fi
	done
done

cat > "${path}" <<'EOF'
<settings xmlns="http://maven.apache.org/SETTINGS/1.2.0">
  <proxies>
    <proxy>
      <id>sbx-proxy</id>
      <active>true</active>
      <protocol>http</protocol>
      <host>gateway.docker.internal</host>
      <port>3128</port>
      <nonProxyHosts>localhost|127.0.0.1|::1</nonProxyHosts>
    </proxy>
  </proxies>
  <servers>
    <server>
      <id>github</id>
      <username>dboeckli</username>
      <password>${env.GITHUB_MAVEN_TOKEN}</password>
    </server>
  </servers>
EOF

if [ -n "${host_repo}" ]; then
	cat >> "${path}" <<EOF
  <profiles>
    <profile>
      <id>host-m2-cache</id>
      <repositories>
        <repository>
          <id>host-cache</id>
          <url>file://${host_repo}</url>
          <releases><enabled>true</enabled></releases>
          <snapshots><enabled>false</enabled></snapshots>
        </repository>
      </repositories>
    </profile>
  </profiles>
  <activeProfiles>
    <activeProfile>host-m2-cache</activeProfile>
  </activeProfiles>
EOF
fi

echo '</settings>' >> "${path}"
echo "Maven settings geschrieben: ${path} (host-cache: ${host_repo:-nein})"
