import os
import sys
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from qtpy.QtCore import QThread
    from qtpy.QtWidgets import QApplication
    from change_prism.nuke_archive.controller import NukeArchiveController
    from change_prism.nuke_archive.dialog import (
        PackageConfirmDialog,
        create_progress_dialog,
    )
    from change_prism.nuke_archive.service import (
        build_package_plan,
    )
except Exception:
    QApplication = None
    PackageConfirmDialog = None
    create_progress_dialog = None
    build_package_plan = None
    NukeArchiveController = None


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


if __name__ == "__main__":
    unittest.main()
