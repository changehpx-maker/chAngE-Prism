import os
import shutil

from qtpy.QtCore import Qt, QUrl
from qtpy.QtGui import QDesktopServices
from qtpy.QtWidgets import QAction, QMenu


class BatchImportController:
    DEPARTMENTS = {
        "FX": {"name": "Effects", "ext": ".hip", "software": "Houdini"},
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
        self._preset_scenes_cache = None

    def open_dialog(self):
        from change_prism.batch_import.dialog import BatchImportDialog

        parent = self.core.pb if getattr(self.core, "pb", None) else None
        dialog = BatchImportDialog(
            self.core,
            self.plugin.serverRoot,
            create_callback=self._create_project_and_shots,
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
        for label, subdir in (
            ("Animation", "shot_motion/shot_animation"),
            ("Cloth Solution", "shot_solution/cloth_solution"),
            ("Hair Solution", "shot_solution/hair_solution"),
            ("Shot Root", ""),
        ):
            action = QAction(label, submenu)
            action.triggered.connect(
                lambda checked=False, path=subdir: self._open_server_subdir(
                    selected, path
                )
            )
            submenu.addAction(action)

    def _create_project_and_shots(self, data):
        dialog = data["dlg"]
        project_name = data["project_name"]
        project_path = data["project_path"]
        selected = data["selected"]

        try:
            config_path = os.path.join(
                project_path, "00_Pipeline", "project_config.json"
            )
            if os.path.exists(config_path):
                dialog.set_status("Opening existing project '%s'..." % project_name)
                self.core.projects.changeProject(config_path)
            else:
                dialog.set_status("Creating Prism project '%s'..." % project_name)
                config_path = self.core.projects.createProject(
                    name=project_name,
                    path=project_path,
                    preset="Default",
                    parent=dialog,
                )
                if not config_path:
                    dialog.on_create_finished(0, len(selected))
                    return

                dialog.set_status("Loading project '%s'..." % project_name)
                self.core.projects.changeProject(config_path)

            success = 0
            failed = 0
            failures = []
            shots_cache = {}
            for index, item in enumerate(selected):
                dialog.update_progress(index + 1)
                try:
                    self._create_single_shot(item, project_name, shots_cache)
                    success += 1
                except Exception as exc:
                    failed += 1
                    failures.append(
                        "%s/%s/%s: %s"
                        % (
                            item.get("episode", ""),
                            item.get("sequence", ""),
                            item.get("shot", ""),
                            str(exc),
                        )
                    )

            dialog.set_status("Opening Project Browser...")
            if not self.core.pb:
                self.core.projectBrowser()
            else:
                self.core.pb.show()
                self.core.pb.refreshUI()
            dialog.on_create_finished(success, failed, failures)
        except Exception as exc:
            self.core.popup(
                "Error during project creation:\n\n%s" % str(exc),
                severity="error",
                parent=dialog,
            )
            dialog.on_create_finished(0, len(selected))

    def _create_single_shot(self, item, project_name=None, shots_cache=None):
        entity = {
            "type": "shot",
            "sequence": item["episode"],
            "shot": "%s_%s" % (item["sequence"], item["shot"]),
        }

        sequence = entity["sequence"]
        if shots_cache is not None:
            if sequence not in shots_cache:
                shots_cache[sequence] = self.core.entities.getShots(
                    sequence=sequence
                )
            existing = shots_cache[sequence]
        else:
            existing = self.core.entities.getShots(sequence=sequence)
        found = next(
            (shot for shot in existing if shot.get("shot") == entity["shot"]),
            None,
        )

        frame_range = item.get("frame_range") or [1001, 1100]
        metadata = {
            "chAngE_server_project": {
                "show": True,
                "value": project_name or item.get("project_code", ""),
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
            self.core.entities.createEntity(
                entity,
                frameRange=frame_range,
                silent=True,
                metaData=metadata,
            )
            self._ensure_departments(entity)
        else:
            entity = found
            self.core.entities.setShotRange(
                entity, frame_range[0], frame_range[1]
            )
            self.core.entities.setMetaData(entity=entity, metaData=metadata)

        mov_paths = []
        for step in item.get("steps", []):
            mov_paths.extend(step.get("files", {}).get("mov_files", []))
        if mov_paths:
            self._ingest_mov_as_media(entity, mov_paths)

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
        create = getattr(self.core.entities, "createSceneFromPreset", None)
        if not callable(create):
            return None
        preset_path = str(preset.get("path") or "")
        comment = str(preset.get("label") or "") or "chAngE_Prism"
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
        identifier = "review"
        self.core.mediaProducts.createIdentifier(
            entity,
            identifier,
            identifierType="playblasts",
            location="global",
        )

        context = entity.copy()
        context["identifier"] = identifier
        context["identifierType"] = "playblasts"
        context["mediaType"] = "playblasts"
        current = self.core.mediaProducts.getHighestMediaVersion(
            context, getExisting=True
        )
        version = self._next_media_version(
            entity, identifier, "playblasts", current
        )
        version_path = self.core.mediaProducts.createVersion(
            entity,
            identifier,
            version,
            identifierType="playblasts",
            location="global",
        )
        if not version_path:
            return

        os.makedirs(str(version_path), exist_ok=True)
        for source in mov_paths:
            shutil.copy2(
                source,
                os.path.join(str(version_path), os.path.basename(source)),
            )

    def _next_media_version(
        self, entity, identifier, media_type, current_version
    ):
        try:
            base = self.core.paths.getRenderProductBasePaths()["global"]
            context = entity.copy()
            context["identifier"] = identifier
            context["mediaType"] = media_type
            context["version"] = current_version
            context["task"] = "none"
            context["user"] = self.core.user
            context["project_path"] = base
            key = (
                "playblastVersions"
                if media_type == "playblasts"
                else "renderVersions"
            )
            existing = self.core.projects.getResolvedProjectStructurePath(
                key, context
            )
            if existing and os.path.exists(str(existing)):
                return self._increment_version(current_version)
            return current_version
        except Exception:
            return self._increment_version(current_version)

    def _increment_version(self, version):
        version_format = getattr(self.core, "versionFormat", "v%04d")
        try:
            number = int(str(version).lstrip("vV")) + 1
        except (ValueError, TypeError):
            number = self.core.lowestVersion + 1
        return version_format % number

    def _open_server_subdir(self, selected_items, subdir):
        opened = 0
        for item in selected_items:
            shot_data = (
                item.data(0, Qt.UserRole) if hasattr(item, "data") else None
            )
            if not shot_data:
                continue
            sequence = (shot_data.get("sequence") or "").strip()
            if not sequence:
                continue
            metadata = self._read_metadata_from_item(shot_data)
            scene = metadata.get("chAngE_server_scene", "")
            shot_name = metadata.get("chAngE_server_shot", "")
            project = metadata.get("chAngE_server_project", "")
            if not project or not scene or not shot_name:
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
                QDesktopServices.openUrl(QUrl.fromLocalFile(path))
                opened += 1

        if opened == 0:
            self.core.popup(
                "Server folder not found for the selected shots.",
                severity="warning",
            )

    def _read_metadata_from_item(self, shot_data):
        metadata = {}
        raw = self.core.entities.getMetaData(shot_data)
        for key in self.SERVER_META_KEYS:
            value = raw.get(key, {})
            if isinstance(value, dict):
                metadata[key] = value.get("value", "")
            else:
                metadata[key] = str(value) if value else ""
        return metadata
