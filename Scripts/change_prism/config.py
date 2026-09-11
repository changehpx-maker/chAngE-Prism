import os


CONFIG_SECTION = "change_prism"
SETTINGS_LOCATION = "Prism Settings > User > chAngE_Prism"
ASSET_LIBRARY_THUMBNAIL_SIZES = ("small", "medium", "large")

_OS_DEFAULTS = {
    "server_root": "",
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
    asset_library = data.get("asset_library", {})
    if not isinstance(asset_library, dict):
        asset_library = {}

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
        "asset_library": {
            "sources": _normalize_asset_library_sources(
                asset_library.get("sources", [])
            ),
            "thumbnail_sizes": _normalize_asset_library_thumbnail_sizes(
                asset_library.get("thumbnail_sizes", {})
            ),
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


def get_asset_library_sources(core):
    return load_config(core)["asset_library"]["sources"]


def save_asset_library_sources(core, sources):
    section = _read_section(core)
    library = section.get("asset_library", {})
    library = dict(library) if isinstance(library, dict) else {}
    library["sources"] = _normalize_asset_library_sources(sources)
    core.setConfig(cat=CONFIG_SECTION, param="asset_library", val=library)


def get_asset_library_thumbnail_size(core, host_key):
    sizes = load_config(core)["asset_library"]["thumbnail_sizes"]
    return sizes.get(str(host_key or "").lower(), "medium")


def save_asset_library_thumbnail_size(core, host_key, size_key):
    host_key = str(host_key or "").lower()
    if host_key not in ("houdini", "standalone"):
        raise ValueError("Unsupported Asset Library host: %s" % host_key)
    size_key = str(size_key or "").lower()
    if size_key not in ASSET_LIBRARY_THUMBNAIL_SIZES:
        raise ValueError(
            "Unsupported Asset Library thumbnail size: %s" % size_key
        )
    section = _read_section(core)
    library = section.get("asset_library", {})
    library = dict(library) if isinstance(library, dict) else {}
    sizes = _normalize_asset_library_thumbnail_sizes(
        library.get("thumbnail_sizes", {})
    )
    sizes[host_key] = size_key
    library["thumbnail_sizes"] = sizes
    core.setConfig(cat=CONFIG_SECTION, param="asset_library", val=library)


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


def _normalize_asset_library_sources(sources):
    normalized = []
    seen = set()
    for item in sources if isinstance(sources, (list, tuple)) else []:
        if isinstance(item, dict):
            path = item.get("path", "")
            enabled = bool(item.get("enabled", True))
        else:
            path = item
            enabled = True
        path = str(path or "").strip()
        if not path:
            continue
        path = os.path.normpath(os.path.abspath(os.path.expanduser(path)))
        key = os.path.normcase(path)
        if key in seen:
            continue
        seen.add(key)
        normalized.append({"path": path, "enabled": enabled})
    return normalized


def _normalize_asset_library_thumbnail_sizes(sizes):
    sizes = dict(sizes) if isinstance(sizes, dict) else {}
    normalized = {}
    for host_key in ("houdini", "standalone"):
        value = str(sizes.get(host_key, "") or "").lower()
        if value in ASSET_LIBRARY_THUMBNAIL_SIZES:
            normalized[host_key] = value
    return normalized
