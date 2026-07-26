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
from change_prism.batch_import.service import get_log_dir
from change_prism.config import (
    SETTINGS_LOCATION,
    get_houdini_package_directory,
    get_pdg_hip_path,
)
from change_prism.dcc_paths import get_prism_hython


ANIMATION_LABEL = STEP_LABELS["shot_motion/shot_animation"]
PDG_MODE_LABEL = "PDG FBX Convert"


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

    def run(self, shot_data_list, project_name):
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
            stdout_file = open(stdout_path, "w", encoding="utf-8")
            stderr_file = open(stderr_path, "w", encoding="utf-8")
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
                "%s started in the background.\n\nPID: %s\nstdout: %s\nstderr: %s"
                % (
                    PDG_MODE_LABEL,
                    self._pdg_process.pid,
                    stdout_path,
                    stderr_path,
                ),
                severity="info",
            )
            return True
        except Exception as exc:
            self.core.popup(
                "%s could not start:\n\n%s\n\nConfigure paths in %s."
                % (PDG_MODE_LABEL, exc, SETTINGS_LOCATION),
                severity="error",
            )
            return False

    def _on_pdg_finished(
        self, pid, return_code, stdout_path="", stderr_path=""
    ):
        status = "completed" if return_code == 0 else "failed"
        severity = "info" if return_code == 0 else "error"
        self.core.popup(
            "%s %s.\n\nPID: %s\nExit code: %s\nstdout: %s\nstderr: %s"
            % (
                PDG_MODE_LABEL,
                status,
                pid,
                return_code,
                stdout_path,
                stderr_path,
            ),
            severity=severity,
        )
        self._pdg_monitor = None
        self._pdg_process = None

    def _build_pdg_json(self, shot_data_list):
        result = {}
        for shot_data in shot_data_list:
            episode = shot_data.get("episode", "")
            sequence = shot_data.get("sequence", "")
            shot = shot_data.get("shot", "")
            key = "%s/%s/%s" % (episode, sequence, shot)
            source_root = (
                shot_data.get("source_file_root")
                or shot_data.get("source_server_dir")
                or ""
            )

            file_dict = []
            for step in shot_data.get("steps", {}).values():
                for path in step.get("fbx", []):
                    if not str(path).lower().endswith(".fbx"):
                        continue
                    try:
                        relative = (
                            os.path.relpath(path, source_root)
                            if source_root
                            else path
                        )
                    except ValueError:
                        relative = path
                    file_dict.append(
                        {
                            "path": path,
                            "relpath": str(relative).replace("\\", "/"),
                        }
                    )
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
            xml_data["path"] = animation_xml.get("path", "")
            xml_data["attributes"] = animation_xml.get(
                "attributes", {}
            )
        for label, key in (
            ("Cloth", "cloth_solution"),
            ("Hair", "hair_solution"),
        ):
            solution_xml = (
                shot_data.get("steps", {})
                .get(label, {})
                .get("xml", {})
            )
            if solution_xml.get("path"):
                xml_data[key] = {
                    "xml_path": solution_xml.get("path", ""),
                    "attributes": solution_xml.get("attributes", {}),
                }
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
        directory = tempfile.mkdtemp(prefix="change_prism_pdg_")
        path = os.path.join(directory, "shot_data.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(
                data,
                handle,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        return path

    def _make_pdg_log_paths(self, project_name):
        safe_project = "".join(
            char if char.isalnum() or char in ("-", "_") else "_"
            for char in (project_name or "project")
        )
        prefix = "%s_%s" % (
            safe_project,
            time.strftime("%Y%m%d_%H%M%S"),
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
