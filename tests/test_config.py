import sys
import json
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))

from change_prism import config
from change_prism.config import get_config_path


class ConfigTests(unittest.TestCase):
    def test_config_path_remains_at_plugin_root(self):
        self.assertEqual(Path(get_config_path()).resolve(), ROOT / "config.json")

    def test_review_copy_destination_root_uses_nested_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text(
                json.dumps(
                    {"review_copy": {"destination_root": "Z:/daily_review"}}
                ),
                encoding="utf-8",
            )
            with mock.patch.object(config, "_CONFIG_PATH", str(path)):
                self.assertEqual(
                    config.get_review_copy_destination_root(),
                    "Z:/daily_review",
                )


if __name__ == "__main__":
    unittest.main()
