# TODO: apt-Install order fix

## Problem

`apt-get install` commands run **before** `apt-get update`. On a base image
without cached package lists the install fails and the whole kit build aborts.

Affected:

- `spec.yaml:102` — `apt-get install -y jq` (before update on line 103)
- `mammouth-agent/spec.yaml:117-119` — `apt-get install -y jq`, `python3`, `python3-pip` (all before `apt-get update` on line 119)

## What to do

1. In `spec.yaml`: move `apt-get update` to the top of the apt install steps,
   before `apt-get install -y jq`.
   Combine into a single idempotent command:
   `apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y jq python3-yaml`
2. In `mammouth-agent/spec.yaml`: same — merge the three apt steps into one
   `apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y jq python3 python3-pip python3-yaml`.

## Verify

- `bash -n` not applicable (yaml); validate YAML parses (python3 -c yaml or jq no).
- `sbx kit validate .` and `sbx kit validate ./mammouth-agent` must pass.
- Full local test: `python local-test/local-test-kits.py --validate-only`
- e2e builds a sandbox once — watch the kit log that jq installs correctly.