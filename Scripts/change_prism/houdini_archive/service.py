from __future__ import unicode_literals

import datetime
import getpass
import json
import os
import shutil

from change_prism import archive_core
from change_prism.houdini_archive import archive_planning, runner


SCENE_EXTENSIONS = (".hip", ".hiplc", ".hipnc")
COPY_CHUNK_SIZE = 8 * 1024 * 1024


ArchiveError = archive_core.ArchiveError


class PreflightError(ArchiveError):
    pass


class PackageExecutionError(ArchiveError):
    pass


class PackageCancelled(ArchiveError):
    pass


def find_shot_root(source_hip):
    return archive_core.find_shot_root(source_hip)


def build_package_plan(
    source_hip,
    archive_root,
    hython_executable=None,
    worker_env=None,
):
    """Inspect a HIP with hython and return a JSON-serializable plan."""
    source_hip = os.path.abspath(os.fspath(source_hip))
    archive_root = os.path.abspath(os.fspath(archive_root))
    if not os.path.isfile(source_hip):
        raise PreflightError("Houdini scene does not exist:\n%s" % source_hip)
    extension = os.path.splitext(source_hip)[1].lower()
    if extension not in SCENE_EXTENSIONS:
        raise PreflightError(
            "Only .hip, .hiplc and .hipnc files can be archived:\n%s"
            % source_hip
        )

    try:
        source_version = runner.read_hip_version(source_hip)
        selected = runner.resolve_hython(
            source_version,
            explicit_path=hython_executable,
            environ=worker_env,
        )
        inspection = runner.run_worker(
            selected["path"],
            "inspect",
            source_hip,
            worker_env=worker_env,
        )
    except runner.RunnerError as exc:
        raise PreflightError(str(exc))

    errors = list(inspection.get("errors") or [])
    if inspection.get("houdini_version") != selected["version"]:
        errors.append(
            "The Houdini Worker reported version %s, expected %s."
            % (
                inspection.get("houdini_version", "unknown"),
                selected["version"],
            )
        )
    if errors:
        raise PreflightError(
            "Houdini Archive preflight failed:\n\n- "
            + "\n- ".join(str(error) for error in errors)
        )

    try:
        copy_plan = archive_planning.build_copy_plan(inspection)
    except archive_planning.PlanningError as exc:
        raise PreflightError(str(exc))
    references = copy_plan["dependencies"]
    copy_jobs = copy_plan["copy_jobs"]
    external_hdas = copy_plan["external_hdas"]

    scene_context = archive_core.infer_scene_context(source_hip)
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
    source_stem = os.path.splitext(os.path.basename(source_hip))[0]
    packaged_name = "%s_archive_%s%s" % (
        source_stem,
        proposed_version,
        extension,
    )
    dependency_bytes = copy_plan["estimated_dependency_bytes"]
    estimated_total_bytes = dependency_bytes + os.path.getsize(source_hip)
    summary = dict(copy_plan["summary"])
    return {
        "schema_version": 2,
        "application": "houdini",
        "source_hip": source_hip,
        "archive_root": archive_root,
        "version_root": version_root,
        "version_scope": (
            "task"
            if version_root != archive_root
            else "legacy"
        ),
        "proposed_version": proposed_version,
        "packaged_hip_name": packaged_name,
        "source_extension": extension,
        "department": scene_context["department"],
        "task": scene_context["task"],
        "source_houdini_version": source_version,
        "hython_executable": selected["path"],
        "hython_version": selected["version"],
        "version_warning": selected["warning"],
        "worker_environment": _serializable_environment(worker_env),
        "houdini_version": inspection.get("houdini_version", ""),
        "python_version": inspection.get("python_version", ""),
        "save_mode": inspection.get("save_mode", ""),
        "fps": inspection.get("fps"),
        "frame_range": inspection.get("frame_range", []),
        "playback_range": inspection.get("playback_range", []),
        "load_warning": inspection.get("load_warning", ""),
        "inspection_log": inspection.get("worker_log", ""),
        "dependencies": references,
        "external_hdas": external_hdas,
        "copy_jobs": copy_jobs,
        "estimated_file_count": copy_plan["estimated_file_count"] + 1,
        "estimated_dependency_bytes": dependency_bytes,
        "estimated_total_bytes": estimated_total_bytes,
        "available_bytes": archive_core.get_available_bytes(version_root),
        "source_hip_stat": archive_core.file_fingerprint(source_hip),
        "summary": summary,
    }


