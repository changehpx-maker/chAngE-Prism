from __future__ import unicode_literals

import json
import os
import re
import sys
import traceback

import hou

try:
    from change_prism.houdini_archive import archive_planning
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import archive_planning


FRAME_TOKEN_PATTERN = re.compile(
    r"\$(?:\{F\d*\}|F\d*)|%(?:0\d+)?d|#+|<UDIM>",
    re.IGNORECASE,
)
SUPPORTED_EXTENSIONS = {
    ".abc": "alembic",
    ".fbx": "fbx",
    ".vdb": "volumes",
    ".obj": "geometry",
    ".geo": "geometry",
    ".geo.gz": "geometry",
    ".ply": "geometry",
    ".stl": "geometry",
    ".exr": "textures",
    ".hdr": "textures",
    ".png": "textures",
    ".jpg": "textures",
    ".jpeg": "textures",
    ".tif": "textures",
    ".tiff": "textures",
    ".tx": "textures",
    ".tga": "textures",
    ".cube": "lut",
    ".lut": "lut",
    ".3dl": "lut",
    ".wav": "audio",
    ".aif": "audio",
    ".aiff": "audio",
    ".mp3": "audio",
}
USD_EXTENSIONS = {".usd", ".usda", ".usdc", ".usdz"}
INTERNAL_SCHEMES = ("op:", "opdef:", "oplib:", "temp:")
OUTPUT_NODE_NAMES = {
    "configurelayer",
    "rop_geometry",
    "rop_alembic",
    "rop_fbx",
    "usdrender_rop",
    "usd_rop",
}
OUTPUT_PARM_NAMES = {
    "sopoutput",
    "lopoutput",
    "output",
    "outputfile",
    "outputfilepath",
    "savepath",
    "vm_picture",
    "vm_dcmfilename",
    "savetodirectory_directory",
}
PDG_PARM_NAMES = {
    "checkpointfile",
    "taskgraphfile",
    "pdg_workingdir",
    "rendergallerysource",
}


def inspect_scene(source_hip):
    load_warning = _load_scene(source_hip)
    frame_range = list(hou.playbar.frameRange())
    start_frame = frame_range[0]
    references = []
    errors = []

    for parm, reported_path in hou.fileReferences("HIP", True):
        item = _inspect_reference(
            parm,
            reported_path,
            source_hip,
            start_frame,
            frame_range,
        )
        references.append(item)
        if item["classification"] == "Package Input" and item["status"] != "Ready":
            errors.append(
                "%s (%s): %s"
                % (
                    item.get("node_path") or "<unknown node>",
                    item.get("parameter") or "<unknown parameter>",
                    item.get("error") or "Missing input",
                )
            )
        elif item["classification"] == "Unsupported":
            errors.append(
                "%s (%s): unsupported external reference %s"
                % (
                    item.get("node_path") or "<unknown node>",
                    item.get("parameter") or "<unknown parameter>",
                    item.get("evaluated_path") or item.get("original_value"),
                )
            )

    external_hdas, hda_errors = _collect_external_hdas()
    errors.extend(hda_errors)
    if _load_warning_is_fatal(load_warning):
        errors.append("Houdini load warning may hide dependencies: %s" % load_warning)

    return {
        "houdini_version": hou.applicationVersionString(),
        "python_version": sys.version.split()[0],
        "save_mode": str(hou.hipFile.saveMode()).split(".")[-1],
        "fps": hou.fps(),
        "frame_range": frame_range,
        "playback_range": list(hou.playbar.playbackRange()),
        "load_warning": load_warning,
        "references": references,
        "external_hdas": external_hdas,
        "errors": errors,
    }


def rewrite_scene(packaged_hip, plan):
    load_warning = _load_scene(packaged_hip)
    rewrite = _rewrite_loaded_scene(packaged_hip, plan)
    if rewrite["errors"]:
        rewrite["load_warning"] = load_warning
        rewrite["validation"] = []
        return rewrite

    hou.hipFile.clear(suppress_save_prompt=True)
    reopen_warning = _load_scene(packaged_hip)
    validation, validation_errors = _validate_loaded_scene(
        packaged_hip, plan
    )
    rewrite["errors"].extend(validation_errors)
    rewrite["load_warning"] = load_warning
    rewrite["reopen_warning"] = reopen_warning
    rewrite["validation"] = validation
    return rewrite


