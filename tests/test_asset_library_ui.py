import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from qtpy.QtCore import QSize, Qt
    from qtpy.QtGui import QImage
    from qtpy.QtWidgets import (
        QApplication,
        QMenuBar,
        QMessageBox,
        QTabWidget,
        QWidget,
    )
    from change_prism.asset_library import service
    from change_prism.asset_library.dialog import (
        AssetLibraryWidget,
        LazyAssetLibraryWidget,
        _ThumbnailThread,
    )
except Exception:
    QApplication = None
    AssetLibraryWidget = None
    LazyAssetLibraryWidget = None
    _ThumbnailThread = None


class _Media:
    def getQImageFromExrPath(
        self,
        _path,
        width,
        height,
        allowThumb=False,
    ):
        image = QImage(width, height, QImage.Format_RGB32)
        image.fill(0xFF777777)
        return image

    def getMediaResolution(self, _path):
        return {"width": 4096, "height": 2048}


class _Core:
    def __init__(self, sources=None):
        self.data = {
            "change_prism": {
                "asset_library": {"sources": list(sources or [])}
            }
        }
        self.media = _Media() if QApplication else None
        self.popups = []

    def getConfig(self, cat=None, param=None, **_kwargs):
        section = self.data.get(cat)
        if param is None:
            return section
        return section.get(param) if isinstance(section, dict) else None

    def setConfig(self, cat=None, param=None, val=None, **_kwargs):
        self.data.setdefault(cat, {})[param] = val

    def popup(self, message, severity=None):
        self.popups.append((message, severity))


class _Callbacks:
    def __init__(self):
        self.names = []

    def registerCallback(self, name, method, plugin=None):
        self.names.append(name)


class _PluginCore(_Core):
    def __init__(self):
        super(_PluginCore, self).__init__()
        self.callbacks = _Callbacks()


