import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from qtpy.QtCore import QObject, Signal
    from qtpy.QtWidgets import (
        QApplication,
        QLabel,
        QStyle,
        QTabWidget,
        QWidget,
    )
    from change_prism.archive_browser.controller import (
        ArchiveBrowserController,
    )
    from change_prism.archive_browser.dialog import (
        ArchiveBrowserWidget,
        LazyArchiveBrowserWidget,
    )
    from change_prism.archive_core import file_fingerprint
    from change_prism.houdini_archive.dialog import (
        PackageConfirmDialog as HoudiniPackageConfirmDialog,
    )
    from change_prism.nuke_archive.service import (
        build_package_plan,
        execute_package,
    )
except Exception:
    QApplication = None
    ArchiveBrowserWidget = None
    LazyArchiveBrowserWidget = None


if QApplication:
    class _FakePage(QObject):
        itemChanged = Signal(object)


    class _FakeEntityWidget(QWidget):
        creation_count = 0

        def __init__(self, core=None, refresh=False, pages=None):
            super(_FakeEntityWidget, self).__init__()
            type(self).creation_count += 1
            self.entity = {
                "type": "shot",
                "sequence": "SC01",
                "shot": "shot0010",
            }
            self.page = _FakePage()
            self.refresh_count = 0

        def getPage(self, _name):
            return self.page

        def getCurrentData(self):
            return self.entity

        def navigate(self, entity):
            self.entity = entity

        def syncFromWidget(self, widget):
            self.entity = widget.getCurrentData()

        def refreshEntities(
            self,
            restoreSelection=False,
            defaultSelection=True,
        ):
            self.refresh_count += 1


    class _Core:
        def __init__(self, shot_path):
            self.shot_path = shot_path
            self.opened = []
            self.confirmation_result = "Cancel"

        def getEntityPath(self, entity=None):
            return self.shot_path

        def getIconForFileType(self, _extension):
            return QApplication.style().standardIcon(QStyle.SP_FileIcon)

        def openFile(self, path):
            self.opened.append(path)

        def popupQuestion(self, _message, **_kwargs):
            return self.confirmation_result

        def popup(self, _message, severity=None):
            return None


