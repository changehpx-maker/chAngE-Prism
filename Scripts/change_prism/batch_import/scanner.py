import functools
import os
import glob
import re
import xml.etree.ElementTree as ET

_SERVER_STEPS = [
    ("shot_motion", "shot_animation"),
    ("shot_solution", "cloth_solution"),
    ("shot_solution", "hair_solution"),
]

STEP_LABELS = {
    "shot_motion/shot_animation": "Animation",
    "shot_solution/cloth_solution": "Cloth",
    "shot_solution/hair_solution": "Hair",
}

_FILE_CATEGORIES = [
    ("review", ["*.mov"], "mov_files"),
    ("work", ["*.mb", "*.hip", "*.ma"], "scenefile_paths"),
    ("maya", ["*.mb"], "scenefile_paths"),
    ("fbx", ["*.fbx"], "export_paths"),
    ("anim", ["*.anim"], "export_paths"),
    ("vfx", ["*.abc"], "export_paths"),
    ("xml", ["*.xml"], "xml_files"),
    ("json", ["*.json"], "json_files"),
]


@functools.lru_cache(maxsize=64)
def _list_dirs(path):
    if not os.path.isdir(path):
        return []
    try:
        return sorted(
            d for d in os.listdir(path)
            if os.path.isdir(os.path.join(path, d)) and not d.startswith(".")
        )
    except OSError:
        return []


def clear_list_dirs_cache():
    _list_dirs.cache_clear()


def parse_filter_strings(text):
    if not text or not text.strip():
        return []

    parts = re.split(r"[,\n]+", text)
    return [p.strip() for p in parts if p.strip()]


def _parse_filter_parts(filter_str):
    parts = [p.strip() for p in filter_str.split("/") if p.strip()]
    result = {}

    if len(parts) >= 1:
        result["episode"] = parts[0]
    if len(parts) >= 2:
        result["sequence"] = parts[1]
    if len(parts) >= 3:
        result["shot"] = parts[2]

    return result


def _disambiguate_filter_parts(filter_parts, publish_shot_dir):
    if "shot" in filter_parts:
        return filter_parts

    episodes = set() if "episode" not in filter_parts else _list_dirs(publish_shot_dir)
    result = dict(filter_parts)

    if "sequence" not in result:
        if result["episode"] not in episodes:
            result["shot"] = result["episode"]
            result.pop("episode", None)
    elif "shot" not in result:
        if result["episode"] not in episodes:
            result["shot"] = result["sequence"]
            result["sequence"] = result["episode"]
            result.pop("episode", None)

    return result


def _parse_frame_range(xml_path):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        seq_frame = None
        render_start = "1001"
        for attr in root.iter("attribute"):
            name = attr.get("name", "")
            value = attr.get("value", "")
            if name == "sequence_frame":
                seq_frame = value
            elif name == "render_start_frame":
                render_start = value
        if seq_frame:
            s = int(seq_frame)
            start = int(render_start)
            return [start, start + s - 1]
    except Exception:
        pass
    return None


def _collect_step_files(step_dir):
    result = {
        "mov_files": [],
        "scenefile_paths": [],
        "export_paths": [],
        "xml_files": [],
        "json_files": [],
    }

    for subdir, exts, key in _FILE_CATEGORIES:
        target = os.path.join(step_dir, subdir)
        if not os.path.isdir(target):
            continue
        for ext in exts:
            for f in sorted(glob.glob(os.path.join(target, ext))):
                result[key].append(f)

    return result


def scan_server_shots(server_root, filter_strs, project_code=None):
    if not os.path.isdir(server_root):
        return []

    filter_parts_list = [_parse_filter_parts(f) for f in filter_strs]
    if not filter_parts_list:
        return []

    project_dirs = [project_code] if project_code else _list_dirs(server_root)
    seen = set()
    results = []

    for proj in project_dirs:
        publish_shot_dir = os.path.join(server_root, proj, "publish", "shot")
        if not os.path.isdir(publish_shot_dir):
            continue

        for fp in filter_parts_list:
            fp = _disambiguate_filter_parts(fp, publish_shot_dir)
            ep = fp.get("episode")
            seq = fp.get("sequence")
            shot = fp.get("shot")

            episode_dirs = [ep] if ep else _list_dirs(publish_shot_dir)

            for episode in episode_dirs:
                ep_dir = os.path.join(publish_shot_dir, episode)
                seq_dirs = [seq] if seq else _list_dirs(ep_dir)

                for sequence in seq_dirs:
                    seq_dir = os.path.join(ep_dir, sequence)
                    shot_dirs = [shot] if shot else _list_dirs(seq_dir)

                    for shot_name in shot_dirs:
                        key = (proj, episode, sequence, shot_name)
                        if key in seen:
                            continue
                        seen.add(key)

                        shot_dir = os.path.join(seq_dir, shot_name)
                        steps = []
                        for sc, ssc in _SERVER_STEPS:
                            step_full = os.path.join(shot_dir, sc, ssc)
                            if not os.path.isdir(step_full):
                                continue
                            steps.append({
                                "step_category": sc,
                                "step_code": ssc,
                                "label": STEP_LABELS.get("%s/%s" % (sc, ssc), ssc),
                                "files": _collect_step_files(step_full),
                            })

                        if steps:
                            frame_range = None
                            for step in steps:
                                if step["step_code"] == "shot_animation":
                                    for xf in step["files"].get("xml_files", []):
                                        frame_range = _parse_frame_range(xf)
                                        if frame_range:
                                            break
                                if frame_range:
                                    break

                            results.append({
                                "project_code": proj,
                                "episode": episode,
                                "sequence": sequence,
                                "shot": shot_name,
                                "server_dir": shot_dir,
                                "frame_range": frame_range,
                                "steps": steps,
                            })

    return results
