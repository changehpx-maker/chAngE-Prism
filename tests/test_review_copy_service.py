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

    def test_product_sequence_file_copies_whole_version_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            version = os.path.join(tmp, "source", "v0001")
            destination_root = os.path.join(tmp, "review")
            os.makedirs(version)
            first = os.path.join(version, "cache.1001.bgeo.sc")
            second = os.path.join(version, "cache.1002.bgeo.sc")
            Path(first).write_text("1001", encoding="utf-8")
            Path(second).write_text("1002", encoding="utf-8")

            result = service.copy_items(
                [{"path": first, "detect_product_sequence": True}],
                destination_root,
                datetime.date(2026, 7, 23),
            )

            target = os.path.join(result["destination"], "v0001")
            self.assertTrue(os.path.isfile(os.path.join(target, os.path.basename(first))))
            self.assertTrue(os.path.isfile(os.path.join(target, os.path.basename(second))))
            self.assertEqual(result["copied"], [version])

    def test_rejects_destination_nested_inside_source_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = os.path.join(tmp, "source")
            destination_root = os.path.join(source, "daily")
            os.makedirs(source)
            Path(source, "cache.1001.bgeo.sc").touch()

            result = service.copy_items(
                [source],
                destination_root,
                datetime.date(2026, 7, 23),
            )

            self.assertFalse(result["copied"])
            self.assertEqual(len(result["failures"]), 1)
            self.assertIn("inside the source", result["failures"][0]["error"])
            self.assertFalse(os.path.exists(destination_root))

    def test_single_numbered_product_file_stays_a_file_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            version = os.path.join(tmp, "source", "v0001")
            destination_root = os.path.join(tmp, "review")
            os.makedirs(version)
            source = os.path.join(version, "cache.1001.bgeo.sc")
            Path(source).write_text("single", encoding="utf-8")

            result = service.copy_items(
                [{"path": source, "detect_product_sequence": True}],
                destination_root,
                datetime.date(2026, 7, 23),
            )

            target = os.path.join(result["destination"], os.path.basename(source))
            self.assertTrue(os.path.isfile(target))
            self.assertEqual(result["copied"], [source])

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
