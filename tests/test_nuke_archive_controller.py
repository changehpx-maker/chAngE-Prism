import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))

from change_prism.nuke_archive import controller


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


class _Core:
    def __init__(self):
        self.popups = []

    def popup(self, message, **kwargs):
        self.popups.append((message, kwargs))


class NukeArchiveControllerTests(unittest.TestCase):
    def test_menu_is_only_added_for_nuke_file_under_scenefiles(self):
        with tempfile.TemporaryDirectory() as tmp:
            shot = Path(tmp) / "Shots" / "SC01" / "shot0010"
            scene_dir = shot / "Scenefiles" / "cmp" / "Compositing"
            scene_dir.mkdir(parents=True)
            script = scene_dir / "scene.nk"
            script.touch()
            menu = _Menu()

            archive = controller.NukeArchiveController(_Core())
            archive.add_file_context_menu(object(), menu, str(script))

            self.assertEqual(menu.separators, 1)
            self.assertEqual(
                [action.text for action in menu.actions],
                [controller.MENU_LABEL],
            )
            outside = Path(tmp) / "outside.nk"
            outside.touch()
            outside_menu = _Menu()
            archive.add_file_context_menu(
                object(), outside_menu, str(outside)
            )
            self.assertFalse(outside_menu.actions)

    def test_menu_action_forwards_selected_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            scene_dir = (
                Path(tmp)
                / "shot0010"
                / "Scenefiles"
                / "cmp"
                / "Compositing"
            )
            scene_dir.mkdir(parents=True)
            script = scene_dir / "scene.nk"
            script.touch()
            menu = _Menu()
            archive = controller.NukeArchiveController(_Core())

            with mock.patch.object(archive, "package_nuke") as package:
                archive.add_file_context_menu(
                    object(), menu, str(script)
                )
                menu.actions[0].trigger()

            package.assert_called_once_with(str(script))


if __name__ == "__main__":
    unittest.main()
