import os
import shutil
import subprocess

from qtpy.QtCore import (
    QProcess,
    QTemporaryDir,
    QThread,
    QTimer,
    Qt,
    Signal,
)
from qtpy.QtGui import QPixmap
from qtpy.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from change_prism.config import (
    get_project_config_key,
    load_config,
    save_ocio_project_override,
)
from change_prism.ocio.service import (
    build_ffmpeg_args,
    build_oiiotool_args,
    build_validation_args,
    choose_inventory_defaults,
    collect_exr_jobs,
    external_output_path,
    find_tools,
    inspect_exr,
    read_colorconfig_inventory,
    select_ocio_config,
    staging_output_path,
    validate_color_selection,
    validate_fps,
)


_ACTIVE_BACKGROUND_THREADS = set()
_TEMP_CLEANUP_PATHS = []
_TEMP_CLEANUP_THREAD = None


def _track_background_thread(thread):
    _ACTIVE_BACKGROUND_THREADS.add(thread)

    def release():
        _ACTIVE_BACKGROUND_THREADS.discard(thread)
        thread.deleteLater()

    thread.finished.connect(release)
    thread.start()


class InventoryThread(QThread):
    completed = Signal(object, int)
    failed = Signal(str, int)

    def __init__(self, oiiotool, config, generation):
        super(InventoryThread, self).__init__()
        self.oiiotool = oiiotool
        self.config = config
        self.generation = generation

    def run(self):
        try:
            inventory = read_colorconfig_inventory(
                self.oiiotool,
                self.config,
            )
        except Exception as exc:
            self.failed.emit(str(exc), self.generation)
        else:
            self.completed.emit(inventory, self.generation)


class ExrInspectThread(QThread):
    completed = Signal(object, int, str)
    failed = Signal(str, int, str)

    def __init__(self, oiiotool, paths, generation, mode):
        super(ExrInspectThread, self).__init__()
        self.oiiotool = oiiotool
        self.paths = list(paths)
        self.generation = generation
        self.mode = mode

    def run(self):
        try:
            results = []
            for path in self.paths:
                try:
                    results.append(
                        {"info": inspect_exr(self.oiiotool, path)}
                    )
                except Exception as exc:
                    results.append({"error": str(exc)})
        except Exception as exc:
            self.failed.emit(str(exc), self.generation, self.mode)
        else:
            self.completed.emit(
                results,
                self.generation,
                self.mode,
            )


class TempCleanupThread(QThread):
    def __init__(self, path):
        super(TempCleanupThread, self).__init__()
        self.path = path

    def run(self):
        shutil.rmtree(self.path, ignore_errors=True)


def _start_next_temp_cleanup():
    global _TEMP_CLEANUP_THREAD
    if _TEMP_CLEANUP_THREAD is not None or not _TEMP_CLEANUP_PATHS:
        return
    thread = TempCleanupThread(_TEMP_CLEANUP_PATHS.pop(0))
    _TEMP_CLEANUP_THREAD = thread
    _ACTIVE_BACKGROUND_THREADS.add(thread)

    def release():
        global _TEMP_CLEANUP_THREAD
        _ACTIVE_BACKGROUND_THREADS.discard(thread)
        _TEMP_CLEANUP_THREAD = None
        thread.deleteLater()
        _start_next_temp_cleanup()

    thread.finished.connect(release)
    thread.start()


def _queue_temp_cleanup(path):
    if not path:
        return
    _TEMP_CLEANUP_PATHS.append(path)
    _start_next_temp_cleanup()


