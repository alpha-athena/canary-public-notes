"""Tests for notes.settings: no credentials in the committed env file, secrets from the process environment."""

import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import notes  # noqa: E402

SECRET_KEY = re.compile(r"(KEY|SECRET|TOKEN|PASSWORD|PASS|CREDENTIAL)S?$", re.IGNORECASE)


class CommittedEnvFile(unittest.TestCase):
    def test_no_credential_values_committed(self):
        """The tracked env file carries non-secret settings only; secret-shaped keys must be empty."""
        env_file = ROOT / "deploy" / ".env.staging"
        committed = {}
        for line in env_file.read_text().splitlines():
            if line.strip() and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                committed[k.strip()] = v.strip()
        leaked = sorted(k for k, v in committed.items() if SECRET_KEY.search(k) and v)
        self.assertEqual(leaked, [], f"credential-shaped values committed in {env_file.name}: {leaked}")


class EnvironmentOverlay(unittest.TestCase):
    def test_process_environment_supplies_secrets(self):
        """A key left empty in the file is filled from the process environment."""
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ".env"
            p.write_text("NOTES_PORT=8080\nPROVIDER_API_KEY=\n")
            with mock.patch.dict(os.environ, {"PROVIDER_API_KEY": "from-env"}):
                s = notes.settings(p)
        self.assertEqual(s["NOTES_PORT"], "8080")
        self.assertEqual(s["PROVIDER_API_KEY"], "from-env")

    def test_process_environment_wins_over_file(self):
        """The deploy environment overrides whatever the file says."""
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ".env"
            p.write_text("NOTES_PORT=8080\n")
            with mock.patch.dict(os.environ, {"NOTES_PORT": "9090"}):
                s = notes.settings(p)
        self.assertEqual(s["NOTES_PORT"], "9090")


if __name__ == "__main__":
    unittest.main()
