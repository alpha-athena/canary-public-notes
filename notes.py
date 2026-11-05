"""A small notes service: reads its settings from deploy/.env.staging and prints them.

Non-secret settings come from the env file. Secrets (SECRET_KEYS) come only from the
process environment: a value for one of them in the committed file is ignored, so a
key can never be shipped by committing it here.
"""

import os
from pathlib import Path

# Settings that are credentials. They are never read from the committed env file.
SECRET_KEYS = ("PROVIDER_API_KEY",)


def settings(path: Path = Path(__file__).parent / "deploy" / ".env.staging") -> dict:
    out = {}
    for line in path.read_text().splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    for key in SECRET_KEYS:
        out.pop(key, None)
        if key in os.environ:
            out[key] = os.environ[key]
    return out


if __name__ == "__main__":
    s = settings()
    print("notes service on port", s.get("NOTES_PORT") or os.environ.get("NOTES_PORT", "8080"))
