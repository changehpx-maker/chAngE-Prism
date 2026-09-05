import os
import queue
import threading

from qtpy.QtCore import QObject, Qt, QThread, QTimer, Signal, Slot
from qtpy.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


def _scan_project_names(server_root, results):
    from change_prism.batch_import.scanner import list_server_projects

    try:
        results.put((list_server_projects(server_root), ""))
    except OSError as exc:
        results.put(([], str(exc)))


class _SearchWorker(QThread):
    finished_signal = Signal(object, object)
    error_signal = Signal(str)

    def __init__(
        self, server_root, filter_strings, project_code, parent=None
    ):
        super().__init__(parent)
        self.server_root = server_root
        self.filter_strings = filter_strings
        self.project_code = project_code

    def run(self):
        warnings = []
        try:
            from change_prism.batch_import.scanner import (
                clear_list_dirs_cache,
                scan_server_shots,
            )

            clear_list_dirs_cache()
            results = scan_server_shots(
                self.server_root,
                self.filter_strings,
                project_code=self.project_code,
                warnings=warnings,
            )
            self.finished_signal.emit(results, warnings)
        except Exception as exc:
            self.error_signal.emit(str(exc))


class BatchFileWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, processor, mode, payload):
        super(BatchFileWorker, self).__init__()
        self.processor = processor
        self.mode = mode
        self.payload = payload

    @Slot()
    def run(self):
        try:
            if self.mode == "product":
                result = self.processor.build_product_data(
                    self.payload
                )
            else:
                self.processor.execute_review_copies(self.payload)
                result = None
        except Exception as exc:
            self.failed.emit(str(exc))
        else:
            self.finished.emit(result)


class BatchFileUiBridge(QObject):
    def __init__(
        self,
        parent,
        on_finished,
        on_failed,
        on_thread_finished,
    ):
        super(BatchFileUiBridge, self).__init__(parent)
        self._on_finished = on_finished
        self._on_failed = on_failed
        self._on_thread_finished = on_thread_finished

    @Slot(object)
    def work_finished(self, result):
        self._on_finished(result)

    @Slot(str)
    def work_failed(self, message):
        self._on_failed(message)

    @Slot()
    def thread_finished(self):
        self._on_thread_finished()


