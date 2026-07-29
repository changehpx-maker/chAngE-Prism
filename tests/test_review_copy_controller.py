import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))

from change_prism.review_copy import controller


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


class _MediaPlayer:
    def __init__(self, path, sequence, is_sequence=False):
        self.path = path
        self.seq = sequence
        self.prvIsSequence = is_sequence

    def getCurRenders(self):
        return [{"path": self.path}]


class _Index:
    def __init__(self, value):
        self.value = value

    def data(self):
        return self.value


class _Model:
    def __init__(self, paths):
        self.paths = paths

    def columnCount(self):
        return 2

    def index(self, row, column):
        return _Index(self.paths[row] if column == 1 else "v0001")


class _VersionsView:
    def __init__(self, paths):
        self._model = _Model(paths)

    def rowAt(self, y):
        return y

    def model(self):
        return self._model


class _Position:
    def __init__(self, row):
        self.row = row

    def y(self):
        return self.row


class ReviewCopyControllerTests(unittest.TestCase):
    def test_file_menu_is_added_for_existing_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = os.path.join(tmp, "scene.nk")
            Path(source).touch()
            menu = _Menu()

            controller.ReviewCopyController(_Core()).add_file_context_menu(
                object(), menu, source
            )

            self.assertEqual(menu.separators, 1)
            self.assertEqual(
                [action.text for action in menu.actions],
                [controller.MENU_LABEL],
            )

    def test_file_menu_is_not_added_for_invalid_path(self):
        menu = _Menu()
        controller.ReviewCopyController(_Core()).add_file_context_menu(
            object(), menu, "Z:/missing/file.hip"
        )
        self.assertFalse(menu.actions)
        self.assertEqual(menu.separators, 0)

    def test_sequence_selection_uses_whole_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "beauty.1001.exr").touch()
            Path(tmp, "beauty.1002.exr").touch()
            player = _MediaPlayer(
                tmp,
                ["beauty.1001.exr", "beauty.1002.exr"],
                is_sequence=True,
            )
            self.assertEqual(
                controller.ReviewCopyController._get_media_selection(player),
                [tmp],
            )

    def test_single_media_selection_uses_the_media_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "review.mov")
            Path(path).touch()
            player = _MediaPlayer(tmp, ["review.mov"])

            self.assertEqual(
                controller.ReviewCopyController._get_media_selection(player),
                [path],
            )

    def test_product_version_menu_uses_selected_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "model.abc")
            Path(path).touch()
            versions = _VersionsView([path])
            origin = mock.Mock(tw_versions=versions)
            menu = _Menu()

            controller.ReviewCopyController(_Core()).add_product_context_menu(
                origin, versions, _Position(0), menu
            )

            self.assertEqual(
                [action.text for action in menu.actions],
                [controller.MENU_LABEL],
            )

    def test_product_sequence_uses_whole_version_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = os.path.join(tmp, "cache.1001.bgeo.sc")
            Path(first).touch()
            Path(tmp, "cache.1002.bgeo.sc").touch()
            versions = _VersionsView([first])
            origin = mock.Mock(tw_versions=versions)

            self.assertEqual(
                controller.ReviewCopyController._get_product_selection(
                    origin, versions, _Position(0)
                ),
                [tmp],
            )

    def test_product_identifier_menu_is_not_modified(self):
        versions = _VersionsView([])
        origin = mock.Mock(tw_versions=versions)
        identifier_view = object()
        menu = _Menu()

        controller.ReviewCopyController(_Core()).add_product_context_menu(
            origin, identifier_view, _Position(0), menu
        )

        self.assertFalse(menu.actions)

    def test_action_calls_service_and_shows_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = os.path.join(tmp, "review.mov")
            Path(source).touch()
            menu = _Menu()
            core = _Core()
            review_copy = controller.ReviewCopyController(core)
            result = {
                "destination": "Z:/daily_review/2026-07-23",
                "copied": [source],
                "failures": [],
            }

            with mock.patch.object(
                controller,
                "get_review_copy_destination_root",
                return_value="Z:/daily_review",
            ) as get_destination, mock.patch.object(
                review_copy, "_start_copy_job"
            ) as start_copy:
                review_copy.add_file_context_menu(object(), menu, source)
                menu.actions[0].trigger()

            start_copy.assert_called_once_with(
                [source], "Z:/daily_review"
            )
            get_destination.assert_called_once_with(core)
            review_copy._copy_finished(result)
            self.assertIn("Copied 1 item(s)", core.popups[0][0])
            self.assertEqual(core.popups[0][1]["severity"], "info")

    def test_missing_config_shows_warning_without_copying(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = os.path.join(tmp, "review.mov")
            Path(source).touch()
            core = _Core()
            review_copy = controller.ReviewCopyController(core)

            with mock.patch.object(
                controller,
                "get_review_copy_destination_root",
                return_value="",
            ), mock.patch.object(
                review_copy, "_start_copy_job"
            ) as start_copy:
                review_copy.copy_paths([source])

            start_copy.assert_not_called()
            self.assertIn(
                "Prism Settings > User > chAngE_Prism",
                core.popups[0][0],
            )
            self.assertEqual(core.popups[0][1]["severity"], "warning")


if __name__ == "__main__":
    unittest.main()
