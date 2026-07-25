from __future__ import unicode_literals

import os
import re


FRAME_TOKEN_PATTERN = re.compile(
    r"\$(?:\{F\d*\}|F\d*)|%(?:0\d+)?d|#+|<UDIM>",
    re.IGNORECASE,
)
INVALID_MATERIAL_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


class PlanningError(RuntimeError):
    pass


def build_copy_plan(inspection):
    references = [dict(item) for item in inspection.get("references", [])]
    copy_jobs = []
    jobs_by_key = {}
    used_names = {}

    for dependency in references:
        if dependency.get("classification") != "Package Input":
            continue
        source_files = [
            os.path.abspath(os.path.normpath(path))
            for path in dependency.get("source_files", [])
        ]
        if not source_files:
            raise PlanningError(
                "No files were resolved for:\n%s"
                % dependency.get("parameter", "")
            )
        for source_file in source_files:
            if not _is_readable_file(source_file):
                raise PlanningError(
                    "Input file cannot be read:\n%s" % source_file
                )

        pattern = dependency.get("resolved_pattern") or source_files[0]
        is_sequence = bool(FRAME_TOKEN_PATTERN.search(pattern))
        source_key = _copy_source_key(pattern, source_files, is_sequence)
        job = jobs_by_key.get(source_key)
        if job is None:
            category = dependency.get("category") or "other"
            filename = os.path.basename(
                pattern if is_sequence else source_files[0]
            )
            material = _allocate_material_folder(
                category,
                _material_name(filename),
                source_key,
                used_names,
            )
            job = _create_copy_job(
                source_key,
                category,
                material,
                pattern,
                source_files,
                is_sequence,
            )
            jobs_by_key[source_key] = job
            copy_jobs.append(job)

        filename = os.path.basename(
            pattern if is_sequence else source_files[0]
        )
        dependency["copy_job_key"] = source_key
        dependency["material_folder"] = job["material_folder"]
        dependency["packaged_path"] = to_houdini_path(
            os.path.join(
                "$HIP",
                "dependencies",
                job["category"],
                job["material_folder"],
                filename,
            )
        )

    external_hdas = [
        dict(item) for item in inspection.get("external_hdas", [])
    ]
    for hda in external_hdas:
        raw_source = hda.get("source", "")
        source = (
            os.path.abspath(os.path.normpath(raw_source))
            if raw_source
            else ""
        )
        if not _is_readable_file(source):
            raise PlanningError(
                "External HDA does not exist or cannot be read:\n%s"
                % source
            )
        source_key = "hda:%s" % _path_key(source)
        job = jobs_by_key.get(source_key)
        if job is None:
            material = _allocate_material_folder(
                "hda",
                _material_name(os.path.basename(source)),
                source_key,
                used_names,
            )
            job = _create_copy_job(
                source_key,
                "hda",
                material,
                source,
                [source],
                False,
            )
            jobs_by_key[source_key] = job
            copy_jobs.append(job)
        hda["source"] = source
        hda["copy_job_key"] = source_key
        hda["archive_path"] = to_houdini_path(
            os.path.join(
                "dependencies",
                "hda",
                job["material_folder"],
                os.path.basename(source),
            )
        )
        hda["activation"] = "manual"

    skipped_cache_count = _classification_count(
        references, "Skipped Cache"
    )
    skipped_unsupported_count = _classification_count(
        references, "Skipped Unsupported"
    )
    skipped_missing_count = _classification_count(
        references, "Skipped Missing"
    )
    dependency_bytes = sum(job["total_bytes"] for job in copy_jobs)
    return {
        "dependencies": references,
        "external_hdas": external_hdas,
        "copy_jobs": copy_jobs,
        "estimated_file_count": sum(
            job["file_count"] for job in copy_jobs
        ),
        "estimated_dependency_bytes": dependency_bytes,
        "summary": {
            "reference_count": len(references),
            "package_input_count": _classification_count(
                references, "Package Input"
            ),
            "skipped_cache_count": skipped_cache_count,
            "skipped_unsupported_count": skipped_unsupported_count,
            "skipped_missing_count": skipped_missing_count,
            "skipped_count": skipped_cache_count
            + skipped_unsupported_count
            + skipped_missing_count,
            "excluded_count": skipped_cache_count
            + skipped_unsupported_count
            + skipped_missing_count,
            "missing_count": skipped_missing_count,
            "hda_count": len(external_hdas),
        },
    }


