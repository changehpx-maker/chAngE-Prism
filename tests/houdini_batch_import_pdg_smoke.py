"""Hython smoke test for the Batch Import PDG JSON hand-off."""

from __future__ import print_function

import json
import os
import shutil
import tempfile

import hou

from hp_hou.tools.smwh import shot_processo


def main():
    temporary_root = tempfile.mkdtemp(prefix="batch_import_pdg_smoke_")
    try:
        json_path = os.path.join(temporary_root, "shot_data.json")
        with open(json_path, "w", encoding="utf-8") as handle:
            json.dump({}, handle)

        hou.putenv("SHOT_BUILDER_PDG_JSON", json_path)
        resolved = shot_processo.resolve_shot_data_json_path()
        assert os.path.normcase(str(resolved)) == os.path.normcase(json_path)

        try:
            shot_processo.cook_file_work(object())
        except RuntimeError:
            pass
        else:
            raise AssertionError("Empty PDG data must fail instead of succeeding")

        hou.putenv(
            "SHOT_BUILDER_PDG_JSON",
            os.path.join(temporary_root, "missing.json"),
        )
        try:
            shot_processo.resolve_shot_data_json_path()
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("Missing PDG data must fail")

        print("Batch Import PDG Hython smoke test passed")
    finally:
        hou.putenv("SHOT_BUILDER_PDG_JSON", "")
        shutil.rmtree(temporary_root, ignore_errors=True)


if __name__ == "__main__":
    main()
