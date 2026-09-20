# syntax=docker/dockerfile:1
#
# Pinned Mistral Vibe image for the `mistral-vibe-agent` sandbox kit (issue #116).
# Build on the versioned `shell-docker` sandbox template (Docker Engine inside the
# sandbox, tooling parity with the other kits) and bake a pinned Vibe version,
# following https://docs.docker.com/guides/mistral-vibe-sandbox/.
#
# Build + publish (linux/amd64, provenance/SBOM), from this directory.
# amd64 only: `uv tool install` does not run under QEMU arm64 emulation; an
# arm64 build needs a native arm64 runner + a buildx imagetools manifest merge.
#
# CI path (publish-mistral-vibe-image.yml) pushes only the version tag:
#   docker buildx build \
#     --platform linux/amd64 \
#     --provenance=true --sbom=true \
#     -t domboeckli/sbx-mistral-vibe:${VIBE_VERSION} \
#     --push .
#
# Local bootstrap additionally tags `local` (moving tag for a locally built image):
#   docker buildx build \
#     --platform linux/amd64 \
#     --provenance=true --sbom=true \
#     -t domboeckli/sbx-mistral-vibe:${VIBE_VERSION} \
#     -t domboeckli/sbx-mistral-vibe:local \
#     --push .
#
# The kit (spec.yaml `sandbox.image`) references the version tag.

ARG BASE_IMAGE=docker/sandbox-templates:shell-docker-0.5.0
FROM ${BASE_IMAGE}

# Pin the agent version for reproducible sandboxes.
# Check https://pypi.org/project/mistral-vibe/ and bump as needed (Renovate tracks it).
ARG VIBE_VERSION=2.25.5

# Install Vibe as the non-root agent user. The socks extra is installed explicitly
# so the agent works through the sandbox proxy (some releases don't pull it in).
USER agent
RUN uv tool install "mistral-vibe==${VIBE_VERSION}" --with "httpx[socks]" \
    && vibe --version

# Launch Vibe in auto-approve mode; the kit does not override the entrypoint.
CMD ["vibe", "--agent", "auto-approve"]
