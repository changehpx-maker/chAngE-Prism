import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


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
        self.popups = []

    def getExecutableOverride(self, _application):
        return self.executable

    def getConfig(self, cat=None, param=None, **_kwargs):
        section = self.settings.get(cat, {})
        if param is None:
            return section
        return section.get(param)

    def popup(self, message, severity=None, **_kwargs):
        self.popups.append((message, severity))


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

    def test_pdg_json_uses_isolated_temp_path_and_cleans_up(self):
        with tempfile.TemporaryDirectory() as directory:
            first_dir = Path(directory) / "change_prism_pdg_first"
            second_dir = Path(directory) / "change_prism_pdg_second"
            first_dir.mkdir()
            second_dir.mkdir()
            with mock.patch(
                "change_prism.batch_import.pdg.tempfile.mkdtemp",
                side_effect=[str(first_dir), str(second_dir)],
            ), mock.patch(
                "change_prism.batch_import.pdg.tempfile.gettempdir",
                return_value=directory,
            ):
                processor = PDGProcessor(_Core())
                first_path = processor._write_pdg_json({"run": 1})
                second_path = processor._write_pdg_json({"run": 2})
                processor._json_path = first_path
                processor._cleanup_pdg_json()

            self.assertEqual(
                first_path, str(first_dir / "shot_data.json")
            )
            self.assertEqual(
                second_path, str(second_dir / "shot_data.json")
            )
            self.assertFalse(first_dir.exists())
            with open(second_path, "r", encoding="utf-8") as handle:
                self.assertEqual(json.load(handle), {"run": 2})

    def test_stderr_error_marks_run_failed_and_cleans_temp_json(self):
        with tempfile.TemporaryDirectory() as directory:
            temp_dir = Path(directory) / "change_prism_pdg_test"
            temp_dir.mkdir()
            json_path = temp_dir / "shot_data.json"
            json_path.write_text("{}", encoding="utf-8")
            stderr_path = Path(directory) / "stderr.log"
            stderr_path.write_text(
                "ERROR:test:work item generation failed\n",
                encoding="utf-8",
            )
            core = _Core()
            processor = PDGProcessor(core)
            processor._json_path = str(json_path)

            with mock.patch(
                "change_prism.batch_import.pdg.tempfile.gettempdir",
                return_value=directory,
            ):
                processor._on_pdg_finished(
                    123,
                    0,
                    stderr_path=str(stderr_path),
                )

            self.assertEqual(core.popups[-1][1], "error")
            self.assertIn(
                "Detected error output", core.popups[-1][0]
            )
            self.assertFalse(temp_dir.exists())

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