def prepare_archive(source_hip, request):
    inspection = inspect_scene(source_hip)
    errors = list(inspection.get("errors") or [])
    if (
        request.get("hython_version")
        and inspection.get("houdini_version") != request["hython_version"]
    ):
        errors.append(
            "The Houdini Worker reported version %s, expected %s."
            % (
                inspection.get("houdini_version", "unknown"),
                request["hython_version"],
            )
        )
    if errors:
        return {
            "errors": errors,
            "inspection": inspection,
        }

    try:
        copy_plan = archive_planning.build_copy_plan(inspection)
    except archive_planning.PlanningError as exc:
        return {
            "errors": [str(exc)],
            "inspection": inspection,
        }

    rewrite_plan = {
        "dependencies": copy_plan["dependencies"],
    }
    rewrite = _rewrite_loaded_scene(
        request["packaged_hip"],
        rewrite_plan,
    )
    if rewrite["errors"]:
        return {
            "errors": rewrite["errors"],
            "inspection": inspection,
            "copy_plan": copy_plan,
        }

    for job in copy_plan["copy_jobs"]:
        job["destination"] = archive_planning.to_houdini_path(
            os.path.join(
                "dependencies",
                job["category"],
                job["material_folder"],
            )
        )
        job["result"] = "pending"
    for hda in copy_plan["external_hdas"]:
        hda["result"] = "pending"

    packaged_size = os.path.getsize(request["packaged_hip"])
    excluded = copy_plan["summary"]["skipped_count"] > 0 or bool(
        copy_plan["external_hdas"]
    )
    manifest = {
        "schema_version": 2,
        "application": "houdini",
        "status": "Incomplete",
        "archive_version": request["version"],
        "task_version": request["version"],
        "version_scope": request["version_scope"],
        "source_scene": source_hip,
        "packaged_scene": os.path.basename(request["packaged_hip"]),
        "source_scene_stat": request["source_hip_stat"],
        "source_extension": request["source_extension"],
        "department": request["department"],
        "task": request["task"],
        "save_mode": inspection.get("save_mode", ""),
        "houdini_version": inspection.get("houdini_version", ""),
        "hython_version": request.get("hython_version", ""),
        "python_version": inspection.get("python_version", ""),
        "fps": inspection.get("fps"),
        "frame_range": inspection.get("frame_range", []),
        "playback_range": inspection.get("playback_range", []),
        "created_by": request["created_by"],
        "created_at": request["created_at"],
        "version_warning": request.get("version_warning", ""),
        "load_warning": inspection.get("load_warning", ""),
        "rewrite_load_warning": "",
        "reopen_warning": "",
        "validation": [
            {
                "check": "archive_scene_saved",
                "path": os.path.basename(request["packaged_hip"]),
                "valid": True,
            }
        ],
        "summary": {
            "reference_count": copy_plan["summary"]["reference_count"],
            "package_input_count": copy_plan["summary"][
                "package_input_count"
            ],
            "skipped_cache_count": copy_plan["summary"][
                "skipped_cache_count"
            ],
            "skipped_unsupported_count": copy_plan["summary"][
                "skipped_unsupported_count"
            ],
            "skipped_missing_count": copy_plan["summary"][
                "skipped_missing_count"
            ],
            "skipped_count": copy_plan["summary"]["skipped_count"],
            "excluded_count": copy_plan["summary"]["excluded_count"],
            "missing_count": copy_plan["summary"]["missing_count"],
            "copied_dependency_count": 0,
            "hda_count": len(copy_plan["external_hdas"]),
            "copy_job_count": len(copy_plan["copy_jobs"]),
            "file_count": copy_plan["estimated_file_count"] + 1,
            "total_bytes": (
                copy_plan["estimated_dependency_bytes"] + packaged_size
            ),
        },
        "dependencies": archive_planning.manifest_dependencies(
            copy_plan["dependencies"],
            packaged_status="Pending Copy",
        ),
        "external_hdas": copy_plan["external_hdas"],
        "copy_jobs": archive_planning.manifest_copy_jobs(
            copy_plan["copy_jobs"]
        ),
    }
    manifest["completion_status"] = (
        "Complete with Exclusions" if excluded else "Complete"
    )
    _write_result(request["manifest_path"], manifest)
    return {
        "errors": [],
        "manifest_path": request["manifest_path"],
        "changed_count": rewrite["changed_count"],
    }


