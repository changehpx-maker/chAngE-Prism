"""HOM smoke test for Asset Library environment-light node creation.

Run this file with a Houdini 20.5+ hython executable. The test creates nodes
only in the temporary unsaved Hython session and removes them before exit.
"""

from __future__ import print_function

import json
import os
import sys
import tempfile
from pathlib import Path

import hou


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))

from change_prism.houdini_asset_bridge import (  # noqa: E402
    HoudiniAssetBridge,
    LOP_TEXTURE_PARM,
)


def main():
    handle, asset_path = tempfile.mkstemp(suffix=".exr")
    os.close(handle)
    asset_path = asset_path.replace("\\", "/")
    created_nodes = []
    try:
        obj = hou.node("/obj")
        stage = hou.node("/stage")
        with hou.undos.group("Asset Library HOM Smoke"):
            object_light = HoudiniAssetBridge._create_object_light(
                obj,
                "__change_prism_hdri_smoke",
                asset_path,
            )
            created_nodes.append(object_light)

            upstream = stage.createNode(
                "null",
                "__change_prism_stage_smoke",
            )
            created_nodes.append(upstream)
            upstream.setDisplayFlag(True)
            dome_light = HoudiniAssetBridge._create_lop_light(
                stage,
                "__change_prism_hdri_smoke",
                asset_path,
            )
            created_nodes.append(dome_light)

        assert object_light.type().name() == "envlight"
        assert object_light.parm("env_map").unexpandedString() == asset_path
        assert dome_light.type().name() == "domelight::3.0"
        assert dome_light.parm(
            LOP_TEXTURE_PARM
        ).unexpandedString() == asset_path
        assert dome_light.input(0) == upstream
        assert stage.displayNode() == dome_light

        print(
            json.dumps(
                {
                    "houdini": hou.applicationVersionString(),
                    "object_type": object_light.type().name(),
                    "object_parameter": "env_map",
                    "lop_type": dome_light.type().name(),
                    "lop_parameter": LOP_TEXTURE_PARM,
                    "lop_connected": True,
                },
                sort_keys=True,
            )
        )
    finally:
        for node in reversed(created_nodes):
            try:
                node.destroy()
            except hou.Error:
                pass
        try:
            os.remove(asset_path)
        except OSError:
            pass


if __name__ == "__main__":
    main()
