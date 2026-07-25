import os

from qtpy.QtCore import Qt
from qtpy.QtGui import *
from qtpy.QtWidgets import *


class BatchImportDialog(QDialog):
    def __init__(self, core, server_root, create_callback, parent=None):
        super().__init__(parent)
        self.core = core
        self.server_root = server_root
        self.create_callback = create_callback
        self.scan_results = []

        self.setWindowTitle("Batch Import from Server")
        self.setMinimumSize(780, 580)
        self.resize(820, 620)

        if parent:
            self.core.parentWindow(self, parent)

        self._build_ui()
        self._populate_server_projects()
        self._connect_signals()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)

        server_group = QGroupBox("Server")
        server_layout = QHBoxLayout(server_group)
        server_layout.addWidget(QLabel("Server Root:"))
        self.server_root_edit = QLineEdit(self.server_root)
        server_layout.addWidget(self.server_root_edit)
        browse_btn = QPushButton("...")
        browse_btn.setFixedWidth(30)
        browse_btn.clicked.connect(self._browse_server_root)
        server_layout.addWidget(browse_btn)
        server_layout.addWidget(QLabel("   Project:"))
        self.project_combo = QComboBox()
        self.project_combo.setMinimumWidth(120)
        server_layout.addWidget(self.project_combo)
        server_layout.addStretch()
        main_layout.addWidget(server_group)

        local_group = QGroupBox("Local Prism Project")
        local_layout = QHBoxLayout(local_group)
        local_layout.addWidget(QLabel("Create at:"))
        local_default = self._get_local_default()
        self.local_path_edit = QLineEdit(local_default)
        local_layout.addWidget(self.local_path_edit)
        browse_local_btn = QPushButton("...")
        browse_local_btn.setFixedWidth(30)
        browse_local_btn.clicked.connect(self._browse_local_path)
        local_layout.addWidget(browse_local_btn)
        local_layout.addSpacing(20)
        self.local_name_label = QLabel("")
        local_layout.addWidget(self.local_name_label)
        local_layout.addStretch()
        main_layout.addWidget(local_group)

        filter_group = QGroupBox("Filter (episode/sequence/shot, one per line)")
        filter_layout = QVBoxLayout(filter_group)
        self.filter_edit = QPlainTextEdit()
        self.filter_edit.setPlaceholderText(
            "PV001/SC01/shot021\nQ2EP007/SC01/shot001"
        )
        self.filter_edit.setMaximumHeight(80)
        filter_layout.addWidget(self.filter_edit)

        btn_layout = QHBoxLayout()
        self.search_btn = QPushButton("Search Server")
        btn_layout.addStretch()
        btn_layout.addWidget(self.search_btn)
        filter_layout.addLayout(btn_layout)
        main_layout.addWidget(filter_group)

        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout(results_group)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["", "Shot Path", "Steps", "Status"])
        self.tree.setColumnWidth(0, 30)
        self.tree.setColumnWidth(1, 280)
        self.tree.setColumnWidth(2, 140)
        self.tree.setColumnWidth(3, 100)
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        results_layout.addWidget(self.tree)

        select_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(lambda: self._set_all_checked(Qt.Checked))
        select_layout.addWidget(select_all_btn)
        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(lambda: self._set_all_checked(Qt.Unchecked))
        select_layout.addWidget(deselect_all_btn)
        select_layout.addStretch()
        results_layout.addLayout(select_layout)
        main_layout.addWidget(results_group)

        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        self.create_btn = QPushButton("Create Prism Project && Shots")
        self.create_btn.setMinimumWidth(200)
        bottom_layout.addWidget(self.create_btn)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        bottom_layout.addWidget(close_btn)
        main_layout.addLayout(bottom_layout)

    def _connect_signals(self):
        self.search_btn.clicked.connect(self.on_search)
        self.create_btn.clicked.connect(self._on_create_clicked)
        self.project_combo.currentTextChanged.connect(self._on_project_changed)
        self.local_path_edit.textChanged.connect(self._on_project_changed)
        self.local_path_edit.editingFinished.connect(self._on_local_root_changed)
        self.server_root_edit.editingFinished.connect(self._on_server_root_changed)

    def _on_server_root_changed(self):
        path = self.server_root_edit.text().strip()
        if path:
            self._save_config_value("server_root", path)
        self._populate_server_projects()

    def _populate_server_projects(self):
        self.project_combo.clear()
        server_root = self.server_root_edit.text().strip()
        if not os.path.isdir(server_root):
            return

        try:
            entries = sorted(os.listdir(server_root))
        except OSError:
            return

        for e in entries:
            full = os.path.join(server_root, e)
            if os.path.isdir(full) and not e.startswith("."):
                if os.path.isdir(os.path.join(full, "publish", "shot")):
                    self.project_combo.addItem(e)

    def _on_project_changed(self, _text=None):
        proj = self.project_combo.currentText().strip()
        base = self.local_path_edit.text().strip()
        if proj and base:
            self.local_name_label.setText(
                "-> %s/%s" % (base.rstrip("/"), proj)
            )
        else:
            self.local_name_label.setText("")

    def _browse_server_root(self):
        path = QFileDialog.getExistingDirectory(
            self, "Select Server Root", self.server_root_edit.text()
        )
        if path:
            self.server_root_edit.setText(path)
            self._save_config_value("server_root", path)
            self._populate_server_projects()

    def _save_config_value(self, key, value):
        try:
            from change_prism.config import save_config_value
            save_config_value(key, value)
        except ImportError:
            pass

    def _on_local_root_changed(self):
        path = self.local_path_edit.text().strip()
        if path:
            self._save_config_value("local_projects_root", path)

    def _get_local_default(self):
        try:
            from change_prism.config import get_local_projects_root
            return get_local_projects_root()
        except ImportError:
            return os.path.expanduser("~/Desktop/Projects")

    def _browse_local_path(self):
        path = QFileDialog.getExistingDirectory(
            self, "Select Local Projects Directory", self.local_path_edit.text()
        )
        if path:
            self.local_path_edit.setText(path)
            self._save_config_value("local_projects_root", path)

    def on_search(self):
        from change_prism.batch_import.scanner import (
            parse_filter_strings,
            scan_server_shots,
            clear_list_dirs_cache,
        )

        clear_list_dirs_cache()

        filter_text = self.filter_edit.toPlainText().strip()
        if not filter_text:
            self.core.popup("Please enter at least one filter string.")
            return

        filter_strs = parse_filter_strings(filter_text)
        if not filter_strs:
            self.core.popup("No valid filter strings found.")
            return

        server_root = self.server_root_edit.text().strip()
        if not os.path.isdir(server_root):
            self.core.popup("Server root directory not found:\n%s" % server_root)
            return

        project_code = self.project_combo.currentText().strip()
        if not project_code:
            self.core.popup("Please select a server project first.")
            return

        self.scan_results = scan_server_shots(
            server_root, filter_strs, project_code=project_code
        )

        if not self.scan_results:
            self.core.popup(
                "No matching shots found.\n\n"
                "Server: %s\nProject: %s\nSearched: %s\n\n"
                "Check that the paths are correct."
                % (server_root, project_code, ", ".join(filter_strs)),
                severity="info",
            )
        self._populate_results()

    def _populate_results(self):
        self.tree.clear()
        if not self.scan_results:
            return

        self.tree.setUpdatesEnabled(False)
        for shot_data in self.scan_results:
            ep = shot_data.get("episode", "")
            seq = shot_data.get("sequence", "")
            sh = shot_data.get("shot", "")

            steps = shot_data.get("steps", [])
            step_labels = [s.get("label", "") for s in steps]
            mov_count = sum(len(s.get("files", {}).get("mov_files", [])) for s in steps)
            mov_str = "%d mov" % mov_count if mov_count > 0 else "no mov"

            item = QTreeWidgetItem()
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Checked)
            item.setData(0, Qt.UserRole, shot_data)
            item.setText(1, "%s/%s/%s" % (ep, seq, sh))
            item.setText(2, ", ".join(step_labels) if step_labels else "-")
            item.setText(3, mov_str)
            self.tree.addTopLevelItem(item)
        self.tree.setUpdatesEnabled(True)

    def _set_all_checked(self, state):
        for i in range(self.tree.topLevelItemCount()):
            self.tree.topLevelItem(i).setCheckState(0, state)

    def _on_create_clicked(self):
        selected = []
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.checkState(0) != Qt.Checked:
                continue
            data = item.data(0, Qt.UserRole)
            if data is not None:
                selected.append(data)

        if not selected:
            self.core.popup("No shots selected.")
            return

        project_name = self.project_combo.currentText().strip()
        if not project_name:
            self.core.popup("Please select a server project first.")
            return

        local_base = self.local_path_edit.text().strip()
        if not local_base:
            self.core.popup("Please select a local projects directory.")
            return

        project_path = os.path.join(local_base, project_name)

        self.core.popup(
            "Starting to create project:\n\n%s\n\n%d shots selected."
            % (project_path, len(selected)),
            severity="info",
        )

        self.create_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(selected))
        self.progress_bar.setValue(0)
        QApplication.processEvents()

        self.create_callback(dict(
            project_name=project_name,
            project_path=project_path,
            selected=selected,
            dlg=self,
        ))

    def set_status(self, text):
        self.status_label.setText(text)
        QApplication.processEvents()

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        self.status_label.setText(
            "Creating shots... %d/%d" % (value, self.progress_bar.maximum())
        )
        QApplication.processEvents()

    def on_create_finished(self, success_count, fail_count, failures=None):
        self.create_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("")
        msg = "Done.\n\nCreated: %d\nFailed: %d" % (success_count, fail_count)
        if failures:
            msg += "\n\nFailures:\n" + "\n".join(failures[:20])
            if len(failures) > 20:
                msg += "\n... and %d more" % (len(failures) - 20)
        self.core.popup(msg, severity="info")
