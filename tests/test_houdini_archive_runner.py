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


if __name__ == "__main__":
    unittest.main()
