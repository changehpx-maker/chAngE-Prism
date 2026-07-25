import os
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))

from change_prism import config


class _Core:
    def __init__(self, data=None, project_path=""):
        self.data = data or {}
        self.projectPath = project_path
        self.saved = []

    def getConfig(self, cat=None, param=None, **_kwargs):
        section = self.data.get(cat)
        if param is None:
            return section
        return section.get(param) if isinstance(section, dict) else None

    def setConfig(self, cat=None, param=None, val=None, **_kwargs):
        section = self.data.setdefault(cat, {})
        section[param] = val
        self.saved.append((cat, param, val))


class ConfigTests(unittest.TestCase):
    def test_defaults_are_used_when_prism_section_is_empty(self):
        core = _Core()
        self.assertEqual(
            config.get_server_root(core),
            "P:\\" if sys.platform == "win32" else "",
        )
        self.assertEqual(
            config.get_local_projects_root(core),
            os.path.expanduser("~/Desktop/Projects"),
        )

    def test_review_copy_destination_root_uses_prism_user_settings(self):
        core = _Core(
            {
                config.CONFIG_SECTION: {
                    "review_copy": {"destination_root": "Z:/daily_review"}
                }
            }
        )
        self.assertEqual(
            config.get_review_copy_destination_root(core),
            "Z:/daily_review",
        )

    def test_runtime_path_edits_are_saved_through_prism(self):
        core = _Core()
        config.save_config_value(core, "server_root", "Z:/publish")
        self.assertEqual(
            core.saved,
            [(config.CONFIG_SECTION, "server_root", "Z:/publish")],
        )

    def test_pdg_paths_are_read_from_prism_user_settings(self):
        core = _Core(
            {
                config.CONFIG_SECTION: {
                    "pdg": {
                        "hip_path": "D:/pipeline/tools/Convert_assets.hip",
                        "houdini_package_directory": "D:/pipeline/hou_pkgs",
                    }
                }
            }
        )
        self.assertEqual(
            config.get_pdg_hip_path(core),
            "D:/pipeline/tools/Convert_assets.hip",
        )
        self.assertEqual(
            config.get_houdini_package_directory(core),
            "D:/pipeline/hou_pkgs",
        )
        self.assertNotIn("hython_path", config.load_config(core)["pdg"])

    def test_ocio_override_updates_mapping_without_losing_other_projects(self):
        core = _Core(
            {
                config.CONFIG_SECTION: {
                    "server_root": "P:/",
                    "ocio_converter": {
                        "project_overrides": {"show_a": "A:/config.ocio"}
                    },
                }
            }
        )
        config.save_ocio_project_override(
            core, "show_b", "B:/config.ocio"
        )
        overrides = core.data[config.CONFIG_SECTION]["ocio_converter"][
            "project_overrides"
        ]
        self.assertEqual(
            overrides,
            {
                "show_a": "A:/config.ocio",
                "show_b": "B:/config.ocio",
            },
        )
        config.save_ocio_project_override(core, "show_a", "")
        self.assertNotIn(
            "show_a",
            core.data[config.CONFIG_SECTION]["ocio_converter"][
                "project_overrides"
            ],
        )


if __name__ == "__main__":
    unittest.main()
