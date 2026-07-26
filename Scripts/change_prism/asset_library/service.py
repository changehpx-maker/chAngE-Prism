from __future__ import unicode_literals

import os
import re
import stat


SUPPORTED_EXTENSIONS = frozenset(
    (
        ".bmp",
        ".exr",
        ".hdr",
        ".jpeg",
        ".jpg",
        ".png",
        ".tga",
        ".tif",
        ".tiff",
    )
)
THUMBNAIL_DIRECTORY = "_thumbs"


def normalize_source_path(path):
    text = str(path or "").strip()
    if not text:
        return ""
    return os.path.normpath(os.path.abspath(os.path.expanduser(text)))


def source_key(path):
    normalized = normalize_source_path(path)
    return os.path.normcase(normalized) if normalized else ""


def source_name(path):
    normalized = normalize_source_path(path)
    if not normalized:
        return ""
    trimmed = normalized.rstrip("\\/")
    name = os.path.basename(trimmed)
    return name or trimmed


def normalize_source_specs(sources):
    normalized = []
    seen = set()
    for item in sources if isinstance(sources, (list, tuple)) else []:
        if isinstance(item, dict):
            path = normalize_source_path(item.get("path"))
            enabled = bool(item.get("enabled", True))
        else:
            path = normalize_source_path(item)
            enabled = True
        key = source_key(path)
        if not key or key in seen:
            continue
        seen.add(key)
        normalized.append({"path": path, "enabled": enabled})
    return normalized


def scan_sources(sources, extensions=None, cancel_event=None):
    extensions = frozenset(
        str(ext).lower() for ext in (extensions or SUPPORTED_EXTENSIONS)
    )
    result = {
        "sources": [],
        "directories": [],
        "assets": [],
        "failures": [],
        "cancelled": False,
    }

    for spec in normalize_source_specs(sources):
        if _is_cancelled(cancel_event):
            result["cancelled"] = True
            break

        root = spec["path"]
        key = source_key(root)
        source = {
            "id": key,
            "path": root,
            "name": source_name(root),
            "enabled": spec["enabled"],
            "available": os.path.isdir(root),
            "file_count": 0,
        }
        result["sources"].append(source)
        result["directories"].append(_directory_record(root, root, key))

        if not spec["enabled"]:
            continue
        if not source["available"]:
            result["failures"].append(
                {
                    "source_path": root,
                    "path": root,
                    "error": "Source directory is unavailable.",
                }
            )
            continue

        asset_start = len(result["assets"])
        _scan_directory(
            root,
            root,
            key,
            extensions,
            result,
            cancel_event,
        )
        source["file_count"] = len(result["assets"]) - asset_start
        if result["cancelled"]:
            break

    return result


def _scan_directory(root, directory, source_id, extensions, result, cancel_event):
    if _is_cancelled(cancel_event):
        result["cancelled"] = True
        return

    try:
        with os.scandir(directory) as iterator:
            entries = list(iterator)
    except OSError as exc:
        result["failures"].append(
            {
                "source_path": root,
                "path": directory,
                "error": str(exc),
            }
        )
        return

    entries.sort(key=lambda entry: entry.name.casefold())
    child_directories = []
    for entry in entries:
        if _is_cancelled(cancel_event):
            result["cancelled"] = True
            return
        try:
            if entry.is_symlink() or _is_reparse_point(entry):
                continue
            if entry.is_dir(follow_symlinks=False):
                if entry.name.casefold() == THUMBNAIL_DIRECTORY:
                    continue
                child_directories.append(entry.path)
                result["directories"].append(
                    _directory_record(root, entry.path, source_id)
                )
                continue
            if not entry.is_file(follow_symlinks=False):
                continue
            extension = os.path.splitext(entry.name)[1].lower()
            if extension not in extensions:
                continue
            stat_result = entry.stat(follow_symlinks=False)
        except OSError as exc:
            result["failures"].append(
                {
                    "source_path": root,
                    "path": entry.path,
                    "error": str(exc),
                }
            )
            continue

        result["assets"].append(
            _asset_record(
                root,
                entry.path,
                source_id,
                extension,
                stat_result,
            )
        )

    for child in child_directories:
        _scan_directory(
            root,
            child,
            source_id,
            extensions,
            result,
            cancel_event,
        )
        if result["cancelled"]:
            return


