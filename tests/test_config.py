import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from freshnessguard.config import load_env


class ConfigTests(unittest.TestCase):
    def test_explicit_file_quotes_and_literal_values(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {}, clear=True):
            path = Path(folder) / ".env"
            path.write_text('# comment\nTAVILY_API_KEY="test-only"\nBIFROST_MODEL=provider/model\nFRESHNESSGUARD_TOKEN=$(never-execute)\n', encoding="utf-8")
            load_env(path)
            self.assertEqual(os.environ["TAVILY_API_KEY"], "test-only")
            self.assertEqual(os.environ["FRESHNESSGUARD_TOKEN"], "$(never-execute)")

    def test_rejects_unrelated_environment_overrides(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / ".env"
            path.write_text('PATH=unexpected\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_env(path)

    def test_no_implicit_file_load(self):
        with patch.dict(os.environ, {}, clear=True):
            load_env(None)
            self.assertNotIn("TAVILY_API_KEY", os.environ)
