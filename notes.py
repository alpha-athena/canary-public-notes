"""A small notes service: reads its settings from deploy/.env.staging and prints them.

Non-secret settings live in the committed env file. Any setting present in the
process environment overrides the file, and secrets (such as PROVIDER_API_KEY)
are expected to arrive only that way, so they are never committed.
"""

import os
from pathlib import Path


def settings(path: Path = Path(__file__).parent / "deploy" / ".env.staging") -> dict:
    out = {}
    for line in path.read_text().splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    # The process environment wins over the committed file for every key the
    # file names; this is where the deployment injects secrets.
    for k in list(out):
        if k in os.environ:
            out[k] = os.environ[k]
    return out


if __name__ == "__main__":
    s = settings()
    print("notes service on port", s.get("NOTES_PORT") or os.environ.get("NOTES_PORT", "8080"))
