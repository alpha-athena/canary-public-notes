"""A small notes service: reads its settings from deploy/.env.staging, overlaid with the process environment."""

import os
from pathlib import Path


def settings(path: Path = Path(__file__).parent / "deploy" / ".env.staging") -> dict:
    """Return settings from the env file, with the process environment taking precedence.

    The env file is tracked in git and must hold only non-secret settings; secrets such as
    PROVIDER_API_KEY are left empty in the file and supplied by the deploy environment.
    """
    out = {}
    for line in path.read_text().splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    for k in list(out):
        if k in os.environ:
            out[k] = os.environ[k]
    return out


if __name__ == "__main__":
    s = settings()
    print("notes service on port", s.get("NOTES_PORT") or os.environ.get("NOTES_PORT", "8080"))
