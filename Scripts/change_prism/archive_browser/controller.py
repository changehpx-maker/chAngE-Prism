from __future__ import unicode_literals


TAB_LABEL = "Archives"
TAB_TYPE = "Archive"


class ArchiveBrowserController:
    def __init__(self, core):
        self.core = core
        self.browser_widget = None

    def add_project_browser_tab(self, origin):
        tab_widget = getattr(origin, "tbw_project", None)
        if tab_widget is not None:
            for index in range(tab_widget.count()):
                widget = tab_widget.widget(index)
                if (
                    widget.property("tabType") in (TAB_TYPE, TAB_LABEL)
                    and widget.property("archiveBrowserKind")
                    == "multi_dcc"
                ):
                    tab_widget.setTabText(index, TAB_LABEL)
                    widget.setProperty("tabType", TAB_TYPE)
                    self.browser_widget = widget
                    return
                if widget.property("tabType") in (TAB_TYPE, TAB_LABEL):
                    tab_widget.removeTab(index)
                    widget.deleteLater()
                    break

        from change_prism.archive_browser.dialog import (
            LazyArchiveBrowserWidget,
        )

        widget = LazyArchiveBrowserWidget(self.core, parent=origin)
        origin.addTab(TAB_LABEL, widget)
        widget.setProperty("tabType", TAB_TYPE)
        self.browser_widget = widget

    def refresh(self):
        widget = self.browser_widget
        if widget is not None:
            try:
                widget.refresh_versions()
            except RuntimeError:
                self.browser_widget = None
