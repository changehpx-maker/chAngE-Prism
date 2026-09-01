import datetime
import os
import re
import shutil


class DestinationNotConfiguredError(ValueError):
    pass


def create_daily_directory(destination_root, current_date=None):
    daily_directory = _daily_directory_path(destination_root, current_date)
    os.makedirs(daily_directory, exist_ok=True)
    return daily_directory


def copy_items(paths, destination_root, current_date=None):
    daily_directory = _daily_directory_path(destination_root, current_date)
    copied = []
    failures = []
    copy_sources = []

    for item in _unique_sources(paths):
        try:
            source = _resolve_source(item)
            if not os.path.exists(source):
                raise FileNotFoundError("Path does not exist.")

            name = os.path.basename(os.path.normpath(source))
            target = os.path.join(daily_directory, name)
            _validate_copy_target(source, target)
            copy_sources.append((source, target))
        except Exception as exc:
            failures.append({
                "source": _source_path(item),
                "error": str(exc),
            })

    if copy_sources:
        os.makedirs(daily_directory, exist_ok=True)

    for source, target in copy_sources:
        try:
            if os.path.isdir(source):
                shutil.copytree(source, target, dirs_exist_ok=True)
            else:
                shutil.copy2(source, target)
            copied.append(source)
        except Exception as exc:
            failures.append({"source": source, "error": str(exc)})

    return {
        "destination": daily_directory,
        "copied": copied,
        "failures": failures,
    }


def _daily_directory_path(destination_root, current_date=None):
    destination_root = os.fspath(destination_root).strip() if destination_root else ""
    if not destination_root:
        raise DestinationNotConfiguredError(
            "review_copy.destination_root is not configured."
        )
    current_date = current_date or datetime.date.today()
    return os.path.join(
        os.path.normpath(destination_root),
        current_date.strftime("%Y-%m-%d"),
    )


def _resolve_source(item):
    path = _source_path(item)
    if (
        isinstance(item, dict)
        and item.get("detect_product_sequence")
        and os.path.isfile(path)
        and _has_sequence_sibling(path)
    ):
        return os.path.dirname(path)
    return path


def _has_sequence_sibling(path):
    filename = os.path.basename(path)
    match = re.match(
        r"^(?P<prefix>.*[._-])(?P<frame>\d+)"
        r"(?P<suffix>(?:\.[^.]+)+)$",
        filename,
    )
    if not match:
        return False

    sequence_pattern = re.compile(
        r"^%s\d{%d}%s$"
        % (
            re.escape(match.group("prefix")),
            len(match.group("frame")),
            re.escape(match.group("suffix")),
        ),
        re.IGNORECASE,
    )
    matches = 0
    with os.scandir(os.path.dirname(path)) as entries:
        for entry in entries:
            if entry.is_file() and sequence_pattern.match(entry.name):
                matches += 1
                if matches > 1:
                    return True
    return False


def _validate_copy_target(source, target):
    source_path = os.path.normcase(os.path.realpath(os.path.abspath(source)))
    target_path = os.path.normcase(os.path.realpath(os.path.abspath(target)))
    if source_path == target_path:
        raise ValueError("Copy target is the same as the source.")
    if not os.path.isdir(source):
        return
    try:
        common = os.path.commonpath([source_path, target_path])
    except ValueError:
        return
    if common == source_path:
        raise ValueError("Copy target is inside the source directory.")
    if common == target_path:
        raise ValueError("Source directory is inside the copy target.")


def _source_path(item):
    path = item.get("path", "") if isinstance(item, dict) else item
    return os.path.normpath(os.fspath(path)) if path else ""


def _unique_sources(paths):
    unique = []
    seen = set()
    for item in paths or []:
        path = _source_path(item)
        if not path:
            continue
        key = os.path.normcase(os.path.abspath(path))
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique
