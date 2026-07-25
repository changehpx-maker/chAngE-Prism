"""Run with: Nuke13.2.exe --safe -t tests/nuke13_archive_smoke.py."""

from __future__ import print_function

import os
import shutil
import sys
import tempfile

import nuke


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "Scripts"))

from change_prism.nuke_archive.service import (
    build_package_plan,
    execute_package,
)


def main():
    temporary_root = tempfile.mkdtemp(prefix="nuke_archive_nuke13_")
    try:
        source_directory = os.path.join(temporary_root, "source")
        os.makedirs(source_directory)
        for frame in (1001, 1002):
            path = os.path.join(
                source_directory, "plate.%04d.exr" % frame
            )
            with open(path, "wb") as handle:
                handle.write(b"test")

        source_nk = os.path.join(temporary_root, "scene.nk")
        source_pattern = os.path.join(
            source_directory, "plate.%04d.exr"
        ).replace("\\", "/")
        with open(source_nk, "w", encoding="utf-8") as handle:
            handle.write(
                "#! Nuke13.2 -nx\n"
                "version 13.2 v1\n"
                "Root {\n"
                " inputs 0\n"
                " first_frame 1001\n"
                " last_frame 1002\n"
                "}\n"
                "Read {\n"
                " inputs 0\n"
                " file %s\n"
                " first 1001\n"
                " last 1002\n"
                " name Read1\n"
                "}\n" % source_pattern
            )

        result = execute_package(
            build_package_plan(
                source_nk, os.path.join(temporary_root, "Archives")
            )
        )
        nuke.scriptOpen(result["packaged_nk"])
        nuke.frame(1001)

        read_node = nuke.toNode("Read1")
        if read_node is None:
            raise AssertionError("Read1 was not loaded by Nuke 13.")

        project_directory = nuke.root()["project_directory"].evaluate()
        expected_directory = os.path.dirname(result["packaged_nk"])
        if os.path.normcase(os.path.normpath(project_directory)) != os.path.normcase(
            os.path.normpath(expected_directory)
        ):
            raise AssertionError(
                "project_directory mismatch: %s != %s"
                % (project_directory, expected_directory)
            )

        resolved_frame = read_node["file"].evaluate()
        if not os.path.isfile(resolved_frame):
            raise AssertionError(
                "Nuke 13 did not resolve the archived Read: %s"
                % resolved_frame
            )

        nuke.scriptSave()
        nuke.scriptClear(ignoreUnsavedChanges=True)
        nuke.scriptOpen(result["packaged_nk"])
        if nuke.toNode("Read1") is None:
            raise AssertionError("Saved Archive did not reopen in Nuke 13.")

        print("NUKE13_ARCHIVE_SMOKE_OK")
        print(result["packaged_nk"])
    finally:
        try:
            nuke.scriptClear(ignoreUnsavedChanges=True)
        except Exception:
            pass
        shutil.rmtree(temporary_root, ignore_errors=True)


if __name__ == "__main__":
    main()
