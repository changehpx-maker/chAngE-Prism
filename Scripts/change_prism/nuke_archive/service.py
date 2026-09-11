from __future__ import unicode_literals

import codecs
import datetime
import getpass
import json
import locale
import os
import re
import shutil

from change_prism import archive_core


VERSION_PATTERN = archive_core.VERSION_PATTERN
FRAME_TOKEN_PATTERN = re.compile(r"%(?:0\d+)?d|#+")
ENV_TOKEN_PATTERN = re.compile(
    r"\$(?:[A-Za-z_][A-Za-z0-9_]*|\{[A-Za-z_][A-Za-z0-9_]*\})"
    r"|%[A-Za-z_][A-Za-z0-9_]*%"
)
NODE_START_PATTERN = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_.]*)\s*\{\s*$")
FILE_KNOB_PATTERN = re.compile(r"^(\s+)file\s+(.+?)(\r?\n)?$")
NAME_KNOB_PATTERN = re.compile(r"^\s+name\s+(.+?)(?:\r?\n)?$")
PROJECT_DIRECTORY_PATTERN = re.compile(
    r"^(\s+)project_directory\s+(.+?)(\r?\n)?$"
)
INVALID_MATERIAL_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
PROJECT_DIRECTORY_VALUE = r'"\[python \{nuke.script_directory()\}]"'


class ArchiveError(Exception):
    pass


class PreflightError(ArchiveError):
    pass


class PackageExecutionError(ArchiveError):
    pass


class PackageCancelled(ArchiveError):
    pass


def find_shot_root(source_nk):
    return archive_core.find_shot_root(source_nk)


def scan_archive_versions(archive_root):
    versions = []
    for archive in archive_core.scan_archive_versions(archive_root):
        if archive.get("application") != "nuke":
            continue
        item = dict(archive)
        item["read_count"] = archive.get("reference_count", 0)
        versions.append(item)
    return versions


def build_package_plan(source_nk, archive_root):
    """Inspect a Nuke script and return a copy/rewrite plan without writing."""
    source_nk = os.path.abspath(os.fspath(source_nk))
    archive_root = os.path.abspath(os.fspath(archive_root))

    if not os.path.isfile(source_nk):
        raise PreflightError("Nuke script does not exist:\n%s" % source_nk)
    if os.path.splitext(source_nk)[1].lower() != ".nk":
        raise PreflightError("Only .nk files can be archived:\n%s" % source_nk)

    document = _read_nuke_document(source_nk)
    parsed_reads = _parse_read_nodes(document["lines"])
    if document["root_end_index"] is None:
        raise PreflightError("Could not find the Root block in:\n%s" % source_nk)

    copy_jobs = []
    jobs_by_source = {}
    used_material_names = {}
    planned_reads = []

    for read_index, parsed in enumerate(parsed_reads):
        raw_path = _decode_knob_value(parsed["raw_path"])
        resolved_path = _resolve_source_path(raw_path, source_nk)
        # Only the file name can carry a frame token; a "#" or "%04d"
        # inside a parent directory name must not turn a single file
        # into a whole-directory copy.
        is_sequence = bool(
            FRAME_TOKEN_PATTERN.search(os.path.basename(resolved_path))
        )

        if is_sequence:
            source_item = os.path.dirname(resolved_path)
            if not os.path.isdir(source_item):
                raise PreflightError(
                    "%s references a missing sequence folder:\n%s"
                    % (parsed["node_name"], source_item)
                )
            if not _sequence_has_matching_file(resolved_path):
                raise PreflightError(
                    "%s has no frames matching:\n%s"
                    % (parsed["node_name"], resolved_path)
                )
            kind = "directory"
        else:
            source_item = resolved_path
            if not os.path.isfile(source_item):
                raise PreflightError(
                    "%s references a missing file:\n%s"
                    % (parsed["node_name"], source_item)
                )
            kind = "file"

        source_item = os.path.abspath(os.path.normpath(source_item))
        if kind == "directory" and _is_path_within(archive_root, source_item):
            raise PreflightError(
                "Archive destination is inside a source sequence folder:\n%s"
                % source_item
            )

        source_key = _path_key(source_item)
        job = jobs_by_source.get(source_key)
        if job is None:
            material_base = _material_name(os.path.basename(resolved_path))
            material_folder = _allocate_material_folder(
                material_base, used_material_names, source_key
            )
            job = {
                "kind": kind,
                "source": source_item,
                "source_key": source_key,
                "material_folder": material_folder,
            }
            file_count, total_bytes = _measure_source_item(source_item, kind)
            job["file_count"] = file_count
            job["total_bytes"] = total_bytes
            job["source_mtime_ns"] = int(
                os.stat(source_item).st_mtime_ns
            )
            jobs_by_source[source_key] = job
            copy_jobs.append(job)

        filename = os.path.basename(resolved_path)
        packaged_path = _to_nuke_path(
            os.path.join("..", "sequences", job["material_folder"], filename)
        )
        planned_reads.append(
            {
                "index": read_index,
                "node_name": parsed["node_name"],
                "line_index": parsed["file_line_index"],
                "original_path": raw_path,
                "resolved_path": resolved_path,
                "source": source_item,
                "kind": kind,
                "material_folder": job["material_folder"],
                "packaged_path": packaged_path,
            }
        )

    scene_context = archive_core.infer_scene_context(source_nk)
    version_root = archive_core.get_task_archive_root(
        archive_root,
        scene_context["department"],
        scene_context["task"],
    )
    proposed_version = archive_core.get_next_task_archive_version(
        archive_root,
        scene_context["department"],
        scene_context["task"],
    )
    source_stem = os.path.splitext(os.path.basename(source_nk))[0]
    packaged_name = "%s_archive_%s.nk" % (source_stem, proposed_version)
    estimated_file_count = sum(job["file_count"] for job in copy_jobs)
    estimated_total_bytes = sum(job["total_bytes"] for job in copy_jobs)

    return {
        "schema_version": 1,
        "application": "nuke",
        "source_nk": source_nk,
        "department": scene_context["department"],
        "task": scene_context["task"],
        "archive_root": archive_root,
        "version_root": version_root,
        "version_scope": (
            "task"
            if version_root != archive_root
            else "legacy"
        ),
        "proposed_version": proposed_version,
        "packaged_nk_name": packaged_name,
        "reads": planned_reads,
        "copy_jobs": copy_jobs,
        "estimated_file_count": estimated_file_count,
        "estimated_total_bytes": estimated_total_bytes,
        "available_bytes": _get_available_bytes(version_root),
        "source_nk_stat": _file_fingerprint(source_nk),
        "_document": document,
    }


def execute_package(plan, progress_callback=None, is_cancelled=None):
    """Execute a package plan transactionally and return the final paths."""
    if not isinstance(plan, dict):
        raise PackageExecutionError("Package plan must be a dictionary.")

    fresh_plan = _validated_execution_plan(plan)
    source_nk = fresh_plan["source_nk"]
    archive_root = fresh_plan["archive_root"]

    version_path = ""
    try:
        required_bytes = fresh_plan["estimated_total_bytes"]
        available_bytes = fresh_plan["available_bytes"]
        if (
            available_bytes is not None
            and required_bytes > available_bytes
        ):
            raise PackageExecutionError(
                "Not enough free space for the Nuke Archive.\n"
                "Required: %s\nAvailable: %s"
                % (
                    format_bytes(required_bytes),
                    format_bytes(available_bytes),
                )
            )

        version, version_path = (
            archive_core.reserve_task_version_directory(
                archive_root,
                fresh_plan["department"],
                fresh_plan["task"],
            )
        )
        incomplete_path = os.path.join(version_path, ".incomplete")
        with open(incomplete_path, "w", encoding="utf-8") as handle:
            handle.write("Nuke Archive package is being created.\n")

        nk_directory = os.path.join(version_path, "nk")
        sequences_directory = os.path.join(version_path, "sequences")
        os.makedirs(nk_directory)
        os.makedirs(sequences_directory)

        total = len(fresh_plan["copy_jobs"])
        _notify_progress(progress_callback, 0, total, "Preparing Archive %s" % version)
        for index, job in enumerate(fresh_plan["copy_jobs"]):
            _raise_if_cancelled(is_cancelled)
            destination = os.path.join(
                sequences_directory, job["material_folder"]
            )
            _notify_progress(
                progress_callback,
                index,
                total,
                "Copying %s" % job["material_folder"],
            )
            if job["kind"] == "directory":
                _copy_directory(job["source"], destination, is_cancelled)
            else:
                os.makedirs(destination)
                _copy_file(
                    job["source"],
                    os.path.join(destination, os.path.basename(job["source"])),
                    is_cancelled,
                )
            _notify_progress(
                progress_callback,
                index + 1,
                total,
                "Copied %s" % job["material_folder"],
            )

        _raise_if_cancelled(is_cancelled)
        source_stem = os.path.splitext(os.path.basename(source_nk))[0]
        packaged_name = "%s_archive_%s.nk" % (source_stem, version)
        packaged_nk = os.path.join(nk_directory, packaged_name)
        _write_packaged_nuke(fresh_plan, packaged_nk)

        created_at = datetime.datetime.now().astimezone().isoformat()
        manifest = {
            "schema_version": 1,
            "application": "nuke",
            "status": "Complete",
            "archive_version": version,
            "task_version": version,
            "version_scope": fresh_plan["version_scope"],
            "source_nk": source_nk,
            "department": fresh_plan["department"],
            "task": fresh_plan["task"],
            "packaged_nk": _to_nuke_path(
                os.path.relpath(packaged_nk, version_path)
            ),
            "created_by": getpass.getuser(),
            "created_at": created_at,
            "source_nk_stat": fresh_plan["source_nk_stat"],
            "summary": {
                "read_count": len(fresh_plan["reads"]),
                "copy_job_count": len(fresh_plan["copy_jobs"]),
                "file_count": fresh_plan["estimated_file_count"],
                "total_bytes": fresh_plan["estimated_total_bytes"],
            },
            "reads": [
                {
                    "node_name": item["node_name"],
                    "original_path": item["original_path"],
                    "resolved_path": item["resolved_path"],
                    "packaged_path": item["packaged_path"],
                    "material_folder": item["material_folder"],
                    "copy_kind": item["kind"],
                }
                for item in fresh_plan["reads"]
            ],
            "copy_jobs": [
                {
                    "kind": job["kind"],
                    "source": job["source"],
                    "material_folder": job["material_folder"],
                    "file_count": job["file_count"],
                    "total_bytes": job["total_bytes"],
                    "result": "copied",
                }
                for job in fresh_plan["copy_jobs"]
            ],
        }
        manifest_path = os.path.join(version_path, "manifest.json")
        temporary_manifest = manifest_path + ".tmp"
        with open(temporary_manifest, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary_manifest, manifest_path)
        os.remove(incomplete_path)

        return {
            "version": version,
            "version_path": version_path,
            "packaged_nk": packaged_nk,
            "manifest_path": manifest_path,
            "read_count": len(fresh_plan["reads"]),
            "copy_job_count": len(fresh_plan["copy_jobs"]),
        }
    except PackageCancelled:
        _cleanup_failed_version(version_path)
        raise
    except Exception as exc:
        cleanup_error = _cleanup_failed_version(version_path)
        if isinstance(exc, ArchiveError):
            if cleanup_error:
                raise PackageExecutionError(
                    "%s\n\nCould not clean the incomplete Archive:\n%s"
                    % (exc, cleanup_error)
                )
            raise

        message = "Could not create the Nuke Archive:\n%s" % exc
        if cleanup_error:
            message += "\n\nCould not clean the incomplete Archive:\n%s" % cleanup_error
        raise PackageExecutionError(message)


def _validated_execution_plan(plan):
    source_nk = os.path.abspath(os.fspath(plan.get("source_nk", "")))
    archive_root = os.path.abspath(
        os.fspath(plan.get("archive_root", ""))
    )
    if not os.path.isfile(source_nk):
        raise PackageExecutionError(
            "Nuke script no longer exists:\n%s" % source_nk
        )

    recorded_stat = plan.get("source_nk_stat") or {}
    current_stat = _file_fingerprint(source_nk)
    if current_stat is None:
        raise PackageExecutionError(
            "Nuke script no longer exists:\n%s" % source_nk
        )
    if (
        int(current_stat.get("size", -1))
        != int(recorded_stat.get("size", -2))
        or int(
            current_stat.get(
                "mtime_ns",
                current_stat.get("modified_ns", -1),
            )
        )
        != int(
            recorded_stat.get(
                "mtime_ns",
                recorded_stat.get("modified_ns", -2),
            )
        )
    ):
        raise PackageExecutionError(
            "The Nuke script changed after preflight. "
            "Run Package Nuke Archive again."
        )

    for job in plan.get("copy_jobs", []):
        source = job.get("source", "")
        kind = job.get("kind")
        exists = (
            os.path.isdir(source)
            if kind == "directory"
            else os.path.isfile(source)
        )
        if not exists:
            raise PackageExecutionError(
                "A package source changed after preflight:\n%s" % source
            )
        recorded_mtime = job.get("source_mtime_ns")
        if recorded_mtime is not None:
            current_mtime = int(os.stat(source).st_mtime_ns)
            if current_mtime != int(recorded_mtime):
                raise PackageExecutionError(
                    "A package source changed after preflight:\n%s" % source
                )

    validated = dict(plan)
    validated["source_nk"] = source_nk
    validated["archive_root"] = archive_root
    validated["available_bytes"] = _get_available_bytes(
        validated.get("version_root") or archive_root
    )
    return validated


def _read_nuke_document(path):
    with open(path, "rb") as handle:
        data = handle.read()

    has_bom = data.startswith(codecs.BOM_UTF8)
    encoding = "utf-8-sig" if has_bom else "utf-8"
    try:
        text = data.decode(encoding)
    except UnicodeDecodeError:
        fallback = locale.getpreferredencoding(False) or "utf-8"
        try:
            text = data.decode(fallback)
            encoding = fallback
        except UnicodeDecodeError as exc:
            raise PreflightError(
                "Nuke script is not valid UTF-8 or %s:\n%s" % (fallback, exc)
            )

    lines = text.splitlines(True)
    if text and not lines:
        lines = [text]

    root_end_index = None
    project_directory_index = None
    in_root = False
    for index, line in enumerate(lines):
        match = NODE_START_PATTERN.match(line.rstrip("\r\n"))
        if match and match.group(1) == "Root":
            in_root = True
            continue
        if not in_root:
            continue
        if PROJECT_DIRECTORY_PATTERN.match(line):
            project_directory_index = index
        if line.rstrip("\r\n") == "}":
            root_end_index = index
            break

    newline = "\r\n" if "\r\n" in text else "\n"
    return {
        "lines": lines,
        "encoding": encoding,
        "newline": newline,
        "root_end_index": root_end_index,
        "project_directory_index": project_directory_index,
    }


def _parse_read_nodes(lines):
    reads = []
    in_read = False
    node_name = ""
    file_line_index = None
    raw_path = None
    read_number = 0

    for index, line in enumerate(lines):
        stripped_line = line.rstrip("\r\n")
        if not in_read:
            match = NODE_START_PATTERN.match(stripped_line)
            if match and match.group(1) == "Read":
                in_read = True
                read_number += 1
                node_name = "Read%d" % read_number
                file_line_index = None
                raw_path = None
            continue

        file_match = FILE_KNOB_PATTERN.match(line)
        if file_match and file_line_index is None:
            file_line_index = index
            raw_path = file_match.group(2)

        name_match = NAME_KNOB_PATTERN.match(line)
        if name_match:
            try:
                node_name = _decode_knob_value(name_match.group(1))
            except PreflightError:
                pass

        if stripped_line == "}":
            if file_line_index is None or raw_path is None:
                raise PreflightError("%s has no supported file knob." % node_name)
            reads.append(
                {
                    "node_name": node_name,
                    "file_line_index": file_line_index,
                    "raw_path": raw_path,
                }
            )
            in_read = False

    if in_read:
        raise PreflightError("Nuke script contains an unterminated Read node.")
    return reads


def _decode_knob_value(value):
    value = value.strip()
    if not value:
        raise PreflightError("A Read node has an empty file path.")

    if value.startswith("{"):
        if not value.endswith("}"):
            raise PreflightError("Multiline or malformed file paths are unsupported.")
        value = value[1:-1]
    elif value.startswith('"'):
        if not value.endswith('"'):
            raise PreflightError("Multiline or malformed file paths are unsupported.")
        value = value[1:-1]

    if "[" in value or "]" in value:
        raise PreflightError(
            "Tcl/Python expressions in Read paths are unsupported:\n%s" % value
        )
    return value


def _resolve_source_path(raw_path, source_nk):
    expanded = os.path.expandvars(raw_path)
    frame_safe = FRAME_TOKEN_PATTERN.sub("", expanded)
    if ENV_TOKEN_PATTERN.search(frame_safe):
        raise PreflightError(
            "Read path contains an undefined environment variable:\n%s" % raw_path
        )

    native = expanded.replace("/", os.sep).replace("\\", os.sep)
    if not os.path.isabs(native):
        native = os.path.join(os.path.dirname(source_nk), native)
    return os.path.abspath(os.path.normpath(native))


def _sequence_has_matching_file(pattern_path):
    directory = os.path.dirname(pattern_path)
    filename_pattern = os.path.basename(pattern_path)
    expression = []
    position = 0
    for match in FRAME_TOKEN_PATTERN.finditer(filename_pattern):
        expression.append(re.escape(filename_pattern[position : match.start()]))
        token = match.group(0)
        if token.startswith("#"):
            expression.append(r"\d{%d}" % len(token))
        else:
            width_match = re.match(r"%0(\d+)d", token)
            if width_match:
                expression.append(r"\d{%d}" % int(width_match.group(1)))
            else:
                expression.append(r"\d+")
        position = match.end()
    expression.append(re.escape(filename_pattern[position:]))
    flags = re.IGNORECASE if os.name == "nt" else 0
    regex = re.compile("^%s$" % "".join(expression), flags)

    try:
        return any(
            regex.match(name) and os.path.isfile(os.path.join(directory, name))
            for name in os.listdir(directory)
        )
    except OSError:
        return False


def _material_name(filename):
    stem = os.path.splitext(filename)[0]
    stem = FRAME_TOKEN_PATTERN.sub("", stem)
    stem = stem.rstrip(" ._-")
    stem = INVALID_MATERIAL_CHARS.sub("_", stem)
    stem = re.sub(r"_+", "_", stem).strip(" ._")
    return stem or "read"


def format_bytes(value):
    if value is None:
        return "Not recorded"

    size = float(value)
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit = units[0]
    for unit in units:
        if abs(size) < 1024.0 or unit == units[-1]:
            break
        size /= 1024.0

    if unit == "B":
        return "%d %s" % (int(size), unit)
    return "%.2f %s" % (size, unit)


def calculate_archive_payload_stats(version_path, copy_jobs):
    sequences_root = os.path.join(version_path, "sequences")
    file_count = 0
    total_bytes = 0
    for job in copy_jobs:
        material_folder = job.get("material_folder", "")
        destination = os.path.abspath(
            os.path.join(sequences_root, material_folder)
        )
        if (
            not material_folder
            or not _is_path_within(destination, sequences_root)
            or not os.path.isdir(destination)
        ):
            return None, None
        try:
            job_file_count, job_total_bytes = _measure_source_item(
                destination, "directory"
            )
        except ArchiveError:
            return None, None
        file_count += job_file_count
        total_bytes += job_total_bytes
    return file_count, total_bytes


def delete_archive_version(version_path, archive_root):
    archive_root = os.path.abspath(os.fspath(archive_root))
    version_path = os.path.abspath(os.fspath(version_path))
    version_name = os.path.basename(version_path)

    if not VERSION_PATTERN.match(version_name):
        raise ArchiveError(
            "Refusing to delete a folder which is not an Archive version:\n%s"
            % version_path
        )
    if _path_key(os.path.dirname(version_path)) != _path_key(archive_root):
        raise ArchiveError(
            "Refusing to delete a folder outside the selected Archives root:\n%s"
            % version_path
        )
    if not os.path.isdir(archive_root) or not os.path.isdir(version_path):
        raise ArchiveError(
            "Archive version does not exist:\n%s" % version_path
        )

    resolved_root = os.path.realpath(archive_root)
    resolved_version = os.path.realpath(version_path)
    if (
        _path_key(resolved_root) == _path_key(resolved_version)
        or not _is_path_within(resolved_version, resolved_root)
    ):
        raise ArchiveError(
            "Refusing to delete an Archive path outside its resolved root:\n%s"
            % version_path
        )
    if os.path.isfile(os.path.join(version_path, ".incomplete")):
        raise ArchiveError(
            "This Archive version is incomplete or currently being packaged "
            "and cannot be deleted from the browser:\n%s" % version_path
        )

    try:
        shutil.rmtree(version_path)
    except OSError as exc:
        raise ArchiveError(
            "Could not delete Archive %s:\n%s\n\n%s"
            % (version_name, version_path, exc)
        )
    return {
        "version": version_name,
        "deleted_path": version_path,
    }


def _measure_source_item(source, kind):
    if kind == "file":
        try:
            return 1, os.path.getsize(source)
        except OSError as exc:
            raise PreflightError(
                "Could not inspect source file:\n%s\n\n%s" % (source, exc)
            )

    file_count = 0
    total_bytes = 0

    def on_error(error):
        raise error

    try:
        for current, _directory_names, file_names in os.walk(
            source, onerror=on_error
        ):
            for filename in file_names:
                path = os.path.join(current, filename)
                file_count += 1
                total_bytes += os.path.getsize(path)
    except OSError as exc:
        raise PreflightError(
            "Could not inspect source sequence folder:\n%s\n\n%s"
            % (source, exc)
        )
    return file_count, total_bytes


def _get_available_bytes(path):
    current = os.path.abspath(path)
    while not os.path.exists(current):
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent

    try:
        return shutil.disk_usage(current).free
    except OSError:
        return None


def _file_fingerprint(path):
    try:
        stat_result = os.stat(path)
    except OSError:
        return None
    return {
        "size": stat_result.st_size,
        "modified_ns": stat_result.st_mtime_ns,
    }


def _allocate_material_folder(base, used_names, source_key):
    candidate = base
    suffix = 2
    while True:
        name_key = os.path.normcase(candidate)
        existing_source = used_names.get(name_key)
        if existing_source is None:
            used_names[name_key] = source_key
            return candidate
        if existing_source == source_key:
            return candidate
        candidate = "%s_%d" % (base, suffix)
        suffix += 1


def _write_packaged_nuke(plan, destination):
    document = plan["_document"]
    lines = list(document["lines"])
    for item in plan["reads"]:
        index = item["line_index"]
        original = lines[index]
        match = FILE_KNOB_PATTERN.match(original)
        if not match:
            raise PackageExecutionError(
                "Read file line changed after preflight at line %d." % (index + 1)
            )
        newline = match.group(3)
        if newline is None:
            newline = document["newline"]
        lines[index] = "%sfile %s%s" % (
            match.group(1),
            _encode_knob_value(item["packaged_path"]),
            newline,
        )

    project_line = " project_directory %s%s" % (
        PROJECT_DIRECTORY_VALUE,
        document["newline"],
    )
    project_index = document["project_directory_index"]
    if project_index is not None:
        original = lines[project_index]
        match = PROJECT_DIRECTORY_PATTERN.match(original)
        indent = match.group(1) if match else " "
        newline = match.group(3) if match and match.group(3) else document["newline"]
        lines[project_index] = "%sproject_directory %s%s" % (
            indent,
            PROJECT_DIRECTORY_VALUE,
            newline,
        )
    else:
        lines.insert(document["root_end_index"], project_line)

    text = "".join(lines)
    try:
        data = text.encode(document["encoding"])
    except UnicodeEncodeError as exc:
        raise PackageExecutionError(
            "Could not preserve the Nuke script encoding:\n%s" % exc
        )
    with open(destination, "wb") as handle:
        handle.write(data)


def _encode_knob_value(value):
    if re.search(r"\s", value) or "{" in value or "}" in value:
        return "{%s}" % value.replace("}", r"\}")
    return value


def _copy_directory(source, destination, is_cancelled):
    os.makedirs(destination)
    for current, directory_names, file_names in os.walk(source):
        _raise_if_cancelled(is_cancelled)
        relative = os.path.relpath(current, source)
        target_current = (
            destination
            if relative == "."
            else os.path.join(destination, relative)
        )
        os.makedirs(target_current, exist_ok=True)
        for directory_name in directory_names:
            os.makedirs(
                os.path.join(target_current, directory_name), exist_ok=True
            )
        for filename in file_names:
            _copy_file(
                os.path.join(current, filename),
                os.path.join(target_current, filename),
                is_cancelled,
            )


def _copy_file(source, destination, is_cancelled):
    _raise_if_cancelled(is_cancelled)
    shutil.copy2(source, destination)
    _raise_if_cancelled(is_cancelled)


def _raise_if_cancelled(is_cancelled):
    if is_cancelled and is_cancelled():
        raise PackageCancelled("Nuke Archive packaging was cancelled.")


def _notify_progress(callback, completed, total, message):
    if callback:
        callback(completed, total, message)


def _cleanup_failed_version(version_path):
    return archive_core.cleanup_failed_version(version_path)


def _path_key(path):
    return os.path.normcase(os.path.realpath(os.path.abspath(path)))


def _is_path_within(path, parent):
    try:
        return os.path.commonpath(
            [os.path.abspath(path), os.path.abspath(parent)]
        ) == os.path.abspath(parent)
    except ValueError:
        return False


def _to_nuke_path(path):
    return path.replace("\\", "/")


