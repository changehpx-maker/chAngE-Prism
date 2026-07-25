import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from qtpy.QtWidgets import QApplication, QFileDialog
    from change_prism.batch_import.dialog import BatchImportDialog
except Exception:
    QApplication = None
    QFileDialog = None
    BatchImportDialog = None


@unittest.skipUnless(QApplication, "Requires Prism Qt runtime")
class BatchImportDialogTests(unittest.TestCase):
    def test_browse_local_path_updates_and_saves_config(self):
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            dialog = BatchImportDialog(object(), tmp, lambda _data: None)
            saved = []
            dialog._save_config_value = (
                lambda key, value: saved.append((key, value))
            )
            try:
                with mock.patch.object(
                    QFileDialog, "getExistingDirectory", return_value=tmp
                ):
                    dialog._browse_local_path()
                self.assertEqual(dialog.local_path_edit.text(), tmp)
                self.assertEqual(saved, [("local_projects_root", tmp)])
            finally:
                dialog.close()
        app.processEvents()


if __name__ == "__main__":
    unittest.main()
