#!/usr/bin/env python3
"""Seed the OpenCode model-picker favorites in ~/.local/state/opencode/model.json.

OpenCode keeps the model picker state in
~/.local/state/opencode/model.json and reads it once at startup. Existing
favorites keep their order; only missing seed models are appended.

Must run BEFORE the opencode TUI starts: lifecycle `startup` hooks
concurrently with (in practice after) the sandbox entrypoint, so seeding there
loses the race — opencode loads an empty state and later writes it back,
wiping the seeded favorites. The image bakes the file at build time and
`opencode-entrypoint` re-runs this script right before `exec opencode`.
"""

import json
import os

FAVORITES = [
    {"providerID": "deepseek", "modelID": "deepseek-flash"},
    {"providerID": "deepseek", "modelID": "deepseek-v4-pro"},
    {"providerID": "zai", "modelID": "glm-5.3-flash"},
    {"providerID": "zai", "modelID": "glm-5.3"},
    {"providerID": "zai", "modelID": "glm-4.7-flash"},
    {"providerID": "mistral", "modelID": "zai-glm-5-3"},
]


def main():
    path = os.path.expanduser("~/.local/state/opencode/model.json")
    data = {"recent": [], "favorite": [], "variant": {}}
    if os.path.exists(path):
        try:
            with open(path) as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                data.update(loaded)
        except Exception:
            pass
    current = [f for f in data.get("favorite", []) if isinstance(f, dict)]

    def key(f):
        return (f.get("providerID"), f.get("modelID"))

    have = {key(f) for f in current}
    missing = [f for f in FAVORITES if key(f) not in have]
    if not missing:
        return
    data["favorite"] = current + missing
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, path)


if __name__ == "__main__":
    main()
