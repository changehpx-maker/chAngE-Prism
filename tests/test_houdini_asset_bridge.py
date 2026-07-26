import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))

from change_prism.houdini_asset_bridge import (  # noqa: E402
    HoudiniAssetBridge,
    LOP_KIND,
    LOP_TEXTURE_PARM,
    OBJECT_KIND,
)


class _AppPlugin:
    pluginName = "Houdini"


class _Core:
    def __init__(self, plugin_name="Houdini"):
        self.appPlugin = _AppPlugin()
        self.appPlugin.pluginName = plugin_name


class _Category:
    def __init__(self, name):
        self.name = name


class _NodeType:
    def __init__(self, category):
        self._category = category

    def category(self):
        return self._category


class _Parameter:
    def __init__(self):
        self.value = None

    def set(self, value):
        self.value = value


class _Node:
    def __init__(
        self,
        hou,
        path,
        category,
        child_category=None,
        parent=None,
        editable=True,
        type_name="node",
    ):
        self.hou = hou
        self._path = path
        self._category = category
        self._child_category = child_category
        self._parent = parent
        self._editable = editable
        self.type_name = type_name
        self.children = []
        self.parameters = {}
        self.inputs = {}
        self._display_node = None
        self.display_flag = False
        self.current = False
        self.destroyed = False
        self.missing_light_parameter = False
        if parent is not None:
            parent.children.append(self)
        hou.nodes[path] = self

    def path(self):
        return self._path

    def type(self):
        return _NodeType(self._category)

    def childTypeCategory(self):
        return self._child_category

    def parent(self):
        return self._parent

    def isEditable(self):
        return self._editable

    def allSubChildren(self):
        result = []
        for child in self.children:
            result.append(child)
            result.extend(child.allSubChildren())
        return tuple(result)

    def displayNode(self):
        return self._display_node

    def createNode(self, type_name, node_name, force_valid_node_name=False):
        del force_valid_node_name
        candidate = node_name
        suffix = 1
        while ("%s/%s" % (self._path, candidate)) in self.hou.nodes:
            candidate = "%s%d" % (node_name, suffix)
            suffix += 1
        category = (
            self.hou.object_category
            if type_name == "envlight"
            else self.hou.lop_category
        )
        node = _Node(
            self.hou,
            "%s/%s" % (self._path, candidate),
            category,
            parent=self,
            type_name=type_name,
        )
        if not self.missing_light_parameter:
            parameter_name = (
                "env_map"
                if type_name == "envlight"
                else LOP_TEXTURE_PARM
            )
            node.parameters[parameter_name] = _Parameter()
        return node

    def parm(self, name):
        return self.parameters.get(name)

    def setInput(self, index, node):
        self.inputs[index] = node

    def setDisplayFlag(self, enabled):
        self.display_flag = bool(enabled)
        if enabled and self._parent is not None:
            self._parent._display_node = self

    def moveToGoodPosition(self):
        return None

    def setCurrent(self, enabled, clear_all_selected=False):
        del clear_all_selected
        self.current = bool(enabled)

    def destroy(self):
        self.destroyed = True
        self.hou.nodes.pop(self._path, None)
        if self._parent is not None and self in self._parent.children:
            self._parent.children.remove(self)


class _UndoGroup:
    def __init__(self, labels, label):
        self.labels = labels
        self.label = label

    def __enter__(self):
        self.labels.append(self.label)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        del exc_type, exc_value, traceback
        return False


class _Undos:
    def __init__(self):
        self.labels = []

    def group(self, label):
        return _UndoGroup(self.labels, label)


class _Ui:
    def __init__(self):
        self.messages = []
        self.network_editor = None

    def setStatusMessage(self, message):
        self.messages.append(message)

    def currentPaneTabs(self):
        if self.network_editor is None:
            return ()
        return (self.network_editor,)

    def paneTabOfType(self, pane_type):
        if (
            self.network_editor is not None
            and self.network_editor.type() == pane_type
        ):
            return self.network_editor
        return None


class _PaneTabType:
    NetworkEditor = object()


