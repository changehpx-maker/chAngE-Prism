import json
import os
import re
import shutil
import subprocess
import sys


_FRAME_RE = re.compile(r"^(.*?)(\d+)$")
_INVENTORY_CACHE = {}


def _clean_inventory_name(value):
    value = value.strip().replace(" (*)", "").strip()
    value = value.strip('"').strip()
    if value.endswith(" (linear)"):
        value = value[:-9].rstrip()
    return value


def _split_inventory_values(value):
    values = []
    for quoted, plain in re.findall(r'"([^"]+)"|([^,]+)', value):
        item = _clean_inventory_name(quoted or plain)
        if item and item != "(*)":
            values.append(item)
    return values


def parse_colorconfig_info(text):
    """Parse the stable sections printed by ``oiiotool --colorconfiginfo``."""
    inventory = {
        "config": "",
        "colorspaces": [],
        "roles": {},
        "displays": {},
        "default_display": "",
        "default_views": {},
    }
    section = ""
    current_display = ""
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if line.startswith("Color config:"):
            inventory["config"] = line.split(":", 1)[1].strip()
            continue
        if line == "Known color spaces:":
            section = "colorspaces"
            continue
        if line == "Known roles:":
            section = "roles"
            continue
        if line == "Known looks:":
            section = "looks"
            continue
        if line.startswith("Known displays:"):
            section = "displays"
            continue
        if line == "Named transforms:":
            section = "named_transforms"
            continue

        if section == "colorspaces" and line.startswith("- "):
            name = _clean_inventory_name(line[2:])
            if name and name not in inventory["colorspaces"]:
                inventory["colorspaces"].append(name)
        elif section == "roles" and line.startswith("- ") and "->" in line:
            role, colorspace = line[2:].split("->", 1)
            inventory["roles"][role.strip()] = _clean_inventory_name(colorspace)
        elif section == "displays" and line.startswith("- "):
            current_display = _clean_inventory_name(line[2:])
            inventory["displays"].setdefault(current_display, [])
            if "(*)" in line:
                inventory["default_display"] = current_display
        elif section == "displays" and line.startswith("views:") and current_display:
            view_text = line.split(":", 1)[1].strip()
            views = _split_inventory_values(view_text)
            inventory["displays"][current_display] = views
            default_match = re.search(r'"([^"]+)"\s*\(\*\)', view_text)
            if default_match:
                inventory["default_views"][current_display] = default_match.group(1)
            elif views:
                inventory["default_views"][current_display] = views[0]

    return inventory


def choose_inventory_defaults(inventory):
    colorspaces = inventory.get("colorspaces") or []
    roles = inventory.get("roles") or {}
    displays = inventory.get("displays") or {}

    input_space = roles.get("scene_linear", "")
    if input_space not in colorspaces:
        input_space = next(
            (c for c in colorspaces if c.lower() in ("acescg", "aces - acescg")),
            next((c for c in colorspaces if "acescg" in c.lower()), ""),
        )

    display = ""
    preferences = (
        "rec.1886 rec.709",
        "gamma 2.4 rec.709",
        "rec.709",
        "srgb",
    )
    for preference in preferences:
        display = next(
            (name for name in displays if preference in name.lower()), ""
        )
        if display:
            break
    display = display or inventory.get("default_display", "")
    if not display and displays:
        display = next(iter(displays))

    views = displays.get(display, [])
    view = ""
    view_preferences = (
        "aces 1.0 sdr-video",
        "aces 2.0 - sdr 100 nits (rec.709)",
        "aces sdr",
        "sdr",
    )
    for preference in view_preferences:
        view = next((name for name in views if preference in name.lower()), "")
        if view:
            break
    view = view or inventory.get("default_views", {}).get(display, "")
    if not view and views:
        view = views[0]

    return input_space, display, view


def validate_color_selection(inventory, input_space, display, view):
    errors = []
    if input_space not in (inventory.get("colorspaces") or []):
        errors.append("Input colorspace not found: %s" % input_space)
    if display not in (inventory.get("displays") or {}):
        errors.append("Display not found: %s" % display)
    elif view not in inventory["displays"].get(display, []):
        errors.append("View not found for %s: %s" % (display, view))
    return errors


def select_ocio_config(project_key, config_data=None, environ=None):
    config_data = config_data or {}
    environ = environ if environ is not None else os.environ
    converter_cfg = config_data.get("ocio_converter", {})
    overrides = converter_cfg.get("project_overrides", {})
    override = overrides.get(project_key, "") if project_key else ""
    if override:
        return override, "project_override"
    env_value = environ.get("OCIO", "")
    if env_value:
        return env_value, "environment"
    return "ocio://default", "oiio_default"


