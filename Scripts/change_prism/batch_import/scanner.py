import ast
import fnmatch
import functools
import os
import re
import xml.etree.ElementTree as ET


SERVER_STEPS = [
    ("shot_motion", "shot_animation"),
    ("shot_solution", "cloth_solution"),
    ("shot_solution", "hair_solution"),
]

STEP_LABELS = {
    "shot_motion/shot_animation": "Animation",
    "shot_solution/cloth_solution": "Cloth",
    "shot_solution/hair_solution": "Hair",
}

_SOLUTION_STEP_SPEC = [
    ("vfx", ["*.abc"], "abc_files"),
    ("review", ["*.mov"], "mov_files"),
    ("xml", ["*.xml"], "xml_files"),
]

_STEP_FILE_SPEC = {
    "shot_animation": [
        ("fbx", ["*.fbx"], "fbx_files"),
        ("review", ["*.mov"], "mov_files"),
        ("xml", ["*.xml"], "xml_files"),
    ],
    "cloth_solution": _SOLUTION_STEP_SPEC,
    "hair_solution": _SOLUTION_STEP_SPEC,
}


@functools.lru_cache(maxsize=64)
def _list_dirs(path):
    if not os.path.isdir(path):
        return []
    try:
        names = os.listdir(path)
    except OSError:
        return []
    return sorted(
        name
        for name in names
        if os.path.isdir(os.path.join(path, name))
        and not name.startswith(".")
    )


def clear_list_dirs_cache():
    _list_dirs.cache_clear()


def parse_filter_strings(text):
    if not text or not text.strip():
        return []
    parts = [
        part.strip()
        for part in re.split(r"[,\n]+", text)
        if part.strip()
    ]
    return _merge_filter_triplets(parts)


def _merge_filter_triplets(parts):
    result = []
    index = 0
    while index < len(parts):
        current = parts[index].strip()
        if "/" in current.strip("/"):
            result.append(current)
            index += 1
            continue
        if index + 2 < len(parts):
            sequence = parts[index + 1].strip()
            shot = parts[index + 2].strip()
            if current.endswith("/") and sequence.endswith("/"):
                episode = current.rstrip("/")
                sequence = sequence.rstrip("/")
                shot = shot.strip("/")
                if episode and sequence and shot:
                    result.append(
                        "%s/%s/%s" % (episode, sequence, shot)
                    )
                    index += 3
                    continue
        result.append(current)
        index += 1
    return result


def _parse_filter_parts(filter_string):
    parts = [
        part.strip()
        for part in filter_string.split("/")
        if part.strip()
    ]
    keys = ("episode", "sequence", "shot")
    return dict(zip(keys, parts[:3]))


def _disambiguate_filter_parts(filter_parts, publish_shot_dir):
    if "shot" in filter_parts:
        return filter_parts
    result = dict(filter_parts)
    episode_exists = (
        "episode" in result
        and os.path.isdir(
            os.path.join(publish_shot_dir, result["episode"])
        )
    )
    if "sequence" not in result:
        if not episode_exists:
            result["shot"] = result.pop("episode")
    elif not episode_exists:
        result["shot"] = result["sequence"]
        result["sequence"] = result.pop("episode")
    return result


def _convert_attr_value(value):
    if not value:
        return value
    for converter in (int, float):
        try:
            return converter(value)
        except (TypeError, ValueError):
            pass
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return value


def parse_xml_attributes(xml_path):
    try:
        root = ET.parse(xml_path).getroot()
        attributes = {}
        for attribute in root.iter("attribute"):
            attributes[attribute.get("name", "")] = _convert_attr_value(
                attribute.get("value", "")
            )

        frame_range = None
        frame_count = attributes.get("sequence_frame")
        start = attributes.get("render_start_frame", 1001)
        if (
            isinstance(frame_count, (int, float))
            and not isinstance(frame_count, bool)
            and float(frame_count).is_integer()
        ):
            frame_range = [
                int(start),
                int(start) + int(frame_count) - 1,
            ]
        return {
            "attributes": attributes,
            "frame_range": frame_range,
        }
    except Exception:
        return {"attributes": {}, "frame_range": None}


