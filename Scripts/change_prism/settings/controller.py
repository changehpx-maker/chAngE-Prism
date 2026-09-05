from change_prism.config import (
    CONFIG_SECTION,
    get_project_config_key,
    normalize_config,
)
from change_prism.dcc_paths import get_prism_hython


class SettingsController(object):
    TAB_NAME = "chAngE_Prism"

    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin
        self.widget = None

    def load_ui(self, origin):
        from change_prism.settings.dialog import PluginSettingsWidget

        self.widget = PluginSettingsWidget(
            self.core,
            project_key=get_project_config_key(self.core),
            parent=origin,
        )
        origin.addTab(self.widget, self.TAB_NAME)

    def load_settings(self, _origin, settings):
        if not self._widget_alive():
            return
        settings = settings if isinstance(settings, dict) else {}
        section = settings.get(CONFIG_SECTION, {})
        config = normalize_config(section)
        project_key = get_project_config_key(self.core)
        override = config["ocio_converter"]["project_overrides"].get(
            project_key, ""
        )
        self.widget.set_values(
            config["server_root"],
            config["local_projects_root"],
            config["review_copy"]["destination_root"],
            get_prism_hython(self.core),
            config["pdg"]["hip_path"],
            config["pdg"]["houdini_package_directory"],
            override,
        )

    def _widget_alive(self):
        if self.widget is None:
            return False
        try:
            # Prism may have destroyed the settings window since
            # load_ui; a deleted widget's C++ object raises here.
            self.widget.isVisible()
        except RuntimeError:
            self.widget = None
            return False
        return True

    def save_settings(self, _origin, settings):
        if not self._widget_alive() or not isinstance(settings, dict):
            return

        section = settings.get(CONFIG_SECTION, {})
        section = dict(section) if isinstance(section, dict) else {}
        values = self.widget.values()
        section["server_root"] = values["server_root"]
        section["local_projects_root"] = values["local_projects_root"]

        review_copy = section.get("review_copy", {})
        review_copy = dict(review_copy) if isinstance(review_copy, dict) else {}
        review_copy["destination_root"] = values["review_copy_destination_root"]
        section["review_copy"] = review_copy

        pdg = section.get("pdg", {})
        pdg = dict(pdg) if isinstance(pdg, dict) else {}
        pdg["hip_path"] = values["pdg_hip_path"]
        pdg["houdini_package_directory"] = values[
            "houdini_package_directory"
        ]
        section["pdg"] = pdg

        converter = section.get("ocio_converter", {})
        converter = dict(converter) if isinstance(converter, dict) else {}
        overrides = converter.get("project_overrides", {})
        overrides = dict(overrides) if isinstance(overrides, dict) else {}
        project_key = get_project_config_key(self.core)
        ocio_path = values["ocio_project_override"]
        if ocio_path:
            overrides[project_key] = ocio_path
        else:
            overrides.pop(project_key, None)
        converter["project_overrides"] = overrides
        section["ocio_converter"] = converter

        settings[CONFIG_SECTION] = section
        self.plugin.serverRoot = values["server_root"]
