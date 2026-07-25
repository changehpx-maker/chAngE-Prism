import datetime
import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))

from change_prism.review_copy import service


class ReviewCopyServiceTests(unittest.TestCase):
    def test_creates_daily_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            daily = service.create_daily_directory(
                tmp, datetime.date(2026, 7, 23)
            )
            self.assertEqual(daily, os.path.join(tmp, "2026-07-23"))
            self.assertTrue(os.path.isdir(daily))

    def test_missing_destination_is_clear_error(self):
        with self.assertRaisesRegex(
            service.DestinationNotConfiguredError,
            "review_copy.destination_root",
        ):
            service.create_daily_directory("")

    def test_file_copy_overwrites_same_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            source_dir = os.path.join(tmp, "source")
            destination_root = os.path.join(tmp, "review")
            os.makedirs(source_dir)
            source = os.path.join(source_dir, "scene.hip")
            Path(source).write_text("v1", encoding="utf-8")
            date = datetime.date(2026, 7, 23)

            service.copy_items([source], destination_root, date)
            Path(source).write_text("v2", encoding="utf-8")
            result = service.copy_items([source], destination_root, date)

            target = os.path.join(result["destination"], "scene.hip")
            self.assertEqual(Path(target).read_text(encoding="utf-8"), "v2")
            self.assertFalse(result["failures"])

    def test_folder_copy_merges_and_overwrites_without_deleting_extra_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = os.path.join(tmp, "source", "sequence")
            destination_root = os.path.join(tmp, "review")
            os.makedirs(source)
            Path(source, "beauty.1001.exr").write_text("new", encoding="utf-8")
            date = datetime.date(2026, 7, 23)
            target = os.path.join(destination_root, "2026-07-23", "sequence")
            os.makedirs(target)
            Path(target, "beauty.1001.exr").write_text("old", encoding="utf-8")
            Path(target, "keep.txt").write_text("keep", encoding="utf-8")

            result = service.copy_items([source], destination_root, date)

            self.assertEqual(
                Path(target, "beauty.1001.exr").read_text(encoding="utf-8"),
                "new",
            )
            self.assertTrue(os.path.isfile(os.path.join(target, "keep.txt")))
            self.assertFalse(result["failures"])

    def test_partial_failure_is_collected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = os.path.join(tmp, "review.mov")
            missing = os.path.join(tmp, "missing.mov")
            Path(source).write_bytes(b"video")

            result = service.copy_items(
                [source, missing],
                os.path.join(tmp, "destination"),
                datetime.date(2026, 7, 23),
            )

            self.assertEqual(result["copied"], [source])
            self.assertEqual(len(result["failures"]), 1)
            self.assertEqual(result["failures"][0]["source"], missing)


if __name__ == "__main__":
    unittest.main()
