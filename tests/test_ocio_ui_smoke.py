import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from qtpy.QtWidgets import QApplication, QMenu
    from change_prism.ocio.dialog import OCIOConvertDialog
    from Prism_chAngE_Prism_init import Prism_chAngE_Prism
except Exception:
    QApplication = None
    OCIOConvertDialog = None
    Prism_chAngE_Prism = None


class _Media:
    def __init__(self, prism_root):
        self.ffmpeg = os.path.join(prism_root, "Tools", "FFmpeg", "bin", "ffmpeg.exe")

    def getFFmpeg(self, validate=False):
        return self.ffmpeg


class _Core:
    def __init__(self, prism_root):
        self.prismLibs = prism_root
        self.projectPath = "D:/test_project"
        self.prismIni = ""
        self.media = _Media(prism_root)
        self.pb = None

    def getConfig(self, *args, **kwargs):
        return 24

    def popup(self, *args, **kwargs):
        return None


class _Callbacks:
    def __init__(self):
        self.names = []

    def registerCallback(self, name, method, plugin=None):
        self.names.append(name)


class _PluginCore(_Core):
    def __init__(self, prism_root):
        super().__init__(prism_root)
        self.callbacks = _Callbacks()


class _BrowserOrigin:
    def getCurrentAOV(self):
        return {}


class _MediaPlayer:
    def __init__(self, directory, filename):
        self.directory = directory
        self.seq = [filename]
        self.origin = _BrowserOrigin()

    def getCurRenders(self):
        return [{"path": self.directory}]