class BatchImportDialog(QDialog):
    def __init__(
        self,
        core,
        server_root,
        create_callback,
        finish_callback=None,
        parent=None,
    ):
        super().__init__(parent)
        self.core = core
        self.server_root = server_root
        self.create_callback = create_callback
        self.finish_callback = finish_callback
        self.scan_results = []
        self._search_worker = None
        self._import_running = False
        self._project_results = None
        self._project_timer = QTimer(self)
        self._project_timer.setInterval(50)
        self._project_timer.timeout.connect(self._receive_server_projects)

        self.setWindowTitle("Batch Import from Server")
        self.setMinimumSize(1050, 620)
        self.resize(1180, 680)
        if parent:
            self.core.parentWindow(self, parent)

        self._build_ui()
        self._populate_server_projects()
        self._connect_signals()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)
        main_layout.addWidget(self._build_paths_panel())

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_filter_panel())
        splitter.addWidget(self._build_results_panel())
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([420, 720])
        main_layout.addWidget(splitter, 1)

        self.status_label = QLabel("")
        self.status_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )
        main_layout.addWidget(self.status_label)

        bottom = QHBoxLayout()
        bottom.addStretch()
        self.pdg_cb = QCheckBox("Run PDG FBX Convert")
        bottom.addWidget(self.pdg_cb)
        self.create_btn = QPushButton(
            "Create Prism Project && Import Shots"
        )
        self.create_btn.setDefault(True)
        self.create_btn.setMinimumWidth(240)
        bottom.addWidget(self.create_btn)
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.reject)
        bottom.addWidget(self.close_btn)
        main_layout.addLayout(bottom)

    def _build_paths_panel(self):
        group = QGroupBox("Paths")
        layout = QGridLayout(group)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(4, 1)

        layout.addWidget(QLabel("Server Root"), 0, 0)
        self.server_root_edit = QLineEdit(self.server_root)
        self.server_root_edit.setToolTip(self.server_root)
        self.server_root_edit.setCursorPosition(0)
        layout.addWidget(self.server_root_edit, 0, 1, 1, 3)
        browse_server = QPushButton("Browse...")
        browse_server.setFixedWidth(88)
        browse_server.clicked.connect(self._browse_server_root)
        layout.addWidget(browse_server, 0, 4)

        layout.addWidget(QLabel("Project"), 1, 0)
        self.project_combo = QComboBox()
        layout.addWidget(self.project_combo, 1, 1)

        layout.addWidget(QLabel("Projects Root"), 2, 0)
        self.local_path_edit = QLineEdit(self._get_local_default())
        self.local_path_edit.setToolTip(self.local_path_edit.text())
        self.local_path_edit.setCursorPosition(0)
        layout.addWidget(self.local_path_edit, 2, 1, 1, 3)
        browse_local = QPushButton("Browse...")
        browse_local.setFixedWidth(88)
        browse_local.clicked.connect(self._browse_local_path)
        layout.addWidget(browse_local, 2, 4)

        layout.addWidget(QLabel("Create Path"), 3, 0)
        self.local_name_label = QLabel("")
        self.local_name_label.setWordWrap(True)
        self.local_name_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )
        layout.addWidget(self.local_name_label, 3, 1, 1, 4)
        return group

    def _build_filter_panel(self):
        panel = QWidget()
        panel.setMinimumWidth(360)
        layout = QVBoxLayout(panel)

        header = QHBoxLayout()
        header.addWidget(QLabel("Shot Filter"))
        header.addStretch()
        self.search_btn = QPushButton("Search Server")
        header.addWidget(self.search_btn)
        layout.addLayout(header)

        self.filter_edit = QPlainTextEdit()
        self.filter_edit.setPlaceholderText(
            "Full path, one per line:\n"
            "PV001/SC01/shot021\n"
            "Q2EP007/SC01/shot001\n\n"
            "Or 3 lines per shot:\n"
            "Q2EP014/\n"
            "SC02/\n"
            "shot014a"
        )
        self.filter_edit.setMinimumHeight(150)
        layout.addWidget(self.filter_edit, 1)

        mode_group = QGroupBox("Mode")
        mode_layout = QHBoxLayout(mode_group)
        self.create_only_cb = QCheckBox("Create shot only")
        mode_layout.addWidget(self.create_only_cb)
        self.copy_to_local_cb = QCheckBox("Copy to local")
        mode_layout.addWidget(self.copy_to_local_cb)
        mode_layout.addStretch()
        layout.addWidget(mode_group)
        return panel

    def _build_results_panel(self):
        panel = QWidget()
        panel.setMinimumWidth(520)
        layout = QVBoxLayout(panel)

        header = QHBoxLayout()
        header.addWidget(QLabel("Results"))
        header.addStretch()
        self.result_count_label = QLabel("0 shots")
        self.result_count_label.setStyleSheet("color: #888;")
        header.addWidget(self.result_count_label)
        select_all = QPushButton("Select All")
        select_all.clicked.connect(
            lambda: self._set_all_checked(Qt.Checked)
        )
        header.addWidget(select_all)
        deselect_all = QPushButton("Deselect All")
        deselect_all.clicked.connect(
            lambda: self._set_all_checked(Qt.Unchecked)
        )
        header.addWidget(deselect_all)
        layout.addLayout(header)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(
            ["", "Shot Path", "Steps", "Status"]
        )
        self.tree.setColumnWidth(0, 30)
        self.tree.setColumnWidth(1, 230)
        self.tree.setColumnWidth(2, 150)
        self.tree.setColumnWidth(3, 80)
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(
            QAbstractItemView.ExtendedSelection
        )
        layout.addWidget(self.tree, 1)
        return panel

    def _connect_signals(self):
        self.search_btn.clicked.connect(self.on_search)
        self.create_btn.clicked.connect(self._on_create_clicked)
        self.project_combo.currentTextChanged.connect(
            self._on_project_changed
        )
        self.local_path_edit.textChanged.connect(
            self._on_project_changed
        )
        self.local_path_edit.editingFinished.connect(
            self._on_local_root_changed
        )
        self.server_root_edit.editingFinished.connect(
            self._on_server_root_changed
        )
        self.create_only_cb.toggled.connect(
            self._on_create_only_toggled
        )

    def _on_create_only_toggled(self, checked):
        if checked:
            self.copy_to_local_cb.setChecked(False)
            self.pdg_cb.setChecked(False)
        self.copy_to_local_cb.setEnabled(not checked)
        self.pdg_cb.setEnabled(not checked)

    def _on_server_root_changed(self):
        path = self.server_root_edit.text().strip()
        if path:
            self._save_config_value("server_root", path)
            self.server_root_edit.setToolTip(path)
            self.server_root_edit.setCursorPosition(0)
        # editingFinished also fires on plain focus loss; rebuilding the
        # project combo then would reset the user's selection.
        if path != getattr(self, "_populated_server_root", None):
            self._populate_server_projects()

    def _populate_server_projects(self):
        server_root = self.server_root_edit.text().strip()
        self._populated_server_root = server_root
        self.project_combo.clear()
        self.project_combo.setToolTip("Loading server projects...")
        # Each scan owns a queue, so a previous root cannot replace new results.
        self._project_results = queue.Queue()
        threading.Thread(
            target=_scan_project_names,
            args=(server_root, self._project_results),
            daemon=True,
        ).start()
        self._project_timer.start()

    def _receive_server_projects(self):
        try:
            projects, error = self._project_results.get_nowait()
        except queue.Empty:
            return
        self._project_timer.stop()
        self.project_combo.addItems(projects)
        self.project_combo.setToolTip(
            "Could not list server projects: %s" % error if error else ""
        )

    def _on_project_changed(self, _text=None):
        project = self.project_combo.currentText().strip()
        base = self.local_path_edit.text().strip()
        self.local_name_label.setText(
            "-> %s" % os.path.join(base, project)
            if project and base
            else ""
        )

    def _browse_server_root(self):
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Server Root",
            self.server_root_edit.text(),
        )
        if path:
            self.server_root_edit.setText(path)
            self._on_server_root_changed()

    def _browse_local_path(self):
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Local Projects Directory",
            self.local_path_edit.text(),
        )
        if path:
            self.local_path_edit.setText(path)
            self._on_local_root_changed()

    def _save_config_value(self, key, value):
        try:
            from change_prism.config import save_config_value

            save_config_value(self.core, key, value)
        except (AttributeError, ImportError):
            pass

    def _on_local_root_changed(self):
        path = self.local_path_edit.text().strip()
        if path:
            self._save_config_value("local_projects_root", path)
            self.local_path_edit.setToolTip(path)
            self.local_path_edit.setCursorPosition(0)

    def _get_local_default(self):
        try:
            from change_prism.config import get_local_projects_root

            return get_local_projects_root(self.core)
        except ImportError:
            return os.path.expanduser("~/Desktop/Projects")

    def on_search(self):
        from change_prism.batch_import.scanner import (
            parse_filter_strings,
        )

        filters = parse_filter_strings(
            self.filter_edit.toPlainText().strip()
        )
        if not filters:
            self.core.popup(
                "Please enter at least one valid shot filter."
            )
            return
        server_root = self.server_root_edit.text().strip()
        if not os.path.isdir(server_root):
            self.core.popup(
                "Server root directory not found:\n%s" % server_root
            )
            return
        project = self.project_combo.currentText().strip()
        if not project:
            self.core.popup(
                "Please select a server project first."
            )
            return

        self._set_busy(True, "Searching server...")
        self._search_worker = _SearchWorker(
            server_root, filters, project, self
        )
        self._search_worker.finished_signal.connect(
            lambda results, warnings: self._on_search_finished(
                results, warnings, server_root, project, filters
            )
        )
        self._search_worker.error_signal.connect(
            self._on_search_error
        )
        self._search_worker.finished.connect(
            self._clear_search_worker
        )
        self._search_worker.start()

    def _on_search_finished(
        self, results, warnings, server_root, project, filters
    ):
        self.scan_results = results
        if not results:
            self.core.popup(
                "No matching shots found.\n\n"
                "Server: %s\nProject: %s\nSearched: %s"
                % (server_root, project, ", ".join(filters)),
                severity="info",
            )
        if warnings:
            shown = warnings[:20]
            message = (
                "Some server directories could not be read and were "
                "skipped:\n\n%s" % "\n".join(shown)
            )
            if len(warnings) > len(shown):
                message += "\n... and %d more" % (len(warnings) - len(shown))
            self.core.popup(message, severity="warning")
        self._populate_results()
        self._set_busy(False, "")

    def _on_search_error(self, message):
        self._set_busy(False, "")
        self.core.popup(
            "Search failed:\n\n%s" % message, severity="error"
        )

    def _clear_search_worker(self):
        worker = self._search_worker
        self._search_worker = None
        if worker is not None:
            worker.deleteLater()

    def _populate_results(self):
        self.tree.clear()
        self.result_count_label.setText(
            "%d shots" % len(self.scan_results)
        )
        self.tree.setUpdatesEnabled(False)
        for shot_data in self.scan_results:
            steps = shot_data.get("steps", [])
            mov_count = sum(
                len(step.get("files", {}).get("mov_files", []))
                for step in steps
            )
            item = QTreeWidgetItem()
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Checked)
            item.setData(0, Qt.UserRole, shot_data)
            item.setText(
                1,
                "%s/%s/%s"
                % (
                    shot_data.get("episode", ""),
                    shot_data.get("sequence", ""),
                    shot_data.get("shot", ""),
                ),
            )
            item.setText(
                2,
                ", ".join(
                    step.get("label", "") for step in steps
                )
                or "-",
            )
            item.setText(
                3, "%d mov" % mov_count if mov_count else "no mov"
            )
            self.tree.addTopLevelItem(item)
        self.tree.setUpdatesEnabled(True)

    def _set_all_checked(self, state):
        for index in range(self.tree.topLevelItemCount()):
            self.tree.topLevelItem(index).setCheckState(0, state)

    def _on_create_clicked(self):
        selected = []
        for index in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(index)
            if item.checkState(0) == Qt.Checked:
                data = item.data(0, Qt.UserRole)
                if data is not None:
                    selected.append(data)
        if not selected:
            self.core.popup("No shots selected.")
            return

        project = self.project_combo.currentText().strip()
        local_root = self.local_path_edit.text().strip()
        if not project or not local_root:
            self.core.popup(
                "Please select a server project and local projects root."
            )
            return

        data = {
            "project_name": project,
            "project_path": os.path.join(local_root, project),
            "selected": selected,
            "parent": self,
            "create_only": self.create_only_cb.isChecked(),
            "copy_to_local": self.copy_to_local_cb.isChecked(),
            "pdg_enabled": self.pdg_cb.isChecked(),
            "_reporter": self,
            "_finished_callback": self._on_import_finished,
        }
        self._import_running = True
        self._set_busy(True, "Importing shots...")
        try:
            result = self.create_callback(data)
        except Exception as exc:
            self._on_import_error(str(exc))
            return
        if result is not None:
            self._on_import_finished(result)

    def _on_import_finished(self, result):
        self._import_running = False
        if self.finish_callback:
            self.finish_callback(self, result)
        else:
            self.on_create_finished(
                result.get("success", 0),
                result.get("fail", 0),
                result.get("failures", []),
                result.get("summary", {}),
            )

    def _on_import_error(self, message):
        self._import_running = False
        self._set_busy(False, "")
        self.core.popup(
            "Import failed:\n\n%s" % message, severity="error"
        )

    def set_status(self, text):
        self.status_label.setText(text)

    def update_progress(self, value):
        self.status_label.setText("Importing shot %d..." % value)

    def _set_busy(self, busy, status_text):
        self.search_btn.setEnabled(not busy)
        self.create_btn.setEnabled(not busy)
        self.close_btn.setEnabled(not busy)
        self.status_label.setText(status_text)

    def reject(self):
        if self._search_worker is not None:
            self.core.popup(
                "Server search is still running. Please wait."
            )
            return
        if self._import_running:
            self.core.popup(
                "Shot import is still running. Please wait."
            )
            return
        self._project_timer.stop()
        super().reject()

    def on_create_finished(
        self,
        success_count,
        fail_count,
        failures=None,
        summary=None,
    ):
        summary = summary or {}
        pdg_status = (
            "PDG FBX Convert is running in the background. "
            "You will be notified when it finishes."
            if summary.get("pdg_started")
            else ""
        )
        self._set_busy(False, pdg_status)
        lines = [
            "Import Complete",
            "",
            "Project: %s" % summary.get("project", ""),
            "Shots: %d total | %d succeeded | %d failed"
            % (
                summary.get("total", success_count + fail_count),
                success_count,
                fail_count,
            ),
        ]
        modes = []
        if summary.get("create_only"):
            modes.append("Create Only")
        else:
            modes.append(
                "Copy to Local"
                if summary.get("copy_to_local")
                else "Reference Server Files"
            )
            if summary.get("pdg_enabled"):
                modes.append("PDG FBX Convert")
        if modes:
            lines.append("Mode: %s" % " + ".join(modes))
        if summary.get("pdg_started"):
            lines.append(
                "PDG: Running in the background. "
                "A completion notification will appear."
            )
        if summary.get("failure_report"):
            lines.append(
                "Report: %s" % summary["failure_report"]
            )
        if failures:
            lines.append("")
            lines.append("Failures:")
            lines.extend(
                self._format_failure(failure)
                for failure in failures[:20]
            )
            if len(failures) > 20:
                lines.append(
                    "... and %d more" % (len(failures) - 20)
                )
        self.core.popup("\n".join(lines), severity="info")

    @staticmethod
    def _format_failure(failure):
        if isinstance(failure, dict):
            return "%s/%s/%s: %s" % (
                failure.get("episode", ""),
                failure.get("sequence", ""),
                failure.get("shot", ""),
                failure.get("error", ""),
            )
        return str(failure)
