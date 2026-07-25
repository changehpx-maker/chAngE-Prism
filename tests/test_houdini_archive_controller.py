import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))

from change_prism.houdini_archive import controller


class _Signal:
    def __init__(self):
        self.callback = None

    def connect(self, callback):
        self.callback = callback


class _Action:
    def __init__(self, text):
        self.text = text
        self.triggered = _Signal()

    def trigger(self):
        self.triggered.callback(False)


class _Menu:
    def __init__(self):
        self.actions = []
        self.separators = 0

    def addSeparator(self):
        self.separators += 1

    def addAction(self, text):
        action = _Action(text)
        self.actions.append(action)
        return action


class HoudiniArchiveControllerTests(unittest.TestCase):
    def test_menu_supports_all_hip_license_extensions_under_scenefiles(self):
        with tempfile.TemporaryDirectory() as tmp:
            scene_dir = (
                Path(tmp)
                / "shot0010"
                / "Scenefiles"
                / "fx"
                / "Effects"
            )
            scene_dir.mkdir(parents=True)
            for extension in (".hip", ".hiplc", ".hipnc"):
                scene = scene_dir / ("scene" + extension)
                scene.touch()
                menu = _Menu()
                archive = controller.HoudiniArchiveController(object())
                archive.add_file_context_menu(None, menu, str(scene))
                self.assertEqual(
                    [item.text for item in menu.actions],
                    [controller.MENU_LABEL],
                )

            outside = Path(tmp) / "outside.hip"
            outside.touch()
            menu = _Menu()
            archive.add_file_context_menu(None, menu, str(outside))
            self.assertFalse(menu.actions)

    def test_menu_action_forwards_selected_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            scene_dir = Path(tmp) / "shot" / "Scenefiles" / "fx"
            scene_dir.mkdir(parents=True)
            scene = scene_dir / "scene.hip"
            scene.touch()
            menu = _Menu()
            archive = controller.HoudiniArchiveController(object())
            with mock.patch.object(
                archive, "package_houdini"
            ) as package:
                archive.add_file_context_menu(None, menu, str(scene))
                menu.actions[0].trigger()
            package.assert_called_once_with(str(scene))

    def test_incompatible_prism_override_falls_back_to_installed_hython(self):
        class Core:
            startEnv = {}
            users = None
            projects = None

            @staticmethod
            def getExecutableOverride(_name):
                return str(houdini)

            @staticmethod
            def callback(**_kwargs):
                return None

        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            houdini = directory / "houdini.exe"
            override_hython = directory / "hython.exe"
            installed_hython = directory / "installed_hython.exe"
            for path in (houdini, override_hython, installed_hython):
                path.touch()

            archive = controller.HoudiniArchiveController(Core())
            with mock.patch.object(
                controller.runner,
                "read_hip_version",
                return_value="21.0.631",
            ), mock.patch.object(
                controller.runner,
                "resolve_hython",
                side_effect=[
                    controller.runner.RunnerError("incompatible"),
                    {
                        "path": str(installed_hython),
                        "version": "21.0.631",
                        "warning": "",
                    },
                ],
            ) as resolve:
                selected, environment = archive._worker_configuration(
                    str(directory / "scene.hip")
                )

            self.assertEqual(selected, str(installed_hython))
            self.assertEqual(environment, {})
            self.assertEqual(resolve.call_count, 2)
            self.assertEqual(
                resolve.call_args_list[0].kwargs["explicit_path"],
                str(override_hython),
            )
            self.assertNotIn(
                "explicit_path", resolve.call_args_list[1].kwargs
            )


if __name__ == "__main__":
    unittest.main()