@unittest.skipUnless(QApplication, "Requires Prism Qt runtime")
class AssetLibraryUiTests(unittest.TestCase):
    def test_full_widget_is_created_only_when_lazy_tab_is_entered(self):
        app = QApplication.instance() or QApplication([])
        widget = LazyAssetLibraryWidget(_Core())
        try:
            self.assertIsNone(widget._browser)
            widget.refresh_sources()
            self.assertIsNone(widget._browser)
            widget.entered()
            self.assertIsInstance(widget._browser, AssetLibraryWidget)
            self.assertEqual(widget.refreshStatus, "valid")
        finally:
            widget.close()
        app.processEvents()

    def test_plugin_facade_adds_asset_tab_next_to_existing_library(self):
        app = QApplication.instance() or QApplication([])
        try:
            from Prism_chAngE_Prism_init import Prism_chAngE_Prism
        except Exception as exc:
            self.skipTest("Requires Prism plugin runtime: %s" % exc)

        class Origin(QWidget):
            def __init__(self):
                super(Origin, self).__init__()
                self.menubar = QMenuBar(self)
                self.tbw_project = QTabWidget(self)

            def addTab(self, name, widget):
                widget.setProperty("tabType", name)
                self.tbw_project.addTab(widget, name)

        origin = Origin()
        official = QWidget(origin)
        official.setProperty("tabType", "Libraries")
        origin.addTab("Libraries", official)
        plugin = Prism_chAngE_Prism(_PluginCore())
        try:
            plugin.onProjectBrowserStartup(origin)
            plugin.onProjectBrowserStartup(origin)
            tab_types = [
                origin.tbw_project.widget(index).property("tabType")
                for index in range(origin.tbw_project.count())
            ]
            self.assertEqual(
                tab_types,
                ["Libraries", "Archive", "AssetLibrary"],
            )
            self.assertIs(origin.tbw_project.widget(0), official)
        finally:
            origin.close()
        app.processEvents()

    def test_root_is_exact_folder_name_and_folder_view_is_direct_only(self):
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            source = os.path.join(tmp, "categories")
            clear = os.path.join(source, "clear")
            outdoor = os.path.join(source, "outdoor")
            os.makedirs(clear)
            os.makedirs(outdoor)
            first = os.path.join(clear, "sky_4k.exr")
            second = os.path.join(outdoor, "sky_4k.exr")
            Path(first).write_bytes(b"same")
            Path(second).write_bytes(b"same")
            timestamp = 1784990000
            os.utime(first, (timestamp, timestamp))
            os.utime(second, (timestamp, timestamp))

            core = _Core([{"path": source, "enabled": True}])
            widget = AssetLibraryWidget(core)
            try:
                widget.scan_result = service.scan_sources(
                    core.data["change_prism"]["asset_library"]["sources"]
                )
                widget._populate_tree()
                widget._refresh_asset_view()
                widget._thumbnail_timer.stop()

                root_item = widget.source_tree.topLevelItem(0)
                self.assertEqual(root_item.text(0), "categories")
                self.assertEqual(root_item.childCount(), 2)
                self.assertEqual(widget.asset_model.rowCount(), 0)

                widget.source_tree.setCurrentItem(root_item.child(0))
                widget._refresh_asset_view()
                widget._thumbnail_timer.stop()
                self.assertEqual(widget.asset_model.rowCount(), 1)

                widget.search_edit.setText("sky")
                widget._search_timer.stop()
                widget._refresh_asset_view()
                widget._thumbnail_timer.stop()
                self.assertEqual(widget.asset_model.rowCount(), 1)
                record = widget.asset_model.records[0]
                self.assertEqual(record["location_count"], 2)

                widget.asset_view.setCurrentIndex(
                    widget.asset_model.index(0, 0)
                )
                self.assertEqual(widget.location_combo.count(), 2)
                self.assertTrue(
                    widget.detail_path.text().endswith("sky_4k.exr")
                )
            finally:
                widget.close()
        app.processEvents()

    def test_regular_thumbnail_is_cached_with_original_extension(self):
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "plate.png")
            source = QImage(40, 20, QImage.Format_RGB32)
            source.fill(0xFF336699)
            self.assertTrue(source.save(path))
            results = []
            thread = _ThumbnailThread(
                _Core(),
                path,
                ("record",),
                1,
                QSize(20, 20),
            )
            thread.resultReady.connect(results.append)
            thread.run()

            self.assertEqual(len(results), 1)
            self.assertFalse(results[0]["image"].isNull())
            self.assertEqual(
                (results[0]["width"], results[0]["height"]),
                (40, 20),
            )
            self.assertTrue(
                os.path.isfile(
                    os.path.join(tmp, "_thumbs", "plate.png.jpg")
                )
            )
        app.processEvents()

    def test_thumbnails_are_generated_only_by_selected_folder_button(self):
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            source = os.path.join(tmp, "categories")
            clear = os.path.join(source, "clear")
            os.makedirs(clear)
            cached_path = os.path.join(clear, "cached.png")
            missing_path = os.path.join(clear, "missing.png")
            for path in (cached_path, missing_path):
                image = QImage(20, 10, QImage.Format_RGB32)
                image.fill(0xFF336699)
                self.assertTrue(image.save(path))

            cache = service.thumbnail_path(cached_path)
            os.makedirs(os.path.dirname(cache))
            cached_image = QImage(10, 5, QImage.Format_RGB32)
            cached_image.fill(0xFF777777)
            self.assertTrue(cached_image.save(cache))
            source_mtime = os.path.getmtime(cached_path)
            os.utime(cache, (source_mtime + 1, source_mtime + 1))

            core = _Core([{"path": source, "enabled": True}])
            widget = AssetLibraryWidget(core)
            try:
                widget.scan_result = service.scan_sources(
                    core.data["change_prism"]["asset_library"]["sources"]
                )
                widget._populate_tree()
                clear_item = widget.source_tree.topLevelItem(0).child(0)
                widget.source_tree.setCurrentItem(clear_item)
                widget._refresh_asset_view()
                widget._thumbnail_timer.stop()

                widget._thumbnail_queue.clear()
                with mock.patch.object(widget, "_start_next_thumbnail"):
                    widget._queue_visible_thumbnails()
                self.assertEqual(len(widget._thumbnail_queue), 1)
                self.assertEqual(
                    widget._thumbnail_queue[0]["path"],
                    cached_path,
                )
                self.assertFalse(widget._thumbnail_queue[0]["manual"])

                widget._thumbnail_queue.clear()
                with mock.patch.object(widget, "_start_next_thumbnail"):
                    widget.generate_selected_thumbnails()
                self.assertEqual(len(widget._thumbnail_queue), 1)
                self.assertEqual(
                    widget._thumbnail_queue[0]["path"],
                    missing_path,
                )
                self.assertTrue(widget._thumbnail_queue[0]["manual"])
                self.assertFalse(
                    widget.generate_thumbnails_button.isEnabled()
                )
                self.assertIn(
                    "1 up to date",
                    widget.status_label.text(),
                )
            finally:
                widget.close()
        app.processEvents()

    def test_thumbnail_scheduler_limits_total_and_hdr_concurrency(self):
        app = QApplication.instance() or QApplication([])
        widget = AssetLibraryWidget(_Core())
        started = []

        class FakeSignal:
            def connect(self, _callback):
                return None

        class FakeThumbnailThread:
            def __init__(
                self,
                _core,
                path,
                _record_key,
                _generation,
                _target_size,
                manual=False,
            ):
                self.path = path
                self.manual = manual
                self.resultReady = FakeSignal()
                self.finished = FakeSignal()
                self.running = False

            def start(self):
                self.running = True
                started.append(self)

            def isRunning(self):
                return self.running

        try:
            paths = [
                "one.exr",
                "two.hdr",
                "three.exr",
                "one.png",
                "two.jpg",
                "three.tif",
            ]
            for path in paths:
                widget._thumbnail_queue.append(
                    {
                        "path": path,
                        "record_key": (path,),
                        "generation": 1,
                        "manual": True,
                    }
                )

            with mock.patch(
                "change_prism.asset_library.dialog._ThumbnailThread",
                FakeThumbnailThread,
            ), mock.patch(
                "change_prism.asset_library.dialog._track_thread"
            ):
                widget._start_next_thumbnail()
                self.assertEqual(len(started), 4)
                self.assertEqual(
                    sum(1 for thread in started if thread.is_hdr),
                    2,
                )
                self.assertEqual(len(widget._thumbnail_queue), 2)

                finished_hdr = next(
                    thread for thread in started if thread.is_hdr
                )
                finished_hdr.running = False
                widget._on_thumbnail_finished(finished_hdr)
                self.assertEqual(len(started), 5)
                self.assertEqual(
                    sum(
                        1
                        for thread in widget._thumbnail_threads
                        if thread.is_hdr
                    ),
                    2,
                )
        finally:
            widget._thumbnail_threads.clear()
            widget.close()
        app.processEvents()

    def test_add_toggle_and_remove_source_only_updates_registration(self):
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            source = os.path.join(tmp, "categories")
            os.makedirs(source)
            core = _Core()
            widget = AssetLibraryWidget(core)
            try:
                with mock.patch(
                    "change_prism.asset_library.dialog.QFileDialog.getExistingDirectory",
                    return_value=source,
                ), mock.patch.object(widget, "refresh_sources"):
                    widget.add_source()
                configured = core.data["change_prism"]["asset_library"][
                    "sources"
                ]
                self.assertEqual(
                    configured,
                    [{"path": os.path.normpath(source), "enabled": True}],
                )

                widget._populate_tree()
                root_item = widget.source_tree.topLevelItem(0)
                with mock.patch.object(widget, "refresh_sources"):
                    root_item.setCheckState(0, Qt.Unchecked)
                configured = core.data["change_prism"]["asset_library"][
                    "sources"
                ]
                self.assertFalse(configured[0]["enabled"])

                widget.source_tree.setCurrentItem(root_item)
                with mock.patch(
                    "change_prism.asset_library.dialog.QMessageBox.question",
                    return_value=QMessageBox.Yes,
                ), mock.patch.object(widget, "refresh_sources"):
                    widget.remove_source()
                self.assertEqual(
                    core.data["change_prism"]["asset_library"]["sources"],
                    [],
                )
                self.assertTrue(os.path.isdir(source))
            finally:
                widget.close()
        app.processEvents()

    def test_stale_scan_result_does_not_replace_current_state(self):
        app = QApplication.instance() or QApplication([])
        widget = AssetLibraryWidget(_Core())
        try:
            current = widget.scan_result
            widget._scan_generation = 2
            widget._on_scan_result(
                {
                    "sources": [{"id": "stale"}],
                    "directories": [],
                    "assets": [{"filename": "stale.exr"}],
                    "failures": [],
                    "cancelled": False,
                },
                1,
            )
            self.assertIs(widget.scan_result, current)
        finally:
            widget.close()
        app.processEvents()

    def test_thumbnail_cache_write_failure_keeps_in_memory_preview(self):
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "plate.png")
            source = QImage(20, 10, QImage.Format_RGB32)
            source.fill(0xFF336699)
            self.assertTrue(source.save(path))
            results = []
            thread = _ThumbnailThread(
                _Core(),
                path,
                ("record",),
                1,
                QSize(20, 20),
            )
            thread.resultReady.connect(results.append)
            cache = os.path.join(tmp, "blocked", "plate.png.jpg")
            with mock.patch.object(
                service,
                "thumbnail_path",
                return_value=cache,
            ), mock.patch(
                "change_prism.asset_library.dialog.os.makedirs",
                side_effect=OSError("read only"),
            ):
                thread.run()

            self.assertFalse(results[0]["image"].isNull())
            self.assertIn("read only", results[0]["cache_error"])
            self.assertFalse(os.path.exists(cache))
        app.processEvents()

    def test_thumbnail_cache_directory_creation_race_is_not_a_failure(self):
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "plate.png")
            source = QImage(20, 10, QImage.Format_RGB32)
            source.fill(0xFF336699)
            self.assertTrue(source.save(path))
            results = []
            thread = _ThumbnailThread(
                _Core(),
                path,
                ("record",),
                1,
                QSize(20, 20),
            )
            thread.resultReady.connect(results.append)
            original_makedirs = os.makedirs

            def racing_makedirs(directory):
                original_makedirs(directory)
                raise OSError("created by another worker")

            with mock.patch(
                "change_prism.asset_library.dialog.os.makedirs",
                side_effect=racing_makedirs,
            ):
                thread.run()

            self.assertEqual(results[0]["cache_error"], "")
            self.assertTrue(
                os.path.isfile(
                    os.path.join(tmp, "_thumbs", "plate.png.jpg")
                )
            )
        app.processEvents()

    def test_hdr_thumbnail_uses_prism_media_preview_without_default_cache(self):
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "sky.exr")
            Path(path).write_bytes(b"fake")
            results = []
            thread = _ThumbnailThread(
                _Core(),
                path,
                ("record",),
                1,
                QSize(64, 32),
            )
            thread.resultReady.connect(results.append)
            thread.run()

            self.assertEqual(
                (results[0]["width"], results[0]["height"]),
                (4096, 2048),
            )
            self.assertTrue(
                os.path.isfile(
                    os.path.join(tmp, "_thumbs", "sky.exr.jpg")
                )
            )
            self.assertFalse(os.path.exists(os.path.join(tmp, "_thumbs", "sky.jpg")))
        app.processEvents()


if __name__ == "__main__":
    unittest.main()