def _rewrite_loaded_scene(packaged_hip, plan):
    errors = []
    changed = 0
    for dependency in plan.get("dependencies", []):
        if dependency.get("classification") != "Package Input":
            continue
        parm = hou.parm(dependency.get("parameter", ""))
        if parm is None:
            errors.append(
                "Parameter no longer exists: %s"
                % dependency.get("parameter", "")
            )
            continue
        try:
            if parm.isLocked():
                errors.append("Parameter is locked: %s" % parm.path())
                continue
        except AttributeError:
            pass
        try:
            parm.set(dependency["packaged_path"])
            changed += 1
        except Exception as exc:
            errors.append("Could not rewrite %s: %s" % (parm.path(), exc))

    if errors:
        return {
            "errors": errors,
            "changed_count": changed,
        }

    hou.hipFile.save(file_name=packaged_hip)
    return {
        "errors": [],
        "changed_count": changed,
    }


def _validate_loaded_scene(packaged_hip, plan):
    validation = []
    errors = []
    archive_root = plan.get("reserved_version_path", "")
    frame_start = plan.get("frame_range", [hou.frame()])[0]
    for dependency in plan.get("dependencies", []):
        if dependency.get("classification") != "Package Input":
            continue
        parm = hou.parm(dependency.get("parameter", ""))
        valid = False
        evaluated = ""
        message = ""
        if parm is None:
            message = "Parameter no longer exists after reopening."
        else:
            try:
                raw = parm.unexpandedString()
            except Exception:
                raw = dependency.get("packaged_path", "")
            try:
                pattern = _expand_pattern(raw, frame_start)
                if FRAME_TOKEN_PATTERN.search(pattern):
                    matches = _sequence_files(pattern)
                    evaluated = pattern
                    valid = bool(matches) and all(
                        _is_within(path, archive_root) for path in matches
                    )
                else:
                    evaluated = parm.evalAtFrame(frame_start)
                    if not os.path.isabs(evaluated):
                        evaluated = os.path.join(
                            os.path.dirname(packaged_hip), evaluated
                        )
                    valid = os.path.isfile(evaluated) and _is_within(
                        evaluated, archive_root
                    )
                if not valid:
                    message = "Packaged input is missing or outside the Archive."
            except Exception as exc:
                message = str(exc)
        validation.append(
            {
                "parameter": dependency.get("parameter", ""),
                "evaluated_path": evaluated,
                "valid": valid,
                "message": message,
            }
        )
        if not valid:
            errors.append(
                "%s: %s"
                % (dependency.get("parameter", ""), message or "Invalid path")
            )
    return validation, errors


