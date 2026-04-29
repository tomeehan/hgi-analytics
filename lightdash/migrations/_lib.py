"""
Shared helpers for lightdash/migrations/* one-shot scripts.

Each migration imports `load_env`, `api`, and the four LIGHTDASH_*
identifiers from this module. Migrations are run-once scripts (see
the directory README), so this is the only piece of shared state
they're allowed to depend on.
"""

import os
import sys
from pathlib import Path

import requests


def load_env():
    """Populate os.environ from <repo_root>/.env if present (no extra dep).

    Migrations live two directories below the repo root
    (lightdash/migrations/), hence parents[2].
    """
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())


load_env()

try:
    BASE_URL = os.environ["LIGHTDASH_URL"]
    TOKEN = os.environ["LIGHTDASH_TOKEN"]
    PROJECT_UUID = os.environ["LIGHTDASH_PROJECT_UUID"]
    SPACE_UUID = os.environ["LIGHTDASH_SPACE_UUID"]
except KeyError as e:
    sys.exit(f"Missing required env var {e}. Populate .env (see .env.example).")

HEADERS = {
    "Authorization": f"ApiKey {TOKEN}",
    "Content-Type": "application/json",
}


def api(method, path, body=None, *, allow_404=False):
    """Make a Lightdash API call, returning the parsed `results` payload.

    Pass `allow_404=True` to suppress sys.exit on 404 (useful for
    idempotent DELETEs where the resource may already be gone).
    """
    url = f"{BASE_URL}/api/v1{path}"
    r = requests.request(method, url, headers=HEADERS, json=body)
    if r.status_code == 404 and allow_404:
        return None
    if not r.ok:
        print(f"  ERROR {method} {path} → {r.status_code}: {r.text[:300]}")
        sys.exit(1)
    if r.status_code == 204 or not r.text:
        return None
    return r.json().get("results")
