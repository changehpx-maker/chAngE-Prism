import os

from qtpy.QtCore import Qt, QUrl
from qtpy.QtGui import QDesktopServices
from qtpy.QtWidgets import QAction, QMenu

from change_prism.batch_import.file_processor import FileProcessor
from change_prism.batch_import.scanner import SERVER_STEPS, STEP_LABELS
from change_prism.batch_import.service import write_failure_report


class BatchImportController(object):
    DEPARTMENTS = {
        "FX": {
            "name": "Effects",
            "ext": ".hip",
            "software": "Houdini",
        },
        "Lighting": {
            "name": "Lighting",
            "ext": ".hip",
            "software": "Houdini",
        },
        "Compositing": {
            "name": "Compositing",
            "ext": ".nk",
            "software": "Nuke",
        },
    }

    SERVER_META_KEYS = (
        "chAngE_server_project",
        "chAngE_server_scene",
        "chAngE_server_shot",
    )

    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin
        self.file_processor = FileProcessor(core)
        self._preset_scenes_cache = None
        self._pdg_processor = None

    def open_dialog(self):
        from change_prism.batch_import.dialog import BatchImportDialog
        from change_prism.config import get_server_root

        parent = getattr(self.core, "pb", None)
        self.plugin.serverRoot = get_server_root(self.core)
        dialog = BatchImportDialog(
            self.core,
            self.plugin.serverRoot,
            create_callback=self._create_project_and_shots,
            finish_callback=self._on_batch_import_finished,
            parent=parent,
        )
        dialog.exec_()

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

    def _create_project_and_shots(self, data, reporter=None):
        project_name = data["project_name"]
        project_path = data["project_path"]
        selected = data["selected"]
        parent = data.get("parent")
        create_only = bool(data.get("create_only"))
        copy_to_local = bool(data.get("copy_to_local"))
        pdg_enabled = bool(data.get("pdg_enabled"))
        reporter = reporter or _NullReporter()
        project_loaded = False
        shot_data_list = []

        try:
            config_path = os.path.join(
                project_path, "00_Pipeline", "project_config.json"
            )
            if os.path.exists(config_path):
                reporter.set_status(
                    "Opening existing project '%s'..." % project_name
                )
                self.core.projects.changeProject(config_path)
                project_loaded = True
            else:
                reporter.set_status(
                    "Creating Prism project '%s'..." % project_name
                )
                config_path = self.core.projects.createProject(
                    name=project_name,
                    path=project_path,
                    preset="Default",
                    parent=parent,
                )
                if not config_path:
                    return self._build_import_result(
                        0,
                        len(selected),
                        [],
                        {
                            "project": project_name,
                            "total": len(selected),
                        },
                        [],
                    )
                reporter.set_status(
                    "Loading project '%s'..." % project_name
                )
                self.core.projects.changeProject(config_path)
                project_loaded = True
                self._set_project_departments()

            success = 0
            failures = []
            shots_cache = {}
            for index, item in enumerate(selected):
                reporter.update_progress(index + 1)
                try:
                    entity = self._create_single_shot(
                        item, project_name, shots_cache
                    )
                    if not create_only:
                        shot_data_list.append(
                            self.file_processor.process(
                                item,
                                entity,
                                project_name,
                                copy_to_local,
                            )
                        )
                    success += 1
                except Exception as exc:
                    failures.append(
                        {
                            "episode": item.get("episode", ""),
                            "sequence": item.get("sequence", ""),
                            "shot": item.get("shot", ""),
                            "server_dir": item.get("server_dir", ""),
                            "error": str(exc),
                        }
                    )

            try:
                failure_report = write_failure_report(
                    self.core, project_name, failures
                )
            except OSError:
                failure_report = ""
            summary = {
                "project": project_name,
                "total": len(selected),
                "create_only": create_only,
                "copy_to_local": copy_to_local,
                "pdg_enabled": (
                    pdg_enabled
                    and not create_only
                    and bool(shot_data_list)
                ),
                "failure_report": failure_report,
            }
            return self._build_import_result(
                success,
                len(failures),
                failures,
                summary,
                shot_data_list,
                project_loaded=project_loaded,
            )
        except Exception as exc:
            return self._build_import_result(
                0,
                len(selected),
                [],
                {
                    "project": project_name,
                    "total": len(selected),
                },
                shot_data_list,
                project_loaded=project_loaded,
                error=str(exc),
            )

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
                "defaultTasks": [info["name"]],
            }
            for code, info in self.DEPARTMENTS.items()
        ]
        setter("shot", departments)

    def _create_single_shot(
        self, item, project_name=None, shots_cache=None
    ):
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
        metadata = {
            "chAngE_server_project": {
                "show": True,
                "value": (
                    project_name or item.get("project_code", "")
                ),
            },
            "chAngE_server_scene": {
                "show": False,
                "value": item["sequence"],
            },
            "chAngE_server_shot": {
                "show": False,
                "value": item["shot"],
            },
        }

        if not found:
            created = self.core.entities.createEntity(
                entity,
                frameRange=frame_range,
                silent=True,
                metaData=metadata,
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
        self.core.entities.setMetaData(
            entity=found, metaData=metadata
        )
        return found

    def _ensure_departments(self, entity):
        presets = self._get_preset_scenes()
        for department, info in self.DEPARTMENTS.items():
            try:
                self.core.entities.createDepartment(
                    department, entity, createCat=False
                )
            except Exception:
                pass
            try:
                self.core.entities.createCategory(
                    entity, department, info["name"]
                )
            except Exception:
                pass
            preset = self._find_preset(
                presets, info["ext"], info["software"]
            )
            if preset:
                self._create_scene_from_preset(
                    entity, preset, department, info["name"]
                )

    def _get_preset_scenes(self):
        if self._preset_scenes_cache is None:
            try:
                self._preset_scenes_cache = list(
                    self.core.entities.getPresetScenes() or []
                )
            except Exception:
                self._preset_scenes_cache = []
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
        try:
            return create(entity, preset_path, department, task)
        except Exception:
            return None

    def _ingest_mov_as_media(self, entity, mov_paths):
        return self.file_processor.import_media_files(
            entity, mov_paths
        )

    def _next_media_version(
        self, entity, identifier, media_type, current_version
    ):
        return self.file_processor._next_media_version(
            entity, identifier, media_type, current_version
        )

    def _increment_version(self, version):
        return self.file_processor._increment_version(version)

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
            sequence = (shot_data.get("sequence") or "").strip()
            metadata = self._read_metadata_from_item(shot_data)
            project = metadata.get(
                "chAngE_server_project", ""
            )
            scene = metadata.get("chAngE_server_scene", "")
            shot_name = metadata.get(
                "chAngE_server_shot", ""
            )
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

    def _read_metadata_from_item(self, shot_data):
        metadata = {}
        raw = self.core.entities.getMetaData(shot_data)
        for key in self.SERVER_META_KEYS:
            value = raw.get(key, {})
            metadata[key] = (
                value.get("value", "")
                if isinstance(value, dict)
                else str(value or "")
            )
        return metadata


class _NullReporter(object):
    def set_status(self, _text):
        pass

    def update_progress(self, _value):
        pass
