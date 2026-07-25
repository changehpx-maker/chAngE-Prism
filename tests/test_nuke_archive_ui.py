import json
import os
import sys
import tempfile
import time
import types
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from qtpy.QtCore import QObject, QThread, Signal
    from qtpy.QtWidgets import QApplication, QStyle, QWidget
    from change_prism.nuke_archive.controller import NukeArchiveController
    from change_prism.nuke_archive.dialog import (
        ArchiveBrowserWidget,
        PackageConfirmDialog,
        create_progress_dialog,
    )
    from change_prism.nuke_archive.service import (
        build_package_plan,
        execute_package,
    )
except Exception:
    QApplication = None
    ArchiveBrowserWidget = None
    PackageConfirmDialog = None
    create_progress_dialog = None
    build_package_plan = None
    execute_package = None
    NukeArchiveController = None


if QApplication:
    class _FakePage(QObject):
        itemChanged = Signal(object)


    class _FakeEntityWidget(QWidget):
        def __init__(self, core=None, refresh=False, pages=None):
            super(_FakeEntityWidget, self).__init__()
            self.entity = {"type": "shot", "sequence": "SC01", "shot": "shot0010"}
            self.page = _FakePage()

        def getPage(self, _name):
            return self.page

        def getCurrentData(self):
            return self.entity

        def refreshEntities(self, **_kwargs):
            return None

        def navigate(self, data):
            self.entity = data

        def syncFromWidget(self, widget):
            self.entity = widget.getCurrentData()


    class _ArchiveCore:
        def __init__(self, shot_path):
            self.shot_path = shot_path
            self.opened_files = []
            self.confirmation_result = "Cancel"
            self.questions = []
            self.popups = []

        def getEntityPath(self, entity=None):
            return self.shot_path

        def getIconForFileType(self, extension):
            if extension == ".nk":
                return QApplication.style().standardIcon(QStyle.SP_FileIcon)
            return None

        def openFile(self, filepath):
            self.opened_files.append(filepath)

        def popupQuestion(self, message, **kwargs):
            self.questions.append((message, kwargs))
            return self.confirmation_result

        def popup(self, message, severity=None):
            self.popups.append((message, severity))


