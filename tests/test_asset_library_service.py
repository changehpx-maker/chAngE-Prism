import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))

from change_prism.asset_library import service


class AssetLibraryServiceTests(unittest.TestCase):
    def test_scan_preserves_directories_and_filters_supported_images(self):
        with tempfile.TemporaryDirectory() as tmp:
            category = os.path.join(tmp, "Natural_Light")
            thumbs = os.path.join(category, "_thumbs")
            os.makedirs(thumbs)
            Path(category, "sky.EXR").write_bytes(b"exr")
            Path(category, "plate.JpEg").write_bytes(b"jpg")
            Path(category, "notes.txt").write_text("ignore", encoding="utf-8")
            Path(thumbs, "cached.exr.jpg").write_bytes(b"thumb")

            result = service.scan_sources(
                [{"path": tmp, "enabled": True}]
            )

            self.assertFalse(result["cancelled"])
            self.assertFalse(result["failures"])
            self.assertEqual(
                sorted(asset["filename"] for asset in result["assets"]),
                ["plate.JpEg", "sky.EXR"],
            )
            relative_directories = {
                item["relative_path"] for item in result["directories"]
            }
            self.assertIn("", relative_directories)
            self.assertIn("Natural_Light", relative_directories)
            self.assertNotIn(
                os.path.join("Natural_Light", "_thumbs"),
                relative_directories,
            )
            self.assertEqual(result["sources"][0]["name"], os.path.basename(tmp))

    def test_directory_view_is_not_recursive(self):
        with tempfile.TemporaryDirectory() as tmp:
            nested = os.path.join(tmp, "category", "nested")
            os.makedirs(nested)
            Path(tmp, "root.hdr").write_bytes(b"root")
            Path(tmp, "category", "category.hdr").write_bytes(b"category")
            Path(nested, "nested.hdr").write_bytes(b"nested")

            result = service.scan_sources([{"path": tmp, "enabled": True}])
            source_id = result["sources"][0]["id"]

            self.assertEqual(
                [
                    item["filename"]
                    for item in service.assets_in_directory(
                        result["assets"], source_id, tmp
                    )
                ],
                ["root.hdr"],
            )
            self.assertEqual(
                [
                    item["filename"]
                    for item in service.assets_in_directory(
                        result["assets"],
                        source_id,
                        os.path.join(tmp, "category"),
                    )
                ],
                ["category.hdr"],
            )

    def test_multiple_directories_combine_direct_files_and_deduplicate_paths(
        self,
    ):
        first = self._asset(
            "source-a",
            "C:/library/clear/first.exr",
            "clear",
        )
        second = self._asset(
            "source-a",
            "C:/library/outdoor/second.exr",
            "outdoor",
        )
        duplicate = dict(first)
        duplicate["source_id"] = "source-b"

        selected = service.assets_in_directories(
            [first, second, duplicate],
            [
                ("source-a", "C:/library/clear"),
                ("source-a", "C:/library/outdoor"),
                ("source-b", "C:/library/clear"),
            ],
        )

        self.assertEqual(selected, [first, second])

    def test_global_search_matches_filename_source_and_relative_directory(self):
        assets = [
            {
                "filename": "studio_4k.exr",
                "source_name": "PolyHaven",
                "relative_directory": "artificial_light",
            },
            {
                "filename": "forest_4k.exr",
                "source_name": "HDRI",
                "relative_directory": "nature",
            },
        ]
        self.assertEqual(
            service.search_assets(assets, "poly studio"),
            [assets[0]],
        )
        self.assertEqual(
            service.search_assets(assets, "NATURE"),
            [assets[1]],
        )

    def test_duplicates_merge_only_inside_the_same_source(self):
        first = self._asset(
            "source-a", "C:/source-a/clear/sky.exr", "clear"
        )
        second = self._asset(
            "source-a", "C:/source-a/outdoor/sky.exr", "outdoor"
        )
        other_source = self._asset(
            "source-b", "D:/source-b/sky.exr", ""
        )

        records = service.aggregate_assets(
            [second, other_source, first]
        )

        self.assertEqual(len(records), 2)
        source_a = next(
            record for record in records if record["source_id"] == "source-a"
        )
        self.assertEqual(source_a["location_count"], 2)
        self.assertEqual(
            [item["relative_directory"] for item in source_a["locations"]],
            ["clear", "outdoor"],
        )

    def test_duplicate_metadata_mismatch_stays_separate(self):
        first = self._asset("source-a", "C:/a/sky.exr", "a")
        second = self._asset("source-a", "C:/b/sky.exr", "b")
        second["mtime_ns"] += 1
        self.assertEqual(
            len(service.aggregate_assets([first, second])),
            2,
        )

    def test_sorting_supports_natural_name_size_and_modified(self):
        first = self._asset("source", "C:/sky10.exr", "")
        second = self._asset("source", "C:/sky2.exr", "")
        first["size"] = 100
        second["size"] = 20
        first["mtime_ns"] = 1
        second["mtime_ns"] = 2

        self.assertEqual(
            [
                item["filename"]
                for item in service.sort_assets([first, second], "name")
            ],
            ["sky2.exr", "sky10.exr"],
        )
        self.assertEqual(
            service.sort_assets([first, second], "size")[0]["size"],
            20,
        )
        self.assertEqual(
            service.sort_assets(
                [first, second], "modified", descending=True
            )[0]["mtime_ns"],
            2,
        )

    def test_missing_disabled_and_cancelled_sources_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = os.path.join(tmp, "missing")
            result = service.scan_sources(
                [
                    {"path": missing, "enabled": True},
                    {"path": tmp, "enabled": False},
                ]
            )
            self.assertFalse(result["sources"][0]["available"])
            self.assertEqual(len(result["failures"]), 1)
            self.assertEqual(result["sources"][1]["file_count"], 0)

            cancelled = threading.Event()
            cancelled.set()
            result = service.scan_sources(
                [{"path": tmp, "enabled": True}],
                cancel_event=cancelled,
            )
            self.assertTrue(result["cancelled"])
            self.assertFalse(result["assets"])

    def test_linked_directories_are_not_followed(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = os.path.join(tmp, "source")
            external = os.path.join(tmp, "external")
            os.makedirs(source)
            os.makedirs(external)
            Path(external, "outside.exr").write_bytes(b"outside")
            link = os.path.join(source, "linked")
            try:
                os.symlink(external, link, target_is_directory=True)
            except (NotImplementedError, OSError):
                self.skipTest("Directory symlinks are unavailable")

            result = service.scan_sources(
                [{"path": source, "enabled": True}]
            )
            self.assertFalse(result["assets"])
            self.assertNotIn(
                "linked",
                [item["relative_path"] for item in result["directories"]],
            )

    def test_thumbnail_cache_name_keeps_the_original_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            asset = os.path.join(tmp, "sky.exr")
            Path(asset).write_bytes(b"source")
            cache = service.thumbnail_path(asset)
            self.assertEqual(
                cache,
                os.path.join(tmp, "_thumbs", "sky.exr.jpg"),
            )
            os.makedirs(os.path.dirname(cache))
            Path(cache).write_bytes(b"thumb")
            source_time = os.path.getmtime(asset)
            os.utime(cache, (source_time + 1, source_time + 1))
            self.assertTrue(service.thumbnail_is_fresh(asset, cache))
            os.utime(asset, (source_time + 2, source_time + 2))
            self.assertFalse(service.thumbnail_is_fresh(asset, cache))

    @staticmethod
    def _asset(source_id, path, relative_directory):
        return {
            "source_id": source_id,
            "source_path": os.path.dirname(path),
            "source_name": source_id,
            "path": os.path.normpath(path),
            "directory": os.path.dirname(os.path.normpath(path)),
            "relative_directory": relative_directory,
            "filename": os.path.basename(path),
            "extension": ".exr",
            "size": 50,
            "mtime_ns": 1000,
        }


if __name__ == "__main__":
    unittest.main()
