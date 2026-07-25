import os
import json
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))

from change_prism.ocio import service as converter


INVENTORY = """
OpenColorIO 2.5.1
Color config: C:/show/config.ocio
Known color spaces:
    - ACES2065-1 (linear)
    - ACEScg (linear)
    - "sRGB Encoded Rec.709 (sRGB)"
Known roles:
    - scene_linear -> ACEScg
Known displays: (* indicates default)
    - "sRGB - Display" (*)
      views: "ACES 2.0 - SDR 100 nits (Rec.709)" (*), Raw
    - "Rec.1886 Rec.709 - Display"
      views: "ACES 1.0 SDR-video" (*), Raw
Named transforms:
"""


class InventoryTests(unittest.TestCase):
    def test_parse_inventory_and_choose_rec709_defaults(self):
        inventory = converter.parse_colorconfig_info(INVENTORY)
        self.assertEqual(inventory["config"], "C:/show/config.ocio")
        self.assertIn("ACEScg", inventory["colorspaces"])
        self.assertEqual(inventory["roles"]["scene_linear"], "ACEScg")
        self.assertEqual(inventory["default_display"], "sRGB - Display")
        self.assertEqual(
            inventory["displays"]["Rec.1886 Rec.709 - Display"],
            ["ACES 1.0 SDR-video", "Raw"],
        )
        self.assertEqual(
            converter.choose_inventory_defaults(inventory),
            ("ACEScg", "Rec.1886 Rec.709 - Display", "ACES 1.0 SDR-video"),
        )

    def test_validate_missing_selection(self):
        inventory = converter.parse_colorconfig_info(INVENTORY)
        errors = converter.validate_color_selection(
            inventory, "linear", "Missing Display", "Missing View"
        )
        self.assertEqual(len(errors), 2)

    def test_inventory_query_is_cached(self):
        converter._INVENTORY_CACHE.clear()
        result = mock.Mock(returncode=0, stdout=INVENTORY, stderr="")
        with mock.patch.object(converter.subprocess, "run", return_value=result) as run:
            first = converter.read_colorconfig_inventory(
                "C:/Prism/oiiotool.exe", "ocio://default"
            )
            second = converter.read_colorconfig_inventory(
                "C:/Prism/oiiotool.exe", "ocio://default"
            )
        self.assertIs(first, second)
        self.assertEqual(run.call_count, 1)

    def test_config_precedence(self):
        data = {
            "ocio_converter": {
                "project_overrides": {"show": "D:/show/config.ocio"}
            }
        }
        self.assertEqual(
            converter.select_ocio_config("show", data, {"OCIO": "D:/env.ocio"}),
            ("D:/show/config.ocio", "project_override"),
        )
        self.assertEqual(
            converter.select_ocio_config("other", data, {"OCIO": "D:/env.ocio"}),
            ("D:/env.ocio", "environment"),
        )
        self.assertEqual(
            converter.select_ocio_config("other", data, {}),
            ("ocio://default", "oiio_default"),
        )

    def test_save_and_clear_project_override_preserves_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "config.json")
            with open(path, "w", encoding="utf-8") as stream:
                json.dump({"server_root": "P:/"}, stream)
            converter.save_project_override(path, "show", "D:/show/config.ocio")
            with open(path, "r", encoding="utf-8") as stream:
                data = json.load(stream)
            self.assertEqual(data["server_root"], "P:/")
            self.assertEqual(
                data["ocio_converter"]["project_overrides"]["show"],
                "D:/show/config.ocio",
            )
            converter.save_project_override(path, "show", "")
            with open(path, "r", encoding="utf-8") as stream:
                data = json.load(stream)
            self.assertNotIn("show", data["ocio_converter"]["project_overrides"])


