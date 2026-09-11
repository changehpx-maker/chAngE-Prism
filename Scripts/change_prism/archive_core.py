from __future__ import unicode_literals

import json
import os
import re
import shutil


VERSION_PATTERN = re.compile(r"^v(\d{4,})$", re.IGNORECASE)


class ArchiveError(Exception):
    pass


def find_shot_root(source_scene):
    """Return the shot folder which owns a Scenefiles descendant."""
    if not source_scene:
        return ""

    current = os.path.abspath(os.fspath(source_scene))
    if os.path.isfile(current):
        current = os.path.dirname(current)

    while True:
        if os.path.basename(current).lower() == "scenefiles":
            return os.path.dirname(current)

        parent = os.path.dirname(current)
        if parent == current:
            return ""
        current = parent


def infer_scene_context(source_scene):
    """Return department/task folders below the Scenefiles segment."""
    parts = [
        part
        for part in re.split(r"[\\/]+", str(source_scene or ""))
        if part
    ]
    for index, part in enumerate(parts):
        if part.lower() != "scenefiles":
            continue
        department = parts[index + 1] if len(parts) > index + 1 else ""
        task = parts[index + 2] if len(parts) > index + 2 else ""
        return {"department": department, "task": task}
    return {"department": "", "task": ""}


def get_task_archive_root(archive_root, department, task):
    """Return the Task-scoped root; department is metadata only."""
    archive_root = os.path.abspath(os.fspath(archive_root))
    task = _scope_component(task)
    if not task:
        return archive_root
    return os.path.join(archive_root, task)


def get_next_task_archive_version(archive_root, department, task):
    """Return the next version for a Task, independent of department."""
    task = str(task or "")
    if not task:
        return get_next_archive_version(archive_root)

    highest = 0
    for version in scan_archive_versions(archive_root):
        if (
            str(version.get("task", "")).casefold()
            != task.casefold()
        ):
            continue
        highest = max(highest, int(version.get("task_number", 0)))
    return "v%04d" % (highest + 1)


def reserve_task_version_directory(archive_root, department, task):
    version_root = get_task_archive_root(
        archive_root, department, task
    )
    os.makedirs(version_root, exist_ok=True)
    version = get_next_task_archive_version(
        archive_root, department, task
    )
    while True:
        version_path = os.path.join(version_root, version)
        try:
            os.mkdir(version_path)
            return version, version_path
        except FileExistsError:
            number = int(VERSION_PATTERN.match(version).group(1)) + 1
            version = "v%04d" % number


def get_next_archive_version(archive_root):
    highest = 0
    if os.path.isdir(archive_root):
        for name in os.listdir(archive_root):
            match = VERSION_PATTERN.match(name)
            if not match:
                continue
            if os.path.isdir(os.path.join(archive_root, name)):
                highest = max(highest, int(match.group(1)))
    return "v%04d" % (highest + 1)


def reserve_version_directory(archive_root):
    os.makedirs(archive_root, exist_ok=True)
    version = get_next_archive_version(archive_root)
    while True:
        version_path = os.path.join(archive_root, version)
        try:
            os.mkdir(version_path)
            return version, version_path
        except FileExistsError:
            number = int(VERSION_PATTERN.match(version).group(1)) + 1
            version = "v%04d" % number


def file_fingerprint(path):
    stat_result = os.stat(path)
    return {
        "size": stat_result.st_size,
        "mtime_ns": getattr(
            stat_result,
            "st_mtime_ns",
            int(stat_result.st_mtime * 1000000000),
        ),
    }


def get_available_bytes(path):
    probe = os.path.abspath(path)
    while not os.path.exists(probe):
        parent = os.path.dirname(probe)
        if parent == probe:
            return None
        probe = parent
    try:
        return shutil.disk_usage(probe).free
    except OSError:
        return None


def format_bytes(value):
    if value is None:
        return "Not recorded"
    size = float(value)
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    for unit in units:
        if size < 1024.0 or unit == units[-1]:
            if unit == "B":
                return "%d B" % int(size)
            return "%.1f %s" % (size, unit)
        size /= 1024.0


