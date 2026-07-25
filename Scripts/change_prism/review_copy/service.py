import datetime
import os
import shutil


class DestinationNotConfiguredError(ValueError):
    pass


def create_daily_directory(destination_root, current_date=None):
    destination_root = os.fspath(destination_root).strip() if destination_root else ""
    if not destination_root:
        raise DestinationNotConfiguredError(
            "review_copy.destination_root is not configured."
        )

    current_date = current_date or datetime.date.today()
    daily_directory = os.path.join(
        os.path.normpath(destination_root),
        current_date.strftime("%Y-%m-%d"),
    )
    os.makedirs(daily_directory, exist_ok=True)
    return daily_directory


def copy_items(paths, destination_root, current_date=None):
    daily_directory = create_daily_directory(destination_root, current_date)
    copied = []
    failures = []

    for source in _unique_paths(paths):
        try:
            if not os.path.exists(source):
                raise FileNotFoundError("Path does not exist.")

            name = os.path.basename(os.path.normpath(source))
            target = os.path.join(daily_directory, name)
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


def _unique_paths(paths):
    unique = []
    seen = set()
    for path in paths or []:
        if not path:
            continue
        normalized = os.path.normpath(os.fspath(path))
        key = os.path.normcase(os.path.abspath(normalized))
        if key in seen:
            continue
        seen.add(key)
        unique.append(normalized)
    return unique
