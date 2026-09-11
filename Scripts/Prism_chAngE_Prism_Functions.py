from qtpy.QtWidgets import QMenu

from PrismUtils.Decorators import err_catcher_plugin as err_catcher

from change_prism.archive_browser.controller import ArchiveBrowserController
from change_prism.asset_library.controller import AssetLibraryController
from change_prism.batch_import.controller import BatchImportController
from change_prism.houdini_archive.controller import HoudiniArchiveController
from change_prism.nuke_archive.controller import NukeArchiveController
from change_prism.ocio.controller import OCIOConvertController
from change_prism.review_copy.controller import ReviewCopyController
from change_prism.settings.controller import SettingsController


class Prism_chAngE_Prism_Functions(object):
    """Prism callback facade; feature logic lives in internal controllers."""

    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin
        self.batch_import = BatchImportController(core, plugin)
        self.archive_browser = ArchiveBrowserController(core)
        self.asset_library = AssetLibraryController(core)
        self.nuke_archive = NukeArchiveController(
            core, refresh_callback=self.archive_browser.refresh
        )
        self.houdini_archive = HoudiniArchiveController(
            core, refresh_callback=self.archive_browser.refresh
        )
        self.ocio_converter = OCIOConvertController(core)
        self.review_copy = ReviewCopyController(core)
        self.settings = SettingsController(core, plugin)

        self.core.callbacks.registerCallback(
            "onProjectBrowserStartup",
            self.onProjectBrowserStartup,
            plugin=self,
        )
        self.core.callbacks.registerCallback(
            "openPBShotContextMenu",
            self.onPBShotContextMenu,
            plugin=self,
        )
        self.core.callbacks.registerCallback(
            "openPBFileContextMenu",
            self.onPBFileContextMenu,
            plugin=self,
        )
        self.core.callbacks.registerCallback(
            "mediaPlayerContextMenuRequested",
            self.onMediaPlayerContextMenuRequested,
            plugin=self,
        )
        self.core.callbacks.registerCallback(
            "productSelectorContextMenuRequested",
            self.onProductSelectorContextMenuRequested,
            plugin=self,
        )
        self.core.callbacks.registerCallback(
            "userSettings_loadUI",
            self.onUserSettingsLoadUI,
            plugin=self,
        )
        self.core.callbacks.registerCallback(
            "userSettings_loadSettings",
            self.onUserSettingsLoadSettings,
            plugin=self,
        )
        self.core.callbacks.registerCallback(
            "userSettings_saveSettings",
            self.onUserSettingsSaveSettings,
            plugin=self,
        )

    @err_catcher(name=__name__)
    def isActive(self):
        return True

    @err_catcher(name=__name__)
    def onProjectBrowserStartup(self, origin):
        old_action = getattr(self, "_chAngE_menu_action", None)
        if old_action is not None:
            try:
                origin.menubar.removeAction(old_action)
            except Exception:
                pass

        menu = QMenu("chAngE")
        action = menu.addAction("Batch Import from Server...")
        action.triggered.connect(self.onBatchImport)
        action = menu.addAction("ACES / OCIO Media Converter...")
        action.triggered.connect(lambda checked=False: self.onOCIOConvert())
        self._chAngE_menu_action = origin.menubar.addMenu(menu)
        self.archive_browser.add_project_browser_tab(origin)
        self.asset_library.add_project_browser_tab(origin)

    @err_catcher(name=__name__)
    def onPBShotContextMenu(self, origin, menu, index):
        self.batch_import.add_shot_context_menu(origin, menu, index)

    @err_catcher(name=__name__)
    def onPBFileContextMenu(self, origin, menu, filepath):
        self.nuke_archive.add_file_context_menu(origin, menu, filepath)
        self.houdini_archive.add_file_context_menu(origin, menu, filepath)
        self.review_copy.add_file_context_menu(origin, menu, filepath)

    @err_catcher(name=__name__)
    def onBatchImport(self):
        self.batch_import.open_dialog()

    @err_catcher(name=__name__)
    def onMediaPlayerContextMenuRequested(self, origin, menu):
        self.ocio_converter.add_media_context_menu(
            origin, menu, self.onOCIOQuickConvert
        )
        self.review_copy.add_media_context_menu(origin, menu)

    @err_catcher(name=__name__)
    def onProductSelectorContextMenuRequested(
        self, origin, view_ui, pos, menu
    ):
        self.review_copy.add_product_context_menu(
            origin, view_ui, pos, menu
        )

    @err_catcher(name=__name__)
    def onOCIOConvert(self, media_player=None):
        self.ocio_converter.open_dialog(media_player=media_player)

    @err_catcher(name=__name__)
    def onOCIOQuickConvert(self, media_player, formats):
        self.ocio_converter.quick_convert(media_player, formats)

    @err_catcher(name=__name__)
    def onUserSettingsLoadUI(self, origin):
        self.settings.load_ui(origin)

    @err_catcher(name=__name__)
    def onUserSettingsLoadSettings(self, origin, settings):
        self.settings.load_settings(origin, settings)

    @err_catcher(name=__name__)
    def onUserSettingsSaveSettings(self, origin, settings):
        self.settings.save_settings(origin, settings)