def collect_step_files(step_dir, step_code, errors=None):
    result = {}
    for subdir, patterns, key in _STEP_FILE_SPEC.get(step_code, []):
        result.setdefault(key, [])
        target = os.path.join(step_dir, subdir)
        if os.path.isdir(target):
            result[key].extend(
                _collect_matching_files(target, patterns, errors)
            )
    return result


def _collect_matching_files(path, patterns, errors=None):
    matches = []
    patterns = [pattern.lower() for pattern in patterns]
    for root, _dirs, files in _safe_walk(path, errors):
        for name in files:
            lowered = name.lower()
            if any(fnmatch.fnmatch(lowered, pattern) for pattern in patterns):
                matches.append(os.path.join(root, name))
    return sorted(matches, key=lambda item: item.lower())


def _safe_walk(path, errors=None):
    def collect_error(error):
        # Unreadable subdirectories are skipped so a single ACL problem
        # cannot discard the whole scan; callers report them in bulk.
        if errors is not None:
            errors.append(str(error))

    for root, directories, files in os.walk(path, onerror=collect_error):
        directories[:] = sorted(
            directory
            for directory in directories
            if not directory.startswith(".")
        )
        yield root, directories, files


def scan_server_shots(
    server_root, filter_strs, project_code=None, warnings=None
):
    if warnings is None:
        warnings = []
    if not os.path.isdir(server_root):
        return []
    filter_parts = [_parse_filter_parts(item) for item in filter_strs]
    if not filter_parts:
        return []

    projects = [project_code] if project_code else _list_dirs(server_root)
    seen = set()
    results = []
    for project in projects:
        publish_root = os.path.join(
            server_root, project, "publish", "shot"
        )
        if not os.path.isdir(publish_root):
            continue
        for raw_filter in filter_parts:
            match = _disambiguate_filter_parts(raw_filter, publish_root)
            episodes = (
                [match["episode"]]
                if match.get("episode")
                else _list_dirs(publish_root)
            )
            for episode in episodes:
                episode_dir = os.path.join(publish_root, episode)
                sequences = (
                    [match["sequence"]]
                    if match.get("sequence")
                    else _list_dirs(episode_dir)
                )
                for sequence in sequences:
                    sequence_dir = os.path.join(episode_dir, sequence)
                    shots = (
                        [match["shot"]]
                        if match.get("shot")
                        else _list_dirs(sequence_dir)
                    )
                    for shot in shots:
                        identity = (project, episode, sequence, shot)
                        if identity in seen:
                            continue
                        seen.add(identity)
                        shot_dir = os.path.join(sequence_dir, shot)
                        steps = []
                        for category, code in SERVER_STEPS:
                            step_dir = os.path.join(
                                shot_dir, category, code
                            )
                            if not os.path.isdir(step_dir):
                                continue
                            steps.append(
                                {
                                    "step_category": category,
                                    "step_code": code,
                                    "label": STEP_LABELS.get(
                                        "%s/%s" % (category, code), code
                                    ),
                                    "files": collect_step_files(
                                        step_dir, code, warnings
                                    ),
                                }
                            )
                        if not steps:
                            continue

                        frame_range = None
                        xml_attributes = {}
                        for step in steps:
                            if step["step_code"] != "shot_animation":
                                continue
                            for xml_path in step["files"].get(
                                "xml_files", []
                            ):
                                parsed = parse_xml_attributes(xml_path)
                                xml_attributes = parsed["attributes"]
                                frame_range = parsed["frame_range"]
                                if frame_range:
                                    break
                            if frame_range:
                                break

                        results.append(
                            {
                                "project_code": project,
                                "episode": episode,
                                "sequence": sequence,
                                "shot": shot,
                                "server_dir": shot_dir,
                                "frame_range": frame_range,
                                "xml_attributes": xml_attributes,
                                "steps": steps,
                            }
                        )
    return results
