import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from change_prism.batch_import.scanner import (
    clear_list_dirs_cache,
    collect_step_files,
    parse_filter_strings,
    parse_xml_attributes,
    scan_server_shots,
)
from change_prism.batch_import import scanner


class BatchImportScannerTests(unittest.TestCase):
    def test_three_line_filters_are_merged(self):
        text = "Q2EP014/\nSC02/\nshot014a\nQ2EP014/\nSC02/\nshot091c"
        self.assertEqual(
            parse_filter_strings(text),
            [
                "Q2EP014/SC02/shot014a",
                "Q2EP014/SC02/shot091c",
            ],
        )

    def test_nested_files_are_collected_case_insensitively(self):
        with tempfile.TemporaryDirectory() as directory:
            step = Path(directory) / "cloth_solution"
            abc = step / "vfx" / "element" / "CLOTH.ABC"
            mov = step / "review" / "nested" / "preview.MOV"
            abc.parent.mkdir(parents=True)
            mov.parent.mkdir(parents=True)
            abc.touch()
            mov.touch()

            files = collect_step_files(
                str(step), "cloth_solution"
            )

        self.assertEqual(len(files["abc_files"]), 1)
        self.assertEqual(len(files["mov_files"]), 1)

    def test_xml_attributes_and_frame_range_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            xml_path = Path(directory) / "description.xml"
            xml_path.write_text(
                "<root>"
                '<attribute name="sequence_frame" value="100.0"/>'
                '<attribute name="render_start_frame" value="1001.0"/>'
                '<attribute name="average_translation" value="[1, 2, 3]"/>'
                "</root>",
                encoding="utf-8",
            )
            parsed = parse_xml_attributes(str(xml_path))

        self.assertEqual(parsed["frame_range"], [1001, 1100])
        self.assertEqual(
            parsed["attributes"]["average_translation"],
            [1, 2, 3],
        )

    def test_corrupt_start_frame_keeps_other_attributes(self):
        with tempfile.TemporaryDirectory() as directory:
            xml_path = Path(directory) / "description.xml"
            xml_path.write_text(
                "<root>"
                '<attribute name="sequence_frame" value="48"/>'
                '<attribute name="render_start_frame" value="abc"/>'
                '<attribute name="average_translation" value="[1, 2, 3]"/>'
                "</root>",
                encoding="utf-8",
            )
            parsed = parse_xml_attributes(str(xml_path))

        self.assertEqual(
            parsed["attributes"]["average_translation"],
            [1, 2, 3],
        )
        self.assertEqual(
            parsed["attributes"]["sequence_frame"],
            48,
        )
        self.assertEqual(parsed["frame_range"], [1001, 1048])

    def test_unreadable_directory_is_skipped_and_collected(self):
        def fake_walk(path, onerror=None):
            if onerror is not None:
                onerror(OSError("permission denied: %s" % path))
            yield path, [], ["keep.fbx"]

        with mock.patch.object(
            scanner.os, "walk", side_effect=fake_walk
        ):
            errors = []
            files = scanner._collect_matching_files(
                r"S:\shot\step", ["*.fbx"], errors
            )

        self.assertEqual(files, [r"S:\shot\step\keep.fbx"])
        self.assertEqual(len(errors), 1)
        self.assertIn("permission denied", errors[0])

    def test_scan_server_shots_reports_walk_warnings(self):
        def fake_walk(path, onerror=None):
            if os.path.basename(str(path)).lower() == "vfx":
                if onerror is not None:
                    onerror(OSError("denied: %s" % path))
                yield path, [], []
                return
            yield path, [], []

        with tempfile.TemporaryDirectory() as directory:
            shot = (
                Path(directory)
                / "proj"
                / "publish"
                / "shot"
                / "EP01"
                / "SC01"
                / "shot0010"
                / "shot_solution"
                / "cloth_solution"
                / "vfx"
            )
            shot.mkdir(parents=True)
            (shot / "anim.fbx").touch()

            with mock.patch.object(
                scanner.os, "walk", side_effect=fake_walk
            ):
                warnings = []
                results = scan_server_shots(
                    directory, ["EP01/SC01/shot0010"],
                    project_code="proj", warnings=warnings,
                )

        self.assertEqual(len(results), 1)
        self.assertEqual(len(warnings), 1)
        self.assertIn("denied", warnings[0])

    def test_list_dirs_returns_empty_on_oserror(self):
        clear_list_dirs_cache()
        with mock.patch.object(
            scanner.os, "listdir", side_effect=OSError("denied")
        ):
            self.assertEqual(scanner._list_dirs(r"S:\inaccessible"), [])
        clear_list_dirs_cache()

    def test_scan_returns_fbx_and_frame_range(self):
        with tempfile.TemporaryDirectory() as directory:
            step = (
                Path(directory)
                / "show"
                / "publish"
                / "shot"
                / "EP01"
                / "SC01"
                / "shot001"
                / "shot_motion"
                / "shot_animation"
            )
            (step / "fbx").mkdir(parents=True)
            (step / "xml").mkdir()
            (step / "fbx" / "camera.fbx").touch()
            (step / "xml" / "description.xml").write_text(
                "<root>"
                '<attribute name="sequence_frame" value="10"/>'
                '<attribute name="render_start_frame" value="1001"/>'
                "</root>",
                encoding="utf-8",
            )
            clear_list_dirs_cache()
            results = scan_server_shots(
                directory,
                ["EP01/SC01/shot001"],
                project_code="show",
            )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["frame_range"], [1001, 1010])
        self.assertEqual(
            len(results[0]["steps"][0]["files"]["fbx_files"]),
            1,
        )
