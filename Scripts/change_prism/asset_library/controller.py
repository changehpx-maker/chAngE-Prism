from __future__ import unicode_literals


TAB_LABEL = "Asset Library"
TAB_TYPE = "AssetLibrary"
LIBRARY_KIND = "change_prism"


class AssetLibraryController(object):
    def __init__(self, core):
        self.core = core
        self.browser_widget = None

    def add_project_browser_tab(self, origin):
        tab_widget = getattr(origin, "tbw_project", None)
        if tab_widget is not None:
            for index in range(tab_widget.count()):
                widget = tab_widget.widget(index)
                if (
                    widget.property("changePrismAssetLibrary")
                    == LIBRARY_KIND
                ):
                    tab_widget.setTabText(index, TAB_LABEL)
                    widget.setProperty("tabType", TAB_TYPE)
                    self.browser_widget = widget
                    return

        from change_prism.asset_library.dialog import (
            LazyAssetLibraryWidget,
        )

        widget = LazyAssetLibraryWidget(self.core, parent=origin)
        origin.addTab(TAB_LABEL, widget)
        widget.setProperty("tabType", TAB_TYPE)
        widget.setProperty("changePrismAssetLibrary", LIBRARY_KIND)
        self.browser_widget = widget

    def refresh(self):
        widget = self.browser_widget
        if widget is not None:
            try:
                widget.refresh_sources()
            except RuntimeError:
                self.browser_widget = None
