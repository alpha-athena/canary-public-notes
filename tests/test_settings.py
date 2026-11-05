"""Secrets never come from the committed env file; they come from the process environment."""

import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import notes  # noqa: E402

ENV_FILE = ROOT / "deploy" / ".env.staging"
# vendor-style prefix followed by a long hex/base64-ish body, e.g. "ak-....<32 hex>"
CREDENTIAL_SHAPE = re.compile(r"^[A-Za-z]{2,8}-[A-Za-z0-9_-]{0,16}[0-9a-fA-F]{24,}$")


def raw_pairs(path: Path) -> dict:
    out = {}
    for line in path.read_text().splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


class CommittedEnvFileHoldsNoSecret(unittest.TestCase):
    def test_no_secret_key_is_assigned_in_the_tracked_file(self):
        pairs = raw_pairs(ENV_FILE)
        for key in notes.SECRET_KEYS:
            self.assertNotIn(key, pairs, f"{key} must not be assigned in {ENV_FILE.relative_to(ROOT)}")

    def test_no_value_in_the_tracked_file_looks_like_a_credential(self):
        for key, value in raw_pairs(ENV_FILE).items():
            self.assertIsNone(
                CREDENTIAL_SHAPE.match(value),
                f"{key} in {ENV_FILE.relative_to(ROOT)} holds a credential-shaped value",
            )


class SecretsComeOnlyFromTheEnvironment(unittest.TestCase):
    def setUp(self):
        self._saved = os.environ.pop("PROVIDER_API_KEY", None)
        self.tmp = tempfile.NamedTemporaryFile("w", suffix=".env", delete=False)
        self.tmp.write("NOTES_PORT=9090\nPROVIDER_API_KEY=should-be-ignored\n")
        self.tmp.close()

    def tearDown(self):
        os.unlink(self.tmp.name)
        os.environ.pop("PROVIDER_API_KEY", None)
        if self._saved is not None:
            os.environ["PROVIDER_API_KEY"] = self._saved

    def test_secret_in_env_file_is_ignored(self):
        s = notes.settings(Path(self.tmp.name))
        self.assertEqual(s["NOTES_PORT"], "9090")
        self.assertNotIn("PROVIDER_API_KEY", s)

    def test_secret_from_process_environment_is_used(self):
        os.environ["PROVIDER_API_KEY"] = "from-environment"
        s = notes.settings(Path(self.tmp.name))
        self.assertEqual(s["PROVIDER_API_KEY"], "from-environment")

    def test_default_settings_still_load_non_secret_values(self):
        s = notes.settings()
        self.assertEqual(s["NOTES_PORT"], "8080")
        self.assertNotIn("PROVIDER_API_KEY", s)


if __name__ == "__main__":
    unittest.main()
