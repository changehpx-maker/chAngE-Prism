from __future__ import unicode_literals

import glob
import json
import os
import re
import shutil
import subprocess
import tempfile
import time


HIP_VERSION_PATTERN = re.compile(
    br"_HIP_SAVEVERSION\s*=\s*['\"]([0-9]+\.[0-9]+\.[0-9]+)['\"]"
)
PATH_VERSION_PATTERN = re.compile(
    r"Houdini[ _-]+([0-9]+\.[0-9]+\.[0-9]+)", re.IGNORECASE
)
MINIMUM_VERSION = (20, 5, 0)
WORKER_TIMEOUT_SECONDS = 3600


class RunnerError(RuntimeError):
    pass


class RunnerCancelled(RunnerError):
    pass


class RunnerTimeout(RunnerError):
    pass


def read_hip_version(source_hip):
    with open(source_hip, "rb") as handle:
        data = handle.read(1024 * 1024)
    match = HIP_VERSION_PATTERN.search(data)
    if not match:
        raise RunnerError(
            "Could not determine the Houdini save version from:\n%s"
            % source_hip
        )
    value = match.group(1).decode("ascii")
    version = parse_version(value)
    if version < MINIMUM_VERSION:
        raise RunnerError(
            "Houdini Archive supports Houdini 20.5 or newer. "
            "The scene was saved with %s." % value
        )
    return value


def parse_version(value):
    parts = str(value).split(".")
    if len(parts) < 2:
        raise RunnerError("Invalid Houdini version: %s" % value)
    while len(parts) < 3:
        parts.append("0")
    try:
        return tuple(int(part) for part in parts[:3])
    except ValueError:
        raise RunnerError("Invalid Houdini version: %s" % value)


def resolve_hython(source_version, explicit_path=None, environ=None):
    requested = parse_version(source_version)
    candidates = []
    if explicit_path:
        candidates.append(os.path.abspath(os.path.expandvars(explicit_path)))
    else:
        candidates.extend(_discover_hython(environ=environ))

    compatible = []
    seen = set()
    for path in candidates:
        key = os.path.normcase(os.path.normpath(path))
        if key in seen or not os.path.isfile(path):
            continue
        seen.add(key)
        version_text = executable_version(path)
        if not version_text:
            continue
        version = parse_version(version_text)
        if version[:2] != requested[:2] or version[2] < requested[2]:
            continue
        compatible.append((version, path))

    if explicit_path and not compatible:
        raise RunnerError(
            "The selected hython is not compatible with Houdini %s:\n%s"
            % (source_version, explicit_path)
        )
    if not compatible:
        raise RunnerError(
            "Could not find hython %s or a newer build in the same "
            "major/minor release. Configure a matching Houdini executable "
            "in Prism or pass --hython." % source_version
        )

    compatible.sort(key=lambda item: item[0])
    selected_version, selected_path = compatible[0]
    warning = ""
    if selected_version != requested:
        warning = (
            "The scene was saved with Houdini %s. Using compatible build %s."
            % (source_version, ".".join(str(part) for part in selected_version))
        )
    return {
        "path": selected_path,
        "version": ".".join(str(part) for part in selected_version),
        "warning": warning,
    }


def executable_version(path):
    current = os.path.abspath(path)
    while True:
        match = PATH_VERSION_PATTERN.search(os.path.basename(current))
        if match:
            return match.group(1)
        parent = os.path.dirname(current)
        if parent == current:
            return ""
        current = parent


