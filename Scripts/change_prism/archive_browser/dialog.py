from __future__ import unicode_literals

import os
import re

from qtpy.QtCore import QSize, Qt, QUrl
from qtpy.QtGui import QDesktopServices, QIcon
from qtpy.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from change_prism.archive_core import (
    calculate_archive_payload_stats,
    delete_archive_version,
    format_bytes,
    scan_archive_versions,
)


class LazyArchiveBrowserWidget(QWidget):
    """Delay construction of Prism's EntityWidget until this tab is opened."""

    def __init__(self, core, parent=None):
        super(LazyArchiveBrowserWidget, self).__init__(parent)
        self.core = core
        self.refreshStatus = "invalid"
        self._browser = None
        self.setProperty("tabType", "Archive")
        self.setProperty("archiveBrowserKind", "multi_dcc")

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._placeholder = QLabel("Open Archives to load Archive data.", self)
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setEnabled(False)
        self._layout.addWidget(self._placeholder)

    def _ensure_browser(self):
        if self._browser is None:
            browser = ArchiveBrowserWidget(self.core, parent=self)
            self._layout.replaceWidget(self._placeholder, browser)
            self._placeholder.deleteLater()
            self._browser = browser
        return self._browser

    def entered(self, prevTab=None, navData=None):
        first_open = self._browser is None
        browser = self._ensure_browser()
        if first_open:
            browser.w_entities.refreshEntities(defaultSelection=False)
        browser.entered(prevTab=prevTab, navData=navData)
        self.refreshStatus = "valid"

    def getSelectedContext(self):
        if self._browser is None:
            return None
        return self._browser.getSelectedContext()

    def refreshUI(self):
        if self._browser is None:
            self.refreshStatus = "invalid"
            return
        self._browser.refreshUI()
        self.refreshStatus = self._browser.refreshStatus

    def refresh_versions(self):
        if self._browser is None:
            self.refreshStatus = "invalid"
            return
        self._browser.refresh_versions()


