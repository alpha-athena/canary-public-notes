"""Tests for notes.settings(): secrets come from the environment, never from a committed file."""

import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import notes  # noqa: E402

# A settings key whose name says it holds a credential.
SECRET_KEY_NAME = re.compile(r"(KEY|SECRET|TOKEN|PASSWORD|PASSWD)$", re.IGNORECASE)


class CommittedSettingsHoldNoSecrets(unittest.TestCase):
    def test_deploy_env_files_have_no_credential_values(self):
        """Every committed deploy/*.env* file may name a credential key only with an empty value."""
        env_files = sorted(p for p in (ROOT / "deploy").iterdir() if p.is_file() and ".env" in p.name)
        self.assertTrue(env_files, "expected at least one deploy/.env* file")
        offenders = []
        for path in env_files:
            for lineno, line in enumerate(path.read_text().splitlines(), 1):
                if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
                    continue
                key, value = (s.strip() for s in line.split("=", 1))
                if SECRET_KEY_NAME.search(key) and value:
                    offenders.append(f"{path.relative_to(ROOT)}:{lineno} assigns a value to {key}")
        self.assertEqual(offenders, [], "credential values must not be committed:\n" + "\n".join(offenders))


class SettingsComeFromEnvironment(unittest.TestCase):
    def test_environment_overrides_file_and_supplies_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env.staging"
            env_file.write_text("NOTES_PORT=8080\nNOTES_DB_HOST=db.example.invalid\nPROVIDER_API_KEY=\n")
            saved = {k: os.environ.get(k) for k in ("NOTES_PORT", "PROVIDER_API_KEY")}
            try:
                os.environ["NOTES_PORT"] = "9090"
                os.environ["PROVIDER_API_KEY"] = "from-environment"
                s = notes.settings(env_file)
            finally:
                for k, v in saved.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v
        self.assertEqual(s["NOTES_DB_HOST"], "db.example.invalid")
        self.assertEqual(s["NOTES_PORT"], "9090", "environment must win over the file")
        self.assertEqual(s["PROVIDER_API_KEY"], "from-environment", "secret must come from the environment")

    def test_file_values_still_used_when_environment_is_unset(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env.staging"
            env_file.write_text("# comment\nNOTES_PORT=8081\n")
            saved = os.environ.pop("NOTES_PORT", None)
            try:
                s = notes.settings(env_file)
            finally:
                if saved is not None:
                    os.environ["NOTES_PORT"] = saved
        self.assertEqual(s, {"NOTES_PORT": "8081"})


if __name__ == "__main__":
    unittest.main()
