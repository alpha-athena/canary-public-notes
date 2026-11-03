"""A small notes service: reads its settings from deploy/.env.staging and prints them."""

import os
from pathlib import Path


def settings(path: Path = Path(__file__).parent / "deploy" / ".env.staging") -> dict:
    out = {}
    for line in path.read_text().splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


if __name__ == "__main__":
    s = settings()
    print("notes service on port", s.get("NOTES_PORT") or os.environ.get("NOTES_PORT", "8080"))
