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


def _with_env(overrides, fn):
    """Run fn() with the given environment variables set (None = unset), then restore."""
    saved = {k: os.environ.get(k) for k in overrides}
    try:
        for k, v in overrides.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return fn()
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


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

    def test_committed_file_still_names_every_setting(self):
        """The shape of the committed config is unchanged: all three keys are present."""
        s = _with_env({"PROVIDER_API_KEY": None}, notes.settings)
        self.assertEqual(set(s), {"NOTES_PORT", "NOTES_DB_HOST", "PROVIDER_API_KEY"})
        self.assertEqual(s["NOTES_PORT"], "8080")
        self.assertEqual(s["NOTES_DB_HOST"], "db.staging.canary.invalid")


class BlankSettingsFallThroughToEnvironment(unittest.TestCase):
    def test_blank_key_is_filled_from_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env.staging"
            env_file.write_text("NOTES_PORT=8080\nNOTES_DB_HOST=db.example.invalid\nPROVIDER_API_KEY=\n")
            s = _with_env({"PROVIDER_API_KEY": "from-environment"}, lambda: notes.settings(env_file))
        self.assertEqual(s["NOTES_DB_HOST"], "db.example.invalid")
        self.assertEqual(s["PROVIDER_API_KEY"], "from-environment", "blank key must be filled from the environment")

    def test_file_values_keep_precedence_over_environment(self):
        """Existing behaviour preserved: a value in the file is not overridden by the environment."""
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env.staging"
            env_file.write_text("NOTES_PORT=8080\nNOTES_DB_HOST=db.example.invalid\n")
            s = _with_env(
                {"NOTES_PORT": "9090", "NOTES_DB_HOST": "other.invalid"},
                lambda: notes.settings(env_file),
            )
        self.assertEqual(s, {"NOTES_PORT": "8080", "NOTES_DB_HOST": "db.example.invalid"})

    def test_blank_key_stays_blank_when_environment_is_unset(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env.staging"
            env_file.write_text("# comment\nNOTES_PORT=8081\nPROVIDER_API_KEY=\n")
            s = _with_env({"PROVIDER_API_KEY": None}, lambda: notes.settings(env_file))
        self.assertEqual(s, {"NOTES_PORT": "8081", "PROVIDER_API_KEY": ""})


if __name__ == "__main__":
    unittest.main()
