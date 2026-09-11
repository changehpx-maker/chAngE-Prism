import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))

from change_prism import archive_core
from change_prism.houdini_archive import archive_planning, service


def _inspection(root):
    source = root / "source"
    references = [
        _reference(source / "cache_named.abc", "alembic", "/obj/abc/file"),
        _reference(source / "model.fbx", "fbx", "/obj/fbx/file"),
        _reference(
            source / "smoke.$F4.vdb",
            "volumes",
            "/obj/vdb/file",
            source_files=[
                source / "smoke.1001.vdb",
                source / "smoke.1002.vdb",
            ],
        ),
        _reference(source / "texture.exr", "textures", "/mat/img/file"),
        {
            "node_path": "/obj/cache/read_back",
            "node_type": "Sop/file",
            "parameter": "/obj/cache/read_back/file",
            "parameter_name": "file",
            "original_value": str(source / "skip.$F4.bgeo.sc"),
            "evaluated_path": str(source / "skip.1001.bgeo.sc"),
            "resolved_pattern": str(source / "skip.$F4.bgeo.sc"),
            "extension": ".bgeo.sc",
            "category": "",
            "classification": "Skipped Cache",
            "status": "Skipped",
            "reason": "File Cache and BGeo payloads are excluded",
            "source_files": [],
        },
        {
            "node_path": "/stage/sublayer1",
            "node_type": "Lop/sublayer",
            "parameter": "/stage/sublayer1/filepath1",
            "parameter_name": "filepath1",
            "original_value": "$HIP/stage.usda",
            "evaluated_path": str(root / "stage.usda"),
            "resolved_pattern": str(root / "stage.usda"),
            "extension": ".usda",
            "category": "",
            "classification": "Skipped Unsupported",
            "status": "Skipped",
            "reason": "USD and PDG dependencies are not packaged",
            "source_files": [],
        },
    ]
    return {
        "houdini_version": "21.0.631",
        "python_version": "3.11.0",
        "save_mode": "Binary",
        "fps": 25.0,
        "frame_range": [1001.0, 1100.0],
        "playback_range": [1001.0, 1100.0],
        "load_warning": "",
        "references": references,
        "external_hdas": [
            {
                "source": str(source / "custom.hda"),
                "node_types": ["Sop/studio::tool::1.0"],
                "status": "Ready",
                "activation": "manual",
            }
        ],
        "errors": [],
        "worker_log": "inspect log",
    }


def _reference(path, category, parm, source_files=None):
    path = Path(path)
    files = source_files or [path]
    return {
        "node_path": parm.rsplit("/", 1)[0],
        "node_type": "Sop/file",
        "parameter": parm,
        "parameter_name": parm.rsplit("/", 1)[-1],
        "original_value": str(path),
        "evaluated_path": str(files[0]),
        "resolved_pattern": str(path),
        "extension": path.suffix.lower(),
        "category": category,
        "classification": "Package Input",
        "status": "Ready",
        "reason": "Supported external input",
        "error": "",
        "locked": False,
        "has_keyframes": False,
        "has_expression": "$F" in str(path),
        "source_files": [str(item) for item in files],
    }


def _skipped_missing_reference():
    return {
        "node_path": "/obj/missing_abc",
        "node_type": "Sop/file",
        "parameter": "/obj/missing_abc/file",
        "parameter_name": "file",
        "original_value": "/mnt/nas/project/missing.abc",
        "evaluated_path": "/mnt/nas/project/missing.abc",
        "resolved_pattern": "/mnt/nas/project/missing.abc",
        "extension": ".abc",
        "category": "alembic",
        "classification": "Skipped Missing",
        "status": "Missing (Skipped)",
        "reason": (
            "Unavailable /mnt/nas input is excluded and keeps its "
            "original path"
        ),
        "error": (
            "File does not exist: /mnt/nas/project/missing.abc"
        ),
        "source_files": [],
    }