def run_worker(
    hython_executable,
    command,
    source_hip,
    plan=None,
    worker_env=None,
    is_cancelled=None,
    timeout_seconds=None,
):
    if timeout_seconds is None:
        timeout_seconds = WORKER_TIMEOUT_SECONDS
    temporary_root = tempfile.mkdtemp(prefix="houdini_archive_worker_")
    result_path = os.path.join(temporary_root, "result.json")
    plan_path = ""
    if plan is not None:
        plan_path = os.path.join(temporary_root, "plan.json")
        with open(plan_path, "w", encoding="utf-8") as handle:
            json.dump(plan, handle, ensure_ascii=False, indent=2)

    worker_path = os.path.join(os.path.dirname(__file__), "houdini_worker.py")
    args = [
        hython_executable,
        worker_path,
        command,
        source_hip,
        result_path,
    ]
    if plan_path:
        args.append(plan_path)

    environment = os.environ.copy()
    if worker_env:
        for key, value in worker_env.items():
            if value is not None:
                environment[str(key)] = str(value)

    process = None
    log_handle = None
    stdout = ""
    started = time.monotonic()
    try:
        log_path = os.path.join(temporary_root, "worker.log")
        try:
            log_handle = open(
                log_path,
                "w",
                encoding="utf-8",
                errors="replace",
            )
            process = subprocess.Popen(
                args,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                env=environment,
                universal_newlines=True,
            )
        except OSError as exc:
            raise RunnerError("Could not start hython:\n%s" % exc)

        while process.poll() is None:
            if is_cancelled and is_cancelled():
                _terminate_process(process)
                raise RunnerCancelled(
                    "Houdini Archive packaging was cancelled."
                )
            if (
                timeout_seconds
                and time.monotonic() - started >= timeout_seconds
            ):
                log_tail = _read_log_tail(log_path)
                _terminate_process(process)
                raise RunnerTimeout(
                    "Houdini Worker did not finish within %s and was "
                    "terminated.\n\n%s"
                    % (_format_duration(timeout_seconds), log_tail)
                )
            time.sleep(0.1)
        log_handle.close()
        log_handle = None
        try:
            with open(
                log_path,
                "r",
                encoding="utf-8",
                errors="replace",
            ) as handle:
                stdout = handle.read()
        except OSError:
            stdout = ""
        if not os.path.isfile(result_path):
            raise RunnerError(
                "Houdini Worker did not produce a result.\n%s"
                % stdout.strip()
            )
        try:
            with open(result_path, "r", encoding="utf-8") as handle:
                result = json.load(handle)
        except (OSError, ValueError, TypeError) as exc:
            raise RunnerError(
                "Houdini Worker returned invalid JSON: %s" % exc
            )
        if process.returncode != 0:
            message = result.get("error") if isinstance(result, dict) else ""
            raise RunnerError(
                message
                or "Houdini Worker failed with exit code %s.\n%s"
                % (process.returncode, stdout.strip())
            )
        if not isinstance(result, dict):
            raise RunnerError("Houdini Worker returned an invalid result.")
        result["worker_log"] = stdout
        return result
    finally:
        if log_handle is not None:
            log_handle.close()
        shutil.rmtree(temporary_root, ignore_errors=True)


def _terminate_process(process):
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _read_log_tail(path, limit=2000):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            data = handle.read()
    except OSError:
        return ""
    return data[-limit:].strip()


def _format_duration(seconds):
    seconds = max(0, int(round(float(seconds or 0))))
    if seconds < 120:
        return "%d seconds" % seconds
    minutes = seconds // 60
    if minutes < 120:
        return "%d minutes" % minutes
    hours, minutes = divmod(minutes, 60)
    return "%d hours %d minutes" % (hours, minutes)


def _discover_hython(environ=None):
    environ = environ or os.environ
    candidates = []
    hfs = environ.get("HFS")
    if hfs:
        candidates.append(os.path.join(hfs, "bin", _hython_name()))

    if os.name == "nt":
        roots = []
        for key in ("ProgramFiles", "PROGRAMFILES"):
            value = environ.get(key)
            if value:
                roots.append(
                    os.path.join(value, "Side Effects Software")
                )
        roots.append(r"C:\Program Files\Side Effects Software")
        for root in roots:
            candidates.extend(
                glob.glob(
                    os.path.join(root, "Houdini *", "bin", "hython.exe")
                )
            )
    else:
        candidates.extend(glob.glob("/opt/hfs*/bin/hython"))
        candidates.extend(glob.glob("/Applications/Houdini*/Frameworks/Houdini.framework/Versions/*/Resources/bin/hython"))
    return candidates


def _hython_name():
    return "hython.exe" if os.name == "nt" else "hython"
