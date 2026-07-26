from __future__ import unicode_literals

import os

from qtpy.QtCore import QObject, QSize, Qt, QThread, QUrl, Signal, Slot
from qtpy.QtGui import QDesktopServices, QIcon
from qtpy.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QProgressDialog,
    QPushButton,
    QSplitter,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from change_prism.nuke_archive.service import (
    PackageCancelled,
    build_package_plan,
    calculate_archive_payload_stats,
    delete_archive_version,
    execute_package,
    format_bytes,
    scan_archive_versions,
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


class ArchiveBrowserWidget(QWidget):
    def __init__(self, core, parent=None):
        super(ArchiveBrowserWidget, self).__init__(parent)
        self.core = core
        self.refreshStatus = "invalid"
        self._versions = []

        import EntityWidget

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Horizontal, self)
        layout.addWidget(splitter)

        self.w_entities = EntityWidget.EntityWidget(
            core=self.core,
            refresh=False,
            pages=["Shots"],
        )
        splitter.addWidget(self.w_entities)

        right = QWidget(splitter)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(16, 12, 16, 16)
        right_layout.setSpacing(10)

        heading_layout = QHBoxLayout()
        heading_layout.setSpacing(8)
        heading_text_layout = QVBoxLayout()
        heading_text_layout.setSpacing(2)

        title = QLabel("Nuke Archives", right)
        title_font = title.font()
        title_font.setPointSize(title_font.pointSize() + 2)
        title_font.setBold(True)
        title.setFont(title_font)
        heading_text_layout.addWidget(title)

        hint = QLabel(
            "Double-click an Archive Nuke to open it, or use the actions on the right.",
            right,
        )
        hint.setEnabled(False)
        heading_text_layout.addWidget(hint)
        heading_layout.addLayout(heading_text_layout, 1)

        self.nuke_icon = self._get_nuke_icon()
        self.open_nuke_button = QPushButton("Open Nuke", right)
        self.open_nuke_button.setMinimumHeight(32)
        self.open_nuke_button.setToolTip(
            "Open with the Nuke executable, mode and environment configured in Prism."
        )
        if not self.nuke_icon.isNull():
            self.open_nuke_button.setIcon(self.nuke_icon)
        self.open_nuke_button.clicked.connect(self.open_selected_nuke)
        heading_layout.addWidget(self.open_nuke_button)

        self.open_folder_button = QPushButton("Open Folder", right)
        self.open_folder_button.setMinimumHeight(32)
        self.open_folder_button.setIcon(
            self.style().standardIcon(QStyle.SP_DirOpenIcon)
        )
        self.open_folder_button.clicked.connect(self.open_selected_folder)
        heading_layout.addWidget(self.open_folder_button)
        right_layout.addLayout(heading_layout)

        self.status_label = QLabel("Select a shot to view its Archives.", right)
        self.status_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        right_layout.addWidget(self.status_label)

        self.table = QTableWidget(0, 7, right)
        self.table.setHorizontalHeaderLabels(
            [
                "Version",
                "Archive Nuke",
                "Source Nuke",
                "Created By",
                "Created At",
                "Status",
                "Actions",
            ]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setWordWrap(False)
        self.table.setTextElideMode(Qt.ElideMiddle)
        self.table.setIconSize(QSize(22, 22))
        self.table.setMinimumHeight(260)
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(38)
        header = self.table.horizontalHeader()
        header.setMinimumSectionSize(72)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.itemDoubleClicked.connect(
            lambda _item, _column: self.open_selected_nuke()
        )
        self.table.itemSelectionChanged.connect(self._selection_changed)

        content_splitter = QSplitter(Qt.Vertical, right)
        content_splitter.addWidget(self.table)

        details_group = QGroupBox("Version Details", content_splitter)
        details_layout = QVBoxLayout(details_group)
        details_layout.setContentsMargins(10, 10, 10, 10)
        details_layout.setSpacing(8)

        summary_layout = QGridLayout()
        summary_layout.setHorizontalSpacing(24)
        summary_fields = [
            ("Status", "detail_status_value"),
            ("Read Nodes", "detail_read_count_value"),
            ("Copy Items", "detail_copy_count_value"),
            ("Files", "detail_file_count_value"),
            ("Material Size", "detail_size_value"),
        ]
        for column, field in enumerate(summary_fields):
            label = QLabel(field[0], details_group)
            label.setEnabled(False)
            summary_layout.addWidget(label, 0, column)
            value = QLabel("-", details_group)
            value.setTextInteractionFlags(Qt.TextSelectableByMouse)
            summary_layout.addWidget(value, 1, column)
            setattr(self, field[1], value)
        summary_layout.setColumnStretch(len(summary_fields), 1)
        details_layout.addLayout(summary_layout)

        path_layout = QGridLayout()
        path_layout.setHorizontalSpacing(8)
        path_layout.addWidget(QLabel("Archive Nuke", details_group), 0, 0)
        self.detail_archive_path = QLineEdit(details_group)
        self.detail_archive_path.setReadOnly(True)
        path_layout.addWidget(self.detail_archive_path, 0, 1)
        path_layout.addWidget(QLabel("Source Nuke", details_group), 1, 0)
        self.detail_source_path = QLineEdit(details_group)
        self.detail_source_path.setReadOnly(True)
        path_layout.addWidget(self.detail_source_path, 1, 1)
        path_layout.setColumnStretch(1, 1)
        details_layout.addLayout(path_layout)

        self.mapping_table = QTableWidget(0, 3, details_group)
        self.mapping_table.setHorizontalHeaderLabels(
            ["Read Node", "Original Path", "Archive Path"]
        )
        self.mapping_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.mapping_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.mapping_table.setAlternatingRowColors(True)
        self.mapping_table.setShowGrid(False)
        self.mapping_table.setWordWrap(False)
        self.mapping_table.setTextElideMode(Qt.ElideMiddle)
        self.mapping_table.verticalHeader().hide()
        mapping_header = self.mapping_table.horizontalHeader()
        mapping_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        mapping_header.setSectionResizeMode(1, QHeaderView.Stretch)
        mapping_header.setSectionResizeMode(2, QHeaderView.Stretch)
        details_layout.addWidget(self.mapping_table)

        content_splitter.addWidget(details_group)
        content_splitter.setSizes([340, 240])
        content_splitter.setStretchFactor(0, 2)
        content_splitter.setStretchFactor(1, 1)
        right_layout.addWidget(content_splitter)
        splitter.addWidget(right)
        splitter.setSizes([320, 900])
        splitter.setStretchFactor(1, 1)
        self._update_action_buttons()
        self._update_details()

        shots_page = self.w_entities.getPage("Shots")
        if shots_page is not None:
            shots_page.itemChanged.connect(
                lambda _items=None: self.refresh_versions()
            )

    def entered(self, prevTab=None, navData=None):
        if navData:
            self.w_entities.navigate(navData)
        elif prevTab is not None and hasattr(prevTab, "w_entities"):
            self.w_entities.syncFromWidget(prevTab.w_entities)

    def getSelectedContext(self):
        return self.w_entities.getCurrentData()

    def refreshUI(self):
        self.w_entities.refreshEntities(restoreSelection=True)
        self.refresh_versions()
        self.refreshStatus = "valid"

    def refresh_versions(self):
        self.table.setRowCount(0)
        self._versions = []
        entity = self.w_entities.getCurrentData()
        if not isinstance(entity, dict) or entity.get("type") != "shot":
            self.status_label.setText("Select a shot to view its Archives.")
            return

        try:
            shot_path = self.core.getEntityPath(entity=entity)
        except Exception:
            shot_path = ""
        if not shot_path:
            self.status_label.setText("Could not resolve the selected shot path.")
            return

        archive_root = os.path.join(shot_path, "Archives")
        self._versions = scan_archive_versions(archive_root)
        self.status_label.setText(archive_root)
        self.status_label.setToolTip(archive_root)
        self.table.setRowCount(len(self._versions))
        for row, version in enumerate(self._versions):
            packaged_name = (
                os.path.basename(version["packaged_nk"])
                if version["packaged_nk"]
                else ""
            )
            source_name = (
                os.path.basename(version["source_nk"])
                if version["source_nk"]
                else ""
            )
            created_at = version["created_at"].replace("T", " ")[:19]
            values = [
                version["version"],
                packaged_name,
                source_name,
                version["created_by"],
                created_at,
                version["status"],
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(Qt.UserRole, version)
                if column == 1:
                    item.setToolTip(version["packaged_nk"])
                    if not self.nuke_icon.isNull():
                        item.setIcon(self.nuke_icon)
                elif column == 2:
                    item.setToolTip(version["source_nk"])
                    if not self.nuke_icon.isNull():
                        item.setIcon(self.nuke_icon)
                elif column == 5:
                    status_icon = (
                        QStyle.SP_DialogApplyButton
                        if version["status"] == "Complete"
                        else QStyle.SP_MessageBoxWarning
                    )
                    item.setIcon(self.style().standardIcon(status_icon))
                self.table.setItem(row, column, item)

            delete_button = QPushButton("Delete", self.table)
            delete_button.setIcon(
                self.style().standardIcon(QStyle.SP_TrashIcon)
            )
            delete_button.setToolTip(
                "Permanently delete this Archive version and all packaged media."
            )
            delete_button.setEnabled(version["status"] != "Incomplete")
            delete_button.clicked.connect(
                lambda checked=False, archive=version: self.delete_archive(
                    archive
                )
            )
            self.table.setCellWidget(row, 6, delete_button)
        if self._versions:
            self.table.selectRow(0)
        self._update_action_buttons()
        self._update_details()

    def _get_nuke_icon(self):
        try:
            icon = self.core.getIconForFileType(".nk")
            if icon and not icon.isNull():
                return icon
        except Exception:
            pass

        prism_root = getattr(self.core, "prismRoot", "")
        icon_path = os.path.join(
            prism_root,
            "Plugins",
            "Apps",
            "Nuke",
            "Resources",
            "NukeXApp.ico",
        )
        return QIcon(icon_path) if os.path.isfile(icon_path) else QIcon()

    def _update_action_buttons(self):
        version = self.selected_version()
        packaged_nk = version.get("packaged_nk", "") if version else ""
        version_path = version.get("path", "") if version else ""
        self.open_nuke_button.setEnabled(
            bool(packaged_nk and os.path.isfile(packaged_nk))
        )
        self.open_folder_button.setEnabled(
            bool(version_path and os.path.isdir(version_path))
        )

    def _selection_changed(self):
        self._update_action_buttons()
        self._update_details()

    def _update_details(self):
        version = self.selected_version()
        if not version:
            self.detail_status_value.setText("-")
            self.detail_read_count_value.setText("-")
            self.detail_copy_count_value.setText("-")
            self.detail_file_count_value.setText("-")
            self.detail_size_value.setText("-")
            self.detail_archive_path.clear()
            self.detail_source_path.clear()
            self.mapping_table.setRowCount(0)
            return

        self.detail_status_value.setText(version.get("status", ""))
        self.detail_read_count_value.setText(
            str(version.get("read_count", 0))
        )
        self.detail_copy_count_value.setText(
            str(version.get("copy_job_count", 0))
        )
        file_count = version.get("file_count")
        total_bytes = version.get("total_bytes")
        if file_count is None or total_bytes is None:
            file_count, total_bytes = calculate_archive_payload_stats(
                version.get("path", ""),
                version.get("copy_jobs", []),
            )
            if file_count is not None and total_bytes is not None:
                version["file_count"] = file_count
                version["total_bytes"] = total_bytes
        self.detail_file_count_value.setText(
            str(file_count) if file_count is not None else "Not recorded"
        )
        self.detail_size_value.setText(format_bytes(total_bytes))
        self.detail_archive_path.setText(version.get("packaged_nk", ""))
        self.detail_source_path.setText(version.get("source_nk", ""))

        reads = version.get("reads", [])
        self.mapping_table.setRowCount(len(reads))
        for row, read in enumerate(reads):
            values = [
                read.get("node_name", ""),
                read.get("original_path", ""),
                read.get("packaged_path", ""),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setToolTip(value)
                self.mapping_table.setItem(row, column, item)

    def selected_version(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.data(Qt.UserRole) if item is not None else None

    def open_selected_nuke(self):
        version = self.selected_version()
        if not version:
            return
        path = version.get("packaged_nk", "")
        if path and os.path.isfile(path):
            prism_opener = getattr(self.core, "openFile", None)
            if callable(prism_opener):
                prism_opener(path)
            else:
                QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def open_selected_folder(self):
        version = self.selected_version()
        if not version:
            return
        path = version.get("path", "")
        if path and os.path.isdir(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def delete_archive(self, version):
        if not version:
            return
        if version.get("status") == "Incomplete":
            self._show_popup(
                "Incomplete Archive versions cannot be deleted while they may "
                "still be packaging.",
                severity="warning",
            )
            return

        version_path = version.get("path", "")
        archive_root = os.path.dirname(version_path)
        message = (
            "Permanently delete Nuke Archive %s?\n\n%s\n\n"
            "The archived Nuke script, manifest and all packaged media will "
            "be removed. This cannot be undone."
            % (version.get("version", ""), version_path)
        )
        popup_question = getattr(self.core, "popupQuestion", None)
        if callable(popup_question):
            answer = popup_question(
                message,
                title="Delete Nuke Archive",
                buttons=["Delete Archive", "Cancel"],
                default="Cancel",
                escapeButton="Cancel",
                icon=QMessageBox.Warning,
                parent=self,
            )
            confirmed = answer == "Delete Archive"
        else:
            answer = QMessageBox.warning(
                self,
                "Delete Nuke Archive",
                message,
                QMessageBox.Yes | QMessageBox.Cancel,
                QMessageBox.Cancel,
            )
            confirmed = answer == QMessageBox.Yes
        if not confirmed:
            return

        try:
            result = delete_archive_version(version_path, archive_root)
        except Exception as exc:
            self._show_popup(str(exc), severity="error")
            return

        self._show_popup(
            "Deleted Nuke Archive %s:\n%s"
            % (result["version"], result["deleted_path"]),
            severity="info",
        )
        self.refresh_versions()

    def _show_popup(self, message, severity):
        popup = getattr(self.core, "popup", None)
        if callable(popup):
            popup(message, severity=severity)
            return
        if severity in ("warning", "error"):
            QMessageBox.warning(self, "Nuke Archive", message)
        else:
            QMessageBox.information(self, "Nuke Archive", message)

    def _show_context_menu(self, position):
        index = self.table.indexAt(position)
        if index.isValid():
            self.table.selectRow(index.row())
        version = self.selected_version()
        if not version:
            return
        menu = QMenu(self)
        open_nuke = menu.addAction("Open Archive Nuke")
        open_nuke.setEnabled(os.path.isfile(version.get("packaged_nk", "")))
        open_nuke.triggered.connect(
            lambda checked=False: self.open_selected_nuke()
        )
        open_folder = menu.addAction("Open Archive Folder")
        open_folder.triggered.connect(
            lambda checked=False: self.open_selected_folder()
        )
        menu.addSeparator()
        delete_action = menu.addAction("Delete Archive...")
        delete_action.setEnabled(version.get("status") != "Incomplete")
        delete_action.triggered.connect(
            lambda checked=False, archive=version: self.delete_archive(archive)
        )
        menu.exec_(self.table.viewport().mapToGlobal(position))
