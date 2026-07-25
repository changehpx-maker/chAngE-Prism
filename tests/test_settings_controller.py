import sys
import types
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))

from change_prism.config import CONFIG_SECTION
from change_prism.settings.controller import SettingsController


class _Core:
    projectPath = "D:/Projects/Show"

    @staticmethod
    def getExecutableOverride(_name):
        return ""


class _Plugin:
    serverRoot = ""


class _Widget:
    def __init__(self):
        self.loaded = None

    def set_values(self, *values):
        self.loaded = values

    def values(self):
        return {
            "server_root": "Z:/publish",
            "local_projects_root": "D:/Projects",
            "review_copy_destination_root": "E:/daily_review",
            "pdg_hip_path": "D:/pipeline/tools/Convert_assets.hip",
            "houdini_package_directory": "D:/pipeline/hou_pkgs",
            "ocio_project_override": "D:/Projects/Show/config.ocio",
        }


class _SettingsOrigin:
    def __init__(self):
        self.added = []

    def addTab(self, widget, name):
        self.added.append((widget, name))


class SettingsControllerTests(unittest.TestCase):
    def test_ui_is_lazy_loaded_and_added_with_prism_signature(self):
        created = []

        class _PluginSettingsWidget:
            def __init__(self, core, project_key, parent=None):
                created.append((core, project_key, parent))

        module = types.ModuleType("change_prism.settings.dialog")
        module.PluginSettingsWidget = _PluginSettingsWidget
        controller = SettingsController(_Core(), _Plugin())
        origin = _SettingsOrigin()
        with mock.patch.dict(
            sys.modules,
            {"change_prism.settings.dialog": module},
        ):
            controller.load_ui(origin)

        self.assertEqual(len(created), 1)
        self.assertIs(created[0][0], controller.core)
        self.assertIs(created[0][2], origin)
        self.assertEqual(origin.added, [(controller.widget, "chAngE_Prism")])

    def test_loads_prism_settings_into_widget(self):
        controller = SettingsController(_Core(), _Plugin())
        controller.widget = _Widget()
        settings = {
            CONFIG_SECTION: {
                "server_root": "Z:/publish",
                "local_projects_root": "D:/Projects",
                "review_copy": {"destination_root": "E:/daily_review"},
                "pdg": {
                    "hip_path": "D:/pipeline/tools/Convert_assets.hip",
                    "houdini_package_directory": "D:/pipeline/hou_pkgs",
                },
                "ocio_converter": {
                    "project_overrides": {
                        "d:\\projects\\show": "D:/Projects/Show/config.ocio"
                    }
                },
            }
        }
        controller.load_settings(None, settings)
        self.assertEqual(
            controller.widget.loaded,
            (
                "Z:/publish",
                "D:/Projects",
                "E:/daily_review",
                "",
                "D:/pipeline/tools/Convert_assets.hip",
                "D:/pipeline/hou_pkgs",
                "D:/Projects/Show/config.ocio",
            ),
        )

    def test_save_merges_section_and_updates_runtime_server_root(self):
        plugin = _Plugin()
        controller = SettingsController(_Core(), plugin)
        controller.widget = _Widget()
        settings = {
            CONFIG_SECTION: {
                "unrelated": "preserved",
                "ocio_converter": {
                    "project_overrides": {"other": "X:/config.ocio"}
                },
            }
        }
        controller.save_settings(None, settings)
        section = settings[CONFIG_SECTION]
        self.assertEqual(section["unrelated"], "preserved")
        self.assertEqual(
            section["review_copy"]["destination_root"],
            "E:/daily_review",
        )
        self.assertEqual(
            section["pdg"]["hip_path"],
            "D:/pipeline/tools/Convert_assets.hip",
        )
        self.assertEqual(
            section["pdg"]["houdini_package_directory"],
            "D:/pipeline/hou_pkgs",
        )
        self.assertNotIn("hython_path", section["pdg"])
        self.assertEqual(
            section["ocio_converter"]["project_overrides"]["other"],
            "X:/config.ocio",
        )
        self.assertEqual(
            section["ocio_converter"]["project_overrides"][
                "d:\\projects\\show"
            ],
            "D:/Projects/Show/config.ocio",
        )
        self.assertEqual(plugin.serverRoot, "Z:/publish")


if __name__ == "__main__":
    unittest.main()
