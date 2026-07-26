import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from qtpy.QtWidgets import QApplication, QFileDialog
    from qtpy.QtWidgets import QWidget
    from change_prism.batch_import.controller import (
        BatchImportController,
    )
    from change_prism.batch_import.dialog import BatchImportDialog
except Exception:
    QApplication = None
    QFileDialog = None
    BatchImportDialog = None
    BatchImportController = None


class _Reporter:
    def __init__(self):
        self.progress = []

    def set_status(self, _text):
        pass

    def update_progress(self, value):
        self.progress.append(value)


class _Projects:
    def createProject(self, name, path, **_kwargs):
        del name
        config = Path(path) / "00_Pipeline" / "project_config.json"
        config.parent.mkdir(parents=True)
        config.write_text("{}", encoding="utf-8")
        return str(config)

    def changeProject(self, _path):
        pass

    def setDepartments(self, _entity_type, _departments):
        pass


class _Entities:
    def getShots(self, sequence=None):
        del sequence
        return []

    def createEntity(self, entity, **_kwargs):
        return {"entity": dict(entity)}

    def createDepartment(self, *_args, **_kwargs):
        pass

    def createCategory(self, *_args, **_kwargs):
        pass

    def getPresetScenes(self):
        return []

    def setShotRange(self, *_args):
        pass

    def getMetaData(self, _entity):
        return {}

    def setMetaData(self, **_kwargs):
        pass


class _Products:
    def __init__(self, root):
        self.root = root

    def createProduct(self, _entity, _name):
        return self.root

    def getNextAvailableVersion(self, _entity, _name):
        return "v0001"


class _MediaProducts:
    pass


class _ImportCore:
    def __init__(self, product_root):
        self.projects = _Projects()
        self.entities = _Entities()
        self.products = _Products(product_root)
        self.mediaProducts = _MediaProducts()
        self.username = "tester"
        self.user = "tester"

    def saveVersionInfo(self, filepath=None, details=None):
        del filepath, details


@unittest.skipUnless(QApplication, "Requires Prism Qt runtime")
class BatchImportDialogTests(unittest.TestCase):
    @staticmethod
    def _wait_for(app, predicate, timeout=10):
        deadline = time.time() + timeout
        while not predicate() and time.time() < deadline:
            app.processEvents()
            time.sleep(0.01)
        return predicate()

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

    def test_async_import_copies_files_without_blocking_prism_phase(self):
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            server = root / "server" / "shot001"
            source = (
                server
                / "shot_motion"
                / "shot_animation"
                / "fbx"
                / "camera.fbx"
            )
            source.parent.mkdir(parents=True)
            source.write_bytes(b"fbx")
            product_root = root / "products" / "published_ref"
            controller = BatchImportController(
                _ImportCore(str(product_root)),
                object(),
            )
            parent = QWidget()
            reporter = _Reporter()
            finished = []
            item = {
                "episode": "EP01",
                "sequence": "SC01",
                "shot": "shot001",
                "server_dir": str(server),
                "frame_range": [1001, 1100],
                "steps": [
                    {
                        "label": "Animation",
                        "files": {"fbx_files": [str(source)]},
                    }
                ],
            }
            try:
                controller._start_project_and_shots(
                    {
                        "project_name": "show",
                        "project_path": str(root / "show"),
                        "selected": [item],
                        "parent": parent,
                        "create_only": False,
                        "copy_to_local": True,
                        "pdg_enabled": False,
                        "_reporter": reporter,
                        "_finished_callback": finished.append,
                    }
                )
                self.assertTrue(
                    self._wait_for(
                        app,
                        lambda: (
                            bool(finished)
                            and controller._file_job is None
                        ),
                    )
                )
                self.assertEqual(finished[0]["success"], 1)
                self.assertEqual(reporter.progress, [1])
                self.assertTrue(
                    (
                        product_root
                        / "v0001"
                        / "shot_motion"
                        / "shot_animation"
                        / "fbx"
                        / "camera.fbx"
                    ).is_file()
                )
            finally:
                parent.close()
        app.processEvents()


if __name__ == "__main__":
    unittest.main()