def execute_background_package(
    source_hip,
    archive_root,
    hython_executable=None,
    worker_env=None,
    is_cancelled=None,
):
    """Create an Archive with one hython launch and copy after it exits."""
    source_hip = os.path.abspath(os.fspath(source_hip))
    archive_root = os.path.abspath(os.fspath(archive_root))
    if not os.path.isfile(source_hip):
        raise PackageExecutionError(
            "Houdini scene does not exist:\n%s" % source_hip
        )
    extension = os.path.splitext(source_hip)[1].lower()
    if extension not in SCENE_EXTENSIONS:
        raise PackageExecutionError(
            "Only .hip, .hiplc and .hipnc files can be archived:\n%s"
            % source_hip
        )

    try:
        source_version = runner.read_hip_version(source_hip)
        selected = runner.resolve_hython(
            source_version,
            explicit_path=hython_executable,
            environ=worker_env,
        )
    except runner.RunnerError as exc:
        raise PackageExecutionError(str(exc))

    scene_context = archive_core.infer_scene_context(source_hip)
    version_root = archive_core.get_task_archive_root(
        archive_root,
        scene_context["department"],
        scene_context["task"],
    )
    version_scope = "task" if version_root != archive_root else "legacy"
    source_stat = archive_core.file_fingerprint(source_hip)
    version_path = ""
    try:
        _raise_if_cancelled(is_cancelled)
        version, version_path = (
            archive_core.reserve_task_version_directory(
                archive_root,
                scene_context["department"],
                scene_context["task"],
            )
        )
        incomplete_path = os.path.join(version_path, ".incomplete")
        with open(incomplete_path, "w", encoding="utf-8") as handle:
            handle.write("Houdini Archive package is being created.\n")

        logs_directory = os.path.join(version_path, "logs")
        os.makedirs(logs_directory)
        source_stem = os.path.splitext(os.path.basename(source_hip))[0]
        packaged_name = "%s_archive_%s%s" % (
            source_stem,
            version,
            extension,
        )
        packaged_hip = os.path.join(version_path, packaged_name)
        manifest_path = os.path.join(version_path, "manifest.json")
        request = {
            "version": version,
            "version_scope": version_scope,
            "version_path": version_path,
            "packaged_hip": packaged_hip,
            "manifest_path": manifest_path,
            "source_extension": extension,
            "source_hip_stat": source_stat,
            "department": scene_context["department"],
            "task": scene_context["task"],
            "created_by": getpass.getuser(),
            "created_at": datetime.datetime.now().astimezone().isoformat(),
            "hython_version": selected["version"],
            "version_warning": selected["warning"],
        }

        try:
            worker_result = runner.run_worker(
                selected["path"],
                "prepare",
                source_hip,
                plan=request,
                worker_env=worker_env,
                is_cancelled=is_cancelled,
            )
        except runner.RunnerCancelled:
            raise PackageCancelled(
                "Houdini Archive packaging was cancelled."
            )
        except runner.RunnerError as exc:
            raise PackageExecutionError(str(exc))

        if worker_result.get("errors"):
            raise PackageExecutionError(
                "The Houdini Archive could not be created:\n\n- "
                + "\n- ".join(worker_result["errors"])
            )
        _assert_source_unchanged(source_hip, source_stat)
        if not os.path.isfile(packaged_hip):
            raise PackageExecutionError(
                "Houdini did not save the Archive scene:\n%s"
                % packaged_hip
            )
        if not os.path.isfile(manifest_path):
            raise PackageExecutionError(
                "Houdini did not write the Archive manifest:\n%s"
                % manifest_path
            )

        with open(manifest_path, "r", encoding="utf-8") as handle:
            manifest = json.load(handle)
        copy_jobs = manifest.get("copy_jobs", [])
        required_bytes = sum(
            int(job.get("total_bytes", 0)) for job in copy_jobs
        )
        available_bytes = archive_core.get_available_bytes(version_path)
        if (
            available_bytes is not None
            and required_bytes > available_bytes
        ):
            raise PackageExecutionError(
                "Not enough free space for the Houdini Archive.\n"
                "Required: %s\nAvailable: %s"
                % (
                    archive_core.format_bytes(required_bytes),
                    archive_core.format_bytes(available_bytes),
                )
            )

        dependencies_root = os.path.join(version_path, "dependencies")
        if copy_jobs:
            os.makedirs(dependencies_root)
        copied_bytes = 0
        validation = []
        for job in copy_jobs:
            _raise_if_cancelled(is_cancelled)
            destination = os.path.join(
                dependencies_root,
                job["category"],
                job["material_folder"],
            )
            os.makedirs(destination)
            job["destination"] = archive_planning.to_houdini_path(
                os.path.relpath(destination, version_path)
            )
            job_valid = True
            for source_file in job["source_files"]:
                _raise_if_cancelled(is_cancelled)
                target = os.path.join(
                    destination, os.path.basename(source_file)
                )
                copied_bytes = _copy_file_chunked(
                    source_file,
                    target,
                    copied_bytes,
                    required_bytes,
                    None,
                    is_cancelled,
                    "",
                )
                if (
                    not os.path.isfile(target)
                    or os.path.getsize(target) != os.path.getsize(source_file)
                ):
                    job_valid = False
            job["result"] = "copied" if job_valid else "failed"
            validation.append(
                {
                    "check": "copied_payload",
                    "path": job["destination"],
                    "valid": job_valid,
                }
            )
            if not job_valid:
                raise PackageExecutionError(
                    "A copied dependency failed size validation:\n%s"
                    % job["source_pattern"]
                )

        completion_status = manifest.pop(
            "completion_status", "Complete"
        )
        manifest["status"] = completion_status
        manifest["validation"].extend(validation)
        for dependency in manifest.get("dependencies", []):
            if dependency.get("classification") == "Package Input":
                dependency["status"] = "Copied"
        for hda in manifest.get("external_hdas", []):
            hda["result"] = "copied"
        manifest["copy_jobs"] = archive_planning.manifest_copy_jobs(
            copy_jobs
        )
        manifest["summary"]["copied_dependency_count"] = (
            manifest["summary"].get("package_input_count", 0)
        )
        manifest["summary"]["total_bytes"] = (
            copied_bytes + os.path.getsize(packaged_hip)
        )
        temporary_manifest = manifest_path + ".tmp"
        with open(temporary_manifest, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary_manifest, manifest_path)

        log_path = os.path.join(logs_directory, "hython.log")
        with open(log_path, "w", encoding="utf-8") as handle:
            handle.write(
                "Hython: %s\nSource: %s\nArchive scene: %s\n\n%s"
                % (
                    selected["path"],
                    source_hip,
                    packaged_hip,
                    worker_result.get("worker_log", "").strip(),
                )
            )
            handle.write("\n")
        os.remove(incomplete_path)
        return {
            "version": version,
            "version_path": version_path,
            "packaged_hip": packaged_hip,
            "manifest_path": manifest_path,
            "reference_count": manifest["summary"][
                "reference_count"
            ],
            "copy_job_count": len(copy_jobs),
            "file_count": manifest["summary"]["file_count"],
            "total_bytes": manifest["summary"]["total_bytes"],
            "status": manifest["status"],
            "skipped_count": manifest["summary"]["skipped_count"],
            "skipped_missing_count": manifest["summary"][
                "skipped_missing_count"
            ],
        }
    except PackageCancelled:
        archive_core.cleanup_failed_version(version_path)
        raise
    except Exception as exc:
        cleanup_error = archive_core.cleanup_failed_version(version_path)
        if isinstance(exc, ArchiveError):
            if cleanup_error:
                raise PackageExecutionError(
                    "%s\n\nCould not clean the incomplete Archive:\n%s"
                    % (exc, cleanup_error)
                )
            raise
        message = "Could not create the Houdini Archive:\n%s" % exc
        if cleanup_error:
            message += (
                "\n\nCould not clean the incomplete Archive:\n%s"
                % cleanup_error
            )
        raise PackageExecutionError(message)


