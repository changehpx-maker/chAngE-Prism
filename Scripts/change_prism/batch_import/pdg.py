import glob
import json
import os
import subprocess
import sys
import tempfile
import time

from qtpy.QtCore import QThread, Signal

from change_prism.batch_import.file_processor import FileProcessor
from change_prism.batch_import.scanner import STEP_LABELS
from change_prism.batch_import.service import (
    get_log_dir,
    get_output_dir,
    prune_old_files,
)
from change_prism.config import (
    SETTINGS_LOCATION,
    get_houdini_package_directory,
    get_pdg_hip_path,
)
from change_prism.dcc_paths import get_prism_hython


ANIMATION_LABEL = STEP_LABELS["shot_motion/shot_animation"]
PDG_MODE_LABEL = "PDG FBX Convert"
PDG_TEMP_PREFIX = "change_prism_pdg_"
MAX_PDG_LOG_FILES = 40
PDG_FRAME_ATTRIBUTE_KEYS = (
    "render_start_frame",
    "start_frame",
    "sequence_frame",
)


class _PDGMonitor(QThread):
    finished_signal = Signal(int, int, str, str)

    def __init__(
        self,
        process,
        stdout_file=None,
        stderr_file=None,
        stdout_path="",
        stderr_path="",
        parent=None,
    ):
        super().__init__(parent)
        self.process = process
        self.stdout_file = stdout_file
        self.stderr_file = stderr_file
        self.stdout_path = stdout_path
        self.stderr_path = stderr_path

    def run(self):
        return_code = -1
        try:
            return_code = self.process.wait()
        except OSError:
            pass
        finally:
            for handle in (self.stdout_file, self.stderr_file):
                if handle is not None:
                    try:
                        handle.close()
                    except OSError:
                        pass
        self.finished_signal.emit(
            self.process.pid,
            return_code,
            self.stdout_path,
            self.stderr_path,
        )


