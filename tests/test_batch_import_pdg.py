import json
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
    from qtpy.QtCore import QThread
    from qtpy.QtWidgets import QApplication
    from change_prism.batch_import.pdg import PDGProcessor
except Exception:
    QApplication = None
    QThread = None
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
        self.popup_kwargs = []
        self.popup_threads = []
        self.messageParent = object()

    def getExecutableOverride(self, _application):
        return self.executable

    def getConfig(self, cat=None, param=None, **_kwargs):
        section = self.settings.get(cat, {})
        if param is None:
            return section
        return section.get(param)

    def popup(self, message, severity=None, **kwargs):
        self.popups.append((message, severity))
        self.popup_kwargs.append(kwargs)
        self.popup_threads.append(QThread.currentThread())


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
                        "xml": {
                            "path": "D:/source/animation/xml/description.xml",
                            "attributes": {
                                "sequence_frame": 100,
                                "average_translation": [1, 2, 3],
                            },
                        },
                    },
                    "Cloth": {
                        "abc": ["D:/source/cloth.abc"],
                        "xml": {
                            "path": "D:/source/cloth.xml",
                            "attributes": {
                                "elements": ["cloth_body"],
                            },
                        },
                    },
                    "Hair": {
                        "abc": ["D:/source/hair.abc"],
                        "xml": {
                            "path": "D:/source/hair.xml",
                            "attributes": {
                                "elements": ["hair_main"],
                            },
                        },
                    },
                },
            }
        ]

        result = PDGProcessor(_Core())._build_pdg_json(data)
        shot = result["EP01/SC01/shot001"]

        self.assertEqual(len(shot["file_dict"]), 1)
        self.assertEqual(
            shot["file_dict"],
            [{"path": "D:/source/animation/fbx/camera.fbx"}],
        )
        self.assertEqual(shot["entity"]["shot"], "SC01_shot001")
        self.assertEqual(
            shot["frame_range"], {"start": 1001, "end": 1100}
        )
        self.assertEqual(
            shot["xml"],
            {
                "path": "D:/source/animation/xml/description.xml",
                "attributes": {"sequence_frame": 100},
                "cloth_solution": {
                    "xml_path": "D:/source/cloth.xml",
                },
                "hair_solution": {
                    "xml_path": "D:/source/hair.xml",
                },
            },
        )

    def test_pdg_json_keeps_solution_xml_without_animation_xml(self):
        data = [
            {
                "episode": "EP01",
                "sequence": "SC01",
                "shot": "shot001",
                "steps": {
                    "Animation": {
                        "fbx": ["D:/source/animation/fbx/camera.fbx"],
                    },
                    "Cloth": {
                        "xml": {"path": "D:/source/cloth.xml"},
                    },
                },
            }
        ]

        result = PDGProcessor(_Core())._build_pdg_json(data)

        self.assertEqual(
            result["EP01/SC01/shot001"]["xml"],
            {
                "cloth_solution": {
                    "xml_path": "D:/source/cloth.xml",
                }
            },
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

    def test_pdg_json_uses_unified_temp_hierarchy_and_explicit_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch(
                "change_prism.batch_import.service.tempfile.gettempdir",
                return_value=directory,
            ):
                processor = PDGProcessor(_Core())
                first_path = processor._write_pdg_json({"run": 1})
                second_path = processor._write_pdg_json({"run": 2})
                first_dir = Path(first_path).parent
                second_dir = Path(second_path).parent
                processor._json_path = first_path
                processor._cleanup_pdg_json()

            json_root = (
                Path(directory)
                / "chAngE_Prism"
                / "batch_import"
                / "pdg"
                / "json"
            )
            self.assertEqual(first_dir.parent, json_root)
            self.assertEqual(second_dir.parent, json_root)
            self.assertTrue(first_dir.name.startswith("change_prism_pdg_"))
            self.assertTrue(second_dir.name.startswith("change_prism_pdg_"))
            self.assertFalse(first_dir.exists())
            with open(second_path, "r", encoding="utf-8") as handle:
                self.assertEqual(json.load(handle), {"run": 2})

    def test_finished_run_reports_failure_and_retains_temp_json(self):
        with tempfile.TemporaryDirectory() as directory:
            stderr_path = Path(directory) / "stderr.log"
            stderr_path.write_text(
                "ERROR:test:work item generation failed\n",
                encoding="utf-8",
            )
            core = _Core()
            processor = PDGProcessor(core)
            processor._started_at = 100
            with mock.patch(
                "change_prism.batch_import.service.tempfile.gettempdir",
                return_value=directory,
            ), mock.patch(
                "change_prism.batch_import.pdg.time.monotonic",
                return_value=225,
            ):
                json_path = Path(
                    processor._write_pdg_json({"run": "failed"})
                )
                processor._json_path = str(json_path)
                processor._on_pdg_finished(
                    123,
                    0,
                    stderr_path=str(stderr_path),
                )

            self.assertEqual(core.popups[-1][1], "error")
            self.assertIn(
                "Detected error output", core.popups[-1][0]
            )
            self.assertIn("Elapsed: 02:05", core.popups[-1][0])
            self.assertIn(str(json_path), core.popups[-1][0])
            self.assertIs(
                core.popup_kwargs[-1]["parent"],
                core.messageParent,
            )
            self.assertTrue(json_path.is_file())
            self.assertEqual(processor._json_path, "")

    def test_successful_launch_uses_queued_completion_without_popup(self):
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stdout_path = root / "stdout.log"
            stderr_path = root / "stderr.log"
            core = _Core()
            processor = PDGProcessor(core)
            process = mock.Mock()
            process.pid = 123
            process.poll.return_value = None
            process.wait.return_value = 0

            with mock.patch.object(
                processor,
                "_build_pdg_json",
                return_value={"EP01/SC01/shot001": {}},
            ), mock.patch.object(
                processor, "_resolve_hython", return_value="hython"
            ), mock.patch.object(
                processor, "_resolve_hip", return_value="template.hip"
            ), mock.patch.object(
                processor, "_resolve_topcook", return_value="topcook.py"
            ), mock.patch.object(
                processor,
                "_resolve_package_directory",
                return_value="hou_pkgs",
            ), mock.patch.object(
                processor, "_validate_runtime"
            ), mock.patch.object(
                processor,
                "_write_pdg_json",
                return_value=str(root / "shot_data.json"),
            ), mock.patch.object(
                processor,
                "_build_houdini_env",
                return_value={},
            ), mock.patch.object(
                processor,
                "_make_pdg_log_paths",
                return_value=(str(stdout_path), str(stderr_path)),
            ), mock.patch(
                "change_prism.batch_import.pdg.prune_old_files"
            ), mock.patch(
                "change_prism.batch_import.pdg.subprocess.Popen",
                return_value=process,
            ):
                launched = processor.run([], "show")

            self.assertTrue(launched)
            self.assertEqual(core.popups, [])
            monitor = processor._pdg_monitor
            deadline = time.time() + 5
            while not core.popups and time.time() < deadline:
                app.processEvents()
                time.sleep(0.01)
            monitor.wait(5000)
            app.processEvents()

            self.assertTrue(core.popups)
            self.assertIn("completed", core.popups[-1][0])
            self.assertEqual(core.popup_threads[-1], app.thread())

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
