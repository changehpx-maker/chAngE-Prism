import os
import tempfile
import unittest
from pathlib import Path

from change_prism.batch_import.service import prune_old_files


class BatchImportServiceTests(unittest.TestCase):
    def test_prune_old_files_keeps_newest_matches_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index in range(5):
                path = root / ("run_%02d.log" % index)
                path.write_text(str(index), encoding="utf-8")
                os.utime(str(path), (index + 1, index + 1))
            unrelated = root / "keep.txt"
            unrelated.write_text("keep", encoding="utf-8")

            prune_old_files(
                str(root),
                prefix="run_",
                suffix=".log",
                keep=2,
            )

            self.assertEqual(
                sorted(path.name for path in root.glob("*.log")),
                ["run_03.log", "run_04.log"],
            )
            self.assertTrue(unrelated.is_file())


if __name__ == "__main__":
    unittest.main()
