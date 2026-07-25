import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))

from change_prism.ocio import service as converter


class BundledToolsIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prism_root = os.getenv("PRISM_TEST_ROOT", "")
        if not cls.prism_root:
            raise unittest.SkipTest("Set PRISM_TEST_ROOT to run bundled-tool integration tests")
        cls.oiiotool = os.path.join(
            cls.prism_root,
            "PythonLibs",
            "Python3",
            "OpenImageIO",
            "bin",
            "oiiotool.exe" if sys.platform == "win32" else "oiiotool",
        )
        cls.ffmpeg = os.path.join(
            cls.prism_root,
            "Tools",
            "FFmpeg",
            "bin",
            "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg",
        )
        if not os.path.isfile(cls.oiiotool) or not os.path.isfile(cls.ffmpeg):
            raise unittest.SkipTest("Prism's bundled oiiotool/ffmpeg were not found")

    def test_acescg_sequence_to_tagged_mp4_and_mov(self):
        inventory = converter.read_colorconfig_inventory(
            self.oiiotool, "ocio://default"
        )
        input_space, display, view = converter.choose_inventory_defaults(inventory)
        with tempfile.TemporaryDirectory() as tmp:
            sources = []
            for frame in range(1001, 1004):
                path = os.path.join(tmp, "beauty.%04d.exr" % frame)
                result = subprocess.run([
                    self.oiiotool,
                    "--pattern", "constant:color=0.18,0.18,0.18", "64x64", "3",
                    "-d", "half", "-o", path,
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
                sources.append(path)

            jobs, errors = converter.collect_exr_jobs([sources[0]])
            self.assertFalse(errors)
            job = jobs[0]
            info = converter.inspect_exr(self.oiiotool, job["source_path"])
            temp_pattern = os.path.join(tmp, "display.%04d.tif")
            result = subprocess.run([
                self.oiiotool,
                *converter.build_oiiotool_args(
                    job,
                    temp_pattern,
                    "ocio://default",
                    input_space,
                    display,
                    view,
                    has_alpha=info["has_alpha"],
                ),
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))

            for extension in (".mp4", ".mov"):
                output = os.path.join(tmp, "review" + extension)
                result = subprocess.run([
                    self.ffmpeg,
                    *converter.build_ffmpeg_args(
                        job,
                        temp_pattern,
                        output,
                        24,
                        extension,
                        prores_encoder=(
                            "prores_aw" if extension == ".mov" else "prores_ks"
                        ),
                    ),
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
                self.assertGreater(os.path.getsize(output), 0)
                validation = subprocess.run([
                    self.ffmpeg,
                    *converter.build_validation_args(output),
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.assertEqual(validation.returncode, 0, validation.stderr.decode("utf-8", "replace"))
                probe = subprocess.run(
                    [self.ffmpeg, "-hide_banner", "-i", output],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                self.assertIn("bt709", probe.stderr.lower())
                if extension == ".mov":
                    self.assertIn("prores (hq)", probe.stderr.lower())
                    self.assertIn("yuv422p10le", probe.stderr.lower())


if __name__ == "__main__":
    unittest.main()
