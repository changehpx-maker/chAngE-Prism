import os
import shutil

from change_prism.batch_import.scanner import (
    SERVER_STEPS,
    STEP_LABELS,
    collect_step_files,
    parse_xml_attributes,
)


_FILE_KEY_MAP = {
    "fbx_files": "fbx",
    "mov_files": "review",
    "abc_files": "abc",
    "xml_files": None,
}
ANIMATION_LABEL = STEP_LABELS["shot_motion/shot_animation"]
_SENSITIVE_CONTEXT_KEYS = {
    "user_phone",
    "user_name",
    "user_icon",
}


class FileProcessor(object):
    PRODUCT_NAME = "published_ref"

    def __init__(self, core):
        self.core = core

    def process(self, item, entity, project_name, copy_to_local):
        prepared = self.prepare(
            item,
            entity,
            project_name,
            copy_to_local,
        )
        try:
            shot_data = self.build_product_data(prepared)
            self.finalize_product(prepared, shot_data)
            review_copies = self.prepare_review_copies(
                entity, shot_data
            )
            self.execute_review_copies(review_copies)
            return shot_data
        except Exception as exc:
            cleanup_errors = []
            try:
                self.cleanup_prepared_product(prepared)
            except Exception as cleanup_exc:
                cleanup_errors.append(str(cleanup_exc))
            if cleanup_errors:
                raise RuntimeError(
                    "%s | Cleanup failed: %s"
                    % (exc, "; ".join(cleanup_errors))
                )
            raise

    def prepare(
        self,
        item,
        entity,
        project_name,
        copy_to_local,
    ):
        del project_name
        server_dir = item.get("server_dir", "")
        product_root = self.core.products.createProduct(
            entity, self.PRODUCT_NAME
        )
        version = self.core.products.getNextAvailableVersion(
            entity, self.PRODUCT_NAME
        )
        version_dir = os.path.join(str(product_root), str(version))
        if os.path.exists(version_dir):
            raise FileExistsError(
                "Product version already exists: %s" % version_dir
            )
        os.makedirs(version_dir)
        return {
            "item": item,
            "entity": entity,
            "copy_to_local": bool(copy_to_local),
            "server_dir": server_dir,
            "product_root": str(product_root),
            "version": version,
            "version_dir": version_dir,
        }

    def build_product_data(self, prepared):
        item = prepared["item"]
        server_dir = prepared["server_dir"]
        version_dir = prepared["version_dir"]
        if prepared["copy_to_local"] and server_dir:
            self._copy_server_files(server_dir, version_dir)
            shot_data = self._build_copied_shot_data(
                item,
                server_dir,
                version_dir,
            )
        else:
            shot_data = self._build_shot_data(item)

        shot_data.update(
            {
                "product": self.PRODUCT_NAME,
                "product_version": prepared["version"],
                "product_root_path": prepared["product_root"],
                "products_path": version_dir,
            }
        )
        return shot_data

    def finalize_product(self, prepared, shot_data):
        self._write_product_version(
            prepared["version_dir"],
            shot_data,
            prepared["version"],
        )
        self._apply_shot_attributes(prepared["entity"], shot_data)

    @staticmethod
    def cleanup_prepared_product(prepared):
        if not prepared:
            return
        product_root = os.path.abspath(
            os.path.normpath(prepared["product_root"])
        )
        version_dir = os.path.abspath(
            os.path.normpath(prepared["version_dir"])
        )
        expected_version = str(prepared["version"])
        if (
            os.path.normcase(os.path.dirname(version_dir))
            != os.path.normcase(product_root)
            or os.path.basename(version_dir) != expected_version
        ):
            raise ValueError(
                "Refusing to clean unexpected product path: %s"
                % version_dir
            )
        if os.path.isdir(version_dir):
            shutil.rmtree(version_dir)

    def _build_copied_shot_data(
        self,
        item,
        server_dir,
        version_dir,
    ):
        if not item.get("steps"):
            return self._build_shot_data(
                item,
                source_dir=version_dir,
            )

        copied_item = dict(item)
        copied_steps = []
        for step in item.get("steps", []):
            copied_step = dict(step)
            copied_files = {}
            for key, paths in step.get("files", {}).items():
                copied_files[key] = [
                    self._retarget_copied_path(
                        path,
                        server_dir,
                        version_dir,
                    )
                    for path in paths
                ]
            copied_step["files"] = copied_files
            copied_steps.append(copied_step)
        copied_item["steps"] = copied_steps
        return self._build_shot_data(
            copied_item,
            file_root=version_dir,
        )

    @staticmethod
    def _retarget_copied_path(path, server_dir, version_dir):
        source = os.path.abspath(os.path.normpath(path))
        server_root = os.path.abspath(os.path.normpath(server_dir))
        try:
            common = os.path.commonpath([source, server_root])
            if os.path.normcase(common) != os.path.normcase(server_root):
                return path
        except (OSError, ValueError):
            return path
        return os.path.join(
            version_dir,
            os.path.relpath(source, server_root),
        )

    @staticmethod
    def _copy_server_files(server_dir, version_dir):
        for category, code in SERVER_STEPS:
            source = os.path.join(server_dir, category, code)
            if not os.path.isdir(source):
                continue
            destination = os.path.join(version_dir, category, code)
            shutil.copytree(source, destination, dirs_exist_ok=True)

    @staticmethod
    def _make_step_entry(
        files, xml_path=None, xml_attributes=None, frame_range=None
    ):
        entry = {}
        for source_key, values in files.items():
            target_key = _FILE_KEY_MAP.get(source_key, source_key)
            if target_key is not None:
                entry[target_key] = values
        if xml_path and xml_attributes is not None:
            entry["xml"] = {
                "path": xml_path,
                "attributes": FileProcessor._redact_xml_attributes(
                    xml_attributes
                ),
                "frame_range": frame_range,
            }
        return entry

    @staticmethod
    def _redact_xml_attributes(attributes):
        result = dict(attributes or {})
        for key in _SENSITIVE_CONTEXT_KEYS:
            result.pop(key, None)
        context = result.get("context")
        if isinstance(context, dict):
            context = dict(context)
            for key in _SENSITIVE_CONTEXT_KEYS:
                context.pop(key, None)
            result["context"] = context
            if not result.get("project_code") and context.get(
                "project_code"
            ):
                result["project_code"] = context["project_code"]
        return result

    @staticmethod
    def _make_shot_data(item, steps, frame_range, file_root=None):
        return {
            "project_code": item.get("project_code", ""),
            "episode": item.get("episode", ""),
            "sequence": item.get("sequence", ""),
            "shot": item.get("shot", ""),
            "prism_sequence": item.get("episode", ""),
            "prism_shot": "%s_%s"
            % (item.get("sequence", ""), item.get("shot", "")),
            "source_server_dir": item.get("server_dir", ""),
            "source_file_root": file_root or item.get("server_dir", ""),
            "frame_range": frame_range,
            "steps": steps,
        }

    def _build_shot_data(
        self,
        item,
        source_dir=None,
        file_root=None,
    ):
        pairs = (
            self._iter_fs_steps(source_dir)
            if source_dir
            else self._iter_scan_steps(item)
        )
        steps = {}
        for label, files in pairs:
            xml_files = files.get("xml_files", [])
            if xml_files:
                parsed = parse_xml_attributes(xml_files[0])
                entry = self._make_step_entry(
                    files,
                    xml_files[0],
                    parsed["attributes"],
                    parsed["frame_range"],
                )
            else:
                entry = self._make_step_entry(files)
            if entry:
                steps[label] = entry

        frame_range = (
            steps.get(ANIMATION_LABEL, {})
            .get("xml", {})
            .get("frame_range")
            if source_dir
            else item.get("frame_range")
        )
        return self._make_shot_data(
            item,
            steps,
            frame_range,
            file_root=file_root or source_dir,
        )

    @staticmethod
    def _iter_fs_steps(source_dir):
        for category, code in SERVER_STEPS:
            step_dir = os.path.join(source_dir, category, code)
            if os.path.isdir(step_dir):
                yield (
                    STEP_LABELS.get("%s/%s" % (category, code), code),
                    collect_step_files(step_dir, code),
                )

    @staticmethod
    def _iter_scan_steps(item):
        for step in item.get("steps", []):
            yield step.get("label", ""), step.get("files", {})

    def _write_product_version(self, version_dir, shot_data, version):
        details = {
            "product": self.PRODUCT_NAME,
            "version": version,
            "username": getattr(self.core, "username", ""),
            "user": getattr(self.core, "user", ""),
        }
        details.update(shot_data)
        self.core.saveVersionInfo(filepath=version_dir, details=details)

    def _apply_shot_attributes(self, entity, shot_data):
        frame_range = shot_data.get("frame_range")
        if frame_range:
            self.core.entities.setShotRange(
                entity, frame_range[0], frame_range[1]
            )

    def import_media_files(self, entity, paths):
        shot_data = {"steps": {"Review": {"review": list(paths)}}}
        self._import_media(entity, shot_data)

    def _import_media(self, entity, shot_data):
        copies = self.prepare_review_copies(entity, shot_data)
        self.execute_review_copies(copies)

    def prepare_review_copies(self, entity, shot_data):
        media_files = []
        for label, step in shot_data.get("steps", {}).items():
            for path in step.get("review", []):
                media_files.append((label, path))
        if not media_files:
            return []

        identifier = "review"
        self.core.mediaProducts.createIdentifier(
            entity,
            identifier,
            identifierType="playblasts",
            location="global",
        )
        context = entity.copy()
        context.update(
            {
                "identifier": identifier,
                "identifierType": "playblasts",
                "mediaType": "playblasts",
            }
        )
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
            return []

        duplicates = self._duplicate_basenames(
            path for _label, path in media_files
        )
        used = set()
        copies = []
        for label, source in media_files:
            name = self._review_media_name(label, source, duplicates, used)
            copies.append(
                (source, os.path.join(str(version_path), name))
            )
        return copies

    @staticmethod
    def execute_review_copies(copies):
        completed = []
        try:
            for source, destination in copies:
                if os.path.exists(destination):
                    raise FileExistsError(
                        "Review destination already exists: %s"
                        % destination
                    )
                os.makedirs(
                    os.path.dirname(destination), exist_ok=True
                )
                shutil.copy2(source, destination)
                completed.append((source, destination))
        except Exception:
            FileProcessor.cleanup_review_copies(completed)
            raise

    @staticmethod
    def cleanup_review_copies(copies):
        parents = set()
        for _source, destination in copies or []:
            destination = os.path.abspath(os.path.normpath(destination))
            parents.add(os.path.dirname(destination))
            if os.path.isfile(destination):
                os.remove(destination)
        for parent in sorted(parents, key=len, reverse=True):
            try:
                os.rmdir(parent)
            except OSError:
                pass

    def _next_media_version(
        self, entity, identifier, media_type, current_version
    ):
        try:
            base = self.core.paths.getRenderProductBasePaths()["global"]
            context = entity.copy()
            context.update(
                {
                    "identifier": identifier,
                    "mediaType": media_type,
                    "version": current_version,
                    "task": "none",
                    "user": self.core.user,
                    "project_path": base,
                }
            )
            key = (
                "playblastVersions"
                if media_type == "playblasts"
                else "renderVersions"
            )
            existing = (
                self.core.projects.getResolvedProjectStructurePath(
                    key, context
                )
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
        except (TypeError, ValueError):
            number = getattr(self.core, "lowestVersion", 1) + 1
        return version_format % number

    @staticmethod
    def _duplicate_basenames(paths):
        counts = {}
        for path in paths:
            name = os.path.basename(path)
            counts[name] = counts.get(name, 0) + 1
        return {
            name for name, count in counts.items() if count > 1
        }

    @classmethod
    def _review_media_name(
        cls, step_label, source, duplicate_names, used_names
    ):
        basename = os.path.basename(source)
        if basename in duplicate_names:
            basename = "%s_%s" % (
                cls._safe_filename_part(step_label), basename
            )
        stem, extension = os.path.splitext(basename)
        candidate = basename
        index = 2
        while candidate in used_names:
            candidate = "%s_%02d%s" % (stem, index, extension)
            index += 1
        used_names.add(candidate)
        return candidate

    @staticmethod
    def _safe_filename_part(value):
        text = str(value or "review")
        safe = "".join(
            char
            if char.isalnum() or char in ("-", "_")
            else "_"
            for char in text
        )
        return safe.strip("_") or "review"