def project_config_key(core):
    path = getattr(core, "projectPath", "") or ""
    return os.path.normcase(os.path.normpath(path)) if path else "__no_project__"


def save_project_override(config_path, project_key, ocio_path):
    data = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as stream:
                data = json.load(stream)
        except (OSError, ValueError):
            data = {}
    converter_cfg = data.setdefault("ocio_converter", {})
    overrides = converter_cfg.setdefault("project_overrides", {})
    if ocio_path:
        overrides[project_key] = ocio_path
    else:
        overrides.pop(project_key, None)
    with open(config_path, "w", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)


def find_tools(core=None):
    ffmpeg = ""
    if core is not None:
        try:
            ffmpeg = core.media.getFFmpeg(validate=True) or ""
        except Exception:
            ffmpeg = ""

    executable = "oiiotool.exe" if sys.platform == "win32" else "oiiotool"
    oiiotool = ""
    prism_libs = getattr(core, "prismLibs", "") if core is not None else ""
    if prism_libs:
        candidate = os.path.join(
            prism_libs, "PythonLibs", "Python3", "OpenImageIO", "bin", executable
        )
        if os.path.isfile(candidate):
            oiiotool = candidate

    ffmpeg = ffmpeg if ffmpeg and os.path.isfile(ffmpeg) else (shutil.which("ffmpeg") or "")
    oiiotool = oiiotool or (shutil.which("oiiotool") or "")
    return {"ffmpeg": ffmpeg, "oiiotool": oiiotool}


def _inventory_cache_key(oiiotool, config):
    values = [os.path.normcase(os.path.abspath(oiiotool)), config]
    for path in (oiiotool, config):
        if not path or str(path).startswith("ocio://"):
            values.append(None)
            continue
        try:
            stat = os.stat(path)
            values.append((stat.st_mtime_ns, stat.st_size))
        except OSError:
            values.append(None)
    return tuple(values)


def read_colorconfig_inventory(oiiotool, config, timeout=30):
    cache_key = _inventory_cache_key(oiiotool, config)
    cached = _INVENTORY_CACHE.get(cache_key)
    if cached:
        return cached
    args = [oiiotool]
    if config:
        args.extend(["--colorconfig", config])
    args.append("--colorconfiginfo")
    result = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        shell=False,
    )
    output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    if result.returncode:
        raise RuntimeError(output.strip() or "Failed to read OCIO config")
    inventory = parse_colorconfig_info(output)
    if not inventory["colorspaces"] or not inventory["displays"]:
        raise RuntimeError("The OCIO config contains no usable colorspaces/displays")
    _INVENTORY_CACHE[cache_key] = inventory
    return inventory


def _sequence_key(path):
    directory = os.path.dirname(path)
    stem, extension = os.path.splitext(os.path.basename(path))
    match = _FRAME_RE.match(stem)
    if not match or match.group(1).lower().endswith("v"):
        return (os.path.normcase(path),), None
    prefix, frame_text = match.groups()
    return (
        os.path.normcase(directory),
        os.path.normcase(prefix),
        len(frame_text),
        extension.lower(),
    ), (prefix, len(frame_text), int(frame_text), extension)


def collect_exr_jobs(paths):
    """Return sequence jobs and user-facing validation errors."""
    jobs = []
    errors = []
    seen = set()
    for raw_path in paths or []:
        path = os.path.abspath(os.path.normpath(str(raw_path)))
        if os.path.splitext(path)[1].lower() != ".exr":
            errors.append("Not an EXR file: %s" % path)
            continue
        if not os.path.isfile(path):
            errors.append("File not found: %s" % path)
            continue

        key, frame_data = _sequence_key(path)
        if key in seen:
            continue
        seen.add(key)

        if not frame_data:
            jobs.append({
                "name": os.path.basename(path),
                "files": [path],
                "input_pattern": path,
                "first": None,
                "last": None,
                "padding": 0,
                "frame_count": 1,
                "missing_frames": [],
                "is_sequence": False,
                "source_path": path,
            })
            continue

        prefix, padding, selected_frame, extension = frame_data
        expression = re.compile(
            r"^%s(\d{%d})%s$" % (
                re.escape(prefix), padding, re.escape(extension)
            ),
            re.IGNORECASE,
        )
        matches = []
        try:
            names = os.listdir(os.path.dirname(path))
        except OSError as exc:
            errors.append("Cannot scan %s: %s" % (os.path.dirname(path), exc))
            continue
        for name in names:
            match = expression.match(name)
            if match:
                matches.append((int(match.group(1)), os.path.join(os.path.dirname(path), name)))

        matches.sort(key=lambda item: item[0])
        if not matches:
            matches = [(selected_frame, path)]
        frames = [item[0] for item in matches]
        first, last = frames[0], frames[-1]
        existing = set(frames)
        missing = [frame for frame in range(first, last + 1) if frame not in existing]
        pattern = os.path.join(
            os.path.dirname(path), "%s%%0%dd%s" % (prefix, padding, extension)
        )
        jobs.append({
            "name": os.path.basename(pattern),
            "files": [item[1] for item in matches],
            "input_pattern": pattern if len(matches) > 1 else path,
            "first": first if len(matches) > 1 else None,
            "last": last if len(matches) > 1 else None,
            "padding": padding if len(matches) > 1 else 0,
            "frame_count": len(matches),
            "missing_frames": missing if len(matches) > 1 else [],
            "is_sequence": len(matches) > 1,
            "source_path": matches[0][1],
        })
    return jobs, errors


