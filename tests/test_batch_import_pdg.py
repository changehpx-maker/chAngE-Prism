import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))

try:
    from change_prism.batch_import.pdg import PDGProcessor
except Exception:
    PDGProcessor = None


class _Products:
    @staticmethod
    def createProduct(_entity, _product):
        return "D:/project/Products/published_ref"


class _Core:
    def __init__(self, executable="", settings=None):
        self.executable = executable
        self.settings = settings or {}
        self.products = _Products()
        self.startEnv = {"BASE": "1"}
        self.users = None
        self.projects = None

    def getExecutableOverride(self, _application):
        return self.executable

    def getConfig(self, cat=None, param=None, **_kwargs):
        section = self.settings.get(cat, {})
        if param is None:
            return section
        return section.get(param)


@unittest.skipUnless(PDGProcessor, "Requires Prism Qt runtime")
class PDGProcessorTests(unittest.TestCase):
    def test_pdg_json_contains_only_animation_fbx(self):
        data = [
            {
                "episode": "EP01",
                "sequence": "SC01",
                "shot": "shot001",
                "prism_sequence": "EP01",
                "prism_shot": "SC01_shot001",
                "source_file_root": "D:/source",
                "products_path": "D:/products/v0001",
                "frame_range": [1001, 1100],
                "steps": {
                    "Animation": {
                        "fbx": ["D:/source/animation/fbx/camera.fbx"],
                        "review": ["D:/source/review.mov"],
                    },
                    "Cloth": {"abc": ["D:/source/cloth.abc"]},
                },
            }
        ]

        result = PDGProcessor(_Core())._build_pdg_json(data)
        shot = result["EP01/SC01/shot001"]

        self.assertEqual(len(shot["file_dict"]), 1)
        self.assertTrue(
            shot["file_dict"][0]["path"].endswith("camera.fbx")
        )
        self.assertEqual(
            shot["file_dict"][0]["relpath"],
            "animation/fbx/camera.fbx",
        )
        self.assertEqual(shot["entity"]["shot"], "SC01_shot001")
        self.assertEqual(
            shot["frame_range"], {"start": 1001, "end": 1100}
        )

    def test_runtime_paths_come_from_prism_and_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bin_dir = root / "bin"
            python_lib = (
                root
                / "houdini"
                / "python3.11libs"
                / "pdgjob"
            )
            package_dir = root / "hou_pkgs"
            bin_dir.mkdir()
            python_lib.mkdir(parents=True)
            package_dir.mkdir()
            houdini = bin_dir / "houdini.exe"
            hython = bin_dir / "hython.exe"
            topcook = python_lib / "topcook.py"
            hip = root / "Convert_assets.hip"
            for path in (houdini, hython, topcook, hip):
                path.touch()
            settings = {
                "change_prism": {
                    "pdg": {
                        "hip_path": str(hip),
                        "houdini_package_directory": str(package_dir),
                    }
                }
            }
            processor = PDGProcessor(
                _Core(str(houdini), settings)
            )

            self.assertEqual(
                processor._resolve_hython(), str(hython)
            )
            self.assertEqual(processor._resolve_hip(), str(hip))
            self.assertEqual(
                processor._resolve_topcook(str(hython)),
                str(topcook),
            )
            self.assertEqual(
                processor._resolve_package_directory(),
                str(package_dir),
            )

    def test_houdini_environment_uses_settings_not_pipeline_root(self):
        with tempfile.TemporaryDirectory() as directory:
            package_dir = str(Path(directory) / "hou_pkgs")
            json_path = str(Path(directory) / "shot_data.json")
            environment = PDGProcessor(_Core())._build_houdini_env(
                "",
                package_dir,
                json_path,
            )

        self.assertEqual(
            environment["HOUDINI_PACKAGE_DIR"], package_dir
        )
        self.assertEqual(
            environment["SHOT_BUILDER_PDG_JSON"], json_path
        )
        self.assertNotIn("PIPELINE_ROOT", environment)


if __name__ == "__main__":
    unittest.main()