class OCIOConvertDialog(QDialog):
    inventoryLoaded = Signal(bool)
    conversionFinished = Signal(object)

    def __init__(
        self,
        core,
        initial_paths=None,
        initial_context=None,
        media_player=None,
        parent=None,
    ):
        super().__init__(parent)
        self.core = core
        self.initial_context = initial_context or {}
        self.media_player = media_player
        self.tools = find_tools(core)
        self.inventory = {}
        self.process = None
        self.process_output = ""
        self.process_output_chunks = []
        self.process_stage = ""
        self.cancel_requested = False
        self.run_jobs = []
        self.run_index = 0
        self.current_job = None
        self.current_temp = None
        self.pending_formats = []
        self.current_extension = ""
        self.completed_outputs = []
        self.format_failures = []
        self.successes = []
        self.failures = []
        self.preview_temp = None
        self.existing_policy = "replace"
        self.quick_mode = False
        self._quick_finished = False
        self._inventory_generation = 0
        self._inventory_thread = None
        self._pending_inventory = None
        self._inventory_requests = {}
        self._inspect_generation = 0
        self._inspect_thread = None
        self._preview_request = None
        self._conversion_preflight = None

        self.setWindowTitle("ACES / OCIO Media Converter")
        self.setMinimumSize(980, 720)
        self.resize(1080, 780)
        if parent:
            try:
                self.core.parentWindow(self, parent)
            except Exception:
                pass

        self._build_ui()
        self._load_initial_config()
        if initial_paths:
            self.add_paths(initial_paths, context=self.initial_context)
        self._update_tool_status()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        color_group = QGroupBox("OCIO Color Transform")
        color_layout = QVBoxLayout(color_group)
        config_row = QHBoxLayout()
        config_row.addWidget(QLabel("Config:"))
        self.ocio_edit = QLineEdit()
        self.ocio_edit.editingFinished.connect(self._reload_inventory)
        config_row.addWidget(self.ocio_edit)
        browse_config = QPushButton("...")
        browse_config.setFixedWidth(32)
        browse_config.clicked.connect(self._browse_config)
        config_row.addWidget(browse_config)
        self.reset_config_btn = QPushButton("Use Project OCIO")
        self.reset_config_btn.clicked.connect(self._reset_project_config)
        config_row.addWidget(self.reset_config_btn)
        color_layout.addLayout(config_row)

        form = QFormLayout()
        self.input_combo = QComboBox()
        self.input_combo.setEditable(False)
        form.addRow("Input Colorspace:", self.input_combo)
        self.display_combo = QComboBox()
        self.display_combo.currentTextChanged.connect(self._display_changed)
        form.addRow("Display:", self.display_combo)
        self.view_combo = QComboBox()
        form.addRow("View:", self.view_combo)
        color_layout.addLayout(form)
        self.config_status = QLabel("")
        self.config_status.setWordWrap(True)
        color_layout.addWidget(self.config_status)
        layout.addWidget(color_group)

        options_row = QHBoxLayout()
        options_row.addWidget(QLabel("FPS:"))
        self.fps_spin = QDoubleSpinBox()
        self.fps_spin.setDecimals(3)
        self.fps_spin.setRange(0.001, 240.0)
        self.fps_spin.setValue(self._project_fps())
        options_row.addWidget(self.fps_spin)
        options_row.addSpacing(24)
        self.mp4_check = QCheckBox("H.264 MP4")
        self.mp4_check.setChecked(True)
        options_row.addWidget(self.mp4_check)
        self.mov_check = QCheckBox("ProRes 422 HQ MOV")
        self.mov_check.setChecked(True)
        options_row.addWidget(self.mov_check)
        options_row.addSpacing(12)
        options_row.addWidget(QLabel("MOV encoder:"))
        self.prores_combo = QComboBox()
        self.prores_combo.addItem("Fast (prores_aw)", "prores_aw")
        self.prores_combo.addItem("Compatibility (prores_ks)", "prores_ks")
        self.prores_combo.setToolTip(
            "Fast is recommended for review media. Use Compatibility if a "
            "downstream application rejects the fast output."
        )
        self.mov_check.toggled.connect(self.prores_combo.setEnabled)
        options_row.addWidget(self.prores_combo)
        options_row.addStretch()
        layout.addLayout(options_row)

        splitter = QSplitter(Qt.Horizontal)
        queue_widget = QWidget()
        queue_layout = QVBoxLayout(queue_widget)
        queue_layout.setContentsMargins(0, 0, 0, 0)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["EXR Source", "Frames", "Status"])
        self.tree.setColumnWidth(0, 430)
        self.tree.setColumnWidth(1, 110)
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        queue_layout.addWidget(self.tree)
        queue_buttons = QHBoxLayout()
        add_btn = QPushButton("Add EXR...")
        add_btn.clicked.connect(self._browse_inputs)
        queue_buttons.addWidget(add_btn)
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._remove_selected)
        queue_buttons.addWidget(remove_btn)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.tree.clear)
        queue_buttons.addWidget(clear_btn)
        queue_buttons.addStretch()
        self.preview_btn = QPushButton("Test Frame")
        self.preview_btn.clicked.connect(self._start_preview)
        queue_buttons.addWidget(self.preview_btn)
        queue_layout.addLayout(queue_buttons)
        splitter.addWidget(queue_widget)

        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.addWidget(QLabel("Rec.709 test frame"))
        self.preview_label = QLabel("Select a queue item and click Test Frame")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(360, 240)
        self.preview_label.setStyleSheet("QLabel { background: #202020; color: #999; }")
        preview_layout.addWidget(self.preview_label, 1)
        splitter.addWidget(preview_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter, 1)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(150)
        layout.addWidget(self.log)

        self.tool_status = QLabel("")
        self.tool_status.setWordWrap(True)
        layout.addWidget(self.tool_status)
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        bottom = QHBoxLayout()
        bottom.addStretch()
        self.convert_btn = QPushButton("Convert Queue")
        self.convert_btn.setMinimumWidth(150)
        self.convert_btn.clicked.connect(self.start_conversion)
        bottom.addWidget(self.convert_btn)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_conversion)
        bottom.addWidget(self.cancel_btn)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        bottom.addWidget(close_btn)
        layout.addLayout(bottom)

    def _project_fps(self):
        for kwargs in (
            {"config": "project"},
            {"configPath": getattr(self.core, "prismIni", None)},
        ):
            try:
                value = self.core.getConfig("globals", "fps", **kwargs)
                if value:
                    return validate_fps(value)
            except Exception:
                pass
        return 25.0

    def _update_tool_status(self):
        missing = [name for name, path in self.tools.items() if not path]
        if missing:
            self.tool_status.setText("Missing tools: %s" % ", ".join(missing))
            self.tool_status.setStyleSheet("color: #e06c75;")
        else:
            self.tool_status.setText(
                "OpenImageIO: %s    FFmpeg: %s"
                % (self.tools["oiiotool"], self.tools["ffmpeg"])
            )
            self.tool_status.setStyleSheet("")

    def _load_initial_config(self):
        config, source = select_ocio_config(
            get_project_config_key(self.core), load_config(self.core), os.environ
        )
        self.ocio_edit.setText(config)
        self.config_status.setText("Loading OCIO configuration...")
        self.convert_btn.setEnabled(False)
        self._initial_config_source = source
        QTimer.singleShot(0, self._load_deferred_inventory)

    def _load_deferred_inventory(self):
        queued = self._reload_inventory(
            source=self._initial_config_source,
            emit_loaded=True,
        )
        if not queued:
            self.inventoryLoaded.emit(False)

    def start_quick_conversion(self, formats):
        formats = set(formats)
        if not formats or not formats.issubset({".mp4", ".mov"}):
            raise ValueError("Quick conversion requires MP4 and/or MOV output")
        self.quick_mode = True
        self.mp4_check.setChecked(".mp4" in formats)
        self.mov_check.setChecked(".mov" in formats)
        if self.inventory:
            QTimer.singleShot(0, self.start_conversion)
            return
        self.inventoryLoaded.connect(self._quick_inventory_loaded)

    def _quick_inventory_loaded(self, loaded):
        try:
            self.inventoryLoaded.disconnect(self._quick_inventory_loaded)
        except (RuntimeError, TypeError):
            pass
        if loaded:
            QTimer.singleShot(0, self.start_conversion)
            return
        self.core.popup(
            "Quick conversion could not load a valid OCIO configuration.",
            severity="warning",
            parent=self,
        )
        self._finish_quick_runner()

    def _reload_inventory(
        self,
        source=None,
        save_override=False,
        restore_text="",
        emit_loaded=False,
    ):
        config = self.ocio_edit.text().strip()
        manual_change = (
            source is None
            and config != getattr(self, "_loaded_config_text", "")
        )
        if not self.tools.get("oiiotool"):
            self.config_status.setText("Cannot load OCIO config: oiiotool was not found.")
            self.inventory = {}
            self.convert_btn.setEnabled(False)
            return False
        if not config:
            self.config_status.setText("Select an OCIO config.")
            self.inventory = {}
            self.convert_btn.setEnabled(False)
            return False
        if not config.startswith("ocio://") and not os.path.isfile(config):
            self.config_status.setText("OCIO config not found: %s" % config)
            self.inventory = {}
            self.convert_btn.setEnabled(False)
            return False

        self._inventory_generation += 1
        generation = self._inventory_generation
        request = {
            "config": config,
            "source": source,
            "manual_change": manual_change,
            "save_override": bool(save_override),
            "restore_text": restore_text,
            "emit_loaded": bool(emit_loaded),
            "generation": generation,
        }
        self._inventory_requests[generation] = request
        self._pending_inventory = request
        self.inventory = {}
        self.convert_btn.setEnabled(False)
        self.config_status.setText("Loading OCIO configuration...")
        self.config_status.setStyleSheet("")
        self._start_pending_inventory()
        return True

    def _start_pending_inventory(self):
        if (
            self._inventory_thread is not None
            or self._pending_inventory is None
        ):
            return
        request = self._pending_inventory
        self._pending_inventory = None
        thread = InventoryThread(
            self.tools["oiiotool"],
            request["config"],
            request["generation"],
        )
        thread.completed.connect(self._inventory_completed)
        thread.failed.connect(self._inventory_failed)
        self._inventory_thread = thread
        _track_background_thread(thread)

    def _inventory_completed(self, inventory, generation):
        self._inventory_thread = None
        request = self._inventory_requests.pop(generation, None)
        if request and generation == self._inventory_generation:
            self._apply_inventory(inventory, request)
        self._start_pending_inventory()

    def _inventory_failed(self, message, generation):
        self._inventory_thread = None
        request = self._inventory_requests.pop(generation, None)
        if request and generation == self._inventory_generation:
            self.inventory = {}
            self.convert_btn.setEnabled(False)
            self.config_status.setText(
                "Failed to load OCIO config: %s" % message
            )
            self.config_status.setStyleSheet("color: #e06c75;")
            if request["emit_loaded"]:
                self.inventoryLoaded.emit(False)
            restore_text = request["restore_text"]
            if restore_text:
                self.ocio_edit.setText(restore_text)
                self._reload_inventory(source="project_override")
        self._start_pending_inventory()

    def _apply_inventory(self, inventory, request):
        config = request["config"]
        source = request["source"]
        self.inventory = inventory
        input_space, display, view = choose_inventory_defaults(inventory)
        self.input_combo.blockSignals(True)
        self.input_combo.clear()
        self.input_combo.addItems(inventory["colorspaces"])
        self._set_combo_text(self.input_combo, input_space)
        self.input_combo.blockSignals(False)

        self.display_combo.blockSignals(True)
        self.display_combo.clear()
        self.display_combo.addItems(list(inventory["displays"].keys()))
        self._set_combo_text(self.display_combo, display)
        self.display_combo.blockSignals(False)
        self._populate_views(view)

        if source == "oiio_default" or config == "ocio://default":
            self.config_status.setText(
                "Warning: using OpenImageIO's default ACES config. Select the same "
                "config used by Houdini/Nuke for an exact match."
            )
            self.config_status.setStyleSheet("color: #e5c07b;")
        else:
            self.config_status.setText("OCIO config loaded: %s" % config)
            self.config_status.setStyleSheet("color: #98c379;")
        if request["manual_change"] or request["save_override"]:
            try:
                save_ocio_project_override(
                    self.core, get_project_config_key(self.core), config
                )
            except Exception as exc:
                self._append_log("Could not save OCIO override: %s" % exc)
        self._loaded_config_text = config
        self.convert_btn.setEnabled(True)
        if request["emit_loaded"]:
            self.inventoryLoaded.emit(True)

    @staticmethod
    def _set_combo_text(combo, text):
        index = combo.findText(text)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _display_changed(self, _text):
        self._populate_views()

    def _populate_views(self, preferred=""):
        display = self.display_combo.currentText()
        current = preferred or self.view_combo.currentText()
        self.view_combo.clear()
        self.view_combo.addItems(self.inventory.get("displays", {}).get(display, []))
        if current:
            self._set_combo_text(self.view_combo, current)
        if self.view_combo.currentIndex() < 0 and self.view_combo.count():
            self.view_combo.setCurrentIndex(0)

    def _browse_config(self):
        start = self.ocio_edit.text().strip()
        if not os.path.isfile(start):
            start = os.path.dirname(start) if start else ""
        path, _selected_filter = QFileDialog.getOpenFileName(
            self, "Select OCIO Config", start, "OCIO Config (*.ocio);;All Files (*)"
        )
        if not path:
            return
        previous = self.ocio_edit.text()
        self.ocio_edit.setText(path)
        self._reload_inventory(
            source="project_override",
            save_override=True,
            restore_text=previous,
        )

    def _reset_project_config(self):
        try:
            save_ocio_project_override(
                self.core, get_project_config_key(self.core), ""
            )
        except Exception as exc:
            self._append_log("Could not reset OCIO override: %s" % exc)
        config, source = select_ocio_config(
            get_project_config_key(self.core), load_config(self.core), os.environ
        )
        self.ocio_edit.setText(config)
        self._reload_inventory(source=source)

    def _browse_inputs(self):
        paths, _selected_filter = QFileDialog.getOpenFileNames(
            self, "Select EXR Frames", "", "OpenEXR (*.exr)"
        )
        if paths:
            self.add_paths(paths)

    def add_paths(self, paths, context=None):
        jobs, errors = collect_exr_jobs(paths)
        for error in errors:
            self._append_log(error)
        existing = {
            os.path.normcase(item.data(0, Qt.UserRole)["input_pattern"])
            for item in self._tree_items()
            if item.data(0, Qt.UserRole)
        }
        for job in jobs:
            key = os.path.normcase(job["input_pattern"])
            if key in existing:
                continue
            job["context"] = dict(context or self._context_for_path(job["source_path"]))
            item = QTreeWidgetItem()
            item.setData(0, Qt.UserRole, job)
            item.setText(0, job["input_pattern"])
            if job["is_sequence"]:
                item.setText(1, "%s-%s (%s)" % (
                    job["first"], job["last"], job["frame_count"]
                ))
            else:
                item.setText(1, "single")
            if job["missing_frames"]:
                item.setText(2, "Missing: %s" % self._frame_summary(job["missing_frames"]))
            else:
                item.setText(2, "Ready")
            self.tree.addTopLevelItem(item)
            existing.add(key)

    def _context_for_path(self, path):
        try:
            context = self.core.paths.getMediaProductData(path, isFilepath=True)
            return context or {}
        except Exception:
            return {}

    def _tree_items(self):
        return [self.tree.topLevelItem(i) for i in range(self.tree.topLevelItemCount())]

    def _selected_job(self):
        selected = self.tree.selectedItems()
        item = selected[0] if selected else self.tree.topLevelItem(0)
        return item.data(0, Qt.UserRole) if item else None

    def _remove_selected(self):
        for item in self.tree.selectedItems():
            self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(item))

    @staticmethod
    def _frame_summary(frames, limit=12):
        values = [str(frame) for frame in frames[:limit]]
        if len(frames) > limit:
            values.append("... +%s" % (len(frames) - limit))
        return ", ".join(values)

    def _validate_common_settings(self):
        missing = [name for name, path in self.tools.items() if not path]
        if missing:
            raise RuntimeError("Required tools not found: %s" % ", ".join(missing))
        if not self.inventory:
            raise RuntimeError("Load a valid OCIO config first.")
        errors = validate_color_selection(
            self.inventory,
            self.input_combo.currentText(),
            self.display_combo.currentText(),
            self.view_combo.currentText(),
        )
        if errors:
            raise RuntimeError("\n".join(errors))
        return validate_fps(self.fps_spin.value())

    def _start_preview(self):
        if (
            self._inspect_thread is not None
            or (
                self.process
                and self.process.state() != QProcess.NotRunning
            )
        ):
            self.core.popup("A conversion is already running.")
            return
        job = self._selected_job()
        if not job:
            self.core.popup("Add or select an EXR sequence first.")
            return
        try:
            self._validate_common_settings()
            middle_path = job["files"][len(job["files"]) // 2]
        except Exception as exc:
            self.core.popup(str(exc), severity="warning", parent=self)
            return
        self._preview_request = {
            "job": job,
            "middle_path": middle_path,
        }
        self.preview_btn.setEnabled(False)
        self.convert_btn.setEnabled(False)
        self._start_inspection([middle_path], "preview")

    def _begin_preview(self, job, middle_path, info):
        self._release_temp_directory("preview_temp")
        self.preview_temp = QTemporaryDir()
        if not self.preview_temp.isValid():
            self.core.popup("Could not create a temporary preview directory.")
            self.preview_btn.setEnabled(True)
            self.convert_btn.setEnabled(bool(self.inventory))
            return
        output = os.path.join(self.preview_temp.path(), "preview.png")
        preview_job = dict(job)
        preview_job.update({
            "input_pattern": middle_path,
            "is_sequence": False,
            "first": None,
            "last": None,
            "padding": 0,
            "frame_count": 1,
        })
        args = build_oiiotool_args(
            preview_job,
            output,
            self.ocio_edit.text().strip(),
            self.input_combo.currentText(),
            self.display_combo.currentText(),
            self.view_combo.currentText(),
            has_alpha=info["has_alpha"],
            data_type="uint8",
            compression=None,
        )
        self.preview_output = output
        self._start_process("preview", self.tools["oiiotool"], args)

    def start_conversion(self):
        if (
            self._inspect_thread is not None
            or (
                self.process
                and self.process.state() != QProcess.NotRunning
            )
        ):
            return
        items = self._tree_items()
        if not items:
            self.core.popup("Add at least one EXR sequence.")
            self._finish_quick_runner()
            return
        formats = []
        if self.mp4_check.isChecked():
            formats.append(".mp4")
        if self.mov_check.isChecked():
            formats.append(".mov")
        if not formats:
            self.core.popup("Select at least one output format.")
            self._finish_quick_runner()
            return
        try:
            self._validate_common_settings()
        except Exception as exc:
            self.core.popup(str(exc), severity="warning", parent=self)
            self._finish_quick_runner()
            return

        self.successes = []
        self.failures = []
        candidates = []
        output_owners = {}
        for item in items:
            job = item.data(0, Qt.UserRole)
            job["_tree_item"] = item
            item.setText(2, "Preflight")
            if job["missing_frames"]:
                message = "Missing frames: %s" % self._frame_summary(job["missing_frames"])
                self.failures.append("%s: %s" % (job["name"], message))
                item.setText(2, "Failed: missing frames")
                continue
            try:
                outputs = self._resolve_output_paths(job, formats)
            except Exception as exc:
                self.failures.append("%s: %s" % (job["name"], exc))
                item.setText(2, "Failed: preflight")
                continue
            duplicate = next(
                (path for path in outputs.values() if os.path.normcase(path) in output_owners),
                "",
            )
            if duplicate:
                message = "Output conflicts with %s: %s" % (
                    output_owners[os.path.normcase(duplicate)], duplicate
                )
                self.failures.append("%s: %s" % (job["name"], message))
                item.setText(2, "Failed: output conflict")
                continue
            for path in outputs.values():
                output_owners[os.path.normcase(path)] = job["name"]
            job["outputs"] = outputs
            job["formats"] = list(formats)
            candidates.append(job)

        self._conversion_preflight = {
            "items": items,
            "formats": formats,
            "candidates": candidates,
        }
        self.cancel_requested = False
        self.progress.setVisible(True)
        self.progress.setMaximum(len(items))
        self.progress.setValue(len(items) - len(candidates))
        self.convert_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.preview_btn.setEnabled(False)
        if not candidates:
            self._complete_conversion_preflight([])
            return
        self._start_inspection(
            [job["source_path"] for job in candidates],
            "conversion",
        )

    def _start_inspection(self, paths, mode):
        self._inspect_generation += 1
        generation = self._inspect_generation
        thread = ExrInspectThread(
            self.tools["oiiotool"],
            paths,
            generation,
            mode,
        )
        thread.completed.connect(self._inspection_completed)
        thread.failed.connect(self._inspection_failed)
        self._inspect_thread = thread
        _track_background_thread(thread)

    def _inspection_completed(self, results, generation, mode):
        self._inspect_thread = None
        if generation != self._inspect_generation:
            return
        if mode == "preview":
            request = self._preview_request
            self._preview_request = None
            result = results[0] if results else {
                "error": "No EXR metadata was returned."
            }
            if result.get("error"):
                self.preview_btn.setEnabled(True)
                self.convert_btn.setEnabled(bool(self.inventory))
                self.core.popup(
                    result["error"],
                    severity="warning",
                    parent=self,
                )
                return
            self._begin_preview(
                request["job"],
                request["middle_path"],
                result["info"],
            )
            return
        self._complete_conversion_preflight(results)

    def _inspection_failed(self, message, generation, mode):
        self._inspect_thread = None
        if generation != self._inspect_generation:
            return
        if mode == "preview":
            self._preview_request = None
            self.preview_btn.setEnabled(True)
            self.convert_btn.setEnabled(bool(self.inventory))
        else:
            preflight = self._conversion_preflight or {}
            for job in preflight.get("candidates", []):
                job["_tree_item"].setText(2, "Failed: preflight")
            self._conversion_preflight = None
            self.progress.setVisible(False)
            self.convert_btn.setEnabled(bool(self.inventory))
            self.preview_btn.setEnabled(True)
            self._finish_quick_runner()
        self.core.popup(
            "EXR preflight failed:\n%s" % message,
            severity="warning",
            parent=self,
        )

    def _complete_conversion_preflight(self, results):
        preflight = self._conversion_preflight or {}
        self._conversion_preflight = None
        items = preflight.get("items", [])
        candidates = preflight.get("candidates", [])
        runnable = []
        conflicts = []
        for job, result in zip(candidates, results):
            error = result.get("error")
            if error:
                self.failures.append(
                    "%s: %s" % (job["name"], error)
                )
                job["_tree_item"].setText(2, "Failed: preflight")
                continue
            job["exr_info"] = result["info"]
            runnable.append(job)
            conflicts.extend(
                path
                for path in job["outputs"].values()
                if os.path.exists(path)
            )

        if conflicts:
            policy = self._ask_existing_policy(conflicts)
            if policy == "cancel":
                for job in runnable:
                    job["_tree_item"].setText(2, "Ready")
                self.progress.setVisible(False)
                self.convert_btn.setEnabled(bool(self.inventory))
                self.preview_btn.setEnabled(True)
                self._finish_quick_runner()
                return
            self.existing_policy = policy
        else:
            self.existing_policy = "replace"

        self.run_jobs = runnable
        self.run_index = 0
        self.cancel_requested = False
        self.progress.setMaximum(len(items))
        self.progress.setValue(len(items) - len(runnable))
        self.cancel_btn.setEnabled(True)
        self._append_log("Starting %d job(s)." % len(runnable))
        if not runnable:
            self._finish_queue()
            return
        self._start_next_job()

    def _resolve_output_paths(self, job, formats):
        context = job.get("context") or {}
        managed = context.get("type") in ("asset", "shot") and context.get("identifier")
        outputs = {}
        for extension in formats:
            if managed:
                path = self.core.paths.getMediaConversionOutputPath(
                    dict(context), job["input_pattern"], extension
                )
            else:
                path = external_output_path(job, extension)
            if not path:
                raise RuntimeError("Could not resolve %s output path" % extension)
            outputs[extension] = os.path.abspath(os.path.normpath(str(path)))
        return outputs

    def _ask_existing_policy(self, paths):
        message = QMessageBox(self)
        message.setWindowTitle("Existing Outputs")
        message.setText("%d output file(s) already exist." % len(paths))
        message.setInformativeText("Replace all existing files, skip them, or cancel?")
        replace_btn = message.addButton("Replace All", QMessageBox.AcceptRole)
        skip_btn = message.addButton("Skip Existing", QMessageBox.DestructiveRole)
        cancel_btn = message.addButton(QMessageBox.Cancel)
        message.exec_()
        clicked = message.clickedButton()
        if clicked == replace_btn:
            return "replace"
        if clicked == skip_btn:
            return "skip"
        if clicked == cancel_btn:
            return "cancel"
        return "cancel"

    def _start_next_job(self):
        if self.cancel_requested or self.run_index >= len(self.run_jobs):
            self._finish_queue()
            return
        job = self.run_jobs[self.run_index]
        self.current_job = job
        self.completed_outputs = []
        self.format_failures = []
        self.pending_formats = [
            ext for ext in job["formats"]
            if not (self.existing_policy == "skip" and os.path.exists(job["outputs"][ext]))
        ]
        skipped = len(job["formats"]) - len(self.pending_formats)
        if skipped:
            self._append_log("%s: skipped %d existing output(s)." % (job["name"], skipped))
        if not self.pending_formats:
            job["_tree_item"].setText(2, "Skipped")
            self.run_index += 1
            self.progress.setValue(self.progress.value() + 1)
            self._start_next_job()
            return

        self.current_temp = QTemporaryDir()
        if not self.current_temp.isValid():
            self._complete_current_job("Could not create a temporary directory")
            return
        if ".mov" in self.pending_formats:
            temp_extension = ".dpx"
            data_type = "uint10"
            compression = None
            self._append_log(
                "%s: using 10-bit DPX intermediates for ProRes."
                % job["name"]
            )
        else:
            temp_extension = ".tif"
            data_type = "uint8"
            compression = "none"
            self._append_log(
                "%s: using 8-bit uncompressed TIFF intermediates for H.264."
                % job["name"]
            )
        if job["is_sequence"]:
            temp_pattern = os.path.join(
                self.current_temp.path(),
                "frame.%%0%dd%s" % (job["padding"], temp_extension),
            )
        else:
            temp_pattern = os.path.join(
                self.current_temp.path(), "frame" + temp_extension
            )
        job["temp_pattern"] = temp_pattern
        job["_tree_item"].setText(2, "OCIO transform")
        args = build_oiiotool_args(
            job,
            temp_pattern,
            self.ocio_edit.text().strip(),
            self.input_combo.currentText(),
            self.display_combo.currentText(),
            self.view_combo.currentText(),
            has_alpha=job["exr_info"]["has_alpha"],
            data_type=data_type,
            compression=compression,
        )
        self._start_process("ocio", self.tools["oiiotool"], args)

    def _start_next_format(self):
        if not self.pending_formats:
            self._complete_current_job()
            return
        self.current_extension = self.pending_formats.pop(0)
        final_path = self.current_job["outputs"][self.current_extension]
        os.makedirs(os.path.dirname(final_path), exist_ok=True)
        staging = staging_output_path(final_path)
        if os.path.exists(staging):
            try:
                os.remove(staging)
            except OSError as exc:
                self._record_format_failure("Cannot remove stale staging file: %s" % exc)
                self._start_next_format()
                return
        self.current_job["staging"] = staging
        self.current_job["_tree_item"].setText(
            2, "Encoding %s" % self.current_extension[1:].upper()
        )
        args = build_ffmpeg_args(
            self.current_job,
            self.current_job["temp_pattern"],
            staging,
            self.fps_spin.value(),
            self.current_extension,
            prores_encoder=self.prores_combo.currentData() or "prores_aw",
        )
        self._start_process("encode", self.tools["ffmpeg"], args)

    def _start_validation(self):
        self.current_job["_tree_item"].setText(
            2, "Validating %s" % self.current_extension[1:].upper()
        )
        self._start_process(
            "validate",
            self.tools["ffmpeg"],
            build_validation_args(self.current_job["staging"]),
        )

    def _start_process(self, stage, program, args):
        self.process_stage = stage
        self.process_output = ""
        self.process_output_chunks = []
        self._append_log(subprocess.list2cmdline([program] + list(args)))
        process = QProcess(self)
        self.process = process
        process.setProcessChannelMode(QProcess.MergedChannels)
        process.readyReadStandardOutput.connect(self._read_process_output)
        process.finished.connect(self._process_finished)
        process.errorOccurred.connect(self._process_error)
        process.start(program, list(args))

    def _read_process_output(self):
        if not self.process:
            return
        data = bytes(self.process.readAllStandardOutput()).decode("utf-8", "replace")
        if data:
            self.process_output_chunks.append(data)
            self._append_log(data.rstrip())

    def _process_error(self, error):
        if error != QProcess.FailedToStart:
            return
        QTimer.singleShot(
            0,
            lambda: self._handle_process_result(False, "Process failed to start"),
        )

    def _process_finished(self, exit_code, exit_status):
        self._read_process_output()
        self.process_output = "".join(self.process_output_chunks)
        success = exit_code == 0 and exit_status == QProcess.NormalExit
        self._handle_process_result(success, self.process_output.strip())

    def _handle_process_result(self, success, error_text=""):
        if not self.process_stage:
            return
        stage = self.process_stage
        self.process_stage = ""
        if self.process:
            self.process.deleteLater()
            self.process = None

        if stage == "preview":
            self.preview_btn.setEnabled(True)
            self.convert_btn.setEnabled(bool(self.inventory))
            if success and os.path.isfile(self.preview_output):
                pixmap = QPixmap(self.preview_output)
                if not pixmap.isNull():
                    self.preview_label.setPixmap(
                        pixmap.scaled(
                            self.preview_label.size(),
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation,
                        )
                    )
                    return
            self.core.popup(
                "Test frame conversion failed:\n\n%s" % error_text[-2000:],
                severity="warning",
                parent=self,
            )
            return

        if self.cancel_requested:
            self._cleanup_staging()
            self._finish_queue()
            return
        if not success:
            message = error_text[-2000:] or "%s failed" % stage
            if stage == "ocio":
                self._complete_current_job(message)
            else:
                self._record_format_failure(message)
                self._cleanup_staging()
                self._start_next_format()
            return

        if stage == "ocio":
            self._start_next_format()
        elif stage == "encode":
            self._start_validation()
        elif stage == "validate":
            staging = self.current_job["staging"]
            final = self.current_job["outputs"][self.current_extension]
            try:
                os.replace(staging, final)
            except OSError as exc:
                self._record_format_failure("Cannot commit output: %s" % exc)
            else:
                self.completed_outputs.append(final)
                self.successes.append(final)
            self._start_next_format()

    def _record_format_failure(self, message):
        self.format_failures.append(
            "%s %s: %s" % (
                self.current_job["name"], self.current_extension, message
            )
        )

    def _cleanup_staging(self):
        if not self.current_job:
            return
        staging = self.current_job.get("staging", "")
        if staging and os.path.isfile(staging):
            try:
                os.remove(staging)
            except OSError:
                pass

    def _complete_current_job(self, fatal_error=""):
        job = self.current_job
        if not job:
            return
        if fatal_error:
            self.failures.append("%s: %s" % (job["name"], fatal_error))
        self.failures.extend(self.format_failures)
        if self.completed_outputs and (fatal_error or self.format_failures):
            job["_tree_item"].setText(2, "Partial")
        elif self.completed_outputs:
            job["_tree_item"].setText(2, "Done")
        else:
            job["_tree_item"].setText(2, "Failed")
        self._release_temp_directory("current_temp")
        self.current_job = None
        self.run_index += 1
        self.progress.setValue(self.progress.value() + 1)
        self._start_next_job()

    def cancel_conversion(self):
        self.cancel_requested = True
        self.cancel_btn.setEnabled(False)
        self._append_log("Cancellation requested.")
        if self.process and self.process.state() != QProcess.NotRunning:
            self.process.terminate()
            QTimer.singleShot(3000, self._kill_process_if_running)
        else:
            self._finish_queue()

    def _kill_process_if_running(self):
        if self.process and self.process.state() != QProcess.NotRunning:
            self.process.kill()

    def _finish_queue(self):
        if self.cancel_requested:
            if self.current_job:
                self.current_job["_tree_item"].setText(2, "Cancelled")
            for job in self.run_jobs[self.run_index + 1:]:
                job["_tree_item"].setText(2, "Cancelled")
        self._release_temp_directory("current_temp")
        self.convert_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.preview_btn.setEnabled(True)
        self.progress.setVisible(False)
        self.process_stage = ""
        self.process = None
        self._refresh_media_browser()

        message = "Conversion %s.\n\nOutputs: %d\nFailures: %d" % (
            "cancelled" if self.cancel_requested else "finished",
            len(self.successes),
            len(self.failures),
        )
        if self.successes:
            message += "\n\nCreated:\n" + "\n".join(self.successes[:10])
            if len(self.successes) > 10:
                message += "\n... and %d more" % (len(self.successes) - 10)
        if self.failures:
            message += "\n\nFailures:\n" + "\n".join(self.failures[:10])
            if len(self.failures) > 10:
                message += "\n... and %d more" % (len(self.failures) - 10)
        self.core.popup(
            message,
            severity="warning" if self.failures else "info",
            parent=self,
        )
        if self.quick_mode:
            self._finish_quick_runner()
        else:
            self.conversionFinished.emit(self)

    def _finish_quick_runner(self):
        if not self.quick_mode or self._quick_finished:
            return
        self._quick_finished = True
        self.conversionFinished.emit(self)
        self.deleteLater()

    def _refresh_media_browser(self):
        try:
            if self.media_player and self.media_player.origin:
                self.media_player.origin.updateVersions(restoreSelection=True)
                return
        except Exception:
            pass
        try:
            media_browser = self.core.pb.mediaBrowser
            media_browser.updateVersions(restoreSelection=True)
        except Exception:
            pass

    def _append_log(self, text):
        if not text:
            return
        self.log.appendPlainText(str(text))
        scrollbar = self.log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _release_temp_directory(self, attribute):
        temporary = getattr(self, attribute, None)
        setattr(self, attribute, None)
        if temporary is None:
            return
        path = temporary.path()
        temporary.setAutoRemove(False)
        _queue_temp_cleanup(path)

    def closeEvent(self, event):
        if self.process and self.process.state() != QProcess.NotRunning:
            answer = QMessageBox.question(
                self,
                "Conversion Running",
                "Cancel the running conversion and close?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                event.ignore()
                return
            self.cancel_conversion()
        else:
            self._release_temp_directory("current_temp")
            self._release_temp_directory("preview_temp")
        event.accept()
