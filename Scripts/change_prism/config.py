import os
import sys


CONFIG_SECTION = "change_prism"
SETTINGS_LOCATION = "Prism Settings > User > chAngE_Prism"

_OS_DEFAULTS = {
    "server_root": "P:\\" if sys.platform == "win32" else "",
    "local_projects_root": os.path.expanduser("~/Desktop/Projects"),
}


def _read_section(core):
    if core is None:
        return {}
    try:
        data = core.getConfig(cat=CONFIG_SECTION)
    except (AttributeError, TypeError):
        try:
            data = core.getConfig(CONFIG_SECTION)
        except (AttributeError, TypeError):
            data = {}
    return dict(data) if isinstance(data, dict) else {}


def normalize_config(data):
    data = dict(data) if isinstance(data, dict) else {}
    review_copy = data.get("review_copy", {})
    if not isinstance(review_copy, dict):
        review_copy = {}
    ocio_converter = data.get("ocio_converter", {})
    if not isinstance(ocio_converter, dict):
        ocio_converter = {}
    project_overrides = ocio_converter.get("project_overrides", {})
    if not isinstance(project_overrides, dict):
        project_overrides = {}
    pdg = data.get("pdg", {})
    if not isinstance(pdg, dict):
        pdg = {}

    return {
        "server_root": data.get("server_root", "") or _OS_DEFAULTS["server_root"],
        "local_projects_root": (
            data.get("local_projects_root", "")
            or _OS_DEFAULTS["local_projects_root"]
        ),
        "review_copy": {
            "destination_root": review_copy.get("destination_root", "") or "",
        },
        "pdg": {
            "hip_path": pdg.get("hip_path", "") or "",
            "houdini_package_directory": (
                pdg.get("houdini_package_directory", "") or ""
            ),
        },
        "ocio_converter": {
            "project_overrides": dict(project_overrides),
        },
    }


def load_config(core):
    return normalize_config(_read_section(core))


def get_server_root(core):
    return load_config(core)["server_root"]


def get_local_projects_root(core):
    return load_config(core)["local_projects_root"]


def get_review_copy_destination_root(core):
    return load_config(core)["review_copy"]["destination_root"]


def get_pdg_hip_path(core):
    return load_config(core)["pdg"]["hip_path"]


def get_houdini_package_directory(core):
    return load_config(core)["pdg"]["houdini_package_directory"]


def save_config_value(core, key, value):
    if key not in ("server_root", "local_projects_root"):
        raise ValueError("Unsupported chAngE_Prism setting: %s" % key)
    core.setConfig(cat=CONFIG_SECTION, param=key, val=value)


def get_project_config_key(core):
    path = getattr(core, "projectPath", "") or ""
    return os.path.normcase(os.path.normpath(path)) if path else "__no_project__"


def save_ocio_project_override(core, project_key, ocio_path):
    section = _read_section(core)
    converter = section.get("ocio_converter", {})
    converter = dict(converter) if isinstance(converter, dict) else {}
    overrides = converter.get("project_overrides", {})
    overrides = dict(overrides) if isinstance(overrides, dict) else {}
    if ocio_path:
        overrides[project_key] = ocio_path
    else:
        overrides.pop(project_key, None)
    converter["project_overrides"] = overrides
    core.setConfig(cat=CONFIG_SECTION, param="ocio_converter", val=converter)
