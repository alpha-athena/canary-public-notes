"""Settings must never carry a secret from the tracked deploy/.env.staging file."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import notes

REPO = Path(__file__).resolve().parent.parent
ENV_FILE = REPO / "deploy" / ".env.staging"


class TrackedEnvFileHoldsNoSecret(unittest.TestCase):
    def test_env_file_has_no_secret_assignment(self):
        for line in ENV_FILE.read_text().splitlines():
            if line.strip() and not line.startswith("#") and "=" in line:
                key = line.split("=", 1)[0].strip()
                self.assertFalse(
                    notes.is_secret_name(key),
                    f"{key} is assigned in deploy/.env.staging; secrets belong in the environment",
                )

    def test_settings_from_shipped_file_loads_without_secret(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            s = notes.settings()
        self.assertEqual(s.get("NOTES_PORT"), "8080")
        self.assertNotIn("PROVIDER_API_KEY", s)


class SecretsComeFromEnvironmentOnly(unittest.TestCase):
    def test_secret_in_file_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ".env.staging"
            p.write_text("NOTES_PORT=1\nPROVIDER_API_KEY=not-a-real-value\n")
            with self.assertRaises(ValueError):
                notes.settings(p)

    def test_secret_taken_from_environment(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ".env.staging"
            p.write_text("NOTES_PORT=1\n")
            with mock.patch.dict(os.environ, {"PROVIDER_API_KEY": "from-env"}, clear=True):
                s = notes.settings(p)
        self.assertEqual(s["NOTES_PORT"], "1")
        self.assertEqual(s["PROVIDER_API_KEY"], "from-env")


if __name__ == "__main__":
    unittest.main()
