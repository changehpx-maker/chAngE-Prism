import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from change_prism.batch_import.service import (
    get_log_dir,
    prune_old_files,
    write_failure_report,
)


class BatchImportServiceTests(unittest.TestCase):
    def test_diagnostics_use_plugin_feature_and_type_hierarchy(self):
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch(
                "change_prism.batch_import.service.tempfile.gettempdir",
                return_value=directory,
            ):
                log_dir = get_log_dir(None, "pdg")
                report = write_failure_report(
                    None,
                    "show",
                    [{"shot": "SC03_shot027", "error": "test"}],
                )

            root = Path(directory) / "chAngE_Prism" / "batch_import"
            self.assertEqual(
                Path(log_dir),
                root / "pdg" / "logs",
            )
            self.assertEqual(
                Path(report).parent,
                root / "reports" / "json",
            )
            self.assertTrue(Path(report).is_file())

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
