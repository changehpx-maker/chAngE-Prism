from __future__ import unicode_literals

import os

from change_prism import heavy_jobs
from change_prism.nuke_archive.service import (
    find_shot_root,
)


MENU_LABEL = "Package Nuke Archive..."


class NukeArchiveController:
    def __init__(self, core, refresh_callback=None):
        self.core = core
        self.refresh_callback = refresh_callback
        self._active_jobs = []
        self._preflight_job = None

    def add_file_context_menu(self, origin, menu, filepath):
        if not self.is_packageable_path(filepath):
            return
        menu.addSeparator()
        action = menu.addAction(MENU_LABEL)
        action.triggered.connect(
            lambda checked=False, path=filepath: self.package_nuke(path)
        )

    @staticmethod
    def is_packageable_path(filepath):
        if not filepath:
            return False
        path = os.path.abspath(os.fspath(filepath))
        return (
            os.path.isfile(path)
            and os.path.splitext(path)[1].lower() == ".nk"
            and bool(find_shot_root(path))
        )

    def package_nuke(self, source_nk):
        if (
            self._preflight_job is not None
            or self._active_jobs
            or heavy_jobs.is_active("archive_package")
        ):
            self.core.popup(
                "A Nuke Archive job is already running.",
                severity="info",
            )
            return
        shot_root = find_shot_root(source_nk)
        if not shot_root:
            self.core.popup(
                "Could not determine the shot root for:\n%s" % source_nk,
                severity="warning",
            )
            return

        archive_root = os.path.join(shot_root, "Archives")
        from qtpy.QtWidgets import QApplication

        parent = getattr(self.core, "pb", None) or QApplication.activeWindow()
        self._start_preflight(source_nk, archive_root, parent)

    def _start_preflight(self, source_nk, archive_root, parent):
        from qtpy.QtCore import QThread
        from change_prism.nuke_archive.dialog import (
            PreflightUiBridge,
            PreflightWorker,
            create_preflight_dialog,
        )

        progress_dialog = create_preflight_dialog(parent)
        thread = QThread(parent)
        worker = PreflightWorker(source_nk, archive_root)
        worker.moveToThread(thread)
        job = {
            "thread": thread,
            "worker": worker,
            "dialog": progress_dialog,
        }
        bridge = PreflightUiBridge(
            progress_dialog,
            on_finished=lambda plan: self._preflight_finished(
                job,
                plan,
                parent,
            ),
            on_failed=lambda message: self._preflight_failed(job, message),
            on_thread_finished=lambda: self._cleanup_preflight(job),
        )
        job["bridge"] = bridge
        self._preflight_job = job

        thread.started.connect(worker.run)
        worker.finished.connect(bridge.preflight_finished)
        worker.failed.connect(bridge.preflight_failed)
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(bridge.thread_finished)
        progress_dialog.show()
        thread.start()

    def _preflight_finished(self, job, plan, parent):
        job["dialog"].close()
        if self._preflight_job is job:
            self._preflight_job = None

        from qtpy.QtWidgets import QDialog
        from change_prism.nuke_archive.dialog import PackageConfirmDialog

        dialog = PackageConfirmDialog(plan, parent=parent)
        if dialog.exec_() != QDialog.Accepted:
            return
        self._start_package(plan, parent)

    def _preflight_failed(self, job, message):
        job["dialog"].close()
        if self._preflight_job is job:
            self._preflight_job = None
        self.core.popup(message, severity="warning")

    def _cleanup_preflight(self, job):
        if self._preflight_job is job:
            self._preflight_job = None
        job["thread"].deleteLater()
        job["bridge"].deleteLater()

    def _start_package(self, plan, parent):
        from qtpy.QtCore import QThread
        from change_prism.nuke_archive.dialog import (
            PackageUiBridge,
            PackageWorker,
            create_progress_dialog,
        )

        if (
            self._active_jobs
            or heavy_jobs.is_active("archive_package")
        ):
            self.core.popup(
                "A Nuke Archive job is already running.",
                severity="info",
            )
            return

        progress_dialog = create_progress_dialog(plan, parent=parent)
        thread = QThread(parent)
        worker = PackageWorker(plan)
        worker.moveToThread(thread)
        token = object()
        heavy_jobs.acquire("archive_package", token)
        job = {
            "thread": thread,
            "worker": worker,
            "dialog": progress_dialog,
            "heavy_job_token": token,
        }
        bridge = PackageUiBridge(
            progress_dialog,
            on_finished=lambda result: self._package_finished(job, result),
            on_failed=lambda message: self._package_failed(job, message),
            on_cancelled=lambda: self._package_cancelled(job),
            on_thread_finished=lambda: self._cleanup_job(job),
        )
        job["bridge"] = bridge
        self._active_jobs.append(job)

        thread.started.connect(worker.run)
        worker.progress.connect(bridge.update_progress)
        worker.finished.connect(bridge.package_finished)
        worker.failed.connect(bridge.package_failed)
        worker.cancelled.connect(bridge.package_cancelled)
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        worker.cancelled.connect(worker.deleteLater)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.cancelled.connect(thread.quit)
        progress_dialog.canceled.connect(
            lambda current_worker=worker: current_worker.request_cancel()
        )
        thread.finished.connect(bridge.thread_finished)

        progress_dialog.show()
        thread.start()

    def _package_finished(self, job, result):
        job["dialog"].close()
        self.core.popup(
            "Created Nuke Archive %s:\n%s"
            % (result["version"], result["version_path"]),
            severity="info",
        )
        self.refresh_archive_tab()

    def _package_failed(self, job, message):
        job["dialog"].close()
        self.core.popup(message, severity="error")
        self.refresh_archive_tab()

    def _package_cancelled(self, job):
        job["dialog"].close()
        self.core.popup("Nuke Archive packaging was cancelled.", severity="info")
        self.refresh_archive_tab()

    def _cleanup_job(self, job):
        thread = job["thread"]
        bridge = job["bridge"]
        if job in self._active_jobs:
            self._active_jobs.remove(job)
        heavy_jobs.release(
            "archive_package",
            job.get("heavy_job_token"),
        )
        thread.deleteLater()
        bridge.deleteLater()

    def refresh_archive_tab(self):
        if callable(self.refresh_callback):
            self.refresh_callback()
