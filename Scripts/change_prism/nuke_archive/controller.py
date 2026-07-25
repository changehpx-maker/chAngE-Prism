from __future__ import unicode_literals

import os

from change_prism.nuke_archive.service import (
    ArchiveError,
    build_package_plan,
    find_shot_root,
)


MENU_LABEL = "Package Nuke Archive..."
TAB_LABEL = "Archive"


class NukeArchiveController:
    def __init__(self, core, refresh_callback=None):
        self.core = core
        self.refresh_callback = refresh_callback
        self.browser_widget = None
        self._active_jobs = []

    def add_project_browser_tab(self, origin):
        tab_widget = getattr(origin, "tbw_project", None)
        if tab_widget is not None:
            for index in range(tab_widget.count()):
                widget = tab_widget.widget(index)
                if widget.property("tabType") == TAB_LABEL:
                    self.browser_widget = widget
                    return

        from change_prism.nuke_archive.dialog import ArchiveBrowserWidget

        widget = ArchiveBrowserWidget(self.core, parent=origin)
        origin.addTab(TAB_LABEL, widget)
        self.browser_widget = widget

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
        shot_root = find_shot_root(source_nk)
        if not shot_root:
            self.core.popup(
                "Could not determine the shot root for:\n%s" % source_nk,
                severity="warning",
            )
            return

        archive_root = os.path.join(shot_root, "Archives")
        try:
            plan = build_package_plan(source_nk, archive_root)
        except ArchiveError as exc:
            self.core.popup(str(exc), severity="warning")
            return

        from qtpy.QtWidgets import QApplication, QDialog
        from change_prism.nuke_archive.dialog import PackageConfirmDialog

        parent = getattr(self.core, "pb", None) or QApplication.activeWindow()
        dialog = PackageConfirmDialog(plan, parent=parent)
        if dialog.exec_() != QDialog.Accepted:
            return
        self._start_package(plan, parent)

    def _start_package(self, plan, parent):
        from qtpy.QtCore import QThread
        from change_prism.nuke_archive.dialog import (
            PackageUiBridge,
            PackageWorker,
            create_progress_dialog,
        )

        progress_dialog = create_progress_dialog(plan, parent=parent)
        thread = QThread(parent)
        worker = PackageWorker(plan)
        worker.moveToThread(thread)
        job = {
            "thread": thread,
            "worker": worker,
            "dialog": progress_dialog,
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
        thread.deleteLater()
        bridge.deleteLater()

    def refresh_archive_tab(self):
        if callable(self.refresh_callback):
            self.refresh_callback()
            return
        widget = self.browser_widget
        if widget is not None:
            try:
                widget.refresh_versions()
            except RuntimeError:
                self.browser_widget = None