def manifest_dependencies(dependencies, packaged_status="Copied"):
    allowed = (
        "node_path",
        "node_type",
        "parameter",
        "parameter_name",
        "original_value",
        "reported_path",
        "evaluated_path",
        "resolved_pattern",
        "extension",
        "category",
        "classification",
        "status",
        "reason",
        "error",
        "locked",
        "has_keyframes",
        "has_expression",
        "copy_job_key",
        "material_folder",
        "packaged_path",
    )
    result = []
    for item in dependencies:
        manifest_item = {
            key: item.get(key) for key in allowed if key in item
        }
        if item.get("classification") == "Package Input":
            manifest_item["status"] = packaged_status
        result.append(manifest_item)
    return result


def manifest_copy_jobs(copy_jobs):
    result = []
    for job in copy_jobs:
        result.append(
            {
                "source_key": job["source_key"],
                "kind": job["kind"],
                "category": job["category"],
                "source_pattern": job["source_pattern"],
                "source_files": list(job["source_files"]),
                "material_folder": job["material_folder"],
                "destination": job.get("destination", ""),
                "files": [
                    os.path.basename(path) for path in job["source_files"]
                ],
                "file_count": job["file_count"],
                "total_bytes": job["total_bytes"],
                "result": job.get("result", ""),
            }
        )
    return result


def to_houdini_path(path):
    return path.replace("\\", "/")


def _create_copy_job(
    source_key,
    category,
    material,
    pattern,
    source_files,
    is_sequence,
):
    return {
        "source_key": source_key,
        "category": category,
        "material_folder": material,
        "source_pattern": pattern,
        "source_files": source_files,
        "kind": "sequence" if is_sequence else "file",
        "file_count": len(source_files),
        "total_bytes": sum(os.path.getsize(path) for path in source_files),
    }


def _copy_source_key(pattern, source_files, is_sequence):
    if is_sequence:
        return "sequence:%s|%s" % (
            _path_key(os.path.dirname(pattern)),
            os.path.normcase(os.path.basename(pattern)),
        )
    return "file:%s" % _path_key(source_files[0])


def _material_name(filename):
    clean = FRAME_TOKEN_PATTERN.sub("", filename)
    lower = clean.lower()
    if lower.endswith(".bgeo.sc"):
        clean = clean[:-9]
    elif lower.endswith(".geo.gz"):
        clean = clean[:-7]
    else:
        clean = os.path.splitext(clean)[0]
    clean = INVALID_MATERIAL_CHARS.sub("_", clean)
    clean = clean.strip(" ._-")
    return clean or "dependency"


def _allocate_material_folder(category, base, source_key, used_names):
    category_names = used_names.setdefault(category, {})
    if base not in category_names:
        category_names[base] = source_key
        return base
    if category_names[base] == source_key:
        return base
    suffix = 2
    while True:
        candidate = "%s_%d" % (base, suffix)
        if candidate not in category_names:
            category_names[candidate] = source_key
            return candidate
        if category_names[candidate] == source_key:
            return candidate
        suffix += 1


def _classification_count(references, classification):
    return sum(
        1
        for item in references
        if item.get("classification") == classification
    )


def _is_readable_file(path):
    if not path or not os.path.isfile(path):
        return False
    try:
        with open(path, "rb") as handle:
            handle.read(1)
        return True
    except OSError:
        return False


def _path_key(path):
    return os.path.normcase(os.path.abspath(os.path.normpath(path)))