def _inspect_reference(
    parm, reported_path, source_hip, frame, frame_range=None
):
    node = parm.node() if parm is not None else None
    raw = reported_path or ""
    unexpanded_error = ""
    if parm is not None:
        try:
            raw = parm.unexpandedString()
        except Exception as exc:
            unexpanded_error = str(exc)
    has_keyframes = False
    if parm is not None:
        try:
            has_keyframes = bool(parm.keyframes())
        except Exception:
            pass

    evaluated = ""
    eval_error = ""
    try:
        evaluated = (
            parm.evalAtFrame(frame)
            if parm is not None
            else hou.text.expandStringAtFrame(raw, frame)
        )
    except Exception as exc:
        eval_error = str(exc)

    pattern = ""
    pattern_error = ""
    sample_frames = _reference_sample_frames(parm, frame, frame_range)
    try:
        patterns = _expanded_reference_patterns(
            parm,
            raw or reported_path,
            reported_path,
            sample_frames,
            bool(unexpanded_error and has_keyframes),
        )
        if len(patterns) > 1:
            pattern_error = (
                "The input resolves to multiple source patterns and cannot "
                "be safely rewritten."
            )
        elif patterns:
            pattern = patterns[0]
    except Exception as exc:
        pattern_error = str(exc)
    if not pattern:
        pattern = evaluated
    if pattern and not os.path.isabs(pattern) and not pattern.lower().startswith(
        INTERNAL_SCHEMES
    ):
        pattern = os.path.normpath(
            os.path.join(os.path.dirname(source_hip), pattern)
        )

    extension = _path_extension(pattern or evaluated)
    classification, reason = _classify(
        node,
        parm,
        raw,
        evaluated or pattern,
        extension,
    )
    source_files = []
    error = ""
    status = "Skipped"
    if classification == "Package Input":
        if FRAME_TOKEN_PATTERN.search(pattern):
            source_files = _sequence_files(pattern)
            if source_files:
                status = "Ready"
            else:
                status = "Missing"
                error = "No files match %s" % pattern
        else:
            resolved = evaluated or pattern
            if resolved and not os.path.isabs(resolved):
                resolved = os.path.normpath(
                    os.path.join(os.path.dirname(source_hip), resolved)
                )
            pattern = resolved
            if resolved and os.path.isfile(resolved):
                source_files = [resolved]
                status = "Ready"
            else:
                status = "Missing"
                error = "File does not exist: %s" % resolved
    elif classification == "Unsupported":
        status = "Unsupported"

    locked = False
    if parm is not None:
        try:
            locked = parm.isLocked()
        except Exception:
            pass
    if classification == "Package Input" and locked:
        status = "Blocked"
        error = "The input parameter is locked and cannot be rewritten."
    if classification == "Package Input" and pattern_error:
        status = "Blocked"
        error = pattern_error
    if (
        classification == "Package Input"
        and status == "Missing"
        and _is_unavailable_mnt_nas_reference(raw, evaluated, pattern)
    ):
        classification = "Skipped Missing"
        status = "Missing (Skipped)"
        reason = (
            "Unavailable /mnt/nas input is excluded and keeps its "
            "original path"
        )

    category = SUPPORTED_EXTENSIONS.get(extension, "")
    return {
        "node_path": node.path() if node is not None else "",
        "node_type": _node_type_name(node),
        "parameter": parm.path() if parm is not None else "",
        "parameter_name": parm.name() if parm is not None else "",
        "original_value": raw,
        "reported_path": reported_path or "",
        "evaluated_path": evaluated,
        "resolved_pattern": pattern,
        "extension": extension,
        "category": category,
        "classification": classification,
        "status": status,
        "reason": reason,
        "error": error or eval_error or unexpanded_error,
        "locked": locked,
        "has_keyframes": has_keyframes,
        "has_expression": bool(
            has_keyframes
            or "`" in raw
            or raw != (reported_path or raw)
        ),
        "source_files": source_files,
    }


def _classify(node, parm, raw, evaluated, extension):
    lower_value = str(evaluated or raw).lower()
    if (
        lower_value.startswith(INTERNAL_SCHEMES)
        or _is_builtin_file_reference(evaluated or raw)
        or _is_vop_include(node, parm)
    ):
        return "Internal", "Houdini internal resource"

    inside_filecache = _is_inside_filecache(node)
    if _is_output(node, parm, inside_filecache):
        return "Output", "Output parameter"
    if inside_filecache or extension in (".bgeo", ".bgeo.sc"):
        return "Skipped Cache", "File Cache and BGeo payloads are excluded"
    if _is_pdg_reference(node, parm) or extension in USD_EXTENSIONS:
        return "Skipped Unsupported", "USD and PDG dependencies are not packaged"
    if extension in SUPPORTED_EXTENSIONS:
        return "Package Input", "Supported external input"
    return "Unsupported", "Unknown external reference type"


def _is_unavailable_mnt_nas_reference(*values):
    for value in values:
        normalised = str(value or "").replace("\\", "/").lower()
        if normalised == "/mnt/nas" or normalised.startswith("/mnt/nas/"):
            return True
    return False


def _is_vop_include(node, parm):
    return (
        _node_type_name(node).lower().startswith("vop/inline")
        and parm is not None
        and parm.name().lower() == "includes"
    )


