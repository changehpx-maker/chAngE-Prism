import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))

from change_prism.nuke_archive import service


def _nuke_path(path):
    return str(path).replace("\\", "/")


def _write_script(path, read_paths, write_path=None, metadata_path=None):
    lines = [
        "#! Nuke13.2 -nx\n",
        "version 13.2 v1\n",
        "Root {\n",
        " inputs 0\n",
        " name %s\n" % _nuke_path(path),
        "}\n",
    ]
    for index, read_path in enumerate(read_paths, 1):
        value = _nuke_path(read_path)
        if " " in value:
            value = "{%s}" % value
        lines.extend(
            [
                "Read {\n",
                " inputs 0\n",
                " file %s\n" % value,
                " name Read%d\n" % index,
            ]
        )
        if metadata_path and index == 1:
            lines.append(
                " addUserKnob {26 fileName l File T %s}\n"
                % _nuke_path(metadata_path)
            )
        lines.append("}\n")
    if write_path:
        lines.extend(
            [
                "Write {\n",
                " file %s\n" % _nuke_path(write_path),
                " name Write1\n",
                "}\n",
            ]
        )
    Path(path).write_text("".join(lines), encoding="utf-8")


class NukeArchiveServiceTests(unittest.TestCase):
    def test_execute_reuses_preflight_plan_without_second_tree_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            (source / "plate.1001.exr").write_bytes(b"frame")
            script = root / "scene.nk"
            _write_script(script, [source / "plate.%04d.exr"])
            plan = service.build_package_plan(
                script,
                root / "Archives",
            )

            with mock.patch.object(
                service,
                "build_package_plan",
                side_effect=AssertionError("unexpected second scan"),
            ):
                result = service.execute_package(plan)

            self.assertTrue(Path(result["packaged_nk"]).is_file())

    def test_build_plan_reuses_source_directory_and_suffixes_name_collision(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "first"
            second = root / "second"
            first.mkdir()
            second.mkdir()
            (first / "beauty.1001.exr").write_text("a", encoding="utf-8")
            (first / "mask.1001.exr").write_text("b", encoding="utf-8")
            (second / "beauty.1001.exr").write_text("c", encoding="utf-8")
            script = root / "scene.nk"
            _write_script(
                script,
                [
                    first / "beauty.%04d.exr",
                    first / "mask.%04d.exr",
                    second / "beauty.%04d.exr",
                ],
            )

            plan = service.build_package_plan(script, root / "Archives")

            self.assertEqual(len(plan["reads"]), 3)
            self.assertEqual(len(plan["copy_jobs"]), 2)
            self.assertEqual(
                [job["material_folder"] for job in plan["copy_jobs"]],
                ["beauty", "beauty_2"],
            )
            self.assertEqual(
                plan["reads"][1]["material_folder"],
                "beauty",
            )
            self.assertEqual(plan["estimated_file_count"], 3)
            self.assertEqual(plan["estimated_total_bytes"], 3)
            self.assertIsNotNone(plan["available_bytes"])

    def test_hash_in_directory_name_keeps_single_file_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "renders_v#2"
            folder.mkdir()
            frame = folder / "plate.1001.exr"
            frame.write_bytes(b"frame")
            script = root / "scene.nk"
            _write_script(script, [frame])

            plan = service.build_package_plan(script, root / "Archives")

            self.assertEqual(len(plan["copy_jobs"]), 1)
            self.assertEqual(plan["copy_jobs"][0]["kind"], "file")
            self.assertEqual(plan["estimated_file_count"], 1)

    def test_sequence_match_respects_platform_case_sensitivity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "FRAME.1001.exr").write_bytes(b"frame")
            pattern = str(root / "frame.%04d.exr")

            with mock.patch.object(service.os, "name", "posix"):
                self.assertFalse(
                    service._sequence_has_matching_file(pattern)
                )
            with mock.patch.object(service.os, "name", "nt"):
                self.assertTrue(
                    service._sequence_has_matching_file(pattern)
                )

    def test_execute_rejects_plan_when_source_stat_unreadable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            (source / "plate.1001.exr").write_bytes(b"frame")
            script = root / "scene.nk"
            _write_script(script, [source / "plate.%04d.exr"])
            plan = service.build_package_plan(
                script,
                root / "Archives",
            )

            with mock.patch.object(
                service, "_file_fingerprint", return_value=None
            ):
                with self.assertRaises(service.PackageExecutionError):
                    service.execute_package(plan)

    def test_execute_copies_directories_and_rewrites_only_archive_nuke(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sequence = root / "source with spaces"
            sequence.mkdir()
            (sequence / "beauty.1001.exr").write_text("frame", encoding="utf-8")
            (sequence / "sidecar.txt").write_text("sidecar", encoding="utf-8")
            write_path = root / "renders" / "output.mov"
            metadata_path = root / "old" / "metadata.exr"
            scene_directory = (
                root / "Scenefiles" / "cmp" / "Compositing"
            )
            scene_directory.mkdir(parents=True)
            script = scene_directory / "scene.nk"
            _write_script(
                script,
                [sequence / "beauty.%04d.exr"],
                write_path=write_path,
                metadata_path=metadata_path,
            )
            original = script.read_bytes()
            plan = service.build_package_plan(script, root / "Archives")
            self.assertEqual(plan["estimated_file_count"], 2)
            self.assertEqual(plan["estimated_total_bytes"], 12)
            self.assertEqual(plan["department"], "cmp")
            self.assertEqual(plan["task"], "Compositing")
            self.assertEqual(
                Path(plan["version_root"]),
                root / "Archives" / "Compositing",
            )
            self.assertEqual(plan["proposed_version"], "v0001")

            result = service.execute_package(plan)

            self.assertEqual(result["version"], "v0001")
            self.assertEqual(
                Path(result["version_path"]),
                root
                / "Archives"
                / "Compositing"
                / "v0001",
            )
            self.assertEqual(script.read_bytes(), original)
            packaged = Path(result["packaged_nk"]).read_text(encoding="utf-8")
            self.assertIn(
                r'project_directory "\[python \{nuke.script_directory()\}]"',
                packaged,
            )
            self.assertTrue(packaged.startswith("#! Nuke13.2 -nx\n"))
            self.assertIn(
                "file ../sequences/beauty/beauty.%04d.exr",
                packaged,
            )
            self.assertIn("file %s" % _nuke_path(write_path), packaged)
            self.assertIn(_nuke_path(metadata_path), packaged)
            copied = (
                root
                / "Archives"
                / "Compositing"
                / "v0001"
                / "sequences"
                / "beauty"
            )
            self.assertTrue((copied / "beauty.1001.exr").is_file())
            self.assertTrue((copied / "sidecar.txt").is_file())
            manifest = json.loads(
                Path(result["manifest_path"]).read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["status"], "Complete")
            self.assertEqual(manifest["application"], "nuke")
            self.assertEqual(manifest["archive_version"], "v0001")
            self.assertEqual(manifest["department"], "cmp")
            self.assertEqual(manifest["task"], "Compositing")
            self.assertEqual(manifest["task_version"], "v0001")
            self.assertEqual(manifest["version_scope"], "task")
            self.assertEqual(manifest["copy_jobs"][0]["result"], "copied")
            self.assertEqual(manifest["copy_jobs"][0]["file_count"], 2)
            self.assertEqual(manifest["copy_jobs"][0]["total_bytes"], 12)
            self.assertEqual(
                manifest["summary"],
                {
                    "read_count": 1,
                    "copy_job_count": 1,
                    "file_count": 2,
                    "total_bytes": 12,
                },
            )
            self.assertEqual(
                service.scan_archive_versions(root / "Archives")[0][
                    "total_bytes"
                ],
                12,
            )

    def test_quotes_braces_environment_and_frame_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            quoted = root / "quoted path"
            braced = root / "braced path"
            environment = root / "environment"
            quoted.mkdir()
            braced.mkdir()
            environment.mkdir()
            (quoted / "quoted.1.exr").write_bytes(b"frame")
            (braced / "braced.1001.exr").write_bytes(b"frame")
            (environment / "environment.0001.exr").write_bytes(b"frame")
            script = root / "scene.nk"
            script.write_text(
                "".join(
                    [
                        "#! Nuke13.2 -nx\n",
                        "version 13.2 v1\n",
                        "Root {\n",
                        " inputs 0\n",
                        "}\n",
                        "Read {\n",
                        ' file "%s"\n'
                        % _nuke_path(quoted / "quoted.%d.exr"),
                        " name QuotedRead\n",
                        "}\n",
                        "Read {\n",
                        " file {%s}\n"
                        % _nuke_path(braced / "braced.####.exr"),
                        " name BracedRead\n",
                        "}\n",
                        "Read {\n",
                        " file $NUKE_ARCHIVE_TEST_ROOT/environment.%04d.exr\n",
                        " name EnvironmentRead\n",
                        "}\n",
                    ]
                ),
                encoding="utf-8",
            )

            with mock.patch.dict(
                os.environ,
                {"NUKE_ARCHIVE_TEST_ROOT": str(environment)},
            ):
                plan = service.build_package_plan(
                    script, root / "Archives"
                )

            self.assertEqual(len(plan["reads"]), 3)
            self.assertEqual(
                [job["material_folder"] for job in plan["copy_jobs"]],
                ["quoted", "braced", "environment"],
            )

    def test_existing_project_directory_is_replaced_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            (source / "plate.1001.exr").write_bytes(b"frame")
            script = root / "scene.nk"
            _write_script(script, [source / "plate.%04d.exr"])
            original = script.read_text(encoding="utf-8")
            script.write_text(
                original.replace(
                    " inputs 0\n",
                    " inputs 0\n project_directory old/location\n",
                    1,
                ),
                encoding="utf-8",
            )

            result = service.execute_package(
                service.build_package_plan(script, root / "Archives")
            )
            packaged = Path(result["packaged_nk"]).read_text(encoding="utf-8")

            self.assertEqual(packaged.count(" project_directory "), 1)
            self.assertIn(
                r'project_directory "\[python \{nuke.script_directory()\}]"',
                packaged,
            )

    def test_single_file_does_not_copy_sibling_directory_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "render"
            nested = source / "v99"
            nested.mkdir(parents=True)
            movie = source / "review.mov"
            movie.write_bytes(b"movie")
            (nested / "large.1001.exr").write_bytes(b"frame")
            script = root / "scene.nk"
            _write_script(script, [movie])

            result = service.execute_package(
                service.build_package_plan(script, root / "Archives")
            )

            material = (
                Path(result["version_path"]) / "sequences" / "review"
            )
            self.assertTrue((material / "review.mov").is_file())
            self.assertFalse((material / "v99").exists())

    def test_relative_input_path_resolves_from_source_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_dir = root / "nk"
            source = root / "footage"
            script_dir.mkdir()
            source.mkdir()
            (source / "plate.1001.exr").write_bytes(b"frame")
            script = script_dir / "scene.nk"
            _write_script(script, ["../footage/plate.%04d.exr"])

            plan = service.build_package_plan(script, root / "Archives")

            self.assertEqual(
                plan["copy_jobs"][0]["source"],
                str(source),
            )

    def test_missing_and_expression_paths_fail_without_creating_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_root = root / "Archives"
            missing_script = root / "missing.nk"
            _write_script(missing_script, [root / "none" / "x.%04d.exr"])
            with self.assertRaises(service.PreflightError):
                service.build_package_plan(missing_script, archive_root)
            self.assertFalse(archive_root.exists())

            expression_script = root / "expression.nk"
            _write_script(
                expression_script,
                ["[file dirname [value root.name]]/plate.%04d.exr"],
            )
            with self.assertRaisesRegex(
                service.PreflightError, "expressions"
            ):
                service.build_package_plan(expression_script, archive_root)
            self.assertFalse(archive_root.exists())

            environment_script = root / "environment.nk"
            _write_script(
                environment_script,
                ["$NUKE_ARCHIVE_MISSING/plate.%04d.exr"],
            )
            with mock.patch.dict(
                os.environ,
                {"NUKE_ARCHIVE_MISSING": ""},
                clear=False,
            ):
                del os.environ["NUKE_ARCHIVE_MISSING"]
                with self.assertRaisesRegex(
                    service.PreflightError, "undefined environment"
                ):
                    service.build_package_plan(
                        environment_script, archive_root
                    )
            self.assertFalse(archive_root.exists())

    @unittest.skipUnless(os.name == "nt", "UNC semantics require Windows")
    def test_unc_path_is_recognized_as_absolute(self):
        resolved = service._resolve_source_path(
            r"\\server\share\plates\plate.%04d.exr",
            r"C:\shot\Scenefiles\cmp\scene.nk",
        )
        self.assertEqual(
            resolved,
            r"\\server\share\plates\plate.%04d.exr",
        )

    def test_failure_and_cancellation_remove_reserved_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            (source / "plate.1001.exr").write_bytes(b"frame")
            script = root / "scene.nk"
            _write_script(script, [source / "plate.%04d.exr"])
            archive_root = root / "Archives"
            plan = service.build_package_plan(script, archive_root)

            with mock.patch.object(
                service, "_copy_directory", side_effect=OSError("copy failed")
            ):
                with self.assertRaises(service.PackageExecutionError):
                    service.execute_package(plan)
            self.assertFalse((archive_root / "v0001").exists())

            with self.assertRaises(service.PackageCancelled):
                service.execute_package(plan, is_cancelled=lambda: True)
            self.assertFalse((archive_root / "v0001").exists())

    def test_insufficient_space_fails_before_reserving_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            (source / "plate.1001.exr").write_bytes(b"frame")
            script = root / "scene.nk"
            _write_script(script, [source / "plate.%04d.exr"])
            archive_root = root / "Archives"
            plan = service.build_package_plan(script, archive_root)

            with mock.patch.object(
                service, "_get_available_bytes", return_value=0
            ):
                with self.assertRaisesRegex(
                    service.PackageExecutionError, "Not enough free space"
                ):
                    service.execute_package(plan)

            self.assertFalse(archive_root.exists())

    def test_delete_archive_version_is_scoped_and_refuses_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_root = root / "Archives"
            version_path = archive_root / "v0001"
            version_path.mkdir(parents=True)
            (version_path / "manifest.json").write_text(
                "{}", encoding="utf-8"
            )
            (version_path / ".incomplete").write_text(
                "packaging", encoding="utf-8"
            )

            with self.assertRaisesRegex(
                service.ArchiveError, "incomplete"
            ):
                service.delete_archive_version(version_path, archive_root)
            self.assertTrue(version_path.is_dir())

            outside = root / "other" / "v0002"
            outside.mkdir(parents=True)
            with self.assertRaisesRegex(
                service.ArchiveError, "outside"
            ):
                service.delete_archive_version(outside, archive_root)
            self.assertTrue(outside.is_dir())

            non_version = archive_root / "latest"
            non_version.mkdir()
            with self.assertRaisesRegex(
                service.ArchiveError, "not an Archive version"
            ):
                service.delete_archive_version(non_version, archive_root)
            self.assertTrue(non_version.is_dir())

            (version_path / ".incomplete").unlink()
            result = service.delete_archive_version(
                version_path, archive_root
            )
            self.assertEqual(result["version"], "v0001")
            self.assertFalse(version_path.exists())

    def test_scan_reports_archive_health_states(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            (source / "plate.1001.exr").write_bytes(b"frame")
            script = root / "scene.nk"
            _write_script(script, [source / "plate.%04d.exr"])
            archive_root = root / "Archives"
            result = service.execute_package(
                service.build_package_plan(script, archive_root)
            )
            version_path = Path(result["version_path"])

            self.assertEqual(
                service.scan_archive_versions(archive_root)[0]["status"],
                "Complete",
            )

            script.write_text(
                script.read_text(encoding="utf-8") + "# changed\n",
                encoding="utf-8",
            )
            self.assertEqual(
                service.scan_archive_versions(archive_root)[0]["status"],
                "Source Changed",
            )

            Path(result["packaged_nk"]).unlink()
            self.assertEqual(
                service.scan_archive_versions(archive_root)[0]["status"],
                "Missing Files",
            )

            (version_path / ".incomplete").write_text(
                "interrupted", encoding="utf-8"
            )
            self.assertEqual(
                service.scan_archive_versions(archive_root)[0]["status"],
                "Incomplete",
            )

            (version_path / ".incomplete").unlink()
            (version_path / "manifest.json").write_text(
                "{invalid", encoding="utf-8"
            )
            self.assertEqual(
                service.scan_archive_versions(archive_root)[0]["status"],
                "Invalid Manifest",
            )

            (version_path / "manifest.json").write_text(
                json.dumps({"copy_jobs": "invalid"}),
                encoding="utf-8",
            )
            self.assertEqual(
                service.scan_archive_versions(archive_root)[0]["status"],
                "Invalid Manifest",
            )

    def test_versions_increment_per_archive_root_and_scan_descending(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            (source / "plate.1001.exr").write_bytes(b"frame")
            script = root / "scene.nk"
            _write_script(script, [source / "plate.%04d.exr"])
            archive_root = root / "Archives"

            first = service.execute_package(
                service.build_package_plan(script, archive_root)
            )
            second = service.execute_package(
                service.build_package_plan(script, archive_root)
            )
            (Path(second["version_path"]) / ".incomplete").write_text(
                "interrupted", encoding="utf-8"
            )
            versions = service.scan_archive_versions(archive_root)

            self.assertEqual(first["version"], "v0001")
            self.assertEqual(second["version"], "v0002")
            self.assertEqual(
                [item["version"] for item in versions],
                ["v0002", "v0001"],
            )
            self.assertEqual(versions[0]["status"], "Incomplete")
            self.assertEqual(versions[1]["status"], "Complete")


if __name__ == "__main__":
    unittest.main()
