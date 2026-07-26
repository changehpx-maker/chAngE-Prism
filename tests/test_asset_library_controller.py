import sys
import types
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))

from change_prism.asset_library.controller import (
    AssetLibraryController,
    LIBRARY_KIND,
    TAB_LABEL,
    TAB_TYPE,
)


class _Widget:
    def __init__(self, core=None, parent=None):
        self.core = core
        self.parent = parent
        self.properties = {}
        self.refresh_count = 0

    def property(self, name):
        return self.properties.get(name)

    def setProperty(self, name, value):
        self.properties[name] = value

    def refresh_sources(self):
        self.refresh_count += 1


class _TabWidget:
    def __init__(self, widgets=None):
        self.widgets = list(widgets or [])
        self.labels = [
            widget.property("tabType") or "" for widget in self.widgets
        ]

    def count(self):
        return len(self.widgets)

    def widget(self, index):
        return self.widgets[index]

    def setTabText(self, index, text):
        self.labels[index] = text


class _Origin:
    def __init__(self, widgets=None):
        self.tbw_project = _TabWidget(widgets)

    def addTab(self, name, widget):
        widget.setProperty("tabType", name)
        self.tbw_project.widgets.append(widget)
        self.tbw_project.labels.append(name)


class AssetLibraryControllerTests(unittest.TestCase):
    def test_adds_own_tab_without_touching_official_libraries(self):
        official = _Widget()
        official.setProperty("tabType", "Libraries")
        origin = _Origin([official])
        fake_dialog = types.SimpleNamespace(
            LazyAssetLibraryWidget=_Widget
        )

        with mock.patch.dict(
            sys.modules,
            {"change_prism.asset_library.dialog": fake_dialog},
        ):
            controller = AssetLibraryController(object())
            controller.add_project_browser_tab(origin)
            controller.add_project_browser_tab(origin)

        self.assertEqual(origin.tbw_project.count(), 2)
        self.assertIs(origin.tbw_project.widget(0), official)
        library = origin.tbw_project.widget(1)
        self.assertEqual(
            library.property("changePrismAssetLibrary"),
            LIBRARY_KIND,
        )
        self.assertEqual(library.property("tabType"), TAB_TYPE)
        self.assertEqual(origin.tbw_project.labels[1], TAB_LABEL)

    def test_refresh_is_forwarded_to_the_lazy_widget(self):
        controller = AssetLibraryController(object())
        controller.browser_widget = _Widget()
        controller.refresh()
        self.assertEqual(controller.browser_widget.refresh_count, 1)


if __name__ == "__main__":
    unittest.main()
