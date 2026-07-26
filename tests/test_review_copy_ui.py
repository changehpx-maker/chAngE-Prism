import datetime
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
    from qtpy.QtWidgets import QApplication, QWidget
    from change_prism.review_copy.controller import (
        ReviewCopyController,
    )
    from change_prism.review_copy.dialog import _ACTIVE_COPY_THREADS
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


@unittest.skipUnless(QApplication, "Requires Prism Qt runtime")
class ReviewCopyUiTests(unittest.TestCase):
    @staticmethod
    def _wait_for(app, predicate, timeout=10):
        deadline = time.time() + timeout
        while not predicate() and time.time() < deadline:
            app.processEvents()
            time.sleep(0.01)
        return predicate()

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


if __name__ == "__main__":
    unittest.main()