def _directory_record(root, path, source_id):
    relative_path = os.path.relpath(path, root)
    if relative_path == ".":
        relative_path = ""
    return {
        "source_id": source_id,
        "source_path": root,
        "path": os.path.normpath(path),
        "relative_path": relative_path,
        "name": source_name(path),
    }


def _asset_record(root, path, source_id, extension, stat_result):
    directory = os.path.dirname(path)
    relative_directory = os.path.relpath(directory, root)
    if relative_directory == ".":
        relative_directory = ""
    mtime_ns = getattr(stat_result, "st_mtime_ns", None)
    if mtime_ns is None:
        mtime_ns = int(stat_result.st_mtime * 1000000000)
    return {
        "source_id": source_id,
        "source_path": root,
        "source_name": source_name(root),
        "path": os.path.normpath(path),
        "directory": os.path.normpath(directory),
        "relative_directory": relative_directory,
        "filename": os.path.basename(path),
        "extension": extension,
        "size": int(stat_result.st_size),
        "mtime_ns": int(mtime_ns),
    }


def assets_in_directory(assets, source_id, directory):
    directory_key = os.path.normcase(os.path.normpath(directory or ""))
    return [
        asset
        for asset in assets
        if asset.get("source_id") == source_id
        and os.path.normcase(os.path.normpath(asset.get("directory", "")))
        == directory_key
    ]


def search_assets(assets, query):
    tokens = [
        token.casefold()
        for token in str(query or "").split()
        if token.strip()
    ]
    if not tokens:
        return list(assets)

    matches = []
    for asset in assets:
        haystack = " ".join(
            (
                asset.get("filename", ""),
                asset.get("source_name", ""),
                asset.get("relative_directory", ""),
            )
        ).casefold()
        if all(token in haystack for token in tokens):
            matches.append(asset)
    return matches


def aggregate_assets(assets):
    grouped = {}
    order = []
    for asset in assets:
        key = (
            asset.get("source_id", ""),
            asset.get("filename", "").casefold(),
            int(asset.get("size", 0)),
            int(asset.get("mtime_ns", 0)),
        )
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(asset)

    records = []
    for key in order:
        locations = sorted(
            grouped[key],
            key=lambda item: os.path.normcase(item.get("path", "")),
        )
        primary = dict(locations[0])
        primary["locations"] = locations
        primary["location_count"] = len(locations)
        primary["record_key"] = key
        records.append(primary)
    return records


def display_records(assets):
    records = []
    for asset in assets:
        record = dict(asset)
        record["locations"] = [asset]
        record["location_count"] = 1
        record["record_key"] = (
            asset.get("source_id", ""),
            os.path.normcase(asset.get("path", "")),
        )
        records.append(record)
    return records


def sort_assets(assets, field="name", descending=False):
    field = field if field in ("name", "modified", "size") else "name"

    def key(record):
        filename = record.get("filename", "")
        path = os.path.normcase(record.get("path", ""))
        if field == "modified":
            primary = int(record.get("mtime_ns", 0))
        elif field == "size":
            primary = int(record.get("size", 0))
        else:
            primary = _natural_key(filename)
        return primary, filename.casefold(), path

    return sorted(list(assets), key=key, reverse=bool(descending))


def thumbnail_path(asset_path):
    directory = os.path.dirname(asset_path)
    filename = os.path.basename(asset_path)
    return os.path.join(directory, THUMBNAIL_DIRECTORY, filename + ".jpg")


def thumbnail_is_fresh(asset_path, cache_path=None):
    cache_path = cache_path or thumbnail_path(asset_path)
    try:
        return (
            os.path.getsize(cache_path) > 0
            and os.path.getmtime(cache_path) >= os.path.getmtime(asset_path)
        )
    except OSError:
        return False


def _natural_key(value):
    return tuple(
        (0, int(part)) if part.isdigit() else (1, part.casefold())
        for part in re.split(r"(\d+)", str(value))
    )


def _is_cancelled(cancel_event):
    return bool(
        cancel_event is not None
        and hasattr(cancel_event, "is_set")
        and cancel_event.is_set()
    )


def _is_reparse_point(entry):
    if os.name != "nt":
        return False
    attributes = getattr(
        entry.stat(follow_symlinks=False),
        "st_file_attributes",
        0,
    )
    flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & flag)
