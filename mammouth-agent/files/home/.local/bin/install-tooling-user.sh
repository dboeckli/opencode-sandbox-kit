#!/usr/bin/env bash
set -euo pipefail

# Shared agent-user tooling installation (uid 1000). Single source of truth for the
# `user: "1000"` `setup.install` steps that both kit specs reference:
#   - spec.yaml (mixin, OpenCode/Claude)
#   - mammouth-agent/spec.yaml (Mammouth Code)
#
# The script is bundled into the sandbox via files/home/.local/bin/ (both kits) and
# executed by `setup.install` with user "1000" (~ = /home/agent). It must stay
# identical in both kits — edit one copy, then `cp` it to the other
# (`mammouth-agent/files/home/.local/bin/`). Renovate bumps tool versions in both
# copies together (validate-check fails on drift).

export PATH="/usr/local/share/npm-global/bin:/usr/local/bin:/usr/bin:/bin:${PATH}"

# --- skills (vercel-labs) → ~/.agents/skills ---
/usr/local/share/npm-global/bin/skills add -g -y --all https://github.com/dboeckli/ai-agent-skills.git

# --- Claude Code statusline ---
git clone --depth 1 https://github.com/dboeckli/ai-agent-skills.git /tmp/ai-agent-skills
mkdir -p ~/.claude
cp /tmp/ai-agent-skills/scripts/statusline.sh ~/.claude/statusline.sh
chmod +x ~/.claude/statusline.sh
rm -rf /tmp/ai-agent-skills

# --- Repsy docs (offline reference) → ~/docs/repsy-docs ---
# Shallow clone of the Hugo markdown source (content/), no theme submodule needed.
# Idempotent: existing checkout is fast-forwarded on re-install (e.g. `sbx kit add`).
if [ -d ~/docs/repsy-docs/.git ]; then
  git -C ~/docs/repsy-docs pull --ff-only --quiet
else
  mkdir -p ~/docs
  git clone --depth 1 --single-branch https://github.com/repsyio/repsy-docs.git ~/docs/repsy-docs
fi