class ArchiveBrowserWidget(QWidget):
    def __init__(self, core, parent=None):
        super(ArchiveBrowserWidget, self).__init__(parent)
        self.core = core
        self.refreshStatus = "invalid"
        self._versions = []
        self._version_groups = []
        self.setProperty("tabType", "Archive")
        self.setProperty("archiveBrowserKind", "multi_dcc")

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

        heading = QHBoxLayout()
        heading_text = QVBoxLayout()
        heading_text.setSpacing(2)
        title = QLabel("Archives", right)
        font = title.font()
        font.setPointSize(font.pointSize() + 2)
        font.setBold(True)
        title.setFont(font)
        heading_text.addWidget(title)
        hint = QLabel(
            "Browse packaged Nuke and Houdini scenes for the selected shot.",
            right,
        )
        hint.setEnabled(False)
        heading_text.addWidget(hint)
        heading.addLayout(heading_text, 1)

        self.open_scene_button = QPushButton("Open Scene", right)
        self.open_scene_button.setMinimumHeight(32)
        self.open_scene_button.clicked.connect(self.open_selected_scene)
        heading.addWidget(self.open_scene_button)
        self.open_folder_button = QPushButton("Open Folder", right)
        self.open_folder_button.setMinimumHeight(32)
        self.open_folder_button.setIcon(
            self.style().standardIcon(QStyle.SP_DirOpenIcon)
        )
        self.open_folder_button.clicked.connect(self.open_selected_folder)
        heading.addWidget(self.open_folder_button)
        right_layout.addLayout(heading)

        self.status_label = QLabel(
            "Select a shot to view its Archives.", right
        )
        self.status_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        right_layout.addWidget(self.status_label)

        self.table = QTableWidget(0, 10, right)
        self.table.setHorizontalHeaderLabels(
            [
                "Version",
                "Application",
                "Department",
                "Task",
                "Archive Scene",
                "Source Scene",
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
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.ResizeToContents)
        self.table.itemSelectionChanged.connect(self._selection_changed)
        self.table.itemDoubleClicked.connect(
            lambda _item: self.open_selected_scene()
        )
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(
            self._show_context_menu
        )
        right_layout.addWidget(self.table, 2)

        details = QGroupBox("Version Details", right)
        detail_layout = QGridLayout(details)
        self.detail_values = {}
        labels = (
            ("status", "Status"),
            ("application", "Application"),
            ("department", "Department"),
            ("task", "Task"),
            ("houdini_version", "Houdini Version"),
            ("fps", "FPS"),
            ("frame_range", "Frame Range"),
            ("reference_count", "References"),
            ("package_input_count", "Packaged Inputs"),
            ("copy_job_count", "Copy Items"),
            ("skipped_cache_count", "Skipped Cache"),
            ("skipped_missing_count", "Skipped Missing"),
            ("hda_count", "External HDA"),
            ("file_count", "Files"),
            ("size", "Payload"),
        )
        for index, (key, label) in enumerate(labels):
            row = index // 4
            column = (index % 4) * 2
            detail_layout.addWidget(QLabel(label + ":", details), row, column)
            value = QLabel("-", details)
            value.setTextInteractionFlags(Qt.TextSelectableByMouse)
            detail_layout.addWidget(value, row, column + 1)
            self.detail_values[key] = value

        path_row = (len(labels) + 3) // 4
        detail_layout.addWidget(QLabel("Archive:", details), path_row, 0)
        self.detail_archive_path = QLineEdit(details)
        self.detail_archive_path.setReadOnly(True)
        detail_layout.addWidget(
            self.detail_archive_path, path_row, 1, 1, 7
        )
        detail_layout.addWidget(
            QLabel("Source:", details), path_row + 1, 0
        )
        self.detail_source_path = QLineEdit(details)
        self.detail_source_path.setReadOnly(True)
        detail_layout.addWidget(
            self.detail_source_path, path_row + 1, 1, 1, 7
        )
        right_layout.addWidget(details)

        self.mapping_table = QTableWidget(0, 6, right)
        self.mapping_table.setHorizontalHeaderLabels(
            [
                "Node",
                "Parameter",
                "Original",
                "Archive Path",
                "Classification",
                "Status",
            ]
        )
        self.mapping_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.mapping_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.mapping_table.setWordWrap(False)
        self.mapping_table.verticalHeader().hide()
        mapping_header = self.mapping_table.horizontalHeader()
        mapping_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        mapping_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        mapping_header.setSectionResizeMode(2, QHeaderView.Stretch)
        mapping_header.setSectionResizeMode(3, QHeaderView.Stretch)
        mapping_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        mapping_header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        right_layout.addWidget(self.mapping_table, 1)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        try:
            page = self.w_entities.getPage("Shots")
            page.itemChanged.connect(lambda _item: self.refresh_versions())
        except Exception:
            pass
        self._update_action_buttons()

    def entered(self, prevTab=None, navData=None):
        if navData:
            self.w_entities.navigate(navData)
        elif prevTab is not None and hasattr(prevTab, "w_entities"):
            self.w_entities.syncFromWidget(prevTab.w_entities)
        self.refresh_versions()

    def getSelectedContext(self):
        return self.w_entities.getCurrentData()

    def refreshUI(self):
        self.w_entities.refreshEntities(restoreSelection=True)
        self.refresh_versions()
        self.refreshStatus = "valid"

    def refresh_versions(self):
        entity = self.w_entities.getCurrentData()
        if not entity or entity.get("type") != "shot":
            self._versions = []
            self._version_groups = []
            self.table.setRowCount(0)
            self.status_label.setText(
                "Select a shot to view its Archives."
            )
            self._selection_changed()
            return
        try:
            shot_path = self.core.getEntityPath(entity=entity)
        except TypeError:
            shot_path = self.core.getEntityPath(entity)
        archive_root = os.path.join(shot_path, "Archives")
        self._versions = scan_archive_versions(archive_root)
        self._version_groups = self._group_archive_versions(
            self._versions
        )
        self.status_label.setText(archive_root)
        self.status_label.setToolTip(archive_root)
        self.table.setRowCount(len(self._version_groups))
        for row, versions in enumerate(self._version_groups):
            self._populate_group_row(row, versions)
        if self._version_groups:
            self.table.selectRow(0)
        else:
            self._selection_changed()

    def _populate_group_row(self, row, versions):
        combo = QComboBox(self.table)
        combo.setMinimumWidth(88)
        for version in versions:
            combo.addItem(version.get("version", ""), version)
        combo.currentIndexChanged.connect(
            lambda _index, current_row=row: self._version_changed(
                current_row
            )
        )
        self.table.setCellWidget(row, 0, combo)

        delete_button = QPushButton("Delete", self.table)
        delete_button.setMinimumHeight(28)
        delete_button.clicked.connect(
            lambda checked=False, current_row=row: self.delete_archive(
                self._version_for_row(current_row)
            )
        )
        self.table.setCellWidget(row, 9, delete_button)
        self._set_row_version(row, versions[0])

    def _set_row_version(self, row, version):
        application = version.get("application", "").capitalize()
        archive_scene = version.get("packaged_scene", "")
        source_scene = version.get("source_scene", "")
        values = [
            application,
            version.get("department", ""),
            version.get("task", ""),
            os.path.basename(archive_scene),
            os.path.basename(source_scene),
            version.get("created_by", ""),
            version.get("created_at", ""),
            version.get("status", ""),
        ]
        icon = self._get_application_icon(version.get("application"))
        for offset, value in enumerate(values):
            column = offset + 1
            item = QTableWidgetItem(str(value))
            item.setToolTip(str(value))
            if column == 1:
                item.setData(Qt.UserRole, version)
            if column in (1, 4) and not icon.isNull():
                item.setIcon(icon)
            self.table.setItem(row, column, item)

        delete_button = self.table.cellWidget(row, 9)
        delete_button.setEnabled(version.get("status") != "Incomplete")

    def _version_changed(self, row):
        version = self._version_for_row(row)
        if not version:
            return
        self._set_row_version(row, version)
        self.table.selectRow(row)
        self._selection_changed()

    @staticmethod
    def _group_archive_versions(versions):
        groups = {}
        for version in versions:
            key = _archive_group_key(version)
            groups.setdefault(key, []).append(version)
        result = list(groups.values())
        for group in result:
            group.sort(
                key=lambda item: item.get("task_number", 0),
                reverse=True,
            )
        result.sort(
            key=lambda group: (
                group[0].get("created_at", ""),
                group[0].get("storage_number", 0),
            ),
            reverse=True,
        )
        return result

    def _get_application_icon(self, application):
        extension = ".hip" if application == "houdini" else ".nk"
        try:
            icon = self.core.getIconForFileType(extension)
            if icon and not icon.isNull():
                return icon
        except Exception:
            pass
        prism_root = getattr(self.core, "prismRoot", "")
        if application == "houdini":
            path = os.path.join(
                prism_root,
                "Plugins",
                "Apps",
                "Houdini",
                "UserInterfaces",
                "houdini.ico",
            )
        else:
            path = os.path.join(
                prism_root,
                "Plugins",
                "Apps",
                "Nuke",
                "Resources",
                "NukeXApp.ico",
            )
        return QIcon(path) if os.path.isfile(path) else QIcon()

    def selected_version(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return self._version_for_row(row)

    def _version_for_row(self, row):
        combo = self.table.cellWidget(row, 0)
        if isinstance(combo, QComboBox) and combo.currentIndex() >= 0:
            return combo.itemData(combo.currentIndex())
        item = self.table.item(row, 1)
        return item.data(Qt.UserRole) if item is not None else None

    def _selection_changed(self):
        self._update_action_buttons()
        self._update_details()

    def _update_action_buttons(self):
        version = self.selected_version()
        scene = version.get("packaged_scene", "") if version else ""
        folder = version.get("path", "") if version else ""
        application = version.get("application", "") if version else ""
        self.open_scene_button.setText(
            "Open Houdini"
            if application == "houdini"
            else "Open Nuke"
            if application == "nuke"
            else "Open Scene"
        )
        icon = self._get_application_icon(application) if version else QIcon()
        self.open_scene_button.setIcon(icon)
        self.open_scene_button.setEnabled(
            bool(scene and os.path.isfile(scene))
        )
        self.open_folder_button.setEnabled(
            bool(folder and os.path.isdir(folder))
        )

    def _update_details(self):
        version = self.selected_version()
        if not version:
            for label in self.detail_values.values():
                label.setText("-")
            self.detail_archive_path.clear()
            self.detail_source_path.clear()
            self.mapping_table.setRowCount(0)
            return
        frame_range = version.get("frame_range") or []
        detail_data = {
            "status": version.get("status", ""),
            "application": version.get("application", "").capitalize(),
            "department": version.get("department") or "-",
            "task": version.get("task") or "-",
            "houdini_version": version.get("houdini_version") or "-",
            "fps": (
                str(version.get("fps"))
                if version.get("fps") is not None
                else "-"
            ),
            "frame_range": (
                "%s - %s" % (frame_range[0], frame_range[-1])
                if len(frame_range) >= 2
                else "-"
            ),
            "reference_count": str(version.get("reference_count", 0)),
            "package_input_count": str(
                version.get("package_input_count", 0)
            ),
            "copy_job_count": str(version.get("copy_job_count", 0)),
            "skipped_cache_count": str(
                version.get("skipped_cache_count", 0)
            ),
            "skipped_missing_count": str(
                version.get("skipped_missing_count", 0)
            ),
            "hda_count": str(version.get("hda_count", 0)),
            "file_count": str(version.get("file_count", 0)),
            "size": format_bytes(version.get("total_bytes")),
        }
        for key, label in self.detail_values.items():
            label.setText(detail_data.get(key, "-"))
        self.detail_archive_path.setText(
            version.get("packaged_scene", "")
        )
        self.detail_source_path.setText(version.get("source_scene", ""))
        references = list(version.get("references", []))
        for hda in version.get("external_hdas", []):
            references.append(
                {
                    "node_path": ", ".join(hda.get("node_types", [])),
                    "parameter": "HDA Library",
                    "original_value": hda.get("source", ""),
                    "packaged_path": hda.get("archive_path", ""),
                    "classification": "External HDA",
                    "status": (
                        "Manual activation"
                        if hda.get("activation") == "manual"
                        else hda.get("result", "")
                    ),
                }
            )
        self.mapping_table.setRowCount(len(references))
        for row, reference in enumerate(references):
            values = [
                reference.get("node_path")
                or reference.get("node_name", ""),
                reference.get("parameter", ""),
                reference.get("original_value")
                or reference.get("original_path", ""),
                reference.get("packaged_path", ""),
                reference.get("classification", ""),
                reference.get("status", ""),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setToolTip(str(value))
                self.mapping_table.setItem(row, column, item)

    def open_selected_scene(self):
        version = self.selected_version()
        if not version:
            return
        path = version.get("packaged_scene", "")
        if path and os.path.isfile(path):
            opener = getattr(self.core, "openFile", None)
            if callable(opener):
                opener(path)
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
                "Incomplete Archive versions cannot be deleted while they "
                "may still be packaging.",
                "warning",
            )
            return
        version_path = version.get("path", "")
        archive_root = os.path.dirname(version_path)
        application = version.get("application", "").capitalize()
        message = (
            "Permanently delete %s Archive %s?\n\n%s\n\n"
            "The archived scene, manifest and packaged dependencies will "
            "be removed. This cannot be undone."
            % (application, version.get("version", ""), version_path)
        )
        popup_question = getattr(self.core, "popupQuestion", None)
        if callable(popup_question):
            answer = popup_question(
                message,
                title="Delete Archive",
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
                "Delete Archive",
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
            self._show_popup(str(exc), "error")
            return
        self._show_popup(
            "Deleted Archive %s:\n%s"
            % (
                version.get("version") or result["version"],
                result["deleted_path"],
            ),
            "info",
        )
        self.refresh_versions()

    def _show_popup(self, message, severity):
        popup = getattr(self.core, "popup", None)
        if callable(popup):
            popup(message, severity=severity)
        elif severity in ("warning", "error"):
            QMessageBox.warning(self, "Archive", message)
        else:
            QMessageBox.information(self, "Archive", message)

    def _show_context_menu(self, position):
        index = self.table.indexAt(position)
        if index.isValid():
            self.table.selectRow(index.row())
        version = self.selected_version()
        if not version:
            return
        menu = QMenu(self)
        open_scene = menu.addAction("Open Archive Scene")
        open_scene.setEnabled(
            os.path.isfile(version.get("packaged_scene", ""))
        )
        open_scene.triggered.connect(
            lambda checked=False: self.open_selected_scene()
        )
        open_folder = menu.addAction("Open Archive Folder")
        open_folder.triggered.connect(
            lambda checked=False: self.open_selected_folder()
        )
        menu.addSeparator()
        delete_action = menu.addAction("Delete Archive...")
        delete_action.setEnabled(version.get("status") != "Incomplete")
        delete_action.triggered.connect(
            lambda checked=False, archive=version: self.delete_archive(
                archive
            )
        )
        menu.exec_(self.table.viewport().mapToGlobal(position))


def _archive_group_key(version):
    task = str(version.get("task", ""))
    fallback = ""
    if not task:
        source_name = os.path.basename(version.get("source_scene", ""))
        if not source_name:
            source_name = os.path.basename(
                version.get("packaged_scene", "")
            )
        fallback = os.path.splitext(source_name)[0]
        fallback = re.sub(
            r"_archive_v\d+$", "", fallback, flags=re.IGNORECASE
        )
        fallback = re.sub(
            r"_v\d+$", "", fallback, flags=re.IGNORECASE
        )
    return (
        str(version.get("application", "")).casefold(),
        task.casefold(),
        fallback.casefold(),
    )
