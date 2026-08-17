#!/usr/bin/env bash
set -euo pipefail

# Shared tooling installation (root). Single source of truth for the `setup.install`
# tooling steps that both kit specs reference:
#   - spec.yaml (mixin, OpenCode/Claude)
#   - mammouth-agent/spec.yaml (Mammouth Code)
#
# The script is bundled into the sandbox via files/home/.local/bin/ (both kits) and
# executed by `setup.install` as root. It must stay identical in both kits — edit one
# copy, then `cp` it to the other (`mammouth-agent/files/home/.local/bin/`). Renovate
# bumps tool versions in both copies together (validate-check fails on drift).

export PATH="/usr/local/share/npm-global/bin:/usr/local/bin:/usr/bin:/bin:${PATH}"
export DEBIAN_FRONTEND=noninteractive

# --- Architecture detection ---
UNAME_M="$(uname -m)"
case "${UNAME_M}" in
    x86_64)  DEB_ARCH="amd64"; JDK_ARCH="amd64" ;;
    aarch64) DEB_ARCH="arm64"; JDK_ARCH="aarch64" ;;
    *) echo "Unsupported architecture: ${UNAME_M}"; exit 1 ;;
esac

# --- npm globals (bin-links=true so global CLIs land as symlinks in /usr/local/share/npm-global/bin) ---
npm_config_bin_links=true npm install -g ctx7
npm_config_bin_links=true npm install -g skills
npm_config_bin_links=true npm install -g prettier
npm_config_bin_links=true npm install -g renovate

# --- apt (jq, Python for local-test + setup.startup merge, PyYAML) ---
apt-get update
apt-get install -y jq python3 python3-pip python3-yaml

# --- shfmt ---
SHFMT_VER="3.13.1"
curl -fsSL "https://github.com/mvdan/sh/releases/download/v${SHFMT_VER}/shfmt_v${SHFMT_VER}_linux_${DEB_ARCH}" -o /usr/local/bin/shfmt
chmod +x /usr/local/bin/shfmt
shfmt --version

# --- Liberica JDK (LTS) ---
LIBERICA_VER="25.0.4+9"
curl -fsSL "https://github.com/bell-sw/Liberica/releases/download/${LIBERICA_VER}/bellsoft-jdk${LIBERICA_VER}-linux-${JDK_ARCH}.tar.gz" -o /tmp/jdk.tar.gz
mkdir -p /usr/local/java
tar -xzf /tmp/jdk.tar.gz -C /usr/local/java --strip-components=1
ln -sf /usr/local/java/bin/java /usr/local/bin/java
rm -f /tmp/jdk.tar.gz

# --- Apache Maven ---
MAVEN_VER="3.9.16"
curl -fsSL "https://dlcdn.apache.org/maven/maven-3/${MAVEN_VER}/binaries/apache-maven-${MAVEN_VER}-bin.tar.gz" -o /tmp/maven.tar.gz
mkdir -p /opt/maven
tar -xzf /tmp/maven.tar.gz -C /opt/maven --strip-components=1
rm -f /tmp/maven.tar.gz
ln -sf /opt/maven/bin/mvn /usr/local/bin/mvn

# --- Docker CLI (static binary) ---
DOCKER_VER="27.5.1"
# Docker static binaries use x86_64 / aarch64 in the URL path
case "${UNAME_M}" in
    x86_64)  DOCKER_ARCH="x86_64" ;;
    aarch64) DOCKER_ARCH="aarch64" ;;
esac
curl -fsSL "https://download.docker.com/linux/static/stable/${DOCKER_ARCH}/docker-${DOCKER_VER}.tgz" -o /tmp/docker.tgz
tar -xzf /tmp/docker.tgz -C /usr/local/bin --strip-components=1 docker/docker
rm -f /tmp/docker.tgz

# --- Docker Compose (CLI plugin) ---
# Compose release assets use x86_64/aarch64, not amd64/arm64
COMPOSE_VER="5.5.0"
case "${UNAME_M}" in
    x86_64)  COMPOSE_ARCH="x86_64" ;;
    aarch64) COMPOSE_ARCH="aarch64" ;;
esac
mkdir -p /usr/local/lib/docker/cli-plugins
curl -fsSL "https://github.com/docker/compose/releases/download/v${COMPOSE_VER}/docker-compose-linux-${COMPOSE_ARCH}" -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
docker compose version

# --- kubectl (latest stable) ---
KUBE_VER="$(curl -fsSL https://dl.k8s.io/release/stable.txt)"
curl -fsSL "https://dl.k8s.io/release/${KUBE_VER}/bin/linux/${DEB_ARCH}/kubectl" -o /usr/local/bin/kubectl
chmod +x /usr/local/bin/kubectl

# --- Helm v3 (default `helm`, pinned: v4 breaks kokuwaio/helm-maven-plugin, see #427) ---
# --- Helm v4 (as `helm4`): beide Versionen koexistieren, v3 bleibt der Default auf dem PATH ---
install_helm() {
	local ver="$1" dest="$2"
	curl -fsSL "https://get.helm.sh/helm-v${ver}-linux-${DEB_ARCH}.tar.gz" -o /tmp/helm.tar.gz
	mkdir -p /tmp/helm-extract
	tar -xzf /tmp/helm.tar.gz -C /tmp/helm-extract
	local bin
	bin="$(find /tmp/helm-extract -name helm -type f | head -1)"
	mv "${bin}" "${dest}"
	rm -rf /tmp/helm.tar.gz /tmp/helm-extract
}

HELM_VER="3.21.4"
install_helm "${HELM_VER}" /usr/local/bin/helm
helm version

HELM4_VER="4.2.4"
install_helm "${HELM4_VER}" /usr/local/bin/helm4
helm4 version
