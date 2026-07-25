"""Small HOM integration smoke test for Houdini 20.5, 21 and 22.

Run this file with the target Houdini build's hython executable.
"""

from __future__ import print_function

import json
import os
import shutil
import sys
import tempfile

import hou


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "Scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from change_prism.houdini_archive import houdini_worker


def _write(path, value):
    with open(path, "wb") as handle:
        handle.write(value)


def _scene_file_node(parent, name, path):
    node = parent.createNode("file", name)
    node.parm("file").set(path.replace("\\", "/"))
    return node


def main():
    temporary_root = tempfile.mkdtemp(prefix="houdini_archive_smoke_")
    try:
        source = os.path.join(temporary_root, "source")
        os.makedirs(source)
        assets = {
            "cache_named.abc": b"abc",
            "model.fbx": b"fbx",
            "smoke.1001.vdb": b"vdb1",
            "smoke.1002.vdb": b"vdb2",
            "texture.1001.exr": b"exr1",
            "texture.1002.exr": b"exr2",
            "percent.1001.vdb": b"percent1",
            "percent.1002.vdb": b"percent2",
            "tile.1001.exr": b"tile1",
            "tile.1002.exr": b"tile2",
            "hash.1001.png": b"hash1",
            "hash.1002.png": b"hash2",
            "model.obj": b"obj",
            "grade.cube": b"lut",
            "sound.wav": b"audio",
            "stage.usda": b"usd",
            "dynamic_a.exr": b"dynamic-a",
            "dynamic_b.exr": b"dynamic-b",
            "skip.1001.bgeo.sc": b"bgeo",
        }
        for filename, payload in assets.items():
            _write(os.path.join(source, filename), payload)

        hou.hipFile.clear(suppress_save_prompt=True)
        hou.setFps(25)
        hou.playbar.setFrameRange(1001, 1002)
        hou.playbar.setPlaybackRange(1001, 1002)
        geometry = hou.node("/obj").createNode("geo", "archive_smoke")
        for child in geometry.children():
            child.destroy()
        _scene_file_node(
            geometry,
            "abc_input",
            os.path.join(source, "cache_named.abc"),
        )
        _scene_file_node(
            geometry,
            "fbx_input",
            os.path.join(source, "model.fbx"),
        )
        _scene_file_node(
            geometry,
            "vdb_input",
            os.path.join(source, "smoke.$F4.vdb"),
        )
        _scene_file_node(
            geometry,
            "texture_input",
            os.path.join(source, "texture.$F4.exr"),
        )
        _scene_file_node(
            geometry,
            "percent_input",
            os.path.join(source, "percent.%04d.vdb"),
        )
        _scene_file_node(
            geometry,
            "udim_input",
            os.path.join(source, "tile.<UDIM>.exr"),
        )
        _scene_file_node(
            geometry,
            "hash_input",
            os.path.join(source, "hash.####.png"),
        )
        _scene_file_node(
            geometry,
            "obj_input",
            os.path.join(source, "model.obj"),
        )
        _scene_file_node(
            geometry,
            "lut_input",
            os.path.join(source, "grade.cube"),
        )
        _scene_file_node(
            geometry,
            "audio_input",
            os.path.join(source, "sound.wav"),
        )
        _scene_file_node(
            geometry,
            "usd_input",
            os.path.join(source, "stage.usda"),
        )
        _scene_file_node(
            geometry,
            "bgeo_input",
            os.path.join(source, "skip.$F4.bgeo.sc"),
        )
        _scene_file_node(
            geometry,
            "missing_nas_input",
            "/mnt/nas/archive_smoke/not_available/missing.abc",
        )
        source_hip = os.path.join(temporary_root, "source_scene.hip")
        hou.hipFile.save(file_name=source_hip)

        dynamic = _scene_file_node(
            geometry,
            "dynamic_input",
            os.path.join(source, "dynamic_a.exr"),
        )
        dynamic_expression = "%r if hou.frame() < 1002 else %r" % (
            os.path.join(source, "dynamic_a.exr").replace("\\", "/"),
            os.path.join(source, "dynamic_b.exr").replace("\\", "/"),
        )
        dynamic.parm("file").setExpression(
            dynamic_expression, hou.exprLanguage.Python
        )
        dynamic_reference = houdini_worker._inspect_reference(
            dynamic.parm("file"),
            dynamic.parm("file").evalAtFrame(1001),
            source_hip,
            1001,
            [1001, 1002],
        )
        assert dynamic_reference["status"] == "Blocked"
        assert "multiple source patterns" in dynamic_reference["error"]
        dynamic.destroy()

        locked = _scene_file_node(
            geometry,
            "locked_input",
            os.path.join(source, "dynamic_a.exr"),
        )
        locked.parm("file").lock(True)
        locked_reference = houdini_worker._inspect_reference(
            locked.parm("file"),
            locked.parm("file").evalAtFrame(1001),
            source_hip,
            1001,
            [1001, 1002],
        )
        assert locked_reference["status"] == "Blocked"
        assert "locked" in locked_reference["error"]
        locked.destroy()

        file_cache = geometry.createNode("filecache", "filecache_input")
        file_cache.parm("file").set(
            os.path.join(source, "cache_named.abc").replace("\\", "/")
        )
        cache_reference = houdini_worker._inspect_reference(
            file_cache.parm("file"),
            file_cache.parm("file").evalAtFrame(1001),
            source_hip,
            1001,
            [1001, 1002],
        )
        assert cache_reference["classification"] == "Skipped Cache"
        file_cache.destroy()

        output = hou.node("/out").createNode(
            "geometry", "archive_output"
        )
        output_path = "$HIP/render/output.$F4.bgeo.sc"
        output.parm("sopoutput").set(output_path)
        output_reference = houdini_worker._inspect_reference(
            output.parm("sopoutput"),
            output.parm("sopoutput").evalAtFrame(1001),
            source_hip,
            1001,
            [1001, 1002],
        )
        assert output_reference["classification"] == "Output"
        hou.hipFile.save(file_name=source_hip)

        inspection = houdini_worker.inspect_scene(source_hip)
        package_inputs = [
            item
            for item in inspection["references"]
            if item["classification"] == "Package Input"
        ]
        skipped_cache = [
            item
            for item in inspection["references"]
            if item["classification"] == "Skipped Cache"
        ]
        skipped_missing = [
            item
            for item in inspection["references"]
            if item["classification"] == "Skipped Missing"
        ]
        categories = set(item["category"] for item in package_inputs)
        assert "alembic" in categories
        assert "fbx" in categories
        assert "volumes" in categories
        assert "textures" in categories
        assert "geometry" in categories
        assert "lut" in categories
        assert "audio" in categories
        assert any(item["extension"] == ".bgeo.sc" for item in skipped_cache)
        assert len(skipped_missing) == 1
        assert skipped_missing[0]["status"] == "Missing (Skipped)"
        assert any(
            item["extension"] == ".usda"
            and item["classification"] == "Skipped Unsupported"
            for item in inspection["references"]
        )
        assert not inspection["errors"], inspection["errors"]

        version_root = os.path.join(temporary_root, "Archives", "v0001")
        os.makedirs(version_root)
        packaged_hip = os.path.join(
            version_root, "source_scene_archive_v0001.hip"
        )
        shutil.copy2(source_hip, packaged_hip)
        for index, dependency in enumerate(package_inputs):
            material = "input_%d" % index
            destination = os.path.join(
                version_root,
                "dependencies",
                dependency["category"],
                material,
            )
            os.makedirs(destination)
            for source_file in dependency["source_files"]:
                shutil.copy2(
                    source_file,
                    os.path.join(
                        destination, os.path.basename(source_file)
                    ),
                )
            dependency["packaged_path"] = (
                "$HIP/dependencies/%s/%s/%s"
                % (
                    dependency["category"],
                    material,
                    os.path.basename(dependency["resolved_pattern"]),
                )
            )

        rewrite = houdini_worker.rewrite_scene(
            packaged_hip,
            {
                "dependencies": inspection["references"],
                "reserved_version_path": version_root,
                "frame_range": inspection["frame_range"],
            },
        )
        assert rewrite["changed_count"] == len(package_inputs)
        assert not rewrite["errors"], rewrite["errors"]
        assert all(item["valid"] for item in rewrite["validation"])
        bgeo_parm = hou.parm("/obj/archive_smoke/bgeo_input/file")
        assert bgeo_parm.unexpandedString().replace("\\", "/").endswith(
            "/source/skip.$F4.bgeo.sc"
        )
        assert (
            hou.parm("/out/archive_output/sopoutput").unexpandedString()
            == output_path
        )

        single_version_root = os.path.join(
            temporary_root, "Archives", "v0002"
        )
        os.makedirs(single_version_root)
        single_packaged_hip = os.path.join(
            single_version_root, "source_scene_archive_v0002.hip"
        )
        single_manifest = os.path.join(
            single_version_root, "manifest.json"
        )
        source_stat = os.stat(source_hip)
        prepared = houdini_worker.prepare_archive(
            source_hip,
            {
                "version": "v0002",
                "version_scope": "task",
                "version_path": single_version_root,
                "packaged_hip": single_packaged_hip,
                "manifest_path": single_manifest,
                "source_extension": ".hip",
                "source_hip_stat": {
                    "size": source_stat.st_size,
                    "mtime_ns": getattr(
                        source_stat,
                        "st_mtime_ns",
                        int(source_stat.st_mtime * 1000000000),
                    ),
                },
                "department": "fx",
                "task": "Effects",
                "created_by": "smoke",
                "created_at": "2026-01-01T00:00:00+00:00",
                "hython_version": hou.applicationVersionString(),
                "version_warning": "",
            },
        )
        assert not prepared["errors"], prepared["errors"]
        assert os.path.isfile(single_packaged_hip)
        assert os.path.isfile(single_manifest)
        assert prepared["changed_count"] == len(package_inputs)
        with open(single_manifest, "r", encoding="utf-8") as handle:
            prepared_manifest = json.load(handle)
        assert prepared_manifest["status"] == "Incomplete"
        assert all(
            item["status"] == "Pending Copy"
            for item in prepared_manifest["dependencies"]
            if item["classification"] == "Package Input"
        )

        print(
            json.dumps(
                {
                    "houdini": hou.applicationVersionString(),
                    "python": sys.version.split()[0],
                    "references": len(inspection["references"]),
                    "package_inputs": len(package_inputs),
                    "skipped_cache": len(skipped_cache),
                    "validation": len(rewrite["validation"]),
                    "single_worker_jobs": len(
                        prepared_manifest["copy_jobs"]
                    ),
                },
                sort_keys=True,
            )
        )
        return 0
    finally:
        hou.hipFile.clear(suppress_save_prompt=True)
        shutil.rmtree(temporary_root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
