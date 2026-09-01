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

    def test_start_package_shows_cancel_dialog_and_wires_cancel(self):
        import types

        events = []

        class _BroadcastSignal:
            def __init__(self):
                self.callbacks = []

            def connect(self, callback):
                self.callbacks.append(callback)

            def callback(self, *args):
                for handler in list(self.callbacks):
                    handler(*args)

        class _FakeThread:
            started = _BroadcastSignal()
            finished = _BroadcastSignal()

            def __init__(self, parent=None):
                self.parent = parent

            def moveToThread(self, worker):
                pass

            def start(self):
                events.append("thread-started")

            def quit(self, *args):
                events.append("thread-quit")

            def deleteLater(self):
                events.append("thread-deleted")

        class _FakeWorker:
            finished = _BroadcastSignal()
            failed = _BroadcastSignal()
            cancelled = _BroadcastSignal()

            def __init__(self, *args):
                pass

            def moveToThread(self, thread):
                pass

            def request_cancel(self):
                events.append("cancel-requested")

            def run(self):
                pass

            def deleteLater(self, *args):
                pass

        class _FakeBridge:
            def __init__(
                self,
                parent,
                on_finished,
                on_failed,
                on_cancelled,
                on_thread_finished,
            ):
                self.parent = parent
                self.on_finished = on_finished
                self.on_failed = on_failed
                self.on_cancelled = on_cancelled
                self.on_thread_finished = on_thread_finished

            def package_finished(self, result):
                self.on_finished(result)

            def package_failed(self, message):
                self.on_failed(message)

            def package_cancelled(self):
                self.on_cancelled()

            def thread_finished(self):
                self.on_thread_finished()

            def deleteLater(self):
                events.append("bridge-deleted")

        class _FakeProgressDialog:
            canceled = _Signal()

            def __init__(self, parent=None):
                self.parent = parent

            def show(self):
                events.append("dialog-shown")

            def close(self):
                events.append("dialog-closed")

        class Core:
            def __init__(self):
                self.popups = []

            def popup(self, message, severity="info"):
                self.popups.append((severity, message))

        progress_dialog = _FakeProgressDialog()
        qtpy = types.ModuleType("qtpy")
        qtcore = types.ModuleType("qtpy.QtCore")
        qtcore.QThread = _FakeThread
        qtpy.QtCore = qtcore
        fake_dialog = types.ModuleType(
            "change_prism.houdini_archive.dialog"
        )
        fake_dialog.BackgroundPackageWorker = _FakeWorker
        fake_dialog.BackgroundUiBridge = _FakeBridge
        fake_dialog.create_background_progress_dialog = (
            lambda parent=None: progress_dialog
        )

        core = Core()
        archive = controller.HoudiniArchiveController(core)
        with mock.patch.dict(
            sys.modules,
            {
                "qtpy": qtpy,
                "qtpy.QtCore": qtcore,
                "change_prism.houdini_archive.dialog": fake_dialog,
            },
        ):
            archive._start_package(
                "scene.hip",
                r"S:\shot\Archives",
                "hython.exe",
                {},
                None,
                "source-key",
            )

        self.assertIn("dialog-shown", events)
        self.assertIn("thread-started", events)
        job = archive._active_jobs[0]
        self.assertIs(job["dialog"], progress_dialog)
        self.assertIsNone(job["thread"].parent)

        progress_dialog.canceled.callback()
        self.assertIn("cancel-requested", events)

        _FakeWorker.finished.callback(
            {"version": "v0001", "version_path": r"S:\shot\Archives\v0001"}
        )
        self.assertIn("dialog-closed", events)
        self.assertEqual(core.popups[0][0], "info")

        job["thread"].finished.callback()
        self.assertIn("thread-deleted", events)
        self.assertIn("bridge-deleted", events)
        self.assertFalse(archive._active_jobs)
        self.assertFalse(controller.heavy_jobs.is_active("archive_package"))


if __name__ == "__main__":
    unittest.main()
