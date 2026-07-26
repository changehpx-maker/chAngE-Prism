from __future__ import unicode_literals

import os
import re


HDR_EXTENSIONS = (".exr", ".hdr")
OBJECT_KIND = "object"
LOP_KIND = "lop"
LOP_TEXTURE_PARM = "xn__inputstexturefile_r3ah"


class HoudiniAssetBridge(object):
    """Create Houdini environment lights from Asset Library paths."""

    def __init__(self, core, hou_module=None):
        self.core = core
        self._hou = hou_module
        self._hou_load_attempted = hou_module is not None

    def describe_action(self, asset_path):
        if not self.is_available(asset_path):
            return None
        target = self.resolve_current_target()
        if target is None:
            label = "Create Houdini Environment Light..."
        elif target["kind"] == OBJECT_KIND:
            label = "Create Environment Light in %s" % target["network_path"]
        else:
            label = "Create Dome Light in %s" % target["network_path"]
        return {
            "label": label,
            "target": target,
        }

    def is_available(self, asset_path):
        if not self._is_houdini_app():
            return False
        if not self._is_supported_file(asset_path):
            return False
        hou = self._load_hou()
        if hou is None:
            return False
        is_ui_available = getattr(hou, "isUIAvailable", None)
        if not callable(is_ui_available):
            return False
        try:
            return bool(is_ui_available())
        except Exception:
            return False

    def resolve_current_target(self):
        hou = self._load_hou()
        if hou is None:
            return None
        network_editor, network = self._current_network_editor()
        if network_editor is not None:
            return self._target_from_network(network)
        try:
            current_node = hou.pwd()
        except Exception:
            return None
        return self._target_from_node(current_node)

    def _current_network_editor(self):
        hou = self._load_hou()
        ui = getattr(hou, "ui", None)
        pane_tab_type = getattr(hou, "paneTabType", None)
        network_editor_type = getattr(
            pane_tab_type,
            "NetworkEditor",
            None,
        )
        if ui is None or network_editor_type is None:
            return None, None

        current_tabs = getattr(ui, "currentPaneTabs", None)
        if callable(current_tabs):
            try:
                for pane_tab in current_tabs():
                    if pane_tab.type() == network_editor_type:
                        return pane_tab, pane_tab.pwd()
            except Exception:
                pass

        pane_tab_of_type = getattr(ui, "paneTabOfType", None)
        if not callable(pane_tab_of_type):
            return None, None
        try:
            pane_tab = pane_tab_of_type(network_editor_type)
            if pane_tab is None:
                return None, None
            return pane_tab, pane_tab.pwd()
        except Exception:
            return None, None

    def create_environment_light(self, asset_path, target_path=None):
        if not self.is_available(asset_path):
            return self._failure(
                "Houdini HDRI creation is unavailable for this asset."
            )

        asset_path = self._normalized_asset_path(asset_path)
        target = (
            self._target_from_path(target_path)
            if target_path
            else self.resolve_current_target()
        )
        if target is None:
            return self._failure(
                "Select an Object or LOP target network."
            )

        hou = self._load_hou()
        network = hou.node(target["network_path"])
        if network is None or not self._is_editable(network):
            return self._failure(
                "Target network is unavailable or not editable: %s"
                % target["network_path"]
            )

        created_node = None
        node_name = self._node_name(asset_path)
        try:
            with hou.undos.group("Create HDRI Environment Light"):
                try:
                    if target["kind"] == OBJECT_KIND:
                        created_node = self._create_object_light(
                            network,
                            node_name,
                            asset_path,
                        )
                    else:
                        created_node = self._create_lop_light(
                            network,
                            node_name,
                            asset_path,
                        )
                    self._finish_node(created_node)
                except Exception:
                    if created_node is not None:
                        try:
                            created_node.destroy()
                        except Exception:
                            pass
                    raise
        except Exception as exc:
            return self._failure(str(exc))

        node_path = created_node.path()
        message = "Created Houdini environment light: %s" % node_path
        self._set_status_message(message)
        return {
            "success": True,
            "message": message,
            "node_path": node_path,
        }

    def _is_houdini_app(self):
        app_plugin = getattr(self.core, "appPlugin", None)
        plugin_name = getattr(app_plugin, "pluginName", "")
        return str(plugin_name).lower() == "houdini"

    @staticmethod
    def _is_supported_file(asset_path):
        if not asset_path:
            return False
        extension = os.path.splitext(asset_path)[1].lower()
        return extension in HDR_EXTENSIONS and os.path.isfile(asset_path)

    def _load_hou(self):
        if self._hou_load_attempted:
            return self._hou
        self._hou_load_attempted = True
        try:
            self._hou = __import__("hou")
        except ImportError:
            self._hou = None
        return self._hou

    def _target_from_node(self, node):
        target = self._target_from_network(node)
        if target is not None:
            return target
        if node is None:
            return None

        hou = self._load_hou()
        try:
            category = node.type().category()
        except Exception:
            return None
        if category not in (
            hou.objNodeTypeCategory(),
            hou.lopNodeTypeCategory(),
        ):
            return None
        try:
            parent = node.parent()
        except Exception:
            return None
        return self._target_from_network(parent)

    def _target_from_path(self, network_path):
        hou = self._load_hou()
        try:
            node = hou.node(network_path)
        except Exception:
            return None
        return self._target_from_network(node)

    def _target_from_network(self, network):
        if network is None or not self._is_editable(network):
            return None
        hou = self._load_hou()
        try:
            child_category = network.childTypeCategory()
        except Exception:
            return None
        if child_category == hou.objNodeTypeCategory():
            kind = OBJECT_KIND
            suffix = "Environment Light"
        elif child_category == hou.lopNodeTypeCategory():
            kind = LOP_KIND
            suffix = "Dome Light"
        else:
            return None
        network_path = network.path()
        return {
            "kind": kind,
            "network_path": network_path,
            "display_label": "%s \u2014 %s" % (network_path, suffix),
        }

    @staticmethod
    def _is_editable(node):
        is_editable = getattr(node, "isEditable", None)
        if not callable(is_editable):
            return True
        try:
            return bool(is_editable())
        except Exception:
            return False

    @staticmethod
    def _normalized_asset_path(asset_path):
        return os.path.abspath(
            os.path.normpath(asset_path)
        ).replace("\\", "/")

    @staticmethod
    def _node_name(asset_path):
        stem = os.path.splitext(os.path.basename(asset_path))[0]
        stem = re.sub(r"[^A-Za-z0-9_]+", "_", stem).strip("_")
        return "hdri_%s" % (stem or "environment")

    @staticmethod
    def _create_object_light(network, node_name, asset_path):
        node = network.createNode(
            "envlight",
            node_name,
            force_valid_node_name=True,
        )
        try:
            parameter = node.parm("env_map")
            if parameter is None:
                raise RuntimeError(
                    "Environment Light is missing the env_map parameter."
                )
            parameter.set(asset_path)
        except Exception:
            try:
                node.destroy()
            except Exception:
                pass
            raise
        return node

    @staticmethod
    def _create_lop_light(network, node_name, asset_path):
        upstream = network.displayNode()
        node = network.createNode(
            "domelight::3.0",
            node_name,
            force_valid_node_name=True,
        )
        try:
            if upstream is not None:
                node.setInput(0, upstream)
            parameter = node.parm(LOP_TEXTURE_PARM)
            if parameter is None:
                raise RuntimeError(
                    "Dome Light is missing its Texture parameter."
                )
            parameter.set(asset_path)
            node.setDisplayFlag(True)
        except Exception:
            try:
                node.destroy()
            except Exception:
                pass
            raise
        return node

    @staticmethod
    def _finish_node(node):
        try:
            node.moveToGoodPosition()
        except Exception:
            pass
        try:
            node.setCurrent(True, clear_all_selected=True)
        except Exception:
            pass

    def _set_status_message(self, message):
        hou = self._load_hou()
        ui = getattr(hou, "ui", None)
        set_status_message = getattr(ui, "setStatusMessage", None)
        if callable(set_status_message):
            try:
                set_status_message(message)
            except Exception:
                pass

    @staticmethod
    def _failure(message):
        return {
            "success": False,
            "message": message or "Unable to create Houdini environment light.",
            "node_path": "",
        }
