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
    def __init__(self):
        self.create_calls = 0
        self.changed_path = ""
        self.change_succeeds = True

    def createProject(self, name, path, **_kwargs):
        del name
        self.create_calls += 1
        config = Path(path) / "00_Pipeline" / "pipeline.json"
        config.parent.mkdir(parents=True)
        config.write_text("{}", encoding="utf-8")
        return str(config)

    def changeProject(self, path):
        self.changed_path = str(path)
        return str(path) if self.change_succeeds else None

    def setDepartments(self, _entity_type, _departments):
        pass


class _Configs:
    @staticmethod
    def getProjectConfigPath(path):
        return str(Path(path) / "00_Pipeline" / "pipeline.json")


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
        self.configs = _Configs()
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

    def test_open_only_lists_first_level_project_directories(self):
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ProjectB").mkdir()
            (root / "ProjectA").mkdir()
            (root / ".hidden").mkdir()
            (root / "readme.txt").write_text("", encoding="utf-8")

            with mock.patch(
                "change_prism.batch_import.dialog.os.path.isdir",
                side_effect=AssertionError(
                    "Opening Batch Import must not inspect project contents"
                ),
            ):
                dialog = BatchImportDialog(
                    object(), str(root), lambda _data: None
                )
            try:
                projects = [
                    dialog.project_combo.itemText(index)
                    for index in range(dialog.project_combo.count())
                ]
                self.assertEqual(projects, ["ProjectA", "ProjectB"])
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

    def test_dialog_waits_for_async_callback_and_reuses_pipeline_config(self):
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_root = root / "show"
            config = project_root / "00_Pipeline" / "pipeline.json"
            config.parent.mkdir(parents=True)
            config.write_text("{}", encoding="utf-8")
            core = _ImportCore(
                str(root / "products" / "published_ref")
            )
            controller = BatchImportController(core, object())
            finished = []
            dialog = BatchImportDialog(
                core,
                str(root),
                controller._start_project_and_shots,
                finish_callback=lambda _dialog, result: finished.append(
                    result
                ),
            )
            dialog.project_combo.addItem("show")
            dialog.project_combo.setCurrentText("show")
            dialog.local_path_edit.setText(str(root))
            dialog.create_only_cb.setChecked(True)
            dialog.scan_results = [
                {
                    "project_code": "show",
                    "episode": "EP01",
                    "sequence": "SC01",
                    "shot": "shot001",
                    "server_dir": str(root / "server" / "shot001"),
                    "frame_range": [1001, 1100],
                    "steps": [],
                }
            ]
            dialog._populate_results()
            try:
                dialog._on_create_clicked()
                self.assertTrue(dialog._import_running)
                self.assertEqual(finished, [])
                self.assertTrue(
                    self._wait_for(app, lambda: bool(finished))
                )
                self.assertFalse(dialog._import_running)
                self.assertEqual(finished[0]["success"], 1)
                self.assertEqual(core.projects.create_calls, 0)
                self.assertEqual(
                    core.projects.changed_path, str(config)
                )
            finally:
                dialog.close()
        app.processEvents()

    def test_project_load_failure_stops_before_import(self):
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "show" / "00_Pipeline" / "pipeline.json"
            config.parent.mkdir(parents=True)
            config.write_text("{}", encoding="utf-8")
            core = _ImportCore(
                str(root / "products" / "published_ref")
            )
            core.projects.change_succeeds = False
            controller = BatchImportController(core, object())
            finished = []

            controller._start_project_and_shots(
                {
                    "project_name": "show",
                    "project_path": str(root / "show"),
                    "selected": [
                        {
                            "episode": "EP01",
                            "sequence": "SC01",
                            "shot": "shot001",
                        }
                    ],
                    "_reporter": _Reporter(),
                    "_finished_callback": finished.append,
                }
            )

            self.assertEqual(len(finished), 1)
            self.assertIn(
                "could not load project config",
                finished[0]["error"],
            )
            self.assertIsNone(controller._import_state)
        app.processEvents()


if __name__ == "__main__":
    unittest.main()
