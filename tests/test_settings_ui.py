import os
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from qtpy.QtWidgets import QApplication
    from change_prism.settings.dialog import PluginSettingsWidget
except Exception:
    QApplication = None
    PluginSettingsWidget = None


@unittest.skipUnless(QApplication, "Requires Prism Qt runtime")
class PluginSettingsWidgetTests(unittest.TestCase):
    def test_values_round_trip(self):
        app = QApplication.instance() or QApplication([])
        widget = PluginSettingsWidget(
            object(),
            project_key="D:/Projects/Show",
        )
        try:
            widget.set_values(
                "Z:/publish",
                "D:/Projects",
                "E:/daily_review",
                "C:/Program Files/Side Effects Software/Houdini 21.0/bin/hython.exe",
                "D:/pipeline/tools/Convert_assets.hip",
                "D:/pipeline/hou_pkgs",
                "D:/Projects/Show/config.ocio",
            )
            self.assertEqual(
                widget.values(),
                {
                    "server_root": "Z:/publish",
                    "local_projects_root": "D:/Projects",
                    "review_copy_destination_root": "E:/daily_review",
                    "pdg_hip_path": "D:/pipeline/tools/Convert_assets.hip",
                    "houdini_package_directory": "D:/pipeline/hou_pkgs",
                    "ocio_project_override": "D:/Projects/Show/config.ocio",
                },
            )
        finally:
            widget.close()
        app.processEvents()

    def test_project_label_preserves_display_path_casing(self):
        class _Core:
            projectPath = "D:/Projects/CAKPCG"

        app = QApplication.instance() or QApplication([])
        widget = PluginSettingsWidget(
            _Core(),
            project_key="d:\\projects\\cakpcg",
        )
        try:
            self.assertEqual(
                widget.project_label.text(),
                "Current Prism project: %s"
                % os.path.normpath("D:/Projects/CAKPCG"),
            )
            self.assertEqual(
                widget.project_key, "d:\\projects\\cakpcg"
            )
        finally:
            widget.close()
        app.processEvents()


if __name__ == "__main__":
    unittest.main()