def cleanup_failed_version(version_path):
    if not version_path or not os.path.isdir(version_path):
        return ""
    try:
        shutil.rmtree(version_path)
    except OSError as exc:
        return str(exc)
    return ""


def delete_archive_version(version_path, archive_root):
    archive_root = os.path.abspath(os.fspath(archive_root))
    version_path = os.path.abspath(os.fspath(version_path))
    version_name = os.path.basename(version_path)

    if not VERSION_PATTERN.match(version_name):
        raise ArchiveError("The selected folder is not an Archive version.")
    if _path_key(os.path.dirname(version_path)) != _path_key(archive_root):
        raise ArchiveError("The selected Archive is outside the expected root.")
    if not os.path.isdir(archive_root) or not os.path.isdir(version_path):
        raise ArchiveError("The selected Archive version no longer exists.")

    resolved_root = os.path.realpath(archive_root)
    resolved_version = os.path.realpath(version_path)
    if _path_key(os.path.dirname(resolved_version)) != _path_key(resolved_root):
        raise ArchiveError("The selected Archive resolves outside the expected root.")
    if os.path.isfile(os.path.join(version_path, ".incomplete")):
        raise ArchiveError("Incomplete Archive versions cannot be deleted.")
    manifest_path = os.path.join(version_path, "manifest.json")
    if os.path.isfile(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as handle:
                manifest = json.load(handle)
            if str(manifest.get("status", "")).lower() == "incomplete":
                raise ArchiveError(
                    "Incomplete Archive versions cannot be deleted."
                )
        except (OSError, ValueError, TypeError):
            pass

    shutil.rmtree(version_path)
    return {"version": version_name, "deleted_path": version_path}


def calculate_archive_payload_stats(version_path, copy_jobs):
    recorded_count = 0
    recorded_bytes = 0
    has_recorded = isinstance(copy_jobs, list)
    for job in copy_jobs or []:
        if (
            not isinstance(job, dict)
            or job.get("file_count") is None
            or job.get("total_bytes") is None
        ):
            has_recorded = False
            break
        recorded_count += int(job["file_count"])
        recorded_bytes += int(job["total_bytes"])
    if has_recorded:
        return recorded_count, recorded_bytes

    dependencies = os.path.join(version_path, "dependencies")
    sequences = os.path.join(version_path, "sequences")
    payload_root = dependencies if os.path.isdir(dependencies) else sequences
    if not os.path.isdir(payload_root):
        return 0, 0

    file_count = 0
    total_bytes = 0
    for current, _directories, filenames in os.walk(payload_root):
        for filename in filenames:
            path = os.path.join(current, filename)
            try:
                total_bytes += os.path.getsize(path)
                file_count += 1
            except OSError:
                pass
    return file_count, total_bytes


def scan_archive_versions(archive_root, deep_health=True):
    versions = []
    if not os.path.isdir(archive_root):
        return versions

    for candidate in _iter_archive_version_directories(archive_root):
        versions.append(
            _scan_version(
                candidate["path"],
                candidate["name"],
                candidate["number"],
                scoped_department=candidate["department"],
                scoped_task=candidate["task"],
                version_scope=candidate["version_scope"],
                deep_health=deep_health,
            )
        )

    _assign_task_versions(versions)
    versions.sort(
        key=lambda item: (
            item.get("created_at", ""),
            item.get("storage_number", 0),
        ),
        reverse=True,
    )
    return versions


def _scan_version(
    version_path,
    version_name,
    number,
    scoped_department="",
    scoped_task="",
    version_scope="legacy",
    deep_health=True,
):
    manifest_path = os.path.join(version_path, "manifest.json")
    incomplete = os.path.isfile(os.path.join(version_path, ".incomplete"))
    manifest = {}
    manifest_valid = False
    if os.path.isfile(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as handle:
                manifest = json.load(handle)
            if not isinstance(manifest, dict):
                manifest = {}
            manifest_valid = _is_manifest_valid(manifest)
        except (OSError, ValueError, TypeError):
            manifest = {}

    application = str(manifest.get("application") or "nuke").lower()
    if application not in ("nuke", "houdini"):
        application = str(manifest.get("application") or "unknown").lower()

    if application == "houdini":
        scene_location_mismatch = False
        packaged_scene = _resolve_manifest_path(
            version_path,
            manifest.get("packaged_scene") or manifest.get("packaged_hip"),
        )
        if not packaged_scene or not os.path.isfile(packaged_scene):
            fallback_scene = _first_scene(
                version_path,
                (".hip", ".hiplc", ".hipnc"),
            )
            if not fallback_scene:
                fallback_scene = _first_scene(
                    os.path.join(version_path, "hip"),
                    (".hip", ".hiplc", ".hipnc"),
                )
            if fallback_scene:
                packaged_scene = fallback_scene
                scene_location_mismatch = True
        source_scene = manifest.get("source_scene") or manifest.get("source_hip", "")
        source_stat = manifest.get("source_scene_stat") or manifest.get(
            "source_hip_stat"
        )
        references = _manifest_dependency_items(
            manifest.get("dependencies")
        )
    else:
        scene_location_mismatch = False
        packaged_scene = _resolve_manifest_path(
            version_path, manifest.get("packaged_nk")
        )
        if not packaged_scene:
            packaged_scene = _first_scene(
                os.path.join(version_path, "nk"), (".nk",)
            )
        source_scene = manifest.get("source_nk", "")
        source_stat = manifest.get("source_nk_stat")
        references = _normalise_nuke_reads(manifest.get("reads"))

    inferred_context = infer_scene_context(source_scene)
    department = (
        manifest.get("department")
        or inferred_context["department"]
        or scoped_department
    )
    task = (
        manifest.get("task")
        or inferred_context["task"]
        or scoped_task
    )
    copy_jobs = manifest.get("copy_jobs")
    if not isinstance(copy_jobs, list):
        copy_jobs = []
    summary = manifest.get("summary")
    if not isinstance(summary, dict):
        summary = {}
    status = _health_status(
        version_path,
        packaged_scene,
        source_scene,
        source_stat,
        manifest,
        manifest_valid,
        incomplete,
        references,
        scene_location_mismatch,
        deep_health,
    )
    file_count = summary.get("file_count")
    total_bytes = summary.get("total_bytes")
    if file_count is None or total_bytes is None:
        file_count, total_bytes = calculate_archive_payload_stats(
            version_path, copy_jobs
        )

    return {
        "version": version_name,
        "number": number,
        "storage_version": version_name,
        "storage_number": number,
        "task_version": manifest.get("task_version", ""),
        "task_number": 0,
        "version_scope": manifest.get("version_scope") or version_scope,
        "scope_root": os.path.dirname(version_path),
        "path": version_path,
        "manifest_path": manifest_path,
        "manifest": manifest,
        "application": application,
        "packaged_scene": packaged_scene,
        "source_scene": source_scene,
        "packaged_nk": packaged_scene if application == "nuke" else "",
        "source_nk": source_scene if application == "nuke" else "",
        "packaged_hip": packaged_scene if application == "houdini" else "",
        "source_hip": source_scene if application == "houdini" else "",
        "created_by": manifest.get("created_by", ""),
        "created_at": manifest.get("created_at", ""),
        "department": department,
        "task": task,
        "scene_location_mismatch": scene_location_mismatch,
        "status": status,
        "reference_count": summary.get(
            "reference_count",
            summary.get("read_count", len(references)),
        ),
        "package_input_count": summary.get(
            "package_input_count",
            _classification_count(references, "Package Input"),
        ),
        "copy_job_count": summary.get("copy_job_count", len(copy_jobs)),
        "file_count": file_count,
        "total_bytes": total_bytes,
        "skipped_cache_count": summary.get(
            "skipped_cache_count",
            _classification_count(references, "Skipped Cache"),
        ),
        "skipped_missing_count": summary.get(
            "skipped_missing_count",
            _classification_count(references, "Skipped Missing"),
        ),
        "missing_count": summary.get(
            "missing_count",
            _classification_count(references, "Skipped Missing"),
        ),
        "skipped_count": summary.get(
            "skipped_count",
            _excluded_count(references),
        ),
        "hda_count": summary.get(
            "hda_count", len(manifest.get("external_hdas", []))
        ),
        "houdini_version": manifest.get("houdini_version", ""),
        "fps": manifest.get("fps"),
        "frame_range": manifest.get("frame_range", []),
        "references": references,
        "reads": references if application == "nuke" else [],
        "copy_jobs": copy_jobs,
        "external_hdas": manifest.get("external_hdas", []),
    }


def _is_manifest_valid(manifest):
    if not isinstance(manifest, dict):
        return False
    if not isinstance(manifest.get("copy_jobs", []), list):
        return False
    application = str(manifest.get("application") or "nuke").lower()
    if application == "houdini":
        return (
            manifest.get("schema_version") == 2
            and isinstance(manifest.get("dependencies", []), list)
            and bool(manifest.get("archive_version"))
            and isinstance(manifest.get("source_scene"), str)
            and isinstance(manifest.get("packaged_scene"), str)
            and bool(manifest.get("packaged_scene"))
        )
    return (
        "reads" in manifest
        and "copy_jobs" in manifest
        and isinstance(manifest.get("reads"), list)
        and isinstance(manifest.get("source_nk"), str)
        and isinstance(manifest.get("packaged_nk"), str)
        and bool(manifest.get("packaged_nk"))
    )


def _health_status(
    version_path,
    packaged_scene,
    source_scene,
    source_stat,
    manifest,
    manifest_valid,
    incomplete,
    references,
    scene_location_mismatch=False,
    deep_health=True,
):
    if (
        incomplete
        or str(manifest.get("status", "")).lower() == "incomplete"
        or not os.path.isfile(os.path.join(version_path, "manifest.json"))
    ):
        return "Incomplete"
    if not manifest_valid:
        return "Invalid Manifest"
    if not packaged_scene or not os.path.isfile(packaged_scene):
        return "Missing Files"
    if scene_location_mismatch:
        return "Missing Files"
    if _manifest_payload_missing(
        version_path,
        manifest,
        deep=deep_health,
    ):
        return "Missing Files"
    if source_scene and isinstance(source_stat, dict) and source_stat:
        if not os.path.isfile(source_scene):
            return "Source Changed"
        try:
            current = file_fingerprint(source_scene)
        except OSError:
            return "Source Changed"
        if (
            int(current.get("size", -1)) != int(source_stat.get("size", -2))
            or int(current.get("mtime_ns", -1))
            != int(
                source_stat.get(
                    "mtime_ns",
                    source_stat.get("modified_ns", -2),
                )
            )
        ):
            return "Source Changed"
    if any(
        item.get("classification")
        in ("Skipped Cache", "Skipped Missing", "Skipped Unsupported")
        for item in references
    ) or bool(manifest.get("external_hdas")):
        return "Complete with Exclusions"
    return "Complete"


def _manifest_payload_missing(version_path, manifest, deep=True):
    application = str(manifest.get("application") or "nuke").lower()
    copy_jobs = manifest.get("copy_jobs")
    if not isinstance(copy_jobs, list):
        return False
    for job in copy_jobs:
        if not isinstance(job, dict):
            return False
        destination = job.get("destination")
        if destination:
            path = _resolve_manifest_path(version_path, destination)
            if not os.path.exists(path):
                return True
            if deep:
                for filename in job.get("files", []):
                    if not os.path.isfile(os.path.join(path, filename)):
                        return True
        elif application == "nuke":
            material = job.get("material_folder")
            if material and not os.path.exists(
                os.path.join(version_path, "sequences", material)
            ):
                return True
    return False


def _normalise_nuke_reads(reads):
    if not isinstance(reads, list):
        return []
    result = []
    for read in reads:
        if not isinstance(read, dict):
            continue
        item = dict(read)
        item.setdefault("node_path", read.get("node_name", ""))
        item.setdefault("parameter", "file")
        item.setdefault("original_value", read.get("original_path", ""))
        item.setdefault("evaluated_path", read.get("resolved_path", ""))
        item.setdefault("packaged_path", read.get("packaged_path", ""))
        item.setdefault("classification", "Package Input")
        item.setdefault("status", "Copied")
        result.append(item)
    return result


def _manifest_dependency_items(dependencies):
    if not isinstance(dependencies, list):
        return []
    return [item for item in dependencies if isinstance(item, dict)]


def _resolve_manifest_path(version_path, path):
    if not path:
        return ""
    if os.path.isabs(path):
        return os.path.normpath(path)
    return os.path.normpath(os.path.join(version_path, path))


def _first_scene(directory, extensions):
    if not os.path.isdir(directory):
        return ""
    for name in sorted(os.listdir(directory)):
        path = os.path.join(directory, name)
        if os.path.isfile(path) and os.path.splitext(name)[1].lower() in extensions:
            return path
    return ""


def _classification_count(references, classification):
    return sum(
        1 for item in references if item.get("classification") == classification
    )


def _excluded_count(references):
    return sum(
        1
        for item in references
        if item.get("classification")
        in ("Skipped Cache", "Skipped Missing", "Skipped Unsupported")
    )


def _iter_archive_version_directories(archive_root):
    for name in os.listdir(archive_root):
        path = os.path.join(archive_root, name)
        match = VERSION_PATTERN.match(name)
        if match and os.path.isdir(path):
            yield {
                "name": name,
                "number": int(match.group(1)),
                "path": path,
                "department": "",
                "task": "",
                "version_scope": "legacy",
            }
            continue
        if not os.path.isdir(path):
            continue
        task = name
        children = os.listdir(path)
        for version in children:
            version_path = os.path.join(path, version)
            version_match = VERSION_PATTERN.match(version)
            if not version_match or not os.path.isdir(version_path):
                continue
            yield {
                "name": version,
                "number": int(version_match.group(1)),
                "path": version_path,
                "department": "",
                "task": task,
                "version_scope": "task",
            }

        department = name
        for task in children:
            task_path = os.path.join(path, task)
            if not os.path.isdir(task_path):
                continue
            if VERSION_PATTERN.match(task):
                continue
            for version in os.listdir(task_path):
                version_path = os.path.join(task_path, version)
                version_match = VERSION_PATTERN.match(version)
                if not version_match or not os.path.isdir(version_path):
                    continue
                yield {
                    "name": version,
                    "number": int(version_match.group(1)),
                    "path": version_path,
                    "department": department,
                    "task": task,
                    "version_scope": "department_task",
                }


def _assign_task_versions(versions):
    legacy_groups = {}
    for version in versions:
        department = str(version.get("department", ""))
        task = str(version.get("task", ""))
        if not department or not task:
            version["task_version"] = version["storage_version"]
            version["task_number"] = version["storage_number"]
            version["version"] = version["task_version"]
            version["number"] = version["task_number"]
            continue

        key = task.casefold()
        if version.get("version_scope") != "legacy":
            task_version = (
                version.get("task_version")
                or version["storage_version"]
            )
            match = VERSION_PATTERN.match(str(task_version))
            task_number = (
                int(match.group(1))
                if match
                else version["storage_number"]
            )
            version["task_version"] = "v%04d" % task_number
            version["task_number"] = task_number
            version["version"] = version["task_version"]
            version["number"] = task_number
        else:
            legacy_groups.setdefault(key, []).append(version)

    for group in legacy_groups.values():
        group.sort(key=lambda item: item["storage_number"])
        for index, version in enumerate(group, 1):
            version["task_version"] = "v%04d" % index
            version["task_number"] = index
            version["version"] = version["task_version"]
            version["number"] = index


def _scope_component(value):
    value = str(value or "").strip()
    if not value:
        return ""
    if (
        value in (".", "..")
        or "/" in value
        or "\\" in value
        or re.search(r'[<>:"|?*\x00-\x1f]', value)
    ):
        raise ArchiveError("Invalid Archive scope component: %s" % value)
    return value


def _path_key(path):
    return os.path.normcase(os.path.abspath(os.path.normpath(path)))