class PDGProcessor(object):
    def __init__(self, core):
        self.core = core
        self._pdg_process = None
        self._pdg_monitor = None
        self._json_path = ""

    def is_running(self):
        return (
            self._pdg_process is not None
            and self._pdg_process.poll() is None
        )

    def run(self, shot_data_list, project_name):
        if self.is_running():
            self.core.popup(
                "%s is already running." % PDG_MODE_LABEL,
                severity="warning",
            )
            return False
        try:
            pdg_data = self._build_pdg_json(shot_data_list)
            if not pdg_data:
                self.core.popup(
                    "%s: No FBX files found. PDG was not launched."
                    % PDG_MODE_LABEL,
                    severity="warning",
                )
                return False

            hython_path = self._resolve_hython()
            hip_path = self._resolve_hip()
            topcook_path = self._resolve_topcook(hython_path)
            package_dir = self._resolve_package_directory()
            self._validate_runtime(
                hython_path, hip_path, topcook_path, package_dir
            )

            self._json_path = self._write_pdg_json(pdg_data)
            command = [
                hython_path,
                "-u",
                topcook_path,
                "--hip",
                hip_path,
                "--toppath",
                "/obj/topnet",
                "--verbosity",
                "1",
            ]
            environment = self._build_houdini_env(
                hython_path, package_dir, self._json_path
            )
            callback = getattr(self.core, "callback", None)
            if callable(callback):
                callback(
                    name="preLaunchApp",
                    args=[command, environment],
                )

            stdout_path, stderr_path = self._make_pdg_log_paths(
                project_name
            )
            stdout_file = None
            stderr_file = None
            try:
                stdout_file = open(
                    stdout_path, "w", encoding="utf-8"
                )
                stderr_file = open(
                    stderr_path, "w", encoding="utf-8"
                )
            except Exception:
                for handle in (stdout_file, stderr_file):
                    if handle is not None:
                        handle.close()
                raise
            prune_old_files(
                os.path.dirname(stdout_path),
                suffix=".log",
                keep=MAX_PDG_LOG_FILES,
            )
            kwargs = {
                "env": environment,
                "stdout": stdout_file,
                "stderr": stderr_file,
            }
            if sys.platform == "win32":
                kwargs["creationflags"] = (
                    getattr(subprocess, "CREATE_NO_WINDOW", 0)
                    | getattr(
                        subprocess, "CREATE_NEW_PROCESS_GROUP", 0
                    )
                )
            else:
                kwargs["start_new_session"] = True

            try:
                self._pdg_process = subprocess.Popen(command, **kwargs)
            except OSError:
                stdout_file.close()
                stderr_file.close()
                raise

            self._pdg_monitor = _PDGMonitor(
                self._pdg_process,
                stdout_file,
                stderr_file,
                stdout_path,
                stderr_path,
            )
            self._pdg_monitor.finished_signal.connect(
                self._on_pdg_finished
            )
            self._pdg_monitor.start()
            self.core.popup(
                "%s started in the background.\n\nPID: %s\n"
                "stdout: %s\nstderr: %s\nshot data: %s"
                % (
                    PDG_MODE_LABEL,
                    self._pdg_process.pid,
                    stdout_path,
                    stderr_path,
                    self._json_path,
                ),
                severity="info",
            )
            return True
        except Exception as exc:
            if not self.is_running():
                self._cleanup_pdg_json()
            self.core.popup(
                "%s could not start:\n\n%s\n\nConfigure paths in %s."
                % (PDG_MODE_LABEL, exc, SETTINGS_LOCATION),
                severity="error",
            )
            return False

    def _on_pdg_finished(
        self, pid, return_code, stdout_path="", stderr_path=""
    ):
        json_path = self._json_path
        self._json_path = ""
        stderr_has_errors = self._stderr_has_errors(stderr_path)
        failed = return_code != 0 or stderr_has_errors
        status = "failed" if failed else "completed"
        severity = "error" if failed else "info"
        error_note = (
            "\nDetected error output in stderr."
            if stderr_has_errors and return_code == 0
            else ""
        )
        try:
            self.core.popup(
                "%s %s.\n\nPID: %s\nExit code: %s%s\n"
                "stdout: %s\nstderr: %s\nshot data: %s"
                % (
                    PDG_MODE_LABEL,
                    status,
                    pid,
                    return_code,
                    error_note,
                    stdout_path,
                    stderr_path,
                    json_path,
                ),
                severity=severity,
            )
        finally:
            self._pdg_monitor = None
            self._pdg_process = None

    @staticmethod
    def _stderr_has_errors(stderr_path):
        if not stderr_path or not os.path.isfile(stderr_path):
            return False
        try:
            with open(
                stderr_path, "r", encoding="utf-8", errors="replace"
            ) as handle:
                for line in handle:
                    stripped = line.lstrip()
                    if stripped.startswith(
                        ("ERROR:", "Traceback ", "Error:")
                    ):
                        return True
        except OSError:
            return False
        return False

    def _build_pdg_json(self, shot_data_list):
        result = {}
        for shot_data in shot_data_list:
            episode = shot_data.get("episode", "")
            sequence = shot_data.get("sequence", "")
            shot = shot_data.get("shot", "")
            key = "%s/%s/%s" % (episode, sequence, shot)
            file_dict = []
            for step in shot_data.get("steps", {}).values():
                for path in step.get("fbx", []):
                    if not str(path).lower().endswith(".fbx"):
                        continue
                    file_dict.append({"path": path})
            if not file_dict:
                continue

            entity = {
                "type": "shot",
                "sequence": (
                    shot_data.get("prism_sequence") or episode
                ),
                "shot": (
                    shot_data.get("prism_shot")
                    or "%s_%s" % (sequence, shot)
                ),
            }
            if episode:
                entity["episode"] = episode

            frame_range = shot_data.get("frame_range")
            result[key] = {
                "entity": entity,
                "shot_code": entity["shot"],
                "project_code": shot_data.get("project_code", ""),
                "file_dict": file_dict,
                "xml": self._build_xml_data(shot_data),
                "frame_range": (
                    {
                        "start": frame_range[0],
                        "end": frame_range[1],
                    }
                    if frame_range and len(frame_range) == 2
                    else None
                ),
                "products_path": (
                    shot_data.get("products_path")
                    or self._resolve_products_path(entity)
                ),
            }
        return result

    @staticmethod
    def _build_xml_data(shot_data):
        xml_data = {}
        animation = shot_data.get("steps", {}).get(
            ANIMATION_LABEL, {}
        )
        animation_xml = animation.get("xml", {})
        if animation_xml:
            attributes = animation_xml.get("attributes", {})
            xml_data["path"] = animation_xml.get("path", "")
            xml_data["attributes"] = {
                key: attributes[key]
                for key in PDG_FRAME_ATTRIBUTE_KEYS
                if key in attributes
            }

        for label, key in (
            ("Cloth", "cloth_solution"),
            ("Hair", "hair_solution"),
        ):
            solution_xml = (
                shot_data.get("steps", {})
                .get(label, {})
                .get("xml", {})
            )
            xml_path = solution_xml.get("path", "")
            if xml_path:
                xml_data[key] = {"xml_path": xml_path}

        return xml_data

    def _resolve_products_path(self, entity):
        try:
            return (
                self.core.products.createProduct(
                    entity, FileProcessor.PRODUCT_NAME
                )
                or ""
            )
        except Exception:
            return ""

    def _resolve_hython(self):
        path = get_prism_hython(self.core)
        return path if os.path.isfile(path) else ""

    def _resolve_hip(self):
        path = _expand_path(get_pdg_hip_path(self.core))
        return path if os.path.isfile(path) else ""

    @staticmethod
    def _resolve_topcook(hython_path):
        if not hython_path:
            return ""
        hfs = os.path.dirname(
            os.path.dirname(os.path.realpath(hython_path))
        )
        pattern = os.path.join(
            hfs, "houdini", "python*libs", "pdgjob", "topcook.py"
        )
        for candidate in sorted(glob.glob(pattern), reverse=True):
            if os.path.isfile(candidate):
                return os.path.normpath(candidate)
        return ""

    def _resolve_package_directory(self):
        path = _expand_path(
            get_houdini_package_directory(self.core)
        )
        return path if os.path.isdir(path) else ""

    @staticmethod
    def _validate_runtime(
        hython_path, hip_path, topcook_path, package_dir
    ):
        missing = []
        if not hython_path:
            missing.append(
                "Hython (set Prism User Settings > Apps > Houdini executable override)"
            )
        if not hip_path:
            missing.append("PDG Template HIP")
        if not topcook_path:
            missing.append("topcook.py next to the selected Houdini")
        if not package_dir:
            missing.append("Houdini Package Directory")
        if missing:
            raise ValueError("Missing: %s" % ", ".join(missing))

    def _write_pdg_json(self, data):
        json_root = get_output_dir("pdg", "json")
        directory = tempfile.mkdtemp(
            prefix=PDG_TEMP_PREFIX,
            dir=json_root,
        )
        path = os.path.join(directory, "shot_data.json")
        try:
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(
                    data,
                    handle,
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )
        except Exception:
            try:
                os.remove(path)
            except OSError:
                pass
            try:
                os.rmdir(directory)
            except OSError:
                pass
            raise
        return path

    def _cleanup_pdg_json(self):
        path = self._json_path
        self._json_path = ""
        if not path:
            return
        directory = os.path.realpath(os.path.dirname(path))
        json_root = os.path.realpath(get_output_dir("pdg", "json"))
        if (
            os.path.normcase(os.path.dirname(directory))
            != os.path.normcase(json_root)
            or not os.path.basename(directory).startswith(
                PDG_TEMP_PREFIX
            )
        ):
            return
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
        try:
            os.rmdir(directory)
        except OSError:
            pass

    def _make_pdg_log_paths(self, project_name):
        safe_project = "".join(
            char if char.isalnum() or char in ("-", "_") else "_"
            for char in (project_name or "project")
        )
        prefix = "%s_%s" % (
            safe_project,
            "%s_%s" % (
                time.strftime("%Y%m%d_%H%M%S"),
                os.getpid(),
            ),
        )
        directory = get_log_dir(self.core, "pdg")
        return (
            os.path.join(directory, prefix + "_stdout.log"),
            os.path.join(directory, prefix + "_stderr.log"),
        )

    def _build_houdini_env(
        self, hython_path, package_dir, json_path
    ):
        start_env = getattr(self.core, "startEnv", None)
        environment = dict(
            os.environ if start_env is None else start_env
        )
        users = getattr(self.core, "users", None)
        if users is not None:
            for item in users.getUserEnvironment(
                appPluginName="Houdini"
            ) or []:
                environment[item["key"]] = item["value"]
        projects = getattr(self.core, "projects", None)
        if projects is not None:
            for item in projects.getProjectEnvironment(
                appPluginName="Houdini"
            ) or []:
                environment[item["key"]] = item["value"]

        environment["HOUDINI_PACKAGE_DIR"] = package_dir
        environment["SHOT_BUILDER_PDG_JSON"] = json_path
        qt_plugins, qt_platforms = self._resolve_qt_plugin_paths(
            hython_path
        )
        if qt_plugins:
            environment["QT_PLUGIN_PATH"] = self._prepend_env_path(
                environment.get("QT_PLUGIN_PATH", ""), qt_plugins
            )
        if qt_platforms:
            environment["QT_QPA_PLATFORM_PLUGIN_PATH"] = qt_platforms
        return environment

    @staticmethod
    def _prepend_env_path(current, path):
        parts = [item for item in current.split(os.pathsep) if item]
        if path in parts:
            parts.remove(path)
        return os.pathsep.join([path] + parts)

    @staticmethod
    def _resolve_qt_plugin_paths(hython_path):
        if not hython_path or sys.platform == "win32":
            return "", ""
        resources = os.path.dirname(
            os.path.dirname(os.path.realpath(hython_path))
        )
        version_dir = os.path.dirname(resources)
        plugins = os.path.realpath(
            os.path.join(version_dir, "Libraries", "Qt_plugins")
        )
        platforms = os.path.join(plugins, "platforms")
        if not os.path.isdir(plugins):
            return "", ""
        return (
            plugins,
            platforms if os.path.isdir(platforms) else "",
        )


def _expand_path(path):
    if not path:
        return ""
    return os.path.normpath(
        os.path.expandvars(os.path.expanduser(str(path)))
    )
