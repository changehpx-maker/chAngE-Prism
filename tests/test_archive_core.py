import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))

from change_prism import archive_core


class ArchiveCoreTests(unittest.TestCase):
    def test_fast_health_check_skips_per_file_manifest_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            version = Path(tmp) / "v0001"
            payload = version / "dependencies" / "cache"
            payload.mkdir(parents=True)
            manifest = {
                "application": "houdini",
                "copy_jobs": [
                    {
                        "destination": "dependencies/cache",
                        "files": ["missing.bgeo.sc"],
                    }
                ],
            }
            self.assertTrue(
                archive_core._manifest_payload_missing(
                    str(version),
                    manifest,
                )
            )
            self.assertFalse(
                archive_core._manifest_payload_missing(
                    str(version),
                    manifest,
                    deep=False,
                )
            )

    def test_infers_department_and_task_from_scene_path(self):
        self.assertEqual(
            archive_core.infer_scene_context(
                r"D:\project\shot\Scenefiles\fx\Effects\scene.hip"
            ),
            {"department": "fx", "task": "Effects"},
        )
        self.assertEqual(
            archive_core.infer_scene_context(
                "/project/shot/Scenefiles/cmp/Compositing/scene.nk"
            ),
            {"department": "cmp", "task": "Compositing"},
        )

    def test_scans_legacy_nuke_and_houdini_manifests_together(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archives = root / "Archives"
            source_nk = root / "source.nk"
            source_nk.write_text("Root {}\n", encoding="utf-8")
            nuke_version = archives / "v0001"
            (nuke_version / "nk").mkdir(parents=True)
            (nuke_version / "sequences" / "plate").mkdir(parents=True)
            packaged_nk = nuke_version / "nk" / "scene.nk"
            packaged_nk.write_text("Root {}\n", encoding="utf-8")
            nuke_manifest = {
                "archive_version": "v0001",
                "source_nk": str(source_nk),
                "packaged_nk": "nk/scene.nk",
                "source_nk_stat": archive_core.file_fingerprint(source_nk),
                "reads": [],
                "copy_jobs": [{"material_folder": "plate"}],
            }
            (nuke_version / "manifest.json").write_text(
                json.dumps(nuke_manifest), encoding="utf-8"
            )

            source_hip = root / "source.hip"
            source_hip.write_bytes(b"hip")
            houdini_version = archives / "v0002"
            (houdini_version / "hip").mkdir(parents=True)
            packaged_hip = houdini_version / "hip" / "scene.hip"
            packaged_hip.write_bytes(b"hip")
            houdini_manifest = {
                "schema_version": 2,
                "application": "houdini",
                "archive_version": "v0002",
                "source_scene": str(source_hip),
                "packaged_scene": "hip/scene.hip",
                "source_scene_stat": archive_core.file_fingerprint(source_hip),
                "dependencies": [
                    {
                        "classification": "Skipped Cache",
                        "status": "Skipped",
                    },
                    {
                        "classification": "Skipped Missing",
                        "status": "Missing (Skipped)",
                    }
                ],
                "copy_jobs": [],
                "summary": {
                    "skipped_cache_count": 1,
                    "skipped_missing_count": 1,
                    "missing_count": 1,
                },
            }
            (houdini_version / "manifest.json").write_text(
                json.dumps(houdini_manifest), encoding="utf-8"
            )

            versions = archive_core.scan_archive_versions(archives)

            self.assertEqual(
                [item["application"] for item in versions],
                ["houdini", "nuke"],
            )
            self.assertEqual(
                versions[0]["status"], "Complete with Exclusions"
            )
            self.assertEqual(versions[0]["skipped_missing_count"], 1)
            self.assertEqual(versions[0]["missing_count"], 1)
            self.assertEqual(versions[1]["status"], "Complete")
            self.assertEqual(
                archive_core.get_next_archive_version(archives), "v0003"
            )

            invalid = archives / "v0003"
            (invalid / "nk").mkdir(parents=True)
            (invalid / "nk" / "scene.nk").write_text(
                "Root {}\n", encoding="utf-8"
            )
            (invalid / "manifest.json").write_text(
                "{}", encoding="utf-8"
            )
            self.assertEqual(
                archive_core.scan_archive_versions(archives)[0]["status"],
                "Invalid Manifest",
            )

    def test_reports_moved_houdini_scene_as_missing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.hip"
            source.write_bytes(b"source")
            version = root / "Archives" / "v0001"
            version.mkdir(parents=True)
            moved_scene = version / "scene_archive_v0001.hip"
            moved_scene.write_bytes(b"archive")
            manifest = {
                "schema_version": 2,
                "application": "houdini",
                "archive_version": "v0001",
                "source_scene": str(source),
                "source_scene_stat": archive_core.file_fingerprint(source),
                "packaged_scene": "hip/scene_archive_v0001.hip",
                "dependencies": [],
                "copy_jobs": [],
            }
            (version / "manifest.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )

            scanned = archive_core.scan_archive_versions(
                root / "Archives"
            )[0]

            self.assertEqual(scanned["packaged_scene"], str(moved_scene))
            self.assertTrue(scanned["scene_location_mismatch"])
            self.assertEqual(scanned["status"], "Missing Files")

    def test_versions_are_independent_per_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archives = root / "Archives"
            contexts = (
                ("v0001", "lgt", "Lighting", ".hip"),
                ("v0002", "cmp", "Compositing", ".nk"),
                ("v0003", "fx", "Effects", ".hip"),
            )
            for storage_version, department, task, extension in contexts:
                source_dir = (
                    root / "Scenefiles" / department / task
                )
                source_dir.mkdir(parents=True, exist_ok=True)
                source = source_dir / ("scene" + extension)
                source.write_bytes(b"source")
                version = archives / storage_version
                version.mkdir(parents=True)
                packaged = version / ("archive" + extension)
                packaged.write_bytes(b"archive")
                manifest = {
                    "application": (
                        "nuke" if extension == ".nk" else "houdini"
                    ),
                    "archive_version": storage_version,
                    "department": department,
                    "task": task,
                    "source_scene": str(source),
                    "packaged_scene": packaged.name,
                    "source_scene_stat": archive_core.file_fingerprint(
                        source
                    ),
                    "dependencies": [],
                    "copy_jobs": [],
                }
                if extension == ".nk":
                    manifest["source_nk"] = manifest.pop("source_scene")
                    manifest["packaged_nk"] = manifest.pop(
                        "packaged_scene"
                    )
                    manifest["source_nk_stat"] = manifest.pop(
                        "source_scene_stat"
                    )
                    manifest["reads"] = []
                (version / "manifest.json").write_text(
                    json.dumps(manifest), encoding="utf-8"
                )

            versions = archive_core.scan_archive_versions(archives)
            self.assertEqual(
                {
                    (item["department"], item["task"]): item["version"]
                    for item in versions
                },
                {
                    ("lgt", "Lighting"): "v0001",
                    ("cmp", "Compositing"): "v0001",
                    ("fx", "Effects"): "v0001",
                },
            )
            self.assertEqual(
                {
                    item["storage_version"] for item in versions
                },
                {"v0001", "v0002", "v0003"},
            )
            self.assertEqual(
                archive_core.get_next_task_archive_version(
                    archives, "fx", "Effects"
                ),
                "v0002",
            )
            self.assertEqual(
                archive_core.get_next_task_archive_version(
                    archives, "lgt", "Lighting"
                ),
                "v0002",
            )
            self.assertEqual(
                archive_core.get_next_task_archive_version(
                    archives, "cfx", "Cloth"
                ),
                "v0001",
            )

            task_version, task_path = (
                archive_core.reserve_task_version_directory(
                    archives, "fx", "Effects"
                )
            )
            self.assertEqual(task_version, "v0002")
            self.assertEqual(
                Path(task_path),
                archives / "Effects" / "v0002",
            )
            with self.assertRaises(archive_core.ArchiveError):
                archive_core.delete_archive_version(task_path, archives)
            archive_core.delete_archive_version(
                task_path, archives / "Effects"
            )
            self.assertFalse(Path(task_path).exists())

    def test_previous_department_task_layout_uses_task_only_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archives = root / "Archives"
            source_dir = (
                root / "Scenefiles" / "fx" / "Fire"
            )
            source_dir.mkdir(parents=True)
            source = source_dir / "fire.hip"
            source.write_bytes(b"source")
            previous_version = (
                archives / "fx" / "Fire" / "v0001"
            )
            previous_version.mkdir(parents=True)
            packaged = previous_version / "fire_archive_v0001.hip"
            packaged.write_bytes(b"archive")
            manifest = {
                "schema_version": 2,
                "application": "houdini",
                "archive_version": "v0001",
                "task_version": "v0001",
                "version_scope": "task",
                "department": "fx",
                "task": "Fire",
                "source_scene": str(source),
                "source_scene_stat": archive_core.file_fingerprint(
                    source
                ),
                "packaged_scene": packaged.name,
                "dependencies": [],
                "copy_jobs": [],
            }
            (previous_version / "manifest.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )

            self.assertEqual(
                archive_core.get_next_task_archive_version(
                    archives, "fx", "Fire"
                ),
                "v0002",
            )
            self.assertEqual(
                archive_core.get_next_task_archive_version(
                    archives, "another_department", "Fire"
                ),
                "v0002",
            )
            version, path = archive_core.reserve_task_version_directory(
                archives, "another_department", "Fire"
            )
            self.assertEqual(version, "v0002")
            self.assertEqual(
                Path(path), archives / "Fire" / "v0002"
            )

    def test_delete_is_scoped_and_refuses_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archives = root / "Archives"
            version = archives / "v0001"
            version.mkdir(parents=True)
            (version / ".incomplete").write_text("busy", encoding="utf-8")
            with self.assertRaises(archive_core.ArchiveError):
                archive_core.delete_archive_version(version, archives)
            (version / ".incomplete").unlink()
            (version / "manifest.json").write_text(
                json.dumps({"status": "Incomplete"}), encoding="utf-8"
            )
            with self.assertRaises(archive_core.ArchiveError):
                archive_core.delete_archive_version(version, archives)
            (version / "manifest.json").write_text(
                json.dumps({"status": "Complete"}), encoding="utf-8"
            )
            result = archive_core.delete_archive_version(version, archives)
            self.assertEqual(result["version"], "v0001")
            self.assertFalse(version.exists())


if __name__ == "__main__":
    unittest.main()