def parse_oiio_channels(text):
    channels = []
    for line in (text or "").splitlines():
        match = re.search(r"channel(?: list| names)?\s*:\s*(.+)$", line, re.I)
        if not match:
            continue
        channels = [item.strip() for item in match.group(1).split(",") if item.strip()]
        if channels:
            break
    return channels


def inspect_exr(oiiotool, path, timeout=30):
    result = subprocess.run(
        [oiiotool, "--info", "-v", path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        shell=False,
    )
    output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    if result.returncode:
        raise RuntimeError(output.strip() or "Cannot inspect EXR")
    channels = parse_oiio_channels(output)
    lower = {name.lower() for name in channels}
    missing = [name for name in ("R", "G", "B") if name.lower() not in lower]
    if missing:
        raise RuntimeError("EXR is missing RGB channels: %s" % ", ".join(missing))
    return {"channels": channels, "has_alpha": "a" in lower}


def build_oiiotool_args(
    job,
    output_pattern,
    config,
    input_space,
    display,
    view,
    has_alpha=False,
    data_type="uint16",
    compression="zip",
):
    args = ["--threads", "0"]
    if job.get("is_sequence"):
        args.extend([
            "--parallel-frames",
            "--frames", "%s-%s" % (job["first"], job["last"]),
            "--framepadding", str(job["padding"]),
        ])
    args.extend(["--colorconfig", config, job["input_pattern"]])
    option = "--ociodisplay:from=%s" % input_space
    if has_alpha:
        option += ":unpremult=1"
    args.extend([
        option, display, view,
        "--ch", "R,G,B",
        "-d", data_type,
    ])
    if compression:
        args.extend(["--compression", compression])
    args.extend(["-o", output_pattern])
    return args


def build_ffmpeg_args(
    job,
    input_pattern,
    output_path,
    fps,
    extension,
    prores_encoder="prores_ks",
):
    fps_text = str(float(fps)).rstrip("0").rstrip(".")
    args = ["-hide_banner", "-loglevel", "info", "-framerate", fps_text]
    if job.get("is_sequence"):
        args.extend(["-start_number", str(job["first"])])
    args.extend([
        "-i", input_pattern,
        "-an",
        "-frames:v", str(job["frame_count"]),
        "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2:color=black",
    ])
    if extension == ".mp4":
        args.extend([
            "-c:v", "libx264", "-crf", "18", "-preset", "medium",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        ])
    elif extension == ".mov":
        if prores_encoder not in ("prores_aw", "prores_ks"):
            raise ValueError("Unsupported ProRes encoder: %s" % prores_encoder)
        args.extend([
            "-c:v", prores_encoder, "-profile:v", "3",
            "-pix_fmt", "yuv422p10le",
        ])
    else:
        raise ValueError("Unsupported output extension: %s" % extension)
    args.extend([
        "-color_primaries", "bt709",
        "-color_trc", "bt709",
        "-colorspace", "bt709",
        "-color_range", "tv",
        output_path,
        "-y",
    ])
    return args


def build_validation_args(path, full=False):
    args = ["-hide_banner", "-v", "error", "-i", path]
    if not full:
        args.extend(["-frames:v", "1"])
    args.extend(["-f", "null", "-"])
    return args


def external_output_path(job, extension):
    source = job["source_path"]
    stem = os.path.splitext(os.path.basename(source))[0]
    if job.get("is_sequence"):
        frame_text = str(job["first"]).zfill(job["padding"])
        if stem.endswith(frame_text):
            stem = stem[:-len(frame_text)].rstrip("._-")
    return os.path.join(os.path.dirname(source), stem + ".rec709" + extension)


def staging_output_path(final_path):
    stem, extension = os.path.splitext(final_path)
    return stem + ".chAnGE_tmp" + extension


def validate_fps(value):
    try:
        fps = float(value)
    except (TypeError, ValueError):
        raise ValueError("FPS must be a number")
    if fps <= 0 or fps > 240:
        raise ValueError("FPS must be greater than 0 and no more than 240")
    return fps
