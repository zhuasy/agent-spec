"""Settings. A config file is a JSON object that overrides DEFAULTS."""
import json

DEFAULTS = {
    "sla_hours": 48,
    "page_size": 50,
}


def load_config(path=None):
    config = dict(DEFAULTS)
    if path is None:
        return config
    with open(path, encoding="utf-8") as f:
        overrides = json.load(f)
    for key, value in overrides.items():
        if key not in DEFAULTS:
            raise ValueError("unknown setting: %s" % key)
        config[key] = value
    return config