@unittest.skipUnless(QApplication and os.getenv("PRISM_TEST_ROOT"), "Requires Prism Qt runtime")
class DialogSmokeTests(unittest.TestCase):
    @staticmethod
    def _wait_for(app, predicate, timeout=30):
        deadline = time.time() + timeout
        while not predicate() and time.time() < deadline:
            app.processEvents()
            time.sleep(0.01)
        return predicate()

    def test_plugin_registers_media_context_callback(self):
        core = _PluginCore(os.environ["PRISM_TEST_ROOT"])
        Prism_chAngE_Prism(core)
        self.assertIn("onProjectBrowserStartup", core.callbacks.names)
        self.assertIn("openPBShotContextMenu", core.callbacks.names)
        self.assertIn("openPBFileContextMenu", core.callbacks.names)
        self.assertIn("mediaPlayerContextMenuRequested", core.callbacks.names)
        self.assertIn(
            "productSelectorContextMenuRequested",
            core.callbacks.names,
        )
        self.assertIn("userSettings_loadUI", core.callbacks.names)
        self.assertIn("userSettings_loadSettings", core.callbacks.names)
        self.assertIn("userSettings_saveSettings", core.callbacks.names)

    def test_media_context_menu_uses_hidden_quick_actions(self):
        app = QApplication.instance() or QApplication([])
        core = _PluginCore(os.environ["PRISM_TEST_ROOT"])
        plugin = Prism_chAngE_Prism(core)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "menu.1001.exr")
            Path(path).touch()
            menu = QMenu()
            calls = []
            plugin.onOCIOQuickConvert = (
                lambda player, formats: calls.append(tuple(formats))
            )
            plugin.onMediaPlayerContextMenuRequested(
                _MediaPlayer(tmp, os.path.basename(path)), menu
            )
            quick_menu = next(
                action.menu()
                for action in menu.actions()
                if action.menu()
                and action.menu().title() == "ACES / OCIO Quick Convert"
            )
            self.assertEqual(quick_menu.title(), "ACES / OCIO Quick Convert")
            self.assertEqual(
                [action.text() for action in quick_menu.actions()],
                ["H.264 MP4", "ProRes 422 HQ MOV", "MP4 + MOV"],
            )
            self.assertIn(
                "Copy to Daily Review Folder",
                [action.text() for action in menu.actions()],
            )
            quick_menu.actions()[1].trigger()
            app.processEvents()
            self.assertEqual(calls, [(".mov",)])

    def test_dialog_loads_bundled_ocio_inventory(self):
        app = QApplication.instance() or QApplication([])
        dialog = OCIOConvertDialog(_Core(os.environ["PRISM_TEST_ROOT"]))
        try:
            self.assertTrue(self._wait_for(app, lambda: bool(dialog.inventory), 15))
            self.assertEqual(dialog.input_combo.currentText(), "ACEScg")
            self.assertIn("Rec.709", dialog.display_combo.currentText())
            self.assertEqual(dialog.fps_spin.value(), 24)
            self.assertEqual(dialog.prores_combo.currentData(), "prores_aw")
        finally:
            dialog.close()
        app.processEvents()

    def test_dialog_runs_external_sequence_queue(self):
        app = QApplication.instance() or QApplication([])
        prism_root = os.environ["PRISM_TEST_ROOT"]
        oiiotool = os.path.join(
            prism_root, "PythonLibs", "Python3", "OpenImageIO", "bin", "oiiotool.exe"
        )
        with tempfile.TemporaryDirectory() as tmp:
            first = ""
            for frame in range(1001, 1004):
                path = os.path.join(tmp, "beauty.%04d.exr" % frame)
                result = subprocess.run([
                    oiiotool,
                    "--pattern", "constant:color=0.18,0.18,0.18", "64x64", "3",
                    "-d", "half", "-o", path,
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.assertEqual(result.returncode, 0)
                first = first or path

            dialog = OCIOConvertDialog(_Core(prism_root), initial_paths=[first])
            try:
                self.assertTrue(
                    self._wait_for(app, lambda: bool(dialog.inventory), 15),
                    dialog.config_status.text(),
                )
                dialog.tree.setCurrentItem(dialog.tree.topLevelItem(0))
                dialog._start_preview()
                self.assertTrue(
                    self._wait_for(app, dialog.preview_btn.isEnabled, 15),
                    dialog.log.toPlainText(),
                )
                self.assertFalse(dialog.preview_label.pixmap().isNull())

                dialog.start_conversion()
                self.assertTrue(
                    self._wait_for(app, dialog.convert_btn.isEnabled, 30),
                    dialog.log.toPlainText(),
                )
                self.assertFalse(dialog.failures, dialog.log.toPlainText())
                self.assertTrue(os.path.isfile(os.path.join(tmp, "beauty.rec709.mp4")))
                self.assertTrue(os.path.isfile(os.path.join(tmp, "beauty.rec709.mov")))
            finally:
                dialog.close()
            app.processEvents()

    def test_quick_conversion_runs_hidden_mov_only(self):
        app = QApplication.instance() or QApplication([])
        prism_root = os.environ["PRISM_TEST_ROOT"]
        oiiotool = os.path.join(
            prism_root, "PythonLibs", "Python3", "OpenImageIO", "bin", "oiiotool.exe"
        )
        with tempfile.TemporaryDirectory() as tmp:
            source = ""
            for frame in (1001, 1002):
                path = os.path.join(tmp, "quick.%04d.exr" % frame)
                result = subprocess.run([
                    oiiotool,
                    "--pattern", "constant:color=0.18,0.18,0.18", "64x64", "3",
                    "-d", "half", "-o", path,
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.assertEqual(result.returncode, 0)
                source = source or path

            dialog = OCIOConvertDialog(_Core(prism_root), initial_paths=[source])
            logs = []
            dialog.conversionFinished.connect(
                lambda result: logs.append(result.log.toPlainText())
            )
            self.assertFalse(dialog.isVisible())
            dialog.start_quick_conversion([".mov"])
            self.assertTrue(
                self._wait_for(app, lambda: bool(logs), 30),
                dialog.log.toPlainText(),
            )
            self.assertTrue(os.path.isfile(os.path.join(tmp, "quick.rec709.mov")))
            self.assertFalse(os.path.exists(os.path.join(tmp, "quick.rec709.mp4")))
            self.assertIn("prores_aw", logs[0])


if __name__ == "__main__":
    unittest.main()
