import os

from qtpy.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class PluginSettingsWidget(QWidget):
    def __init__(self, core, project_key, parent=None):
        super().__init__(parent)
        self.core = core
        self.project_key = project_key
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        heading = QLabel("chAngE_Prism Paths")
        heading.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(heading)

        description = QLabel(
            "These paths are stored in Prism's user settings for this workstation."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        form = QFormLayout()
        self.server_root_edit = QLineEdit()
        form.addRow(
            "Server Publish Root:",
            self._path_row(self.server_root_edit, self._browse_server_root),
        )

        self.local_projects_root_edit = QLineEdit()
        form.addRow(
            "Local Projects Root:",
            self._path_row(
                self.local_projects_root_edit,
                self._browse_local_projects_root,
            ),
        )

        self.review_destination_edit = QLineEdit()
        form.addRow(
            "Daily Review Destination:",
            self._path_row(
                self.review_destination_edit,
                self._browse_review_destination,
            ),
        )

        pdg_heading = QLabel("Batch Import / PDG")
        pdg_heading.setStyleSheet(
            "font-size: 14px; font-weight: bold; margin-top: 12px;"
        )
        form.addRow(pdg_heading)

        self.hython_edit = QLineEdit()
        self.hython_edit.setReadOnly(True)
        self.hython_edit.setPlaceholderText(
            "Set Prism User Settings > Apps > Houdini executable override"
        )
        self.hython_edit.setToolTip(
            "Automatically derived from Prism's selected Houdini executable."
        )
        form.addRow("Hython (from Prism):", self.hython_edit)

        self.pdg_hip_edit = QLineEdit()
        form.addRow(
            "PDG Template HIP:",
            self._path_row(self.pdg_hip_edit, self._browse_pdg_hip),
        )

        self.houdini_package_edit = QLineEdit()
        self.houdini_package_edit.setPlaceholderText(
            "Folder containing Houdini package JSON files"
        )
        form.addRow(
            "Houdini Package Directory:",
            self._path_row(
                self.houdini_package_edit,
                self._browse_houdini_package_directory,
            ),
        )

        ocio_heading = QLabel("Media / OCIO")
        ocio_heading.setStyleSheet(
            "font-size: 14px; font-weight: bold; margin-top: 12px;"
        )
        form.addRow(ocio_heading)

        self.ocio_config_edit = QLineEdit()
        self.ocio_config_edit.setPlaceholderText(
            "Empty: use OCIO environment, then ocio://default"
        )
        form.addRow(
            "Current Project OCIO:",
            self._path_row(self.ocio_config_edit, self._browse_ocio_config),
        )
        layout.addLayout(form)

        project_label = QLabel("OCIO project key: %s" % self.project_key)
        project_label.setWordWrap(True)
        project_label.setStyleSheet("color: #999;")
        layout.addWidget(project_label)
        layout.addStretch()

    def _path_row(self, line_edit, callback):
        widget = QWidget(self)
        row = QHBoxLayout(widget)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(line_edit)
        button = QPushButton("...")
        button.setFixedWidth(32)
        button.clicked.connect(callback)
        row.addWidget(button)
        return widget

    def _browse_directory(self, line_edit, title):
        path = QFileDialog.getExistingDirectory(
            self,
            title,
            line_edit.text().strip(),
        )
        if path:
            line_edit.setText(os.path.normpath(path))

    def _browse_server_root(self):
        self._browse_directory(self.server_root_edit, "Select Server Publish Root")

    def _browse_local_projects_root(self):
        self._browse_directory(
            self.local_projects_root_edit,
            "Select Local Projects Root",
        )

    def _browse_review_destination(self):
        self._browse_directory(
            self.review_destination_edit,
            "Select Daily Review Destination",
        )

    def _browse_pdg_hip(self):
        current = self.pdg_hip_edit.text().strip()
        start = current if os.path.isfile(current) else os.path.dirname(current)
        path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Select PDG Template HIP",
            start,
            "Houdini Scene (*.hip *.hiplc *.hipnc);;All Files (*)",
        )
        if path:
            self.pdg_hip_edit.setText(os.path.normpath(path))

    def _browse_houdini_package_directory(self):
        self._browse_directory(
            self.houdini_package_edit,
            "Select Houdini Package Directory",
        )

    def _browse_ocio_config(self):
        current = self.ocio_config_edit.text().strip()
        start = current if os.path.isfile(current) else os.path.dirname(current)
        path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Select OCIO Config",
            start,
            "OCIO Config (*.ocio);;All Files (*)",
        )
        if path:
            self.ocio_config_edit.setText(os.path.normpath(path))

    def set_values(
        self,
        server_root,
        local_projects_root,
        review_destination,
        hython_path,
        pdg_hip_path,
        houdini_package_directory,
        ocio_project_override,
    ):
        self.server_root_edit.setText(server_root)
        self.local_projects_root_edit.setText(local_projects_root)
        self.review_destination_edit.setText(review_destination)
        self.hython_edit.setText(hython_path)
        self.pdg_hip_edit.setText(pdg_hip_path)
        self.houdini_package_edit.setText(houdini_package_directory)
        self.ocio_config_edit.setText(ocio_project_override)

    def values(self):
        return {
            "server_root": self.server_root_edit.text().strip(),
            "local_projects_root": self.local_projects_root_edit.text().strip(),
            "review_copy_destination_root": (
                self.review_destination_edit.text().strip()
            ),
            "pdg_hip_path": self.pdg_hip_edit.text().strip(),
            "houdini_package_directory": (
                self.houdini_package_edit.text().strip()
            ),
            "ocio_project_override": self.ocio_config_edit.text().strip(),
        }
