from __future__ import unicode_literals

import os

from qtpy.QtCore import QObject, Qt, Signal, Slot
from qtpy.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QLabel,
    QProgressDialog,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from change_prism.houdini_archive.service import (
    PackageCancelled,
    execute_background_package,
    execute_package,
    format_bytes,
)


class PackageConfirmDialog(QDialog):
    def __init__(self, plan, parent=None):
        super(PackageConfirmDialog, self).__init__(parent)
        self.setWindowTitle("Package Houdini Archive")
        self.resize(980, 620)
        layout = QVBoxLayout(self)
        summary = plan["summary"]
        lines = [
            "Source: %s" % plan["source_hip"],
            "Houdini: %s (%s)"
            % (plan["houdini_version"], plan["hython_executable"]),
            "Target: %s"
            % os.path.join(
                plan.get("version_root", plan["archive_root"]),
                plan["proposed_version"],
            ),
            (
                "References: %d | Package: %d | Skipped Cache: %d | "
                "Skipped Missing: %d | Skipped Unsupported: %d | "
                "External HDA: %d"
            )
            % (
                summary["reference_count"],
                summary["package_input_count"],
                summary["skipped_cache_count"],
                summary.get("skipped_missing_count", 0),
                summary["skipped_unsupported_count"],
                summary["hda_count"],
            ),
            "Estimated payload: %s across %d files"
            % (
                format_bytes(plan["estimated_total_bytes"]),
                plan["estimated_file_count"],
            ),
        ]
        if plan.get("version_warning"):
            lines.append("WARNING: %s" % plan["version_warning"])
        skipped_missing = summary.get("skipped_missing_count", 0)
        if skipped_missing:
            lines.append(
                "WARNING: %d unavailable /mnt/nas reference(s) will be "
                "skipped and keep their original paths."
                % skipped_missing
            )
        if plan["available_bytes"] is not None:
            lines.append(
                "Available at destination: %s"
                % format_bytes(plan["available_bytes"])
            )
        summary_label = QLabel("\n".join(lines), self)
        summary_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(summary_label)

        rows = len(plan["dependencies"]) + len(plan["external_hdas"])
        self.table = QTableWidget(rows, 6, self)
        self.table.setHorizontalHeaderLabels(
            [
                "Node",
                "Parameter",
                "Original",
                "Classification",
                "Status",
                "Archive Path",
            ]
        )
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setWordWrap(False)
        self.table.verticalHeader().hide()
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        for row, dependency in enumerate(plan["dependencies"]):
            values = [
                dependency.get("node_path", ""),
                dependency.get("parameter", ""),
                dependency.get("original_value", ""),
                dependency.get("classification", ""),
                dependency.get("status", ""),
                dependency.get("packaged_path", ""),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setToolTip(str(value))
                self.table.setItem(row, column, item)
        offset = len(plan["dependencies"])
        for index, hda in enumerate(plan["external_hdas"]):
            values = [
                ", ".join(hda.get("node_types", [])),
                "HDA Library",
                hda.get("source", ""),
                "External HDA",
                hda.get("status", ""),
                hda.get("archive_path", ""),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setToolTip(str(value))
                self.table.setItem(offset + index, column, item)
        layout.addWidget(self.table, 1)

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


def create_progress_dialog(plan, parent=None):
    dialog = QProgressDialog(
        "Preparing Houdini Archive...",
        "Cancel",
        0,
        1000,
        parent,
    )
    dialog.setWindowTitle("Package Houdini Archive")
    dialog.setWindowModality(Qt.WindowModal)
    dialog.setMinimumDuration(0)
    dialog.setAutoClose(False)
    dialog.setAutoReset(False)
    dialog.setValue(0)
    return dialog


def create_background_progress_dialog(parent=None):
    dialog = QProgressDialog(
        "Packaging Houdini Archive in the background...",
        "Cancel",
        0,
        0,
        parent,
    )
    dialog.setWindowTitle("Package Houdini Archive")
    dialog.setWindowModality(Qt.WindowModal)
    dialog.setMinimumDuration(0)
    dialog.setAutoClose(False)
    dialog.setAutoReset(False)
    return dialog


class PackageWorker(QObject):
    progress = Signal(object, object, str)
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


class BackgroundPackageWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(
        self,
        source_hip,
        archive_root,
        hython_executable,
        worker_env,
    ):
        super(BackgroundPackageWorker, self).__init__()
        self.source_hip = source_hip
        self.archive_root = archive_root
        self.hython_executable = hython_executable
        self.worker_env = worker_env
        self._cancel_requested = False

    def request_cancel(self):
        self._cancel_requested = True

    def is_cancelled(self):
        return self._cancel_requested

    @Slot()
    def run(self):
        try:
            result = execute_background_package(
                self.source_hip,
                self.archive_root,
                hython_executable=self.hython_executable,
                worker_env=self.worker_env,
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

    @Slot(object, object, str)
    def update_progress(self, completed, total, message):
        value = int(float(completed) / float(total) * 1000) if total else 0
        self.dialog.setLabelText(
            "%s\n%s / %s"
            % (message, format_bytes(completed), format_bytes(total))
        )
        self.dialog.setValue(max(0, min(1000, value)))

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


class BackgroundUiBridge(QObject):
    def __init__(
        self,
        parent,
        on_finished,
        on_failed,
        on_cancelled,
        on_thread_finished,
    ):
        super(BackgroundUiBridge, self).__init__(parent)
        self.on_finished = on_finished
        self.on_failed = on_failed
        self.on_cancelled = on_cancelled
        self.on_thread_finished = on_thread_finished

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