def execute_package(plan, progress_callback=None, is_cancelled=None):
    if not isinstance(plan, dict):
        raise PackageExecutionError("Package plan must be a dictionary.")
    source_hip = plan.get("source_hip", "")
    archive_root = plan.get("archive_root", "")
    try:
        fresh_plan = build_package_plan(
            source_hip,
            archive_root,
            hython_executable=plan.get("hython_executable"),
            worker_env=plan.get("worker_environment"),
        )
    except PreflightError as exc:
        raise PackageExecutionError(str(exc))
    except OSError as exc:
        # The source can disappear between the existence check and the
        # stat/size probes; report it like any other preflight failure.
        raise PackageExecutionError(
            "Could not inspect the source Houdini scene:\n%s" % exc
        )
    if fresh_plan["source_hip_stat"] != plan.get("source_hip_stat"):
        raise PackageExecutionError(
            "The source Houdini scene changed after preflight. "
            "Run the package command again to review the updated plan."
        )

    version_path = ""
    try:
        required_bytes = fresh_plan["estimated_total_bytes"]
        available_bytes = fresh_plan["available_bytes"]
        if available_bytes is not None and required_bytes > available_bytes:
            raise PackageExecutionError(
                "Not enough free space for the Houdini Archive.\n"
                "Required: %s\nAvailable: %s"
                % (
                    archive_core.format_bytes(required_bytes),
                    archive_core.format_bytes(available_bytes),
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
            handle.write("Houdini Archive package is being created.\n")

        dependencies_root = os.path.join(version_path, "dependencies")
        logs_directory = os.path.join(version_path, "logs")
        os.makedirs(dependencies_root)
        os.makedirs(logs_directory)

        total_bytes = fresh_plan["estimated_total_bytes"]
        copied_bytes = 0
        _notify_progress(
            progress_callback,
            copied_bytes,
            total_bytes,
            "Preparing Houdini Archive %s" % version,
        )
        for job in fresh_plan["copy_jobs"]:
            _raise_if_cancelled(is_cancelled)
            destination = os.path.join(
                dependencies_root,
                job["category"],
                job["material_folder"],
            )
            os.makedirs(destination)
            job["destination"] = _to_houdini_path(
                os.path.relpath(destination, version_path)
            )
            for source_file in job["source_files"]:
                _raise_if_cancelled(is_cancelled)
                target = os.path.join(
                    destination, os.path.basename(source_file)
                )
                copied_bytes = _copy_file_chunked(
                    source_file,
                    target,
                    copied_bytes,
                    total_bytes,
                    progress_callback,
                    is_cancelled,
                    "Copying %s" % job["material_folder"],
                )
            job["result"] = "copied"

        source_stem = os.path.splitext(os.path.basename(source_hip))[0]
        packaged_name = "%s_archive_%s%s" % (
            source_stem,
            version,
            fresh_plan["source_extension"],
        )
        packaged_hip = os.path.join(version_path, packaged_name)
        _assert_source_unchanged(
            source_hip, fresh_plan["source_hip_stat"]
        )
        copied_bytes = _copy_file_chunked(
            source_hip,
            packaged_hip,
            copied_bytes,
            total_bytes,
            progress_callback,
            is_cancelled,
            "Copying source Houdini scene",
        )
        _assert_source_unchanged(
            source_hip, fresh_plan["source_hip_stat"]
        )

        rewrite_plan = {
            "dependencies": fresh_plan["dependencies"],
            "reserved_version_path": version_path,
            "frame_range": fresh_plan["frame_range"],
        }
        _notify_progress(
            progress_callback,
            total_bytes,
            total_bytes,
            "Rewriting and validating the Archive scene",
        )
        try:
            rewrite_result = runner.run_worker(
                fresh_plan["hython_executable"],
                "rewrite",
                packaged_hip,
                plan=rewrite_plan,
                worker_env=fresh_plan.get("worker_environment"),
                is_cancelled=is_cancelled,
            )
        except runner.RunnerCancelled:
            raise PackageCancelled("Houdini Archive packaging was cancelled.")
        except runner.RunnerError as exc:
            raise PackageExecutionError(str(exc))
        if rewrite_result.get("errors"):
            raise PackageExecutionError(
                "The Archive scene could not be validated:\n\n- "
                + "\n- ".join(rewrite_result["errors"])
            )

        worker_log = (
            "Hython: %s\n"
            "Source: %s\n"
            "Archive scene: %s\n\n"
            "[Inspect]\n%s\n\n"
            "[Rewrite and validation]\n%s\n"
            % (
                fresh_plan["hython_executable"],
                source_hip,
                packaged_hip,
                fresh_plan.get("inspection_log", "").strip(),
                rewrite_result.get("worker_log", "").strip(),
            )
        )
        log_path = os.path.join(logs_directory, "hython.log")
        with open(log_path, "w", encoding="utf-8") as handle:
            handle.write(worker_log)
            if worker_log and not worker_log.endswith("\n"):
                handle.write("\n")

        for hda in fresh_plan["external_hdas"]:
            hda["result"] = "copied"
        excluded = fresh_plan["summary"]["skipped_count"] > 0 or bool(
            fresh_plan["external_hdas"]
        )
        created_at = datetime.datetime.now().astimezone().isoformat()
        manifest = {
            "schema_version": 2,
            "application": "houdini",
            "status": (
                "Complete with Exclusions" if excluded else "Complete"
            ),
            "archive_version": version,
            "task_version": version,
            "version_scope": fresh_plan["version_scope"],
            "source_scene": source_hip,
            "packaged_scene": _to_houdini_path(
                os.path.relpath(packaged_hip, version_path)
            ),
            "source_scene_stat": fresh_plan["source_hip_stat"],
            "source_extension": fresh_plan["source_extension"],
            "department": fresh_plan["department"],
            "task": fresh_plan["task"],
            "save_mode": fresh_plan["save_mode"],
            "houdini_version": fresh_plan["houdini_version"],
            "hython_version": fresh_plan["hython_version"],
            "python_version": fresh_plan["python_version"],
            "fps": fresh_plan["fps"],
            "frame_range": fresh_plan["frame_range"],
            "playback_range": fresh_plan["playback_range"],
            "created_by": getpass.getuser(),
            "created_at": created_at,
            "version_warning": fresh_plan["version_warning"],
            "load_warning": fresh_plan["load_warning"],
            "rewrite_load_warning": rewrite_result.get(
                "load_warning", ""
            ),
            "reopen_warning": rewrite_result.get("reopen_warning", ""),
            "validation": rewrite_result.get("validation", []),
            "summary": {
                "reference_count": len(fresh_plan["dependencies"]),
                "package_input_count": fresh_plan["summary"][
                    "package_input_count"
                ],
                "skipped_cache_count": fresh_plan["summary"][
                    "skipped_cache_count"
                ],
                "skipped_unsupported_count": fresh_plan["summary"][
                    "skipped_unsupported_count"
                ],
                "skipped_missing_count": fresh_plan["summary"][
                    "skipped_missing_count"
                ],
                "skipped_count": fresh_plan["summary"]["skipped_count"],
                "excluded_count": fresh_plan["summary"]["excluded_count"],
                "missing_count": fresh_plan["summary"]["missing_count"],
                "copied_dependency_count": fresh_plan["summary"][
                    "package_input_count"
                ],
                "hda_count": len(fresh_plan["external_hdas"]),
                "copy_job_count": len(fresh_plan["copy_jobs"]),
                "file_count": fresh_plan["estimated_file_count"],
                "total_bytes": fresh_plan["estimated_total_bytes"],
            },
            "dependencies": _manifest_dependencies(
                fresh_plan["dependencies"]
            ),
            "external_hdas": fresh_plan["external_hdas"],
            "copy_jobs": _manifest_copy_jobs(fresh_plan["copy_jobs"]),
        }
        manifest_path = os.path.join(version_path, "manifest.json")
        temporary_manifest = manifest_path + ".tmp"
        with open(temporary_manifest, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary_manifest, manifest_path)
        os.remove(incomplete_path)
        _notify_progress(
            progress_callback,
            total_bytes,
            total_bytes,
            "Houdini Archive %s complete" % version,
        )
        return {
            "version": version,
            "version_path": version_path,
            "packaged_hip": packaged_hip,
            "manifest_path": manifest_path,
            "reference_count": len(fresh_plan["dependencies"]),
            "copy_job_count": len(fresh_plan["copy_jobs"]),
        }
    except PackageCancelled:
        archive_core.cleanup_failed_version(version_path)
        raise
    except Exception as exc:
        cleanup_error = archive_core.cleanup_failed_version(version_path)
        if isinstance(exc, ArchiveError):
            if cleanup_error:
                raise PackageExecutionError(
                    "%s\n\nCould not clean the incomplete Archive:\n%s"
                    % (exc, cleanup_error)
                )
            raise
        message = "Could not create the Houdini Archive:\n%s" % exc
        if cleanup_error:
            message += "\n\nCould not clean the incomplete Archive:\n%s" % cleanup_error
        raise PackageExecutionError(message)


def format_bytes(value):
    return archive_core.format_bytes(value)


def _copy_file_chunked(
    source,
    destination,
    completed,
    total,
    progress_callback,
    is_cancelled,
    message,
):
    with open(source, "rb") as source_handle:
        with open(destination, "wb") as destination_handle:
            while True:
                _raise_if_cancelled(is_cancelled)
                chunk = source_handle.read(COPY_CHUNK_SIZE)
                if not chunk:
                    break
                destination_handle.write(chunk)
                completed += len(chunk)
                _notify_progress(
                    progress_callback,
                    completed,
                    total,
                    message,
                )
    shutil.copystat(source, destination)
    return completed


def _raise_if_cancelled(is_cancelled):
    if is_cancelled and is_cancelled():
        raise PackageCancelled("Houdini Archive packaging was cancelled.")


def _notify_progress(callback, completed, total, message):
    if callback:
        callback(completed, total, message)


def _manifest_dependencies(dependencies):
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
            manifest_item["status"] = "Copied"
        result.append(manifest_item)
    return result


def _manifest_copy_jobs(copy_jobs):
    result = []
    for job in copy_jobs:
        result.append(
            {
                "kind": job["kind"],
                "category": job["category"],
                "source_pattern": job["source_pattern"],
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


def _serializable_environment(environment):
    if not environment:
        return {}
    return {
        str(key): str(value)
        for key, value in environment.items()
        if value is not None
    }


def _assert_source_unchanged(source_hip, expected_stat):
    try:
        current_stat = archive_core.file_fingerprint(source_hip)
    except OSError:
        current_stat = None
    if current_stat != expected_stat:
        raise PackageExecutionError(
            "The source Houdini scene changed during packaging. "
            "Packaging has been stopped."
        )


def _to_houdini_path(path):
    return path.replace("\\", "/")
