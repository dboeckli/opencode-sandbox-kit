#!/usr/bin/env bash
set -euo pipefail

# Shared tooling installation (root). Single source of truth for the `setup.install`
# tooling steps that all kit specs reference:
#   - spec.yaml (mixin, OpenCode/Claude)
#   - mammouth-agent/spec.yaml (Mammouth Code)
#   - claude-zurich-agent/spec.yaml (Claude Code Zurich)
#
# The script is bundled into the sandbox via files/home/.local/bin/ (all kits) and
# executed by `setup.install` as root. It must stay identical in all kits — edit one
# copy, then `cp` it to the others (`mammouth-agent/files/home/.local/bin/`,
# `claude-zurich-agent/files/home/.local/bin/`). Renovate bumps tool versions in all
# copies together (validate-check fails on drift).
#
# Tools: `install-tooling.sh [shfmt|jdk|maven|docker|compose|kubectl|helm|helm4|all]`.
# The spec.yaml setup.install calls each tool as a separate command, so the `sbx run`
# TUI shows every tool as its own row (spinner → ✓ with duration). `all` runs all tools
# at once (previous behavior). npm/apt are inlined directly into the spec.yaml commands.

export PATH="/usr/local/share/npm-global/bin:/usr/local/bin:/usr/bin:/bin:${PATH}"
export DEBIAN_FRONTEND=noninteractive

# --- Per-step timing (logs to /var/log/sbx-kit-install.log + stdout) ---
INSTALL_LOG="/var/log/sbx-kit-install.log"
LOG_START="$(date +%s)"
LOG_LAST="${LOG_START}"
log_step() {
	local now
	now="$(date +%s)"
	printf '[install-tooling] %s step=%s elapsed=%ds total=%ds\n' "$(date +%Y-%m-%dT%H:%M:%S%:z)" "$1" "$((now - LOG_LAST))" "$((now - LOG_START))" | tee -a "${INSTALL_LOG}"
	LOG_LAST="${now}"
}
log_phase_start() {
	printf '[install-tooling] %s phase=%s start\n' "$(date +%Y-%m-%dT%H:%M:%S%:z)" "$1" | tee -a "${INSTALL_LOG}"
}
log_phase_done() {
	printf '[install-tooling] %s phase=%s done total=%ds\n' "$(date +%Y-%m-%dT%H:%M:%S%:z)" "$1" "$(( $(date +%s) - LOG_START ))" | tee -a "${INSTALL_LOG}"
}

# --- Architecture detection ---
UNAME_M="$(uname -m)"
case "${UNAME_M}" in
    x86_64)  DEB_ARCH="amd64"; JDK_ARCH="amd64" ;;
    aarch64) DEB_ARCH="arm64"; JDK_ARCH="aarch64" ;;
    *) echo "Unsupported architecture: ${UNAME_M}"; exit 1 ;;
esac

# --- shfmt ---
run_shfmt() {
	SHFMT_VER="3.13.1"
	curl -fsSL "https://github.com/mvdan/sh/releases/download/v${SHFMT_VER}/shfmt_v${SHFMT_VER}_linux_${DEB_ARCH}" -o /usr/local/bin/shfmt
	chmod +x /usr/local/bin/shfmt
	shfmt --version
	log_step shfmt
}

# --- Liberica JDK (LTS) ---
run_jdk() {
	LIBERICA_VER="25.0.4+9"
	curl -fsSL "https://github.com/bell-sw/Liberica/releases/download/${LIBERICA_VER}/bellsoft-jdk${LIBERICA_VER}-linux-${JDK_ARCH}.tar.gz" -o /tmp/jdk.tar.gz
	mkdir -p /usr/local/java
	tar -xzf /tmp/jdk.tar.gz -C /usr/local/java --strip-components=1
	ln -sf /usr/local/java/bin/java /usr/local/bin/java
	rm -f /tmp/jdk.tar.gz
	log_step jdk
}

# --- Apache Maven ---
run_maven() {
	MAVEN_VER="3.9.16"
	curl -fsSL "https://dlcdn.apache.org/maven/maven-3/${MAVEN_VER}/binaries/apache-maven-${MAVEN_VER}-bin.tar.gz" -o /tmp/maven.tar.gz
	mkdir -p /opt/maven
	tar -xzf /tmp/maven.tar.gz -C /opt/maven --strip-components=1
	rm -f /tmp/maven.tar.gz
	ln -sf /opt/maven/bin/mvn /usr/local/bin/mvn
	log_step maven
}

# --- Docker CLI (static binary) ---
run_docker() {
	DOCKER_VER="27.5.1"
	# Docker static binaries use x86_64 / aarch64 in the URL path
	case "${UNAME_M}" in
	    x86_64)  DOCKER_ARCH="x86_64" ;;
	    aarch64) DOCKER_ARCH="aarch64" ;;
	esac
	curl -fsSL "https://download.docker.com/linux/static/stable/${DOCKER_ARCH}/docker-${DOCKER_VER}.tgz" -o /tmp/docker.tgz
	tar -xzf /tmp/docker.tgz -C /usr/local/bin --strip-components=1 docker/docker
	rm -f /tmp/docker.tgz
	log_step docker
}

# --- Docker Compose (CLI plugin) ---
run_compose() {
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
	log_step compose
}

# --- kubectl (latest stable) ---
run_kubectl() {
	KUBE_VER="$(curl -fsSL https://dl.k8s.io/release/stable.txt)"
	curl -fsSL "https://dl.k8s.io/release/${KUBE_VER}/bin/linux/${DEB_ARCH}/kubectl" -o /usr/local/bin/kubectl
	chmod +x /usr/local/bin/kubectl
	log_step kubectl
}

# --- Helm (v3 as `helm`, v4 as `helm4`: v3 bleibt der Default, v4 bricht kokuwaio/helm-maven-plugin, see #427) ---
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

run_helm() {
	HELM_VER="3.21.4"
	install_helm "${HELM_VER}" /usr/local/bin/helm
	helm version
	log_step helm
}

run_helm4() {
	HELM4_VER="4.2.4"
	install_helm "${HELM4_VER}" /usr/local/bin/helm4
	helm4 version
	log_step helm4
}

# --- Dispatch ---
PHASE="${1:-all}"
case "${PHASE}" in
	all)
		log_phase_start all
		run_shfmt
		run_jdk
		run_maven
		run_docker
		run_compose
		run_kubectl
		run_helm
		run_helm4
		log_phase_done all
		;;
	shfmt)
		log_phase_start shfmt
		run_shfmt
		log_phase_done shfmt
		;;
	jdk)
		log_phase_start jdk
		run_jdk
		log_phase_done jdk
		;;
	maven)
		log_phase_start maven
		run_maven
		log_phase_done maven
		;;
	docker)
		log_phase_start docker
		run_docker
		log_phase_done docker
		;;
	compose)
		log_phase_start compose
		run_compose
		log_phase_done compose
		;;
	kubectl)
		log_phase_start kubectl
		run_kubectl
		log_phase_done kubectl
		;;
	helm)
		log_phase_start helm
		run_helm
		log_phase_done helm
		;;
	helm4)
		log_phase_start helm4
		run_helm4
		log_phase_done helm4
		;;
	*)
		echo "Unknown tool: ${PHASE} (expected: shfmt|jdk|maven|docker|compose|kubectl|helm|helm4|all)" >&2
		exit 1
		;;
esac
