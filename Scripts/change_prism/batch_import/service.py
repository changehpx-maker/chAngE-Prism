import json
import os
import tempfile
import time


def get_user_data_dir(core):
    user_ini = getattr(core, "userini", "") if core is not None else ""
    if user_ini:
        base = os.path.dirname(os.path.abspath(str(user_ini)))
    else:
        base = tempfile.gettempdir()
    return os.path.join(base, "chAngE_Prism")


def get_log_dir(core, category=None):
    path = os.path.join(get_user_data_dir(core), "logs")
    if category:
        path = os.path.join(path, category)
    os.makedirs(path, exist_ok=True)
    return path


def write_failure_report(core, project_name, failures):
    if not failures:
        return ""
    safe_project = "".join(
        char if char.isalnum() or char in ("-", "_") else "_"
        for char in (project_name or "project")
    )
    path = os.path.join(
        get_log_dir(core, "reports"),
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
    return path
