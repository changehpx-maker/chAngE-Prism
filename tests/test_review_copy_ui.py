import datetime
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from qtpy.QtCore import Qt, QTimer
    from qtpy.QtTest import QTest
    from qtpy.QtWidgets import (
        QApplication, QMessageBox, QProgressDialog, QPushButton, QWidget,
    )
    from change_prism.review_copy.controller import (
        ReviewCopyController,
    )
    from change_prism.review_copy.dialog import _ACTIVE_COPY_THREADS
    from change_prism.review_copy import dialog as copy_dialog
except Exception:
    QApplication = None
    ReviewCopyController = None


class _Core:
    def __init__(self, destination, parent):
        self.destination = destination
        self.messageParent = parent
        self.popups = []

    def getConfig(self, *args, **kwargs):
        del args, kwargs
        return {
            "review_copy": {
                "destination_root": self.destination,
            }
        }

    def popup(self, message, **kwargs):
        self.popups.append((message, kwargs))


class _PrismPopupCore(_Core):
    prismArgs = []
    uiAvailable = True

    def isPopupTooLong(self, text):
        return False

    def popup(self, message, **kwargs):
        from PrismCore import PrismCore

        super().popup(message, **kwargs)
        return PrismCore.popup(self, message, **kwargs)


@unittest.skipUnless(QApplication, "Requires Prism Qt runtime")
class ReviewCopyUiTests(unittest.TestCase):
    @staticmethod
    def _wait_for(app, predicate, timeout=10):
        deadline = time.time() + timeout
        while not predicate() and time.time() < deadline:
            app.processEvents()
            time.sleep(0.01)
        return predicate()

    def test_background_copy_does_not_create_a_progress_window(self):
        app = QApplication.instance() or QApplication([])
        # Other features may leave closed dialogs pending Qt/Python cleanup.
        existing_progress = {
            widget for widget in app.topLevelWidgets()
            if isinstance(widget, QProgressDialog)
        }
        started = threading.Event()
        release = threading.Event()
        worker_threads = []
        parent = QWidget()
        button = QPushButton("Browser action", parent)
        clicks = []
        button.clicked.connect(lambda: clicks.append(True))
        parent.show()
        core = _Core("unused-test-destination", parent)
        controller = ReviewCopyController(core)

        def slow_copy(sources, destination):
            worker_threads.append(threading.get_ident())
            started.set()
            if not release.wait(5):
                raise RuntimeError("Test did not release the copy worker")
            return {"copied": sources, "destination": destination, "failures": []}

        with mock.patch.object(copy_dialog, "copy_items", side_effect=slow_copy):
            try:
                controller.copy_paths(["review.mov"])
                self.assertTrue(self._wait_for(app, started.is_set))
                self.assertIsNotNone(controller._copy_job)
                self.assertNotIn("progress", controller._copy_job)
                self.assertFalse(any(
                    isinstance(widget, QProgressDialog)
                    and widget not in existing_progress
                    for widget in app.topLevelWidgets()
                ))
                self.assertNotEqual(worker_threads[0], threading.get_ident())
                self.assertFalse(core.popups)
                QTest.mouseClick(button, Qt.LeftButton)
                self.assertEqual(clicks, [True])
            finally:
                release.set()
                finished = self._wait_for(
                    app,
                    lambda: (
                        controller._copy_job is None and not _ACTIVE_COPY_THREADS
                    ),
                )
                parent.close()
                self.assertTrue(finished)

        self.assertIn("Copied 1 item(s)", core.popups[-1][0])
        app.processEvents()

    def test_copy_runs_in_background_and_reports_completion(self):
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "review.mov"
            source.write_bytes(b"review")
            destination = Path(tmp) / "daily"
            parent = QWidget()
            core = _Core(str(destination), parent)
            controller = ReviewCopyController(core)
            try:
                controller.copy_paths([str(source)])
                self.assertIsNotNone(controller._copy_job)
                self.assertTrue(
                    self._wait_for(
                        app,
                        lambda: (
                            controller._copy_job is None
                            and bool(core.popups)
                            and not _ACTIVE_COPY_THREADS
                        ),
                    )
                )
                daily = destination / datetime.date.today().strftime(
                    "%Y-%m-%d"
                )
                self.assertTrue((daily / source.name).is_file())
                self.assertIn("Copied 1 item(s)", core.popups[-1][0])
            finally:
                parent.close()
        app.processEvents()

    def test_product_sequence_detection_and_copy_run_in_background(self):
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            version = Path(tmp) / "source" / "v0001"
            version.mkdir(parents=True)
            first = version / "cache.1001.bgeo.sc"
            second = version / "cache.1002.bgeo.sc"
            first.write_bytes(b"1001")
            second.write_bytes(b"1002")
            destination = Path(tmp) / "daily"
            parent = QWidget()
            core = _Core(str(destination), parent)
            controller = ReviewCopyController(core)
            try:
                controller.copy_paths([
                    {
                        "path": str(first),
                        "detect_product_sequence": True,
                    }
                ])
                self.assertIsNotNone(controller._copy_job)
                self.assertTrue(
                    self._wait_for(
                        app,
                        lambda: (
                            controller._copy_job is None
                            and bool(core.popups)
                            and not _ACTIVE_COPY_THREADS
                        ),
                    )
                )
                daily = destination / datetime.date.today().strftime(
                    "%Y-%m-%d"
                )
                self.assertTrue((daily / "v0001" / first.name).is_file())
                self.assertTrue((daily / "v0001" / second.name).is_file())
            finally:
                parent.close()
        app.processEvents()

    @unittest.skipUnless(os.getenv("PRISM_TEST_ROOT"), "Requires Prism core")
    def test_real_result_popups_allow_browser_input_and_next_copy(self):
        app = QApplication.instance() or QApplication([])
        unexpected_modals = []

        def dismiss_unexpected_modal():
            modal = app.activeModalWidget()
            if isinstance(modal, QMessageBox):
                unexpected_modals.append(modal.windowTitle())
                modal.accept()

        # Let a modal regression fail an assertion instead of hanging the suite.
        guard = QTimer()
        guard.timeout.connect(dismiss_unexpected_modal)
        guard.start(25)
        with tempfile.TemporaryDirectory() as tmp:
            version = Path(tmp) / "source" / "v0001"
            version.mkdir(parents=True)
            first = version / "cache.1001.bgeo.sc"
            second = version / "cache.1002.bgeo.sc"
            first.write_bytes(b"1001")
            second.write_bytes(b"1002")
            destination = Path(tmp) / "daily"
            host = QWidget()
            blocked_destination = Path(tmp) / "not_a_directory"
            blocked_destination.touch()
            browser = QWidget(host, Qt.Window)
            button = QPushButton("Browser action", browser)
            clicks = []
            button.clicked.connect(lambda: clicks.append(True))
            browser.show()
            core = _PrismPopupCore(str(destination), host)
            core.pb = browser
            controller = ReviewCopyController(core)
            product = {"path": str(first), "detect_product_sequence": True}
            cases = [
                ([product], str(destination), "Copied 1 item(s)", "info"),
                (
                    [product, str(Path(tmp) / "missing.abc")],
                    str(destination), "Failed 1 item(s)", "warning",
                ),
                (
                    [product], str(blocked_destination),
                    "Could not create the daily review folder", "warning",
                ),
            ]
            try:
                for index, (paths, target, message, severity) in enumerate(cases):
                    with self.subTest(message=message):
                        core.destination = target
                        controller.copy_paths(paths)
                        self.assertTrue(self._wait_for(
                            app,
                            lambda: (
                                controller._copy_job is None
                                and len(core.popups) == index + 1
                                and not _ACTIVE_COPY_THREADS
                            ),
                        ))
                        self.assertFalse(unexpected_modals)
                        popup = controller._result_popup
                        self.assertIsInstance(popup, QMessageBox)
                        self.assertTrue(popup.isVisible())
                        self.assertFalse(popup.isModal())
                        self.assertIs(popup.parentWidget(), browser)
                        self.assertIsNone(app.activeModalWidget())
                        self.assertIn(message, core.popups[-1][0])
                        self.assertEqual(core.popups[-1][1]["severity"], severity)
                        self.assertFalse(any(
                            isinstance(widget, QProgressDialog) and widget.isVisible()
                            for widget in app.topLevelWidgets()
                        ))
                        QTest.mouseClick(button, Qt.LeftButton)
                        self.assertEqual(len(clicks), index + 1)

                daily = destination / datetime.date.today().strftime("%Y-%m-%d")
                self.assertTrue((daily / "v0001" / first.name).is_file())
                self.assertTrue((daily / "v0001" / second.name).is_file())
            finally:
                guard.stop()
                for popup in browser.findChildren(QMessageBox):
                    popup.close()
                    popup.deleteLater()
                browser.close()
                host.close()
        app.processEvents()


if __name__ == "__main__":
    unittest.main()