class SequenceTests(unittest.TestCase):
    def test_collect_sequence_and_find_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for frame in (1001, 1002, 1004):
                path = os.path.join(tmp, "镜头.beauty.%04d.exr" % frame)
                Path(path).touch()
                paths.append(path)

            jobs, errors = converter.collect_exr_jobs([paths[1], paths[0]])
            self.assertFalse(errors)
            self.assertEqual(len(jobs), 1)
            self.assertTrue(jobs[0]["is_sequence"])
            self.assertEqual(jobs[0]["first"], 1001)
            self.assertEqual(jobs[0]["last"], 1004)
            self.assertEqual(jobs[0]["missing_frames"], [1003])
            self.assertIn("%04d", jobs[0]["input_pattern"])

    def test_version_named_exr_is_single_frame(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "beauty_v001.exr")
            Path(path).touch()
            jobs, errors = converter.collect_exr_jobs([path])
            self.assertFalse(errors)
            self.assertFalse(jobs[0]["is_sequence"])

    def test_reject_non_exr(self):
        jobs, errors = converter.collect_exr_jobs(["C:/tmp/file.png"])
        self.assertFalse(jobs)
        self.assertEqual(len(errors), 1)


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.job = {
            "input_pattern": "D:/show space/shot.%04d.exr",
            "source_path": "D:/show space/shot.1001.exr",
            "first": 1001,
            "last": 1010,
            "padding": 4,
            "frame_count": 10,
            "is_sequence": True,
        }

    def test_oiiotool_command_uses_display_transform(self):
        args = converter.build_oiiotool_args(
            self.job,
            "D:/temp/frame.%04d.tif",
            "D:/show/config.ocio",
            "ACEScg",
            "Rec.1886 Rec.709 - Display",
            "ACES 1.0 SDR-video",
            has_alpha=True,
        )
        self.assertIn("--parallel-frames", args)
        self.assertIn("--ociodisplay:from=ACEScg:unpremult=1", args)
        self.assertIn("Rec.1886 Rec.709 - Display", args)
        self.assertEqual(args[-2:], ["-o", "D:/temp/frame.%04d.tif"])

    def test_oiiotool_command_supports_fast_10bit_dpx(self):
        args = converter.build_oiiotool_args(
            self.job,
            "D:/temp/frame.%04d.dpx",
            "D:/show/config.ocio",
            "ACEScg",
            "Rec.1886 Rec.709 - Display",
            "ACES 1.0 SDR-video",
            data_type="uint10",
            compression=None,
        )
        self.assertIn("uint10", args)
        self.assertNotIn("--compression", args)

    def test_mp4_preset_and_tags(self):
        args = converter.build_ffmpeg_args(
            self.job, "D:/temp/frame.%04d.tif", "D:/out/review.mp4", 23.976, ".mp4"
        )
        self.assertIn("libx264", args)
        self.assertIn("yuv420p", args)
        self.assertEqual(args.count("bt709"), 3)
        self.assertIn("+faststart", args)

    def test_prores_preset_and_tags(self):
        args = converter.build_ffmpeg_args(
            self.job, "D:/temp/frame.%04d.tif", "D:/out/review.mov", 24, ".mov"
        )
        self.assertIn("prores_ks", args)
        self.assertIn("yuv422p10le", args)
        self.assertEqual(args.count("bt709"), 3)

    def test_fast_prores_encoder(self):
        args = converter.build_ffmpeg_args(
            self.job,
            "D:/temp/frame.%04d.dpx",
            "D:/out/review.mov",
            24,
            ".mov",
            prores_encoder="prores_aw",
        )
        self.assertEqual(args[args.index("-c:v") + 1], "prores_aw")
        self.assertEqual(args[args.index("-profile:v") + 1], "3")
        with self.assertRaises(ValueError):
            converter.build_ffmpeg_args(
                self.job,
                "D:/temp/frame.%04d.dpx",
                "D:/out/review.mov",
                24,
                ".mov",
                prores_encoder="invalid",
            )

    def test_validation_decodes_only_first_frame_by_default(self):
        args = converter.build_validation_args("D:/out/review.mov")
        self.assertIn("-frames:v", args)
        self.assertEqual(args[args.index("-frames:v") + 1], "1")
        self.assertNotIn("-frames:v", converter.build_validation_args(
            "D:/out/review.mov", full=True
        ))

    def test_external_output_and_staging_names(self):
        output = converter.external_output_path(self.job, ".mp4")
        self.assertTrue(output.endswith("shot.rec709.mp4"))
        self.assertTrue(
            converter.staging_output_path(output).endswith("shot.rec709.chAnGE_tmp.mp4")
        )

    def test_fps_validation(self):
        self.assertAlmostEqual(converter.validate_fps("23.976"), 23.976)
        with self.assertRaises(ValueError):
            converter.validate_fps(0)


if __name__ == "__main__":
    unittest.main()
