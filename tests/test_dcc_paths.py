import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))

from change_prism.dcc_paths import (  # noqa: E402
    derive_hython,
    get_houdini_executable,
    get_prism_hython,
)


class _Core:
    def __init__(self, executable):
        self.executable = executable

    def getExecutableOverride(self, application):
        self.application = application
        return self.executable


class DccPathTests(unittest.TestCase):
    def test_hython_is_derived_next_to_prism_houdini_override(self):
        with tempfile.TemporaryDirectory() as directory:
            suffix = ".exe" if os.name == "nt" else ""
            houdini = Path(directory) / ("houdini" + suffix)
            hython = Path(directory) / ("hython" + suffix)
            houdini.touch()
            hython.touch()
            core = _Core(str(houdini))

            self.assertEqual(
                get_houdini_executable(core), str(houdini)
            )
            self.assertEqual(
                derive_hython(str(houdini)), str(hython)
            )
            self.assertEqual(get_prism_hython(core), str(hython))
            self.assertEqual(core.application, "Houdini")

    def test_missing_neighbor_does_not_guess_a_nonexistent_hython(self):
        with tempfile.TemporaryDirectory() as directory:
            houdini = Path(directory) / "houdini.exe"
            houdini.touch()
            self.assertEqual(derive_hython(str(houdini)), "")