class HoudiniArchiveServiceTests(unittest.TestCase):
    def test_material_name_preserves_full_stem_for_compound_extensions(self):
        self.assertEqual(
            archive_planning._material_name("sim.bgeo.sc"),
            "sim",
        )
        self.assertEqual(
            archive_planning._material_name("cache.geo.gz"),
            "cache",
        )
        self.assertEqual(
            archive_planning._material_name("smoke.$F4.vdb"),
            "smoke",
        )

    def setUp(self):
        self.runner_patches = [
            mock.patch.object(
                service.runner,
                "read_hip_version",
                return_value="21.0.631",
            ),
            mock.patch.object(
                service.runner,
                "resolve_hython",
                return_value={
                    "path": "fake_hython.exe",
                    "version": "21.0.631",
                    "warning": "",
                },
            ),
        ]
        for patcher in self.runner_patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_build_plan_packages_supported_inputs_and_skips_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scene, inspection = self._make_sources(root)
            with mock.patch.object(
                service.runner, "run_worker", return_value=inspection
            ):
                plan = service.build_package_plan(
                    scene, root / "Archives"
                )

            self.assertEqual(plan["summary"]["package_input_count"], 4)
            self.assertEqual(plan["summary"]["skipped_cache_count"], 1)
            self.assertEqual(
                [job["category"] for job in plan["copy_jobs"]],
                ["alembic", "fbx", "volumes", "textures", "hda"],
            )
            self.assertEqual(plan["copy_jobs"][2]["file_count"], 2)
            json.dumps(plan)
            cache = [
                item
                for item in plan["dependencies"]
                if item["classification"] == "Skipped Cache"
            ][0]
            self.assertNotIn("packaged_path", cache)
            abc = plan["dependencies"][0]
            self.assertIn(
                "$HIP/dependencies/alembic/cache_named/",
                abc["packaged_path"],
            )
            self.assertEqual(plan["department"], "fx")
            self.assertEqual(plan["task"], "Effects")
            self.assertEqual(
                Path(plan["version_root"]),
                root / "Archives" / "Effects",
            )
            self.assertEqual(plan["proposed_version"], "v0001")

    def test_background_package_uses_one_worker_then_copies_from_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scene, inspection = self._make_sources(root)
            original = scene.read_bytes()

            def worker(_hython, command, source_hip, **kwargs):
                self.assertEqual(command, "prepare")
                request = kwargs["plan"]
                copy_plan = service.archive_planning.build_copy_plan(
                    inspection
                )
                Path(request["packaged_hip"]).write_bytes(b"archive hip")
                for job in copy_plan["copy_jobs"]:
                    job["destination"] = (
                        "dependencies/%s/%s"
                        % (job["category"], job["material_folder"])
                    )
                    job["result"] = "pending"
                manifest = {
                    "schema_version": 2,
                    "application": "houdini",
                    "status": "Incomplete",
                    "completion_status": "Complete with Exclusions",
                    "archive_version": request["version"],
                    "task_version": request["version"],
                    "version_scope": request["version_scope"],
                    "source_scene": str(source_hip),
                    "packaged_scene": Path(
                        request["packaged_hip"]
                    ).name,
                    "source_scene_stat": request["source_hip_stat"],
                    "source_extension": request["source_extension"],
                    "department": request["department"],
                    "task": request["task"],
                    "created_by": request["created_by"],
                    "created_at": request["created_at"],
                    "validation": [],
                    "summary": dict(copy_plan["summary"]),
                    "dependencies": (
                        service.archive_planning.manifest_dependencies(
                            copy_plan["dependencies"],
                            packaged_status="Pending Copy",
                        )
                    ),
                    "external_hdas": copy_plan["external_hdas"],
                    "copy_jobs": (
                        service.archive_planning.manifest_copy_jobs(
                            copy_plan["copy_jobs"]
                        )
                    ),
                }
                manifest["summary"].update(
                    {
                        "copied_dependency_count": 0,
                        "copy_job_count": len(copy_plan["copy_jobs"]),
                        "file_count": (
                            copy_plan["estimated_file_count"] + 1
                        ),
                        "total_bytes": (
                            copy_plan["estimated_dependency_bytes"] + 11
                        ),
                    }
                )
                Path(request["manifest_path"]).write_text(
                    json.dumps(manifest),
                    encoding="utf-8",
                )
                return {
                    "errors": [],
                    "dependencies": copy_plan["dependencies"],
                    "external_hdas": copy_plan["external_hdas"],
                    "copy_jobs": copy_plan["copy_jobs"],
                    "summary": copy_plan["summary"],
                    "estimated_dependency_bytes": copy_plan[
                        "estimated_dependency_bytes"
                    ],
                    "worker_log": "single worker",
                }

            with mock.patch.object(
                service.runner, "run_worker", side_effect=worker
            ) as run_worker:
                result = service.execute_background_package(
                    scene,
                    root / "Archives",
                    hython_executable="fake_hython.exe",
                )

            self.assertEqual(run_worker.call_count, 1)
            self.assertEqual(scene.read_bytes(), original)
            version = Path(result["version_path"])
            self.assertTrue(Path(result["packaged_hip"]).is_file())
            self.assertTrue(
                (
                    version
                    / "dependencies"
                    / "fbx"
                    / "model"
                    / "model.fbx"
                ).is_file()
            )
            manifest = json.loads(
                Path(result["manifest_path"]).read_text(encoding="utf-8")
            )
            self.assertEqual(
                manifest["status"], "Complete with Exclusions"
            )
            self.assertNotIn("completion_status", manifest)
            self.assertFalse((version / ".incomplete").exists())
            self.assertIn(
                "single worker",
                (version / "logs" / "hython.log").read_text(
                    encoding="utf-8"
                ),
            )

    def test_skipped_missing_nas_input_is_recorded_without_copying(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scene, inspection = self._make_sources(root)
            inspection["references"].append(_skipped_missing_reference())

            def worker(_hython, command, source_hip, **kwargs):
                if command == "inspect":
                    return dict(inspection)
                dependencies = kwargs["plan"]["dependencies"]
                skipped = [
                    item
                    for item in dependencies
                    if item["classification"] == "Skipped Missing"
                ]
                self.assertEqual(len(skipped), 1)
                self.assertNotIn("packaged_path", skipped[0])
                return {
                    "errors": [],
                    "load_warning": "",
                    "reopen_warning": "",
                    "validation": [],
                    "worker_log": "rewrite log",
                }

            with mock.patch.object(
                service.runner, "run_worker", side_effect=worker
            ):
                plan = service.build_package_plan(
                    scene, root / "Archives"
                )
                self.assertEqual(
                    plan["summary"]["skipped_missing_count"], 1
                )
                self.assertEqual(plan["summary"]["missing_count"], 1)
                self.assertEqual(len(plan["copy_jobs"]), 5)
                result = service.execute_package(plan)

            manifest = json.loads(
                Path(result["manifest_path"]).read_text(encoding="utf-8")
            )
            self.assertEqual(
                manifest["status"], "Complete with Exclusions"
            )
            self.assertEqual(
                manifest["summary"]["skipped_missing_count"], 1
            )
            self.assertEqual(manifest["summary"]["missing_count"], 1)
            skipped = [
                item
                for item in manifest["dependencies"]
                if item["classification"] == "Skipped Missing"
            ]
            self.assertEqual(skipped[0]["status"], "Missing (Skipped)")
            self.assertEqual(
                skipped[0]["original_value"],
                "/mnt/nas/project/missing.abc",
            )
            scanned = archive_core.scan_archive_versions(
                root / "Archives"
            )[0]
            self.assertEqual(scanned["skipped_missing_count"], 1)
            self.assertEqual(
                scanned["status"], "Complete with Exclusions"
            )

    def test_execute_copies_rewrites_manifest_and_preserves_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scene, inspection = self._make_sources(root)
            original = scene.read_bytes()

            def worker(_hython, command, source_hip, **_kwargs):
                if command == "inspect":
                    return dict(inspection)
                return {
                    "errors": [],
                    "load_warning": "",
                    "reopen_warning": "",
                    "validation": [
                        {
                            "parameter": "/obj/abc/file",
                            "valid": True,
                        }
                    ],
                    "worker_log": "rewrite log",
                }

            with mock.patch.object(
                service.runner, "run_worker", side_effect=worker
            ):
                plan = service.build_package_plan(
                    scene, root / "Archives"
                )
                result = service.execute_package(plan)

            self.assertEqual(scene.read_bytes(), original)
            self.assertEqual(result["version"], "v0001")
            version = Path(result["version_path"])
            self.assertEqual(
                version,
                root / "Archives" / "Effects" / "v0001",
            )
            self.assertTrue(Path(result["packaged_hip"]).is_file())
            self.assertEqual(Path(result["packaged_hip"]).parent, version)
            self.assertFalse((version / "hip").exists())
            self.assertTrue(
                (
                    version
                    / "dependencies"
                    / "fbx"
                    / "model"
                    / "model.fbx"
                ).is_file()
            )
            self.assertFalse(
                (version / "dependencies" / "geometry").exists()
            )
            manifest = json.loads(
                Path(result["manifest_path"]).read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["schema_version"], 2)
            self.assertEqual(manifest["application"], "houdini")
            self.assertEqual(manifest["department"], "fx")
            self.assertEqual(manifest["task"], "Effects")
            self.assertEqual(manifest["task_version"], "v0001")
            self.assertEqual(manifest["version_scope"], "task")
            self.assertEqual(
                manifest["packaged_scene"],
                Path(result["packaged_hip"]).name,
            )
            self.assertEqual(
                manifest["status"], "Complete with Exclusions"
            )
            self.assertEqual(
                manifest["external_hdas"][0]["activation"], "manual"
            )
            scanned = archive_core.scan_archive_versions(
                root / "Archives"
            )[0]
            self.assertEqual(scanned["application"], "houdini")
            self.assertEqual(
                scanned["status"], "Complete with Exclusions"
            )

    def test_rewrite_failure_removes_reserved_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scene, inspection = self._make_sources(root)

            def worker(_hython, command, source_hip, **_kwargs):
                if command == "inspect":
                    return dict(inspection)
                return {
                    "errors": ["rewrite failed"],
                    "worker_log": "",
                }

            with mock.patch.object(
                service.runner, "run_worker", side_effect=worker
            ):
                plan = service.build_package_plan(
                    scene, root / "Archives"
                )
                with self.assertRaises(service.PackageExecutionError):
                    service.execute_package(plan)

            self.assertFalse(
                (
                    root
                    / "Archives"
                    / "Effects"
                    / "v0001"
                ).exists()
            )

    def test_insufficient_space_fails_before_reserving_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scene, inspection = self._make_sources(root)
            with mock.patch.object(
                service.runner, "run_worker", return_value=inspection
            ):
                plan = service.build_package_plan(
                    scene, root / "Archives"
                )
                with mock.patch.object(
                    service.archive_core,
                    "get_available_bytes",
                    return_value=0,
                ):
                    with self.assertRaisesRegex(
                        service.PackageExecutionError,
                        "Not enough free space",
                    ):
                        service.execute_package(plan)
            self.assertFalse((root / "Archives").exists())

    def test_execute_rejects_source_changed_after_preflight(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scene, inspection = self._make_sources(root)
            with mock.patch.object(
                service.runner, "run_worker", return_value=inspection
            ):
                plan = service.build_package_plan(
                    scene, root / "Archives"
                )
                scene.write_bytes(scene.read_bytes() + b" changed")
                with self.assertRaisesRegex(
                    service.PackageExecutionError,
                    "changed after preflight",
                ):
                    service.execute_package(plan)
            self.assertFalse((root / "Archives").exists())

    def test_copy_jobs_reuse_same_source_and_suffix_name_collisions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scene, inspection = self._make_sources(root)
            first_dir = root / "first"
            second_dir = root / "second"
            first_dir.mkdir()
            second_dir.mkdir()
            first = first_dir / "shared.exr"
            second = second_dir / "shared.exr"
            first.write_bytes(b"first")
            second.write_bytes(b"second")
            inspection["references"] = [
                _reference(first, "textures", "/mat/a/file"),
                _reference(first, "textures", "/mat/b/file"),
                _reference(second, "textures", "/mat/c/file"),
            ]
            inspection["external_hdas"] = []
            with mock.patch.object(
                service.runner, "run_worker", return_value=inspection
            ):
                plan = service.build_package_plan(
                    scene, root / "Archives"
                )

            self.assertEqual(len(plan["copy_jobs"]), 2)
            self.assertEqual(
                [
                    job["material_folder"]
                    for job in plan["copy_jobs"]
                ],
                ["shared", "shared_2"],
            )
            self.assertEqual(
                plan["dependencies"][0]["copy_job_key"],
                plan["dependencies"][1]["copy_job_key"],
            )
            self.assertNotEqual(
                plan["dependencies"][0]["copy_job_key"],
                plan["dependencies"][2]["copy_job_key"],
            )

    def test_material_folders_do_not_collide_case_insensitively(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scene, inspection = self._make_sources(root)
            first_dir = root / "upper"
            second_dir = root / "lower"
            first_dir.mkdir()
            second_dir.mkdir()
            first = first_dir / "Model.exr"
            second = second_dir / "model.exr"
            first.write_bytes(b"upper")
            second.write_bytes(b"lower")
            inspection["references"] = [
                _reference(first, "textures", "/mat/a/file"),
                _reference(second, "textures", "/mat/b/file"),
            ]
            inspection["external_hdas"] = []
            with mock.patch.object(
                service.runner, "run_worker", return_value=inspection
            ):
                plan = service.build_package_plan(
                    scene, root / "Archives"
                )

            folders = [
                job["material_folder"] for job in plan["copy_jobs"]
            ]
            if os.path.normcase("Model") == os.path.normcase("model"):
                # Case-insensitive filesystem: the folders must be
                # distinct, otherwise one payload silently overwrites
                # the other. Each folder keeps its own source casing.
                self.assertEqual(folders, ["Model", "model_2"])
            else:
                self.assertEqual(folders, ["Model", "model"])
            self.assertNotEqual(
                os.path.normcase(folders[0]), os.path.normcase(folders[1])
            )

    def test_preserves_all_houdini_license_extensions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _scene, inspection = self._make_sources(root)
            for extension in (".hip", ".hiplc", ".hipnc"):
                scene = root / ("licensed" + extension)
                scene.write_bytes(
                    b"_HIP_SAVEVERSION = '21.0.631' scene"
                )
                with mock.patch.object(
                    service.runner,
                    "run_worker",
                    return_value=inspection,
                ):
                    plan = service.build_package_plan(
                        scene, root / "Archives"
                    )
                self.assertTrue(
                    plan["packaged_hip_name"].endswith(extension)
                )

    def test_cancellation_removes_reserved_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scene, inspection = self._make_sources(root)
            cancelled = [False]

            def worker(_hython, command, source_hip, **_kwargs):
                if command == "inspect":
                    return dict(inspection)
                return {"errors": [], "validation": []}

            def progress(completed, _total, _message):
                if completed:
                    cancelled[0] = True

            with mock.patch.object(
                service.runner, "run_worker", side_effect=worker
            ):
                plan = service.build_package_plan(
                    scene, root / "Archives"
                )
                with self.assertRaises(service.PackageCancelled):
                    service.execute_package(
                        plan,
                        progress_callback=progress,
                        is_cancelled=lambda: cancelled[0],
                    )
            self.assertFalse(
                (
                    root
                    / "Archives"
                    / "Effects"
                    / "v0001"
                ).exists()
            )

    def test_source_change_during_copy_removes_reserved_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scene, inspection = self._make_sources(root)
            changed = [False]

            def progress(completed, _total, _message):
                if completed and not changed[0]:
                    scene.write_bytes(scene.read_bytes() + b" changed")
                    changed[0] = True

            with mock.patch.object(
                service.runner, "run_worker", return_value=inspection
            ):
                plan = service.build_package_plan(
                    scene, root / "Archives"
                )
                with self.assertRaisesRegex(
                    service.PackageExecutionError,
                    "changed during packaging",
                ):
                    service.execute_package(
                        plan, progress_callback=progress
                    )
            self.assertFalse(
                (
                    root
                    / "Archives"
                    / "Effects"
                    / "v0001"
                ).exists()
            )

    @staticmethod
    def _make_sources(root):
        source = root / "source"
        source.mkdir()
        for name in (
            "cache_named.abc",
            "model.fbx",
            "smoke.1001.vdb",
            "smoke.1002.vdb",
            "texture.exr",
            "skip.1001.bgeo.sc",
            "custom.hda",
        ):
            (source / name).write_bytes(name.encode("ascii"))
        scene_directory = root / "Scenefiles" / "fx" / "Effects"
        scene_directory.mkdir(parents=True)
        scene = scene_directory / "scene.hip"
        scene.write_bytes(b"_HIP_SAVEVERSION = '21.0.631' scene")
        return scene, _inspection(root)


if __name__ == "__main__":
    unittest.main()