class _NetworkEditor:
    def __init__(self, hou, network):
        self.hou = hou
        self.network = network

    def type(self):
        return self.hou.paneTabType.NetworkEditor

    def pwd(self):
        return self.network


class _HipFile:
    def __init__(self):
        self.save_calls = 0

    def save(self):
        self.save_calls += 1


class _Hou:
    def __init__(self):
        self.object_category = _Category("Object")
        self.lop_category = _Category("Lop")
        self.sop_category = _Category("Sop")
        self.vop_category = _Category("Vop")
        self.root_category = _Category("Root")
        self.nodes = {}
        self.undos = _Undos()
        self.paneTabType = _PaneTabType()
        self.ui = _Ui()
        self.hipFile = _HipFile()
        self.ui_available = True

        self.root = _Node(
            self,
            "/",
            self.root_category,
            parent=None,
        )
        self.obj = _Node(
            self,
            "/obj",
            self.root_category,
            child_category=self.object_category,
            parent=self.root,
            type_name="obj",
        )
        self.stage = _Node(
            self,
            "/stage",
            self.root_category,
            child_category=self.lop_category,
            parent=self.root,
            type_name="stage",
        )
        self.lopnet = _Node(
            self,
            "/obj/lopnet",
            self.object_category,
            child_category=self.lop_category,
            parent=self.obj,
            type_name="lopnet",
        )
        self.locked_lopnet = _Node(
            self,
            "/obj/locked_lopnet",
            self.object_category,
            child_category=self.lop_category,
            parent=self.obj,
            editable=False,
            type_name="lopnet",
        )
        self.geo = _Node(
            self,
            "/obj/geo1",
            self.object_category,
            child_category=self.sop_category,
            parent=self.obj,
            type_name="geo",
        )
        self.box = _Node(
            self,
            "/obj/geo1/box1",
            self.sop_category,
            parent=self.geo,
            type_name="box",
        )
        self.mat = _Node(
            self,
            "/mat",
            self.root_category,
            child_category=self.vop_category,
            parent=self.root,
            type_name="mat",
        )
        self.pwd_node = self.obj

    def isUIAvailable(self):
        return self.ui_available

    def pwd(self):
        return self.pwd_node

    def node(self, path):
        return self.nodes.get(path)

    def objNodeTypeCategory(self):
        return self.object_category

    def lopNodeTypeCategory(self):
        return self.lop_category


