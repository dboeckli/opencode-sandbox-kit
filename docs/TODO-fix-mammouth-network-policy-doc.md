# Task: Fix Mammouth network-policy documentation

## Problem

Two inconsistencies:

1. **Contradiction**: `mammouth-agent/spec.yaml:89` allows `*.exa.ai:443`,
   but `mammouth-agent/files/home/.config/mammouth/AGENTS.md` (Network policy
   section) states „Not reachable (blocked): general web search providers
   (e.g. `*.exa.ai`)".
2. **Missing file**: `AGENTS.md:259` says the network policy is documented in
   3 files („OpenCode, Claude, Mammouth"). The mammouth kit has **no**
   `network-policy.md`; the allow-list is inlined in its `AGENTS.md`.

## What to do

1. Fix the contradiction — decide the intended behavior:
   - If `*.exa.ai` stays allowed (websearch/webfetch provider, `spec.yaml`
     comment), remove it from the block-list sentence in the mammouth AGENTS.md.
   - If it should be blocked, remove `*.exa.ai:443` from
     `mammouth-agent/spec.yaml:89` (and update the mixin accordingly).
2. Align the doc shape with the mixin kits:
   - either add `mammouth-agent/files/home/.config/mammouth/network-policy.md`
     (mirror of `files/home/.config/opencode/network-policy.md`, mammouth-flavored
     allow-list) and update the AGENTS.md to reference it,
   - or keep it inline and correct `AGENTS.md` root text which promises a
     file.
3. Also verify the limit list content matches the mammouth spec (OpenCode APIs
   vs Mammouth APIs differ; `start.spring.io`, `get.helm.sh`, `download.docker.com`,
   pypi etc. currently missing from the inline list).

## Verify

- `grep -rn "exa.ai" mammouth-agent/` — no contradiction left.
- The doc-only network list equals the `permissions.network.allow` of
  `mammouth-agent/spec.yaml` (minus/pus `:443` normalization).