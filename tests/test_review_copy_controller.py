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

    def test_product_version_menu_does_not_touch_filesystem(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "model.abc")
            Path(path).touch()
            versions = _VersionsView([path])
            origin = mock.Mock(tw_versions=versions)
            menu = _Menu()

            with mock.patch.object(
                controller.os.path,
                "exists",
                side_effect=AssertionError("menu touched the filesystem"),
            ), mock.patch.object(
                controller.os.path,
                "isfile",
                side_effect=AssertionError("menu touched the filesystem"),
            ), mock.patch.object(
                controller.os,
                "listdir",
                side_effect=AssertionError("menu touched the filesystem"),
            ):
                controller.ReviewCopyController(
                    _Core()
                ).add_product_context_menu(
                    origin, versions, _Position(0), menu
                )

            self.assertEqual(
                [action.text for action in menu.actions],
                [controller.MENU_LABEL],
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
            self.assertIs(core.popups[0][1].get("modal"), False)

    def test_partial_failure_uses_nonmodal_popup_parented_to_browser(self):
        core = _Core()
        core.pb = mock.Mock()
        core.pb.isVisible.return_value = True
        popup = mock.Mock()
        review_copy = controller.ReviewCopyController(core)
        result = {
            "destination": "Z:/daily_review/2026-07-23",
            "copied": ["model.abc"],
            "failures": [{"source": "missing.abc", "error": "Not found"}],
        }

        with mock.patch.object(core, "popup", return_value=popup) as show:
            review_copy._copy_finished(result)

        message = show.call_args[0][0]
        self.assertIn("Copied 1 item(s)", message)
        self.assertIn("missing.abc\n  Not found", message)
        self.assertEqual(
            show.call_args[1],
            {"severity": "warning", "parent": core.pb, "modal": False},
        )
        self.assertIs(review_copy._result_popup, popup)
        popup.raise_.assert_called_once_with()

    def test_copy_failure_closes_job_before_nonmodal_notification(self):
        core = _Core()
        review_copy = controller.ReviewCopyController(core)
        bridge = mock.Mock()
        review_copy._copy_job = {"bridge": bridge}

        def show(message, **kwargs):
            self.assertIsNone(review_copy._copy_job)
            bridge.deleteLater.assert_called_once_with()
            self.assertIs(kwargs.get("modal"), False)
            self.assertIn("Access denied", message)

        with mock.patch.object(core, "popup", side_effect=show):
            review_copy._copy_failed("Access denied")

    def test_running_copy_cannot_start_another_job(self):
        core = _Core()
        review_copy = controller.ReviewCopyController(core)
        job = {"bridge": mock.Mock()}
        review_copy._copy_job = job

        with mock.patch.object(review_copy, "_start_copy_job") as start_copy:
            review_copy.copy_paths(["review.mov"])

        start_copy.assert_not_called()
        self.assertIs(review_copy._copy_job, job)
        self.assertIn("already running", core.popups[-1][0])

    def test_unavailable_browser_falls_back_to_message_parent(self):
        for deleted in (False, True):
            with self.subTest(deleted=deleted):
                core = _Core()
                core.pb = mock.Mock()
                core.messageParent = object()
                core.pb.isVisible.return_value = False
                if deleted:
                    core.pb.isVisible.side_effect = RuntimeError(
                        "Internal C++ object already deleted"
                    )
                review_copy = controller.ReviewCopyController(core)

                review_copy._copy_failed("Access denied")

                self.assertIs(
                    core.popups[0][1].get("parent"), core.messageParent
                )
                self.assertIs(core.popups[0][1].get("modal"), False)

    def test_next_result_replaces_previous_popup(self):
        core = _Core()
        review_copy = controller.ReviewCopyController(core)
        first = mock.Mock()
        second = mock.Mock()
        with mock.patch.object(core, "popup", side_effect=[first, second]):
            review_copy._copy_failed("First failure")
            review_copy._copy_failed("Second failure")

        first.close.assert_called_once_with()
        first.deleteLater.assert_called_once_with()
        self.assertIs(review_copy._result_popup, second)

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
