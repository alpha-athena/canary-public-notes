"""A small notes service: reads its settings from deploy/.env.staging and prints them.

Secrets (keys, tokens, passwords) are never taken from the tracked settings
file; they come from the process environment only.
"""

import os
from pathlib import Path

# A setting whose name ends in one of these is a secret: it is only ever read
# from the process environment, never from a file that lives in git.
SECRET_SUFFIXES = ("_KEY", "_SECRET", "_TOKEN", "_PASSWORD")


def is_secret_name(name: str) -> bool:
    return name.upper().endswith(SECRET_SUFFIXES)


def settings(path: Path = Path(__file__).parent / "deploy" / ".env.staging") -> dict:
    out = {}
    for line in path.read_text().splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            k = k.strip()
            if is_secret_name(k):
                raise ValueError(
                    f"{k} is a secret and must not be stored in {path.name}; "
                    "set it in the process environment instead"
                )
            out[k] = v.strip()
    for k, v in os.environ.items():
        if is_secret_name(k):
            out[k] = v
    return out


if __name__ == "__main__":
    s = settings()
    print("notes service on port", s.get("NOTES_PORT") or os.environ.get("NOTES_PORT", "8080"))