def _is_output(node, parm, inside_filecache):
    if inside_filecache:
        return False
    node_type = _node_type_name(node).lower()
    base_name = _node_base_name(node)
    parm_name = parm.name().lower() if parm is not None else ""
    if node_type.startswith("driver/"):
        return True
    if base_name in OUTPUT_NODE_NAMES:
        return True
    return parm_name in OUTPUT_PARM_NAMES


def _is_pdg_reference(node, parm):
    node_type = _node_type_name(node).lower()
    parm_name = parm.name().lower() if parm is not None else ""
    return (
        node_type.startswith("top/")
        or node_type.startswith("topnet/")
        or parm_name in PDG_PARM_NAMES
    )


def _is_inside_filecache(node):
    current = node
    while current is not None:
        if "filecache" in _node_base_name(current):
            return True
        current = current.parent()
    return False


def _node_base_name(node):
    if node is None:
        return ""
    try:
        name = node.type().name().lower()
    except Exception:
        return ""
    return name.split("::", 1)[0]


def _node_type_name(node):
    if node is None:
        return ""
    try:
        return node.type().nameWithCategory()
    except Exception:
        return ""


def _is_builtin_file_reference(value):
    value = str(value or "").strip()
    if not value:
        return False
    if os.path.isabs(value):
        return _is_houdini_install_path(value)
    tokens = value.split()
    if not tokens:
        return False
    for token in tokens:
        try:
            found = hou.findFile(token)
        except Exception:
            return False
        if not found or not _is_houdini_install_path(found):
            return False
    return True


def _collect_external_hdas():
    libraries = {}
    errors = []
    for node in hou.node("/").allSubChildren():
        definition = node.type().definition()
        if definition is None:
            continue
        library = definition.libraryFilePath()
        if not library or library == "Embedded":
            continue
        try:
            library = hou.text.expandString(library)
        except Exception:
            pass
        if _is_houdini_install_path(library):
            continue
        key = os.path.normcase(os.path.abspath(os.path.normpath(library)))
        data = libraries.setdefault(
            key,
            {"source": library, "node_types": set()},
        )
        data["node_types"].add(node.type().nameWithCategory())

    result = []
    for key in sorted(libraries):
        item = libraries[key]
        source = item["source"]
        status = "Ready" if os.path.isfile(source) else "Missing"
        if status == "Missing":
            errors.append("External HDA does not exist: %s" % source)
        result.append(
            {
                "source": source,
                "node_types": sorted(item["node_types"]),
                "status": status,
                "activation": "manual",
            }
        )
    return result, errors


def _is_houdini_install_path(path):
    normalised = os.path.normcase(
        os.path.abspath(os.path.normpath(str(path or "")))
    )
    slash_path = normalised.replace("\\", "/").lower()
    if "/houdini/otls/" in slash_path:
        return True
    for variable in ("HFS", "HH"):
        root = os.environ.get(variable)
        if root and _is_within(normalised, root):
            return True
    return False


def _expand_pattern(raw, frame):
    raw = str(raw or "")
    tokens = []

    def protect(match):
        marker = "__CHANGE_ARCHIVE_TOKEN_%d__" % len(tokens)
        tokens.append((marker, match.group(0)))
        return marker

    protected = FRAME_TOKEN_PATTERN.sub(protect, raw)
    expanded = hou.text.expandStringAtFrame(protected, frame)
    for marker, token in tokens:
        expanded = expanded.replace(marker, token)
    return os.path.normpath(expanded)


def _reference_sample_frames(parm, frame, frame_range):
    frames = [float(frame)]
    if frame_range:
        frames.extend(
            [
                float(frame_range[0]),
                (float(frame_range[0]) + float(frame_range[-1])) / 2.0,
                float(frame_range[-1]),
            ]
        )
    if parm is not None:
        try:
            frames.extend(float(key.frame()) for key in parm.keyframes())
        except Exception:
            pass
    result = []
    for value in frames:
        if value not in result:
            result.append(value)
    return result