class HoudiniAssetBridgeTests(unittest.TestCase):
    def _asset(self, directory, name="studio-small_4k.exr"):
        path = os.path.join(directory, name)
        Path(path).write_bytes(b"hdr")
        return path

    def test_availability_requires_houdini_gui_supported_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._asset(tmp)
            hou = _Hou()
            self.assertTrue(
                HoudiniAssetBridge(_Core(), hou).is_available(path)
            )
            self.assertFalse(
                HoudiniAssetBridge(_Core("Standalone"), hou).is_available(
                    path
                )
            )
            hou.ui_available = False
            self.assertFalse(
                HoudiniAssetBridge(_Core(), hou).is_available(path)
            )
            hou.ui_available = True
            png = self._asset(tmp, "preview.png")
            self.assertFalse(
                HoudiniAssetBridge(_Core(), hou).is_available(png)
            )
            self.assertFalse(
                HoudiniAssetBridge(_Core(), hou).is_available(
                    os.path.join(tmp, "missing.exr")
                )
            )

    def test_unavailable_hou_module_is_handled(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._asset(tmp)
            bridge = HoudiniAssetBridge(_Core())
            bridge._hou_load_attempted = True
            self.assertFalse(bridge.is_available(path))

    def test_current_context_uses_child_category_not_path_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._asset(tmp)
            hou = _Hou()
            bridge = HoudiniAssetBridge(_Core(), hou)

            hou.pwd_node = hou.obj
            target = bridge.resolve_current_target()
            self.assertEqual(target["kind"], OBJECT_KIND)
            self.assertEqual(target["network_path"], "/obj")
            self.assertEqual(
                bridge.describe_action(path)["label"],
                "Create Environment Light in /obj",
            )

            hou.pwd_node = hou.stage
            target = bridge.resolve_current_target()
            self.assertEqual(target["kind"], LOP_KIND)
            self.assertEqual(target["network_path"], "/stage")

            hou.pwd_node = hou.lopnet
            target = bridge.resolve_current_target()
            self.assertEqual(target["kind"], LOP_KIND)
            self.assertEqual(target["network_path"], "/obj/lopnet")
            self.assertEqual(
                bridge.describe_action(path)["label"],
                "Create Dome Light in /obj/lopnet",
            )

            hou.pwd_node = hou.box
            self.assertIsNone(bridge.resolve_current_target())
            self.assertEqual(
                bridge.describe_action(path)["label"],
                "Create Houdini Environment Light...",
            )

            hou.pwd_node = hou.mat
            self.assertIsNone(bridge.resolve_current_target())

    def test_visible_network_editor_takes_priority_over_global_pwd(self):
        hou = _Hou()
        bridge = HoudiniAssetBridge(_Core(), hou)
        hou.pwd_node = hou.obj

        hou.ui.network_editor = _NetworkEditor(hou, hou.lopnet)
        target = bridge.resolve_current_target()
        self.assertEqual(target["kind"], LOP_KIND)
        self.assertEqual(target["network_path"], "/obj/lopnet")

        hou.ui.network_editor = _NetworkEditor(hou, hou.geo)
        self.assertIsNone(bridge.resolve_current_target())

    def test_object_creation_sets_path_uses_unique_name_and_one_undo(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._asset(tmp)
            hou = _Hou()
            bridge = HoudiniAssetBridge(_Core(), hou)

            first = bridge.create_environment_light(path, "/obj")
            second = bridge.create_environment_light(path, "/obj")

            self.assertTrue(first["success"])
            self.assertTrue(second["success"])
            self.assertEqual(first["node_path"], "/obj/hdri_studio_small_4k")
            self.assertEqual(
                second["node_path"],
                "/obj/hdri_studio_small_4k1",
            )
            node = hou.node(first["node_path"])
            self.assertEqual(node.type_name, "envlight")
            self.assertEqual(
                node.parm("env_map").value,
                os.path.abspath(path).replace("\\", "/"),
            )
            self.assertTrue(node.current)
            self.assertEqual(
                hou.undos.labels,
                [
                    "Create HDRI Environment Light",
                    "Create HDRI Environment Light",
                ],
            )
            self.assertEqual(hou.hipFile.save_calls, 0)
            self.assertIn(first["node_path"], hou.ui.messages[0])

    def test_lop_creation_appends_after_display_node(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._asset(tmp, "sunset.hdr")
            hou = _Hou()
            upstream = _Node(
                hou,
                "/obj/lopnet/current_stage",
                hou.lop_category,
                parent=hou.lopnet,
                type_name="null",
            )
            hou.lopnet._display_node = upstream
            bridge = HoudiniAssetBridge(_Core(), hou)

            result = bridge.create_environment_light(
                path,
                "/obj/lopnet",
            )

            self.assertTrue(result["success"])
            node = hou.node(result["node_path"])
            self.assertEqual(node.type_name, "domelight::3.0")
            self.assertIs(node.inputs[0], upstream)
            self.assertTrue(node.display_flag)
            self.assertIs(hou.lopnet.displayNode(), node)
            self.assertEqual(
                node.parm(LOP_TEXTURE_PARM).value,
                os.path.abspath(path).replace("\\", "/"),
            )

    def test_parameter_failure_removes_only_new_node(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._asset(tmp)
            hou = _Hou()
            hou.stage.missing_light_parameter = True
            existing_paths = set(hou.nodes)
            bridge = HoudiniAssetBridge(_Core(), hou)

            result = bridge.create_environment_light(path, "/stage")

            self.assertFalse(result["success"])
            self.assertIn("Texture parameter", result["message"])
            self.assertEqual(set(hou.nodes), existing_paths)
            self.assertEqual(hou.hipFile.save_calls, 0)


if __name__ == "__main__":
    unittest.main()