@unittest.skipUnless(QApplication, "Requires Prism Qt runtime")
class NukeArchiveUiTests(unittest.TestCase):
    def test_confirmation_and_progress_dialogs_support_plan(self):
        app = QApplication.instance() or QApplication([])
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
            plan = build_package_plan(script, root / "Archives")
            confirmation = PackageConfirmDialog(plan)
            progress = create_progress_dialog(plan)
            try:
                self.assertIn(
                    "Read nodes: 1",
                    confirmation.findChild(
                        __import__(
                            "qtpy.QtWidgets", fromlist=["QPlainTextEdit"]
                        ).QPlainTextEdit
                    ).toPlainText(),
                )
                self.assertIn(
                    "Estimated payload: 5 B across 1 files",
                    confirmation.findChild(
                        __import__(
                            "qtpy.QtWidgets", fromlist=["QPlainTextEdit"]
                        ).QPlainTextEdit
                    ).toPlainText(),
                )
                self.assertEqual(progress.maximum(), 1)
            finally:
                confirmation.close()
                progress.close()
        app.processEvents()

    def test_background_packaging_callbacks_run_on_ui_thread(self):
        app = QApplication.instance() or QApplication([])
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
            plan = build_package_plan(script, root / "Archives")
            popups = []

            class _Core:
                pb = None

                def popup(self, message, severity=None):
                    popups.append(
                        (
                            message,
                            severity,
                            QThread.currentThread() is app.thread(),
                        )
                    )

            controller = NukeArchiveController(_Core())
            controller._start_package(plan, None)
            deadline = time.monotonic() + 5.0
            while controller._active_jobs and time.monotonic() < deadline:
                app.processEvents()
                time.sleep(0.01)
            app.processEvents()

            self.assertFalse(controller._active_jobs)
            self.assertEqual(len(popups), 1)
            self.assertEqual(popups[0][1], "info")
            self.assertTrue(popups[0][2])
            self.assertTrue((root / "Archives" / "v0001").is_dir())

    def test_archive_browser_lists_completed_versions(self):
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            shot = Path(tmp) / "shot0010"
            source = Path(tmp) / "source"
            source.mkdir()
            (source / "plate.1001.exr").write_bytes(b"frame")
            script = Path(tmp) / "scene.nk"
            script.write_text(
                "Root {\n inputs 0\n}\n"
                "Read {\n file %s\n name Read1\n}\n"
                % str(source / "plate.%04d.exr").replace("\\", "/"),
                encoding="utf-8",
            )
            result = execute_package(
                build_package_plan(script, shot / "Archives")
            )
            manifest_path = Path(result["manifest_path"])
            manifest = json.loads(
                manifest_path.read_text(encoding="utf-8")
            )
            manifest.pop("summary")
            for copy_job in manifest["copy_jobs"]:
                copy_job.pop("file_count")
                copy_job.pop("total_bytes")
            manifest_path.write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            fake_module = types.SimpleNamespace(
                EntityWidget=_FakeEntityWidget
            )
            with mock.patch.dict(sys.modules, {"EntityWidget": fake_module}):
                core = _ArchiveCore(str(shot))
                widget = ArchiveBrowserWidget(core)
                try:
                    widget.refresh_versions()
                    self.assertEqual(widget.table.rowCount(), 1)
                    self.assertEqual(widget.table.item(0, 0).text(), "v0001")
                    self.assertEqual(widget.table.item(0, 5).text(), "Complete")
                    self.assertTrue(widget.table.verticalHeader().isHidden())
                    self.assertGreaterEqual(
                        widget.table.verticalHeader().defaultSectionSize(),
                        38,
                    )
                    self.assertFalse(
                        widget.table.item(0, 1).icon().isNull()
                    )
                    self.assertTrue(widget.open_nuke_button.isEnabled())
                    self.assertTrue(widget.open_folder_button.isEnabled())
                    self.assertEqual(widget.table.columnCount(), 7)
                    delete_button = widget.table.cellWidget(0, 6)
                    self.assertIsNotNone(delete_button)
                    self.assertTrue(delete_button.isEnabled())
                    self.assertEqual(
                        widget.detail_status_value.text(), "Complete"
                    )
                    self.assertEqual(
                        widget.detail_read_count_value.text(), "1"
                    )
                    self.assertEqual(
                        widget.detail_copy_count_value.text(), "1"
                    )
                    self.assertEqual(
                        widget.detail_file_count_value.text(), "1"
                    )
                    self.assertEqual(
                        widget.detail_size_value.text(), "5 B"
                    )
                    self.assertEqual(widget.mapping_table.rowCount(), 1)
                    self.assertEqual(
                        widget.mapping_table.item(0, 0).text(), "Read1"
                    )
                    self.assertIn(
                        "../sequences/plate/plate.%04d.exr",
                        widget.mapping_table.item(0, 2).text(),
                    )
                    widget.open_selected_nuke()
                    self.assertEqual(
                        core.opened_files,
                        [widget.selected_version()["packaged_nk"]],
                    )

                    delete_button.click()
                    self.assertTrue(Path(result["version_path"]).is_dir())
                    self.assertEqual(widget.table.rowCount(), 1)
                    self.assertIn(
                        result["version_path"], core.questions[-1][0]
                    )

                    core.confirmation_result = "Delete Archive"
                    delete_button.click()
                    self.assertFalse(Path(result["version_path"]).exists())
                    self.assertEqual(widget.table.rowCount(), 0)
                    self.assertEqual(core.popups[-1][1], "info")
                finally:
                    widget.close()
        app.processEvents()


if __name__ == "__main__":
    unittest.main()
