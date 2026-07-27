import os

from qtpy.QtCore import QTimer, Qt, QUrl
from qtpy.QtGui import QDesktopServices
from qtpy.QtWidgets import QAction, QMenu

from change_prism.batch_import.file_processor import FileProcessor
from change_prism.batch_import.scanner import SERVER_STEPS, STEP_LABELS
from change_prism.batch_import.service import write_failure_report


class BatchImportController(object):
    DEPARTMENTS = {
        "Fx": {
            "name": "Fx",
            "task": "Effects",
            "ext": ".hip",
            "software": "Houdini",
        },
        "Lighting": {
            "name": "Lighting",
            "task": "Lighting",
            "ext": ".hip",
            "software": "Houdini",
        },
        "Compositing": {
            "name": "Compositing",
            "task": "Compositing",
            "ext": ".nk",
            "software": "Nuke",
        },
    }

    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin
        self.file_processor = FileProcessor(core)
        self._preset_scenes_cache = None
        self._pdg_processor = None
        self._import_state = None
        self._file_job = None

    def open_dialog(self):
        from change_prism.batch_import.dialog import BatchImportDialog
        from change_prism.config import get_server_root

        parent = getattr(self.core, "pb", None)
        self.plugin.serverRoot = get_server_root(self.core)
        dialog = BatchImportDialog(
            self.core,
            self.plugin.serverRoot,
            create_callback=self._start_project_and_shots,
            finish_callback=self._on_batch_import_finished,
            parent=parent,
        )
        dialog.exec_()

    def _load_or_create_project(self, data, reporter):
        project_name = data["project_name"]
        project_path = data["project_path"]
        config_path = self.core.configs.getProjectConfigPath(project_path)
        created = False
        if os.path.exists(config_path):
            reporter.set_status(
                "Opening existing project '%s'..." % project_name
            )
        else:
            reporter.set_status(
                "Creating Prism project '%s'..." % project_name
            )
            config_path = self.core.projects.createProject(
                name=project_name,
                path=project_path,
                preset="Default",
                parent=data.get("parent"),
            )
            if not config_path:
                return False
            created = True

        reporter.set_status("Loading project '%s'..." % project_name)
        loaded = self.core.projects.changeProject(config_path)
        if not loaded:
            raise RuntimeError(
                "Prism could not load project config:\n%s" % config_path
            )

        self._preset_scenes_cache = None
        self._keep_only_shot_ranges()
        if created:
            self._set_project_departments()
        return True

    def _keep_only_shot_ranges(self):
        getter = getattr(self.core, "getConfig", None)
        setter = getattr(self.core, "setConfig", None)
        if not callable(getter) or not callable(setter):
            return
        shot_info = getter(
            config="shotinfo", allowCache=False
        ) or {}
        cleaned = {}
        if "shotRanges" in shot_info:
            cleaned["shotRanges"] = shot_info["shotRanges"]
        if shot_info != cleaned:
            setter(
                data=cleaned,
                config="shotinfo",
                updateNestedData=False,
            )

    def _start_project_and_shots(self, data):
        finished_callback = data.get("_finished_callback")
        reporter = data.get("_reporter") or _NullReporter()
        if not callable(finished_callback):
            raise RuntimeError(
                "Batch import requires a completion callback."
            )
        if self._import_state is not None:
            raise RuntimeError("A Batch Import is already running.")

        project_name = data["project_name"]
        selected = list(data["selected"])
        project_loaded = False
        try:
            project_loaded = self._load_or_create_project(data, reporter)
            if not project_loaded:
                finished_callback(
                    self._build_import_result(
                        0,
                        len(selected),
                        [],
                        {
                            "project": project_name,
                            "total": len(selected),
                        },
                        [],
                    )
                )
                return None
        except Exception as exc:
            finished_callback(
                self._build_import_result(
                    0,
                    len(selected),
                    [],
                    {
                        "project": project_name,
                        "total": len(selected),
                    },
                    [],
                    project_loaded=project_loaded,
                    error=str(exc),
                )
            )
            return None

        self._import_state = {
            "data": data,
            "reporter": reporter,
            "finished_callback": finished_callback,
            "project_name": project_name,
            "selected": selected,
            "project_loaded": project_loaded,
            "create_only": bool(data.get("create_only")),
            "copy_to_local": bool(data.get("copy_to_local")),
            "pdg_enabled": bool(data.get("pdg_enabled")),
            "index": 0,
            "success": 0,
            "failures": [],
            "shot_data_list": [],
            "shots_cache": {},
            "current": None,
        }
        QTimer.singleShot(0, self._advance_async_import)
        return None

    def _advance_async_import(self):
        state = self._import_state
        if state is None:
            return
        if state["index"] >= len(state["selected"]):
            self._finish_async_import()
            return

        item = state["selected"][state["index"]]
        state["index"] += 1
        state["reporter"].update_progress(state["index"])
        state["current"] = {"item": item}
        try:
            entity = self._create_single_shot(
                item,
                state["shots_cache"],
            )
            if state["create_only"]:
                self._complete_async_shot()
                return
            prepared = self.file_processor.prepare(
                item,
                entity,
                state["project_name"],
                state["copy_to_local"],
            )
            state["current"].update(
                {"entity": entity, "prepared": prepared}
            )
            self._start_file_work("product", prepared)
        except Exception as exc:
            self._fail_async_shot(str(exc))

    def _start_file_work(self, mode, payload):
        from qtpy.QtCore import QThread
        from change_prism.batch_import.dialog import (
            BatchFileUiBridge,
            BatchFileWorker,
        )

        state = self._import_state
        parent = state["data"].get("parent") if state else None
        thread = QThread(parent)
        worker = BatchFileWorker(self.file_processor, mode, payload)
        worker.moveToThread(thread)
        job = {
            "thread": thread,
            "worker": worker,
            "mode": mode,
        }
        bridge = BatchFileUiBridge(
            parent,
            on_finished=lambda result: self._file_work_finished(
                job,
                result,
            ),
            on_failed=lambda message: self._file_work_failed(
                job,
                message,
            ),
            on_thread_finished=lambda: self._cleanup_file_job(job),
        )
        job["bridge"] = bridge
        self._file_job = job

        thread.started.connect(worker.run)
        worker.finished.connect(bridge.work_finished)
        worker.failed.connect(bridge.work_failed)
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(bridge.thread_finished)
        thread.start()

    def _file_work_finished(self, job, result):
        state = self._import_state
        if state is None:
            return
        try:
            if job["mode"] == "product":
                current = state["current"]
                current["shot_data"] = result
                self.file_processor.finalize_product(
                    current["prepared"],
                    result,
                )
                copies = self.file_processor.prepare_review_copies(
                    current["entity"],
                    result,
                )
                if copies:
                    self._start_file_work("review", copies)
                    return
            self._complete_async_shot()
        except Exception as exc:
            self._fail_async_shot(str(exc))

    def _file_work_failed(self, job, message):
        del job
        self._fail_async_shot(message)

    def _cleanup_file_job(self, job):
        if self._file_job is job:
            self._file_job = None
        job["thread"].deleteLater()
        job["bridge"].deleteLater()

    def _complete_async_shot(self):
        state = self._import_state
        if state is None:
            return
        current = state["current"] or {}
        shot_data = current.get("shot_data")
        if shot_data is not None:
            state["shot_data_list"].append(shot_data)
        state["success"] += 1
        state["current"] = None
        QTimer.singleShot(0, self._advance_async_import)

    def _fail_async_shot(self, message):
        state = self._import_state
        if state is None:
            return
        current = state.get("current") or {}
        item = current.get("item", {})
        cleanup_errors = []
        for cleanup, payload in (
            (
                self.file_processor.cleanup_prepared_product,
                current.get("prepared"),
            ),
        ):
            if not payload:
                continue
            try:
                cleanup(payload)
            except Exception as exc:
                cleanup_errors.append(str(exc))
        if cleanup_errors:
            message = "%s | Cleanup failed: %s" % (
                message,
                "; ".join(cleanup_errors),
            )
        state["failures"].append(
            {
                "episode": item.get("episode", ""),
                "sequence": item.get("sequence", ""),
                "shot": item.get("shot", ""),
                "server_dir": item.get("server_dir", ""),
                "error": str(message),
            }
        )
        state["current"] = None
        QTimer.singleShot(0, self._advance_async_import)

    def _finish_async_import(self):
        state = self._import_state
        if state is None:
            return
        self._import_state = None
        failures = state["failures"]
        try:
            failure_report = write_failure_report(
                self.core,
                state["project_name"],
                failures,
            )
        except OSError:
            failure_report = ""
        summary = {
            "project": state["project_name"],
            "total": len(state["selected"]),
            "create_only": state["create_only"],
            "copy_to_local": state["copy_to_local"],
            "pdg_enabled": (
                state["pdg_enabled"]
                and not state["create_only"]
                and bool(state["shot_data_list"])
            ),
            "failure_report": failure_report,
        }
        state["finished_callback"](
            self._build_import_result(
                state["success"],
                len(failures),
                failures,
                summary,
                state["shot_data_list"],
                project_loaded=state["project_loaded"],
            )
        )

    def add_shot_context_menu(self, origin, menu, _index):
        tree = getattr(origin, "tw_tree", None)
        if tree is None:
            return
        selected = tree.selectedItems()
        if not selected:
            return

        submenu = QMenu("Open Server Folder", menu)
        menu.addMenu(submenu)
        entries = [
            (
                STEP_LABELS.get("%s/%s" % pair, pair[1]),
                "%s/%s" % pair,
            )
            for pair in SERVER_STEPS
        ]
        entries.append(("Shot Root", ""))
        for label, subdir in entries:
            action = QAction(label, submenu)
            action.triggered.connect(
                lambda checked=False, path=subdir: (
                    self._open_server_subdir(selected, path)
                )
            )
            submenu.addAction(action)

    @staticmethod
    def _build_import_result(
        success,
        fail,
        failures,
        summary,
        shot_data_list,
        project_loaded=False,
        error="",
    ):
        return {
            "success": success,
            "fail": fail,
            "failures": failures,
            "summary": summary,
            "shot_data_list": shot_data_list,
            "project_loaded": project_loaded,
            "error": error,
        }

    def _on_batch_import_finished(self, dialog, result):
        result = result or {}
        if result.get("error"):
            self.core.popup(
                "Error during project creation:\n\n%s"
                % result["error"],
                severity="error",
                parent=dialog,
            )

        summary = result.get("summary", {})
        shot_data_list = result.get("shot_data_list", [])
        if summary.get("pdg_enabled") and shot_data_list:
            from change_prism.batch_import.pdg import PDGProcessor

            if (
                self._pdg_processor is not None
                and self._pdg_processor.is_running()
            ):
                self.core.popup(
                    "PDG FBX Convert is already running. "
                    "This batch was not launched.",
                    severity="warning",
                    parent=dialog,
                )
            else:
                dialog.set_status("Launching PDG FBX Convert...")
                self._pdg_processor = PDGProcessor(self.core)
                self._pdg_processor.run(
                    shot_data_list, summary.get("project", "")
                )

        if result.get("project_loaded"):
            dialog.set_status("Opening Project Browser...")
            if not getattr(self.core, "pb", None):
                self.core.projectBrowser()
            else:
                self.core.pb.show()
                self.core.pb.refreshUI()

        dialog.on_create_finished(
            result.get("success", 0),
            result.get("fail", 0),
            result.get("failures", []),
            summary,
        )

    def _set_project_departments(self):
        setter = getattr(self.core.projects, "setDepartments", None)
        if not callable(setter):
            return
        departments = [
            {
                "name": info["name"],
                "abbreviation": code,
                "defaultTasks": [info["task"]],
            }
            for code, info in self.DEPARTMENTS.items()
        ]
        setter("shot", departments)

    def _create_single_shot(self, item, shots_cache=None):
        entity = {
            "type": "shot",
            "episode": item["episode"],
            "sequence": item["episode"],
            "shot": "%s_%s"
            % (item["sequence"], item["shot"]),
        }
        sequence = entity["sequence"]
        if shots_cache is not None:
            if sequence not in shots_cache:
                shots_cache[sequence] = list(
                    self.core.entities.getShots(
                        sequence=sequence
                    )
                    or []
                )
            existing = shots_cache[sequence]
        else:
            existing = self.core.entities.getShots(
                sequence=sequence
            )
        found = next(
            (
                shot
                for shot in existing
                if shot.get("shot") == entity["shot"]
            ),
            None,
        )

        frame_range = item.get("frame_range") or [1001, 1100]
        if not found:
            created = self.core.entities.createEntity(
                entity,
                frameRange=frame_range,
                silent=True,
            )
            if isinstance(created, dict):
                entity = created.get("entity", entity)
            self._ensure_departments(entity)
            if shots_cache is not None:
                existing.append(entity)
            return entity

        self.core.entities.setShotRange(
            found, frame_range[0], frame_range[1]
        )
        return found

    def _ensure_departments(self, entity):
        presets = self._get_preset_scenes()
        for department, info in self.DEPARTMENTS.items():
            try:
                self.core.entities.createDepartment(
                    department, entity, createCat=False
                )
            except Exception as exc:
                if not self._is_already_exists_error(exc):
                    raise
            try:
                self.core.entities.createCategory(
                    entity, department, info["task"]
                )
            except Exception as exc:
                if not self._is_already_exists_error(exc):
                    raise
            preset = self._find_preset(
                presets, info["ext"], info["software"]
            )
            if preset:
                self._create_scene_from_preset(
                    entity, preset, department, info["task"]
                )

    @staticmethod
    def _is_already_exists_error(exc):
        message = str(exc).lower()
        return "already exist" in message or "已存在" in message

    def _get_preset_scenes(self):
        if self._preset_scenes_cache is None:
            self._preset_scenes_cache = list(
                self.core.entities.getPresetScenes() or []
            )
        return self._preset_scenes_cache

    @staticmethod
    def _find_preset(presets, extension, software):
        for preset in presets or []:
            if isinstance(preset, dict):
                path = str(preset.get("path") or "")
                label = str(preset.get("label") or "")
            else:
                path = str(preset or "")
                label = str(preset or "")
            if not path.lower().endswith(extension.lower()):
                continue
            if label and software.lower() not in label.lower():
                continue
            return {"path": path, "label": label}
        return None

    def _create_scene_from_preset(
        self, entity, preset, department, task
    ):
        create = getattr(
            self.core.entities, "createSceneFromPreset", None
        )
        if not callable(create):
            return None
        preset_path = str(preset.get("path") or "")
        comment = (
            str(preset.get("label") or "") or "chAngE_Prism"
        )
        try:
            return create(
                entity,
                preset_path,
                department,
                task,
                comment=comment,
            )
        except TypeError:
            pass
        return create(entity, preset_path, department, task)

    def _open_server_subdir(self, selected_items, subdir):
        from change_prism.config import get_server_root

        self.plugin.serverRoot = get_server_root(self.core)
        opened = 0
        for item in selected_items:
            shot_data = (
                item.data(0, Qt.UserRole)
                if hasattr(item, "data")
                else None
            )
            if not shot_data:
                continue
            sequence = (
                shot_data.get("sequence")
                or shot_data.get("episode")
                or ""
            ).strip()
            project = str(
                getattr(self.core, "projectName", "") or ""
            ).strip()
            scene, separator, shot_name = str(
                shot_data.get("shot") or ""
            ).partition("_")
            if not separator:
                scene = ""
                shot_name = ""
            scene = scene.strip()
            shot_name = shot_name.strip()
            if not all((sequence, project, scene, shot_name)):
                continue
            path = os.path.join(
                self.plugin.serverRoot,
                project,
                "publish",
                "shot",
                sequence,
                scene,
                shot_name,
                subdir,
            )
            if os.path.exists(path):
                QDesktopServices.openUrl(
                    QUrl.fromLocalFile(path)
                )
                opened += 1
        if not opened:
            self.core.popup(
                "Server folder not found for the selected shots.",
                severity="warning",
            )


class _NullReporter(object):
    def set_status(self, _text):
        pass

    def update_progress(self, _value):
        pass