def _expanded_reference_patterns(
    parm, raw, reported_path, sample_frames, force_parm_evaluation=False
):
    patterns = []
    for frame in sample_frames:
        if force_parm_evaluation and parm is not None:
            value = parm.evalAtFrame(frame)
        else:
            try:
                value = _expand_pattern(raw, frame)
            except Exception:
                if parm is None:
                    raise
                value = parm.evalAtFrame(frame)
        value = os.path.normpath(str(value or ""))
        key = os.path.normcase(value)
        if value and key not in [
            os.path.normcase(existing) for existing in patterns
        ]:
            patterns.append(value)
    if not patterns and reported_path:
        patterns.append(os.path.normpath(str(reported_path)))
    return patterns


def _sequence_files(pattern):
    directory = os.path.dirname(pattern)
    filename = os.path.basename(pattern)
    if not os.path.isdir(directory):
        return []
    expression = []
    cursor = 0
    for match in FRAME_TOKEN_PATTERN.finditer(filename):
        expression.append(re.escape(filename[cursor : match.start()]))
        token = match.group(0)
        padding = _token_padding(token)
        expression.append(
            r"-?\d{%d}" % padding if padding else r"-?\d+"
        )
        cursor = match.end()
    expression.append(re.escape(filename[cursor:]))
    flags = re.IGNORECASE if os.name == "nt" else 0
    matcher = re.compile("^%s$" % "".join(expression), flags)
    result = []
    for name in os.listdir(directory):
        if matcher.match(name):
            path = os.path.join(directory, name)
            if os.path.isfile(path):
                result.append(os.path.abspath(path))
    result.sort()
    return result


def _token_padding(token):
    lower = token.lower()
    if lower == "<udim>" or token.startswith("#"):
        return 4 if lower == "<udim>" else len(token)
    digits = re.search(r"(\d+)", token)
    return int(digits.group(1)) if digits else 0


def _path_extension(path):
    filename = os.path.basename(str(path or ""))
    filename = FRAME_TOKEN_PATTERN.sub("0001", filename)
    lower = filename.lower()
    if lower.endswith(".bgeo.sc"):
        return ".bgeo.sc"
    if lower.endswith(".geo.gz"):
        return ".geo.gz"
    return os.path.splitext(lower)[1]


def _load_scene(path):
    warning = ""
    try:
        hou.hipFile.load(
            path,
            suppress_save_prompt=True,
            ignore_load_warnings=False,
        )
    except hou.LoadWarning as exc:
        warning = str(exc)
    return warning


def _load_warning_is_fatal(message):
    lower = str(message or "").lower()
    return any(
        marker in lower
        for marker in (
            "unknown operator",
            "could not load",
            "missing operator",
            "failed to load",
        )
    )


def _is_within(path, parent):
    if not path or not parent:
        return False
    try:
        return os.path.commonpath(
            [os.path.abspath(path), os.path.abspath(parent)]
        ) == os.path.abspath(parent)
    except (ValueError, OSError):
        return False


def _write_result(path, result):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main(argv=None):
    argv = list(argv or sys.argv[1:])
    if len(argv) < 3:
        raise RuntimeError(
            "Usage: houdini_worker.py inspect|rewrite|prepare "
            "SOURCE RESULT [PLAN]"
        )
    command, source_hip, result_path = argv[:3]
    if command == "inspect":
        result = inspect_scene(source_hip)
    elif command == "rewrite":
        if len(argv) < 4:
            raise RuntimeError("Rewrite requires a plan JSON file.")
        with open(argv[3], "r", encoding="utf-8") as handle:
            plan = json.load(handle)
        result = rewrite_scene(source_hip, plan)
    elif command == "prepare":
        if len(argv) < 4:
            raise RuntimeError("Prepare requires a request JSON file.")
        with open(argv[3], "r", encoding="utf-8") as handle:
            request = json.load(handle)
        result = prepare_archive(source_hip, request)
    else:
        raise RuntimeError("Unknown Houdini Worker command: %s" % command)
    _write_result(result_path, result)
    return 0


if __name__ == "__main__":
    result_path_arg = sys.argv[3] if len(sys.argv) > 3 else ""
    try:
        sys.exit(main())
    except Exception as error:
        if result_path_arg:
            try:
                _write_result(
                    result_path_arg,
                    {
                        "error": str(error),
                        "traceback": traceback.format_exc(),
                    },
                )
            except Exception:
                pass
        traceback.print_exc()
        sys.exit(1)