@unittest.skipUnless(QApplication, "Requires Prism Qt runtime")
class ArchiveBrowserUiTests(unittest.TestCase):
    def test_archive_rows_are_grouped_by_task_not_department(self):
        groups = ArchiveBrowserWidget._group_archive_versions(
            [
                {
                    "application": "houdini",
                    "department": "fx",
                    "task": "Fire",
                    "task_number": 1,
                    "created_at": "2026-01-01T00:00:00+08:00",
                },
                {
                    "application": "houdini",
                    "department": "another_department",
                    "task": "Fire",
                    "task_number": 2,
                    "created_at": "2026-01-02T00:00:00+08:00",
                },
            ]
        )
        self.assertEqual(len(groups), 1)
        self.assertEqual(
            [item["task_number"] for item in groups[0]], [2, 1]
        )

    def test_archive_entity_tree_is_created_only_when_tab_is_opened(self):
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            fake_module = types.SimpleNamespace(
                EntityWidget=_FakeEntityWidget
            )
            with mock.patch.dict(sys.modules, {"EntityWidget": fake_module}):
                _FakeEntityWidget.creation_count = 0

                class Origin(QWidget):
                    def __init__(self):
                        super(Origin, self).__init__()
                        self.tbw_project = QTabWidget(self)

                    def addTab(self, name, widget):
                        widget.setProperty("tabType", name)
                        self.tbw_project.addTab(widget, name)

                origin = Origin()
                controller = ArchiveBrowserController(_Core(tmp))
                controller.add_project_browser_tab(origin)
                widget = controller.browser_widget
                try:
                    self.assertIsInstance(
                        widget, LazyArchiveBrowserWidget
                    )
                    self.assertEqual(
                        widget.property("tabType"), "Archive"
                    )
                    self.assertEqual(_FakeEntityWidget.creation_count, 0)
                    widget.refresh_versions()
                    self.assertEqual(_FakeEntityWidget.creation_count, 0)
                    widget.entered()
                    self.assertEqual(_FakeEntityWidget.creation_count, 1)
                    self.assertEqual(
                        widget._browser.w_entities.refresh_count, 1
                    )
                    self.assertEqual(widget.refreshStatus, "valid")
                finally:
                    origin.close()
        app.processEvents()

    def test_houdini_preflight_table_shows_skipped_missing(self):
        app = QApplication.instance() or QApplication([])
        plan = {
            "source_hip": "scene.hip",
            "archive_root": "Archives",
            "proposed_version": "v0001",
            "houdini_version": "21.0.631",
            "hython_executable": "hython.exe",
            "version_warning": "",
            "estimated_total_bytes": 10,
            "estimated_file_count": 2,
            "available_bytes": None,
            "summary": {
                "reference_count": 1,
                "package_input_count": 0,
                "skipped_cache_count": 0,
                "skipped_missing_count": 1,
                "skipped_unsupported_count": 0,
                "hda_count": 0,
            },
            "dependencies": [
                {
                    "node_path": "/obj/missing_abc",
                    "parameter": "/obj/missing_abc/file",
                    "original_value": "/mnt/nas/project/missing.abc",
                    "classification": "Skipped Missing",
                    "status": "Missing (Skipped)",
                }
            ],
            "external_hdas": [],
        }
        dialog = HoudiniPackageConfirmDialog(plan)
        try:
            self.assertEqual(
                dialog.table.item(0, 3).text(), "Skipped Missing"
            )
            self.assertEqual(
                dialog.table.item(0, 4).text(), "Missing (Skipped)"
            )
            labels = [
                label.text() for label in dialog.findChildren(QLabel)
            ]
            self.assertTrue(
                any(
                    "1 unavailable /mnt/nas reference(s)" in text
                    for text in labels
                )
            )
        finally:
            dialog.close()
        app.processEvents()

    def test_entered_syncs_shot_selection_from_previous_tab(self):
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            fake_module = types.SimpleNamespace(
                EntityWidget=_FakeEntityWidget
            )
            with mock.patch.dict(sys.modules, {"EntityWidget": fake_module}):
                core = _Core(tmp)
                widget = ArchiveBrowserWidget(core)
                previous_entities = _FakeEntityWidget()
                previous_entities.entity = {
                    "type": "shot",
                    "sequence": "SC01",
                    "shot": "shot0510",
                }
                previous_tab = types.SimpleNamespace(
                    w_entities=previous_entities
                )
                try:
                    widget.w_entities.entity = None
                    widget.entered(prevTab=previous_tab)
                    self.assertEqual(
                        widget.getSelectedContext(),
                        previous_entities.entity,
                    )
                    self.assertEqual(
                        widget.status_label.text(),
                        os.path.join(tmp, "Archives"),
                    )

                    widget.refreshUI()
                    self.assertEqual(widget.w_entities.refresh_count, 1)
                    self.assertEqual(widget.refreshStatus, "valid")
                finally:
                    widget.close()
                    previous_entities.close()
        app.processEvents()

    def test_lists_legacy_nuke_and_houdini_and_opens_through_prism(self):
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shot = root / "shot0010"
            source_dir = root / "source"
            source_dir.mkdir()
            plate = source_dir / "plate.exr"
            plate.write_bytes(b"plate")
            nuke_scene_dir = (
                shot / "Scenefiles" / "cmp" / "Compositing"
            )
            nuke_scene_dir.mkdir(parents=True)
            nuke_scene = (
                nuke_scene_dir
                / "SC01-shot0010_Compositing_v0001.nk"
            )
            nuke_scene.write_text(
                "Root {\n inputs 0\n}\n"
                "Read {\n file %s\n name Read1\n}\n"
                % str(plate).replace("\\", "/"),
                encoding="utf-8",
            )
            execute_package(
                build_package_plan(nuke_scene, shot / "Archives")
            )

            houdini_source_dir = (
                shot / "Scenefiles" / "lgt" / "Lighting"
            )
            houdini_source_dir.mkdir(parents=True)
            houdini_source = (
                houdini_source_dir
                / "SC01-shot0010_Lighting_v0001.hip"
            )
            houdini_source.write_bytes(
                b"_HIP_SAVEVERSION = '21.0.631'"
            )
            version = shot / "Archives" / "v0002"
            hip_dir = version / "hip"
            hip_dir.mkdir(parents=True)
            packaged_hip = hip_dir / "scene_archive_v0002.hip"
            packaged_hip.write_bytes(b"archive")
            houdini_manifest = {
                        "schema_version": 2,
                        "application": "houdini",
                        "archive_version": "v0002",
                        "source_scene": str(houdini_source),
                        "source_scene_stat": file_fingerprint(
                            str(houdini_source)
                        ),
                        "packaged_scene": "hip/scene_archive_v0002.hip",
                        "created_by": "artist",
                        "created_at": "2099-07-24T12:00:00+08:00",
                        "houdini_version": "21.0.631",
                        "fps": 25,
                        "frame_range": [101, 790],
                        "dependencies": [
                            {
                                "node_path": "/obj/cache1",
                                "parameter": "/obj/cache1/file",
                                "original_value": "$HIP/cache.$F4.bgeo.sc",
                                "classification": "Skipped Cache",
                                "status": "Skipped",
                            },
                            {
                                "node_path": "/obj/missing_abc",
                                "parameter": "/obj/missing_abc/file",
                                "original_value": (
                                    "/mnt/nas/project/missing.abc"
                                ),
                                "classification": "Skipped Missing",
                                "status": "Missing (Skipped)",
                            },
                        ],
                        "external_hdas": [],
                        "copy_jobs": [],
                        "summary": {
                            "reference_count": 1,
                            "copy_job_count": 0,
                            "skipped_cache_count": 1,
                            "skipped_missing_count": 1,
                            "missing_count": 1,
                            "skipped_count": 2,
                            "hda_count": 0,
                            "file_count": 1,
                            "total_bytes": 7,
                        },
                    }
            (version / "manifest.json").write_text(
                json.dumps(houdini_manifest),
                encoding="utf-8",
            )

            latest_version = shot / "Archives" / "v0003"
            latest_version.mkdir()
            latest_packaged_hip = (
                latest_version / "scene_archive_v0003.hip"
            )
            latest_packaged_hip.write_bytes(b"latest archive")
            latest_manifest = dict(houdini_manifest)
            latest_manifest["archive_version"] = "v0003"
            latest_manifest["packaged_scene"] = (
                "scene_archive_v0003.hip"
            )
            latest_manifest["created_at"] = (
                "2099-07-24T13:00:00+08:00"
            )
            (latest_version / "manifest.json").write_text(
                json.dumps(latest_manifest),
                encoding="utf-8",
            )

            fake_module = types.SimpleNamespace(
                EntityWidget=_FakeEntityWidget
            )
            with mock.patch.dict(sys.modules, {"EntityWidget": fake_module}):
                core = _Core(str(shot))
                widget = ArchiveBrowserWidget(core)
                try:
                    widget.refresh_versions()
                    self.assertEqual(widget.table.columnCount(), 10)
                    self.assertEqual(widget.table.rowCount(), 2)
                    self.assertEqual(
                        widget.table.item(0, 1).text(), "Houdini"
                    )
                    self.assertEqual(
                        widget.table.item(0, 2).text(), "lgt"
                    )
                    self.assertEqual(
                        widget.table.item(0, 3).text(), "Lighting"
                    )
                    version_combo = widget.table.cellWidget(0, 0)
                    self.assertEqual(version_combo.count(), 2)
                    self.assertEqual(
                        version_combo.currentText(), "v0002"
                    )
                    self.assertEqual(
                        widget.open_scene_button.text(), "Open Houdini"
                    )
                    self.assertEqual(
                        widget.detail_values["skipped_cache_count"].text(),
                        "1",
                    )
                    self.assertEqual(
                        widget.detail_values["skipped_missing_count"].text(),
                        "1",
                    )
                    self.assertEqual(widget.mapping_table.rowCount(), 2)
                    self.assertEqual(
                        widget.mapping_table.item(1, 4).text(),
                        "Skipped Missing",
                    )
                    widget.open_selected_scene()
                    self.assertEqual(
                        core.opened, [str(latest_packaged_hip)]
                    )

                    version_combo.setCurrentIndex(1)
                    app.processEvents()
                    self.assertEqual(
                        version_combo.currentText(), "v0001"
                    )
                    widget.open_selected_scene()
                    self.assertEqual(core.opened[-1], str(packaged_hip))

                    widget.table.selectRow(1)
                    app.processEvents()
                    self.assertEqual(
                        widget.table.item(1, 2).text(), "cmp"
                    )
                    self.assertEqual(
                        widget.table.item(1, 3).text(), "Compositing"
                    )
                    self.assertEqual(
                        widget.open_scene_button.text(), "Open Nuke"
                    )
                    widget.open_selected_scene()
                    self.assertEqual(len(core.opened), 3)

                    widget.table.selectRow(0)
                    core.confirmation_result = "Delete Archive"
                    widget.table.cellWidget(0, 9).click()
                    self.assertFalse(version.exists())
                    self.assertEqual(widget.table.rowCount(), 2)
                    self.assertEqual(
                        widget.table.cellWidget(0, 0).currentText(),
                        "v0001",
                    )
                finally:
                    widget.close()
        app.processEvents()


if __name__ == "__main__":
    unittest.main()
