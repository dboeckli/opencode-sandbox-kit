# syntax=docker/dockerfile:1
#
# Pinned Mistral Vibe image for the `mistral-vibe-agent` sandbox kit (issue #116).
# Build on the versioned `shell-docker` sandbox template (Docker Engine inside the
# sandbox, tooling parity with the other kits) and bake a pinned Vibe version,
# following https://docs.docker.com/guides/mistral-vibe-sandbox/.
#
# Build + publish (multi-arch, provenance/SBOM), from this directory.
# CI (build-and-publish-mistral-vibe-image.yml) builds linux/amd64 and linux/arm64 on
# NATIVE runners (ubuntu-latest / ubuntu-24.04-arm) and merges them with
# `docker buildx imagetools create`: `uv tool install` does not run under QEMU
# arm64 emulation (buildx exit 1).
#
# Local build (single arch, from the host architecture), tags version + `local`:
#   docker buildx build \
#     --platform linux/amd64 \
#     --provenance=true --sbom=true \
#     -t domboeckli/sbx-mistral-vibe:${VIBE_VERSION} \
#     -t domboeckli/sbx-mistral-vibe:local \
#     --push .
#
# The kit (spec.yaml `sandbox.image`, arg `imageTag`) references the version tag.

ARG BASE_IMAGE=docker/sandbox-templates:shell-docker-0.7.0
FROM ${BASE_IMAGE}

# Pin the agent version for reproducible sandboxes.
# Check https://pypi.org/project/mistral-vibe/ and bump as needed (Renovate tracks it).
ARG VIBE_VERSION=2.25.8

# Build tools for source builds of native dependencies: `miniaudio` (a transitive
# mistral-vibe dependency) ships no arm64 wheel for Python 3.14, so uv compiles it
# from source — needs a C/C++ compiler and the Python dev headers (pyconfig.h).
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc g++ python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Vibe as the non-root agent user. The socks extra is installed explicitly
# so the agent works through the sandbox proxy (some releases don't pull it in).
USER agent
RUN uv tool install "mistral-vibe==${VIBE_VERSION}" --with "httpx[socks]" \
    && vibe --version

# Launch Vibe in auto-approve mode. For the sandbox the kit sets
# `sandbox.entrypoint` in spec.yaml (sbx starts the default shell otherwise);
# this CMD is kept for plain `docker run`.
CMD ["vibe", "--agent", "auto-approve"]
