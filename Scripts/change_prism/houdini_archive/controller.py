from __future__ import unicode_literals

import os

from change_prism import heavy_jobs
from change_prism.houdini_archive import runner
from change_prism.dcc_paths import derive_hython
from change_prism.houdini_archive.service import (
    ArchiveError,
    find_shot_root,
    format_bytes,
)


MENU_LABEL = "Package Houdini Archive..."
SCENE_EXTENSIONS = (".hip", ".hiplc", ".hipnc")


class HoudiniArchiveController:
    def __init__(self, core, refresh_callback=None):
        self.core = core
        self.refresh_callback = refresh_callback
        self._active_jobs = []

    def add_file_context_menu(self, origin, menu, filepath):
        if not self.is_packageable_path(filepath):
            return
        menu.addSeparator()
        action = menu.addAction(MENU_LABEL)
        action.triggered.connect(
            lambda checked=False, path=filepath: self.package_houdini(path)
        )

    @staticmethod
    def is_packageable_path(filepath):
        if not filepath:
            return False
        path = os.path.abspath(os.fspath(filepath))
        return (
            os.path.isfile(path)
            and os.path.splitext(path)[1].lower() in SCENE_EXTENSIONS
            and bool(find_shot_root(path))
        )

    def package_houdini(self, source_hip):
        shot_root = find_shot_root(source_hip)
        if not shot_root:
            self.core.popup(
                "Could not determine the shot root for:\n%s" % source_hip,
                severity="warning",
            )
            return
        archive_root = os.path.join(shot_root, "Archives")
        source_key = os.path.normcase(os.path.abspath(source_hip))
        if (
            self._active_jobs
            or heavy_jobs.is_active("archive_package")
        ):
            self.core.popup(
                "A Houdini Archive job is already running in the "
                "background.",
                severity="info",
            )
            return

        from qtpy.QtWidgets import QApplication

        try:
            hython, environment = self._worker_configuration(source_hip)
        except (ArchiveError, runner.RunnerError) as exc:
            self.core.popup(str(exc), severity="warning")
            return

        parent = getattr(self.core, "pb", None) or QApplication.activeWindow()
        self._start_package(
            source_hip,
            archive_root,
            hython,
            environment,
            parent,
            source_key,
        )

    def _worker_configuration(self, source_hip):
        start_environment = getattr(self.core, "startEnv", None)
        environment = dict(
            os.environ if start_environment is None else start_environment
        )
        users = getattr(self.core, "users", None)
        if users is not None:
            for item in users.getUserEnvironment(
                appPluginName="Houdini"
            ) or []:
                environment[item["key"]] = item["value"]
        projects = getattr(self.core, "projects", None)
        if projects is not None:
            for item in projects.getProjectEnvironment(
                appPluginName="Houdini"
            ) or []:
                environment[item["key"]] = item["value"]

        override = None
        getter = getattr(self.core, "getExecutableOverride", None)
        if callable(getter):
            override = getter("Houdini")
        explicit_hython = derive_hython(override)
        source_version = runner.read_hip_version(source_hip)
        if explicit_hython:
            try:
                selected = runner.resolve_hython(
                    source_version,
                    explicit_path=explicit_hython,
                    environ=environment,
                )
            except runner.RunnerError:
                selected = runner.resolve_hython(
                    source_version,
                    environ=environment,
                )
        else:
            selected = runner.resolve_hython(
                source_version,
                environ=environment,
            )
        args = [selected["path"]]
        callback = getattr(self.core, "callback", None)
        if callable(callback):
            callback(name="preLaunchApp", args=[args, environment])
        hython = selected["path"]
        if (
            args
            and os.path.isfile(args[0])
            and os.path.basename(args[0]).lower()
            in ("hython", "hython.exe")
        ):
            hython = args[0]
        return hython, environment

    def _start_package(
        self,
        source_hip,
        archive_root,
        hython,
        environment,
        parent,
        source_key,
    ):
        from qtpy.QtCore import QThread
        from change_prism.houdini_archive.dialog import (
            BackgroundPackageWorker,
            BackgroundUiBridge,
        )

        if heavy_jobs.is_active("archive_package"):
            self.core.popup(
                "Another Archive package is already running.",
                severity="info",
            )
            return

        thread = QThread(parent)
        worker = BackgroundPackageWorker(
            source_hip,
            archive_root,
            hython,
            environment,
        )
        worker.moveToThread(thread)
        token = object()
        heavy_jobs.acquire("archive_package", token)
        job = {
            "thread": thread,
            "worker": worker,
            "source_key": source_key,
            "heavy_job_token": token,
        }
        bridge = BackgroundUiBridge(
            parent,
            on_finished=lambda result: self._package_finished(job, result),
            on_failed=lambda message: self._package_failed(job, message),
            on_cancelled=lambda: self._package_cancelled(job),
            on_thread_finished=lambda: self._cleanup_job(job),
        )
        job["bridge"] = bridge
        self._active_jobs.append(job)

        thread.started.connect(worker.run)
        worker.finished.connect(bridge.package_finished)
        worker.failed.connect(bridge.package_failed)
        worker.cancelled.connect(bridge.package_cancelled)
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        worker.cancelled.connect(worker.deleteLater)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.cancelled.connect(thread.quit)
        thread.finished.connect(bridge.thread_finished)
        thread.start()

    def _package_finished(self, job, result):
        details = [
            "Created Houdini Archive %s:" % result["version"],
            result["version_path"],
            "",
            "Status: %s" % result.get("status", "Complete"),
            "Files: %d | Size: %s"
            % (
                result.get("file_count", 0),
                format_bytes(result.get("total_bytes", 0)),
            ),
        ]
        if result.get("skipped_count", 0):
            details.append(
                "Skipped: %d (missing paths: %d)"
                % (
                    result["skipped_count"],
                    result.get("skipped_missing_count", 0),
                )
            )
        self.core.popup(
            "\n".join(details),
            severity="info",
        )
        self._refresh_archive()

    def _package_failed(self, job, message):
        self.core.popup(message, severity="error")
        self._refresh_archive()

    def _package_cancelled(self, job):
        self.core.popup(
            "Houdini Archive packaging was cancelled.",
            severity="info",
        )
        self._refresh_archive()

    def _cleanup_job(self, job):
        if job in self._active_jobs:
            self._active_jobs.remove(job)
        heavy_jobs.release(
            "archive_package",
            job.get("heavy_job_token"),
        )
        job["thread"].deleteLater()
        job["bridge"].deleteLater()

    def _refresh_archive(self):
        if callable(self.refresh_callback):
            self.refresh_callback()
