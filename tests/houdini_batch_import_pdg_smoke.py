"""Hython smoke test for the Batch Import PDG JSON hand-off."""

from __future__ import print_function

import json
import os
import shutil
import tempfile

import hou

from hp_hou.tools.smwh import shot_processo


class _WorkItem:
    def __init__(self):
        self.attributes = {}

    def setStringAttrib(self, name, value):
        self.attributes[name] = value

    def setIntAttrib(self, name, value):
        self.attributes[name] = value

    def setFloatAttrib(self, name, value):
        self.attributes[name] = value


class _ItemHolder:
    def __init__(self):
        self.items = []

    def addWorkItem(self, index):
        assert index == len(self.items)
        item = _WorkItem()
        self.items.append(item)
        return item


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

        fbx_path = os.path.join(temporary_root, "camera.fbx")
        with open(fbx_path, "wb") as handle:
            handle.write(b"fbx")
        with open(json_path, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "EP01/SC03/shot027": {
                        "entity": {
                            "type": "shot",
                            "sequence": "EP01",
                            "shot": "SC03_shot027",
                        },
                        "shot_code": "SC03_shot027",
                        "project_code": "show",
                        "products_path": temporary_root,
                        "file_dict": [
                            {
                                "path": fbx_path,
                            }
                        ],
                        "xml": {
                            "attributes": {
                                "render_start_frame": 1001,
                                "sequence_frame": 100,
                                "average_translation": [1, 2, 3],
                            },
                            "cloth_solution": {
                                "xml_path": os.path.join(
                                    temporary_root, "cloth.xml"
                                ),
                            },
                            "hair_solution": {
                                "xml_path": os.path.join(
                                    temporary_root, "hair.xml"
                                ),
                            },
                        },
                    }
                },
                handle,
            )
        holder = _ItemHolder()
        shot_processo.cook_file_work(holder)
        assert len(holder.items) == 1
        attributes = holder.items[0].attributes
        assert attributes["file_path"] == fbx_path
        assert attributes["shot_code"] == "SC03_shot027"
        assert attributes["cam"] == "True"
        assert attributes["project_code"] == "show"
        assert attributes["products_path"] == temporary_root
        assert attributes["end_frame"] == 1102
        assert attributes["cloth_xml"] == os.path.join(
            temporary_root, "cloth.xml"
        )
        assert attributes["hair_xml"] == os.path.join(
            temporary_root, "hair.xml"
        )
        removed_attributes = {
            "avg_trans_x",
            "avg_trans_y",
            "avg_trans_z",
            "ext",
            "file_parent_name",
            "file_parent_parent",
            "media_path",
            "out_file_json_path",
            "presetScenes",
            "should_build_hip",
            "type",
        }
        assert removed_attributes.isdisjoint(attributes)
        assert "hair_elements" not in attributes
        assert "cloth_elements" not in attributes

        with open(json_path, "r", encoding="utf-8") as handle:
            without_solutions = json.load(handle)
        solution_xml = without_solutions["EP01/SC03/shot027"]["xml"]
        solution_xml.pop("cloth_solution")
        solution_xml.pop("hair_solution")
        with open(json_path, "w", encoding="utf-8") as handle:
            json.dump(without_solutions, handle)
        holder_without_solutions = _ItemHolder()
        shot_processo.cook_file_work(holder_without_solutions)
        attributes_without_solutions = (
            holder_without_solutions.items[0].attributes
        )
        assert "cloth_xml" not in attributes_without_solutions
        assert "hair_xml" not in attributes_without_solutions

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
