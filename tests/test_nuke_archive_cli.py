import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))

from change_prism.nuke_archive import cli


class NukeArchiveCliTests(unittest.TestCase):
    def test_yes_packages_without_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            (source / "plate.1001.exr").write_bytes(b"frame")
            script = root / "scene.nk"
            script.write_text(
                "Root {\n inputs 0\n}\n"
                "Read {\n file %s\n name Read1\n}\n"
                % str(source / "plate.%04d.exr").replace("\\", "/"),
                encoding="utf-8",
            )

            code = cli.main(
                [
                    str(script),
                    "--archive-root",
                    str(root / "Archives"),
                    "--yes",
                ]
            )

            self.assertEqual(code, 0)
            self.assertTrue((root / "Archives" / "v0001").is_dir())


if __name__ == "__main__":
    unittest.main()
