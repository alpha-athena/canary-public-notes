"""A small notes service: reads its settings from deploy/.env.staging and prints them.

Settings come from the committed env file exactly as before. A key the file
names but leaves blank (``PROVIDER_API_KEY=``) is filled from the process
environment, which is where the deployment injects secrets, so they are never
committed. Keys with a value in the file keep that value.
"""

import os
from pathlib import Path


def settings(path: Path = Path(__file__).parent / "deploy" / ".env.staging") -> dict:
    out = {}
    for line in path.read_text().splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    # Fill blank values from the environment (file first, environment as the
    # fallback, the same order __main__ already uses for NOTES_PORT).
    for k, v in out.items():
        if v == "" and k in os.environ:
            out[k] = os.environ[k]
    return out


if __name__ == "__main__":
    s = settings()
    print("notes service on port", s.get("NOTES_PORT") or os.environ.get("NOTES_PORT", "8080"))
