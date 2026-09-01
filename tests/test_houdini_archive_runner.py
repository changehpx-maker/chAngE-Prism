import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))

from change_prism.houdini_archive import runner


class HoudiniArchiveRunnerTests(unittest.TestCase):
    def test_reads_binary_hip_version_and_rejects_old_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            hip = Path(tmp) / "scene.hip"
            hip.write_bytes(b"prefix _HIP_SAVEVERSION = '21.0.631' suffix")
            self.assertEqual(runner.read_hip_version(hip), "21.0.631")

            hip.write_bytes(b"_HIP_SAVEVERSION = '19.5.640'")
            with self.assertRaisesRegex(runner.RunnerError, "20.5"):
                runner.read_hip_version(hip)

    def test_selects_lowest_compatible_build_in_same_release(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            older = root / "Houdini 20.5.500" / "bin" / "hython.exe"
            exact = root / "Houdini 20.5.684" / "bin" / "hython.exe"
            newer = root / "Houdini 20.5.700" / "bin" / "hython.exe"
            for path in (older, exact, newer):
                path.parent.mkdir(parents=True)
                path.touch()
            selected = runner.resolve_hython(
                "20.5.684",
                explicit_path=str(exact),
            )
            self.assertEqual(selected["version"], "20.5.684")
            self.assertFalse(selected["warning"])

            with self.assertRaises(runner.RunnerError):
                runner.resolve_hython(
                    "20.5.684",
                    explicit_path=str(older),
                )
            with mock.patch.object(
                runner,
                "_discover_hython",
                return_value=[str(newer), str(older)],
            ):
                selected = runner.resolve_hython("20.5.684")
            self.assertEqual(selected["version"], "20.5.700")
            self.assertTrue(selected["warning"])

    def test_different_major_minor_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = (
                Path(tmp)
                / "Houdini 21.0.631"
                / "bin"
                / "hython.exe"
            )
            path.parent.mkdir(parents=True)
            path.touch()
            with self.assertRaises(runner.RunnerError):
                runner.resolve_hython(
                    "20.5.684", explicit_path=str(path)
                )

    def test_run_worker_times_out_and_terminates_hung_process(self):
        class _HungProcess:
            def __init__(self):
                self.terminated = False
                self.killed = False

            def poll(self):
                return None

            def terminate(self):
                self.terminated = True

            def kill(self):
                self.killed = True

            def wait(self, timeout=None):
                return 0

        process = _HungProcess()
        with mock.patch.object(
            runner.subprocess, "Popen", return_value=process
        ):
            with self.assertRaisesRegex(
                runner.RunnerTimeout, "did not finish within"
            ):
                runner.run_worker(
                    "hython.exe",
                    "inspect",
                    "scene.hip",
                    timeout_seconds=0.2,
                )
        self.assertTrue(process.terminated)
        self.assertFalse(process.killed)

    def test_run_worker_reports_launch_failure_as_runner_error(self):
        with mock.patch.object(
            runner.subprocess,
            "Popen",
            side_effect=OSError("no such file"),
        ):
            with self.assertRaisesRegex(
                runner.RunnerError, "Could not start hython"
            ):
                runner.run_worker(
                    "missing_hython.exe", "inspect", "scene.hip"
                )

    def test_run_worker_zero_timeout_disables_deadline(self):
        # A zero timeout must disable the deadline entirely: the slow
        # process stays alive past it and must not be terminated.
        class _SlowProcess:
            calls = 0

            def poll(self):
                _SlowProcess.calls += 1
                if _SlowProcess.calls > 3:
                    return 0
                return None

            def terminate(self):
                raise AssertionError("should not terminate")

            def kill(self):
                raise AssertionError("should not kill")

            def wait(self, timeout=None):
                return 0

        with mock.patch.object(
            runner.subprocess, "Popen", return_value=_SlowProcess()
        ):
            with self.assertRaises(runner.RunnerError):
                runner.run_worker(
                    "hython.exe",
                    "inspect",
                    "scene.hip",
                    timeout_seconds=0,
                )


if __name__ == "__main__":
    unittest.main()
