import json
import os
import tempfile
import time


MAX_FAILURE_REPORTS = 20
PLUGIN_TEMP_DIR = "chAngE_Prism"
BATCH_IMPORT_FEATURE = "batch_import"


def get_output_dir(feature, output_type):
    parts = [
        tempfile.gettempdir(),
        PLUGIN_TEMP_DIR,
        BATCH_IMPORT_FEATURE,
    ]
    if feature:
        parts.append(feature)
    parts.append(output_type)
    path = os.path.join(*parts)
    os.makedirs(path, exist_ok=True)
    return path


def get_log_dir(core, category=None):
    del core
    return get_output_dir(category, "logs")


def prune_old_files(directory, prefix="", suffix="", keep=20):
    if keep < 0 or not os.path.isdir(directory):
        return
    entries = []
    with os.scandir(directory) as iterator:
        for entry in iterator:
            try:
                if (
                    entry.is_file()
                    and entry.name.startswith(prefix)
                    and entry.name.endswith(suffix)
                ):
                    entries.append((entry.path, entry.stat().st_mtime))
            except OSError:
                continue
    entries.sort(key=lambda item: item[1], reverse=True)
    for path, _mtime in entries[keep:]:
        try:
            os.remove(path)
        except OSError:
            pass


def write_failure_report(core, project_name, failures):
    if not failures:
        return ""
    safe_project = "".join(
        char if char.isalnum() or char in ("-", "_") else "_"
        for char in (project_name or "project")
    )
    path = os.path.join(
        get_output_dir("reports", "json"),
        "failure_report_%s_%s.json"
        % (safe_project, time.strftime("%Y%m%d_%H%M%S")),
    )
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "project": project_name,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "failures": failures,
            },
            handle,
            ensure_ascii=False,
            indent=2,
        )
    prune_old_files(
        os.path.dirname(path),
        prefix="failure_report_",
        suffix=".json",
        keep=MAX_FAILURE_REPORTS,
    )
    return path
