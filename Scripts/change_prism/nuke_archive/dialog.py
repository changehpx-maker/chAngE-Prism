from __future__ import unicode_literals

import os

from qtpy.QtCore import QObject, Qt, Signal, Slot
from qtpy.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPlainTextEdit,
    QProgressDialog,
    QVBoxLayout,
)

from change_prism.nuke_archive.service import (
    PackageCancelled,
    build_package_plan,
    execute_package,
    format_bytes,
)


class PreflightWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, source_nk, archive_root):
        super(PreflightWorker, self).__init__()
        self.source_nk = source_nk
        self.archive_root = archive_root

    @Slot()
    def run(self):
        try:
            plan = build_package_plan(
                self.source_nk,
                self.archive_root,
            )
        except Exception as exc:
            self.failed.emit(str(exc))
        else:
            self.finished.emit(plan)


class PreflightUiBridge(QObject):
    def __init__(
        self,
        dialog,
        on_finished,
        on_failed,
        on_thread_finished,
    ):
        super(PreflightUiBridge, self).__init__(dialog)
        self._on_finished = on_finished
        self._on_failed = on_failed
        self._on_thread_finished = on_thread_finished

    @Slot(object)
    def preflight_finished(self, plan):
        self._on_finished(plan)

    @Slot(str)
    def preflight_failed(self, message):
        self._on_failed(message)

    @Slot()
    def thread_finished(self):
        self._on_thread_finished()


def create_preflight_dialog(parent=None):
    dialog = QProgressDialog(
        "Scanning Nuke dependencies...",
        "",
        0,
        0,
        parent,
    )
    dialog.setWindowTitle("Package Nuke Archive")
    dialog.setWindowModality(Qt.WindowModal)
    dialog.setCancelButton(None)
    dialog.setMinimumDuration(0)
    dialog.setAutoClose(False)
    dialog.setAutoReset(False)
    return dialog


class PackageConfirmDialog(QDialog):
    def __init__(self, plan, parent=None):
        super(PackageConfirmDialog, self).__init__(parent)
        self.setWindowTitle("Package Nuke Archive")
        self.resize(760, 520)

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(
                "Review the package plan. The source Nuke script will not be modified."
            )
        )

        details = QPlainTextEdit(self)
        details.setReadOnly(True)
        details.setPlainText(self._format_plan(plan))
        layout.addWidget(details)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal,
            self,
        )
        buttons.button(QDialogButtonBox.Ok).setText("Create Archive")
        if (
            plan["available_bytes"] is not None
            and plan["estimated_total_bytes"] > plan["available_bytes"]
        ):
            buttons.button(QDialogButtonBox.Ok).setEnabled(False)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def _format_plan(plan):
        lines = [
            "Source:",
            "  %s" % plan["source_nk"],
            "",
            "Planned target:",
            "  %s" % os.path.join(
                plan.get("version_root", plan["archive_root"]),
                plan["proposed_version"],
            ),
            "",
            "Read nodes: %d" % len(plan["reads"]),
            "Unique copy items: %d" % len(plan["copy_jobs"]),
        ]
        lines.append(
            "Estimated payload: %s across %d files"
            % (
                format_bytes(plan["estimated_total_bytes"]),
                plan["estimated_file_count"],
            )
        )
        if plan["available_bytes"] is not None:
            lines.append(
                "Available at destination: %s"
                % format_bytes(plan["available_bytes"])
            )
            if plan["estimated_total_bytes"] > plan["available_bytes"]:
                lines.append(
                    "WARNING: The destination does not have enough free space."
                )
        lines.extend(["", "Material mapping:"])
        for job in plan["copy_jobs"]:
            lines.append(
                "  %s  <-  %s" % (job["material_folder"], job["source"])
            )
        if not plan["copy_jobs"]:
            lines.append("  No Read dependencies")
        return "\n".join(lines)


def create_progress_dialog(plan, parent=None):
    total = max(1, len(plan["copy_jobs"]))
    dialog = QProgressDialog(
        "Preparing Nuke Archive...",
        "Cancel",
        0,
        total,
        parent,
    )
    dialog.setWindowTitle("Package Nuke Archive")
    dialog.setWindowModality(Qt.WindowModal)
    dialog.setMinimumDuration(0)
    dialog.setAutoClose(False)
    dialog.setAutoReset(False)
    dialog.setValue(0)
    return dialog


class PackageWorker(QObject):
    progress = Signal(int, int, str)
    finished = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, plan):
        super(PackageWorker, self).__init__()
        self.plan = plan
        self._cancel_requested = False

    def request_cancel(self):
        self._cancel_requested = True

    def is_cancelled(self):
        return self._cancel_requested

    @Slot()
    def run(self):
        try:
            result = execute_package(
                self.plan,
                progress_callback=self.progress.emit,
                is_cancelled=self.is_cancelled,
            )
        except PackageCancelled:
            self.cancelled.emit()
        except Exception as exc:
            self.failed.emit(str(exc))
        else:
            self.finished.emit(result)


class PackageUiBridge(QObject):
    def __init__(
        self,
        dialog,
        on_finished,
        on_failed,
        on_cancelled,
        on_thread_finished,
    ):
        super(PackageUiBridge, self).__init__(dialog)
        self.dialog = dialog
        self.on_finished = on_finished
        self.on_failed = on_failed
        self.on_cancelled = on_cancelled
        self.on_thread_finished = on_thread_finished

    @Slot(int, int, str)
    def update_progress(self, completed, total, message):
        self.dialog.setMaximum(max(1, total))
        self.dialog.setLabelText(message)
        self.dialog.setValue(min(completed, max(1, total)))

    @Slot(object)
    def package_finished(self, result):
        self.on_finished(result)

    @Slot(str)
    def package_failed(self, message):
        self.on_failed(message)

    @Slot()
    def package_cancelled(self):
        self.on_cancelled()

    @Slot()
    def thread_finished(self):
        self.on_thread_finished()
