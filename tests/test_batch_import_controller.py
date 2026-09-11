import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))

try:
    from change_prism.batch_import.controller import BatchImportController
except Exception:
    BatchImportController = None


class _MediaProducts:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.identifier_call = None
        self.version_call = None
        self.highest_context = None

    def createIdentifier(self, entity, identifier, **kwargs):
        self.identifier_call = (entity, identifier, kwargs)

    def getHighestMediaVersion(self, context, getExisting=False):
        self.highest_context = dict(context)
        return "v0001"

    def createVersion(self, entity, identifier, version, **kwargs):
        self.version_call = (entity, identifier, version, kwargs)
        return self.output_dir


class _Paths:
    def __init__(self, root):
        self.root = root

    def getRenderProductBasePaths(self):
        return {"global": self.root}


class _Projects:
    def __init__(self, missing_path):
        self.missing_path = missing_path
        self.context = None

    def getResolvedProjectStructurePath(self, _key, context):
        self.context = dict(context)
        return self.missing_path


class _Core:
    def __init__(self, root, output_dir):
        self.mediaProducts = _MediaProducts(output_dir)
        self.paths = _Paths(root)
        self.projects = _Projects(os.path.join(root, "missing"))
        self.user = "tester"
        self.versionFormat = "v%04d"
        self.lowestVersion = 1


class _ShotEntities:
    def __init__(self):
        self.entity = {
            "type": "shot",
            "episode": "EP01",
            "sequence": "EP01",
            "shot": "SC01_shot001",
        }
        self.saved_metadata = None
        self.saved_range = None

    def getShots(self, sequence=None):
        del sequence
        return [dict(self.entity)]

    def setShotRange(self, _entity, start, end):
        self.saved_range = (start, end)

    @staticmethod
    def getMetaData(_entity):
        return {
            "artist_note": {"show": True, "value": "keep"},
        }

    def setMetaData(self, entity=None, metaData=None):
        del entity
        self.saved_metadata = dict(metaData)


class _ShotCore:
    def __init__(self):
        self.entities = _ShotEntities()


class _DepartmentProjects:
    def __init__(self):
        self.departments = None

    def setDepartments(self, _entity_type, departments):
        self.departments = departments


class _DepartmentCore:
    def __init__(self):
        self.projects = _DepartmentProjects()


class _ShotInfoCore:
    def __init__(self):
        self.saved = None

    @staticmethod
    def getConfig(**_kwargs):
        return {
            "shotRanges": {"EP01": {"SC01_shot001": [1001, 1100]}},
            "shots": {
                "EP01": {
                    "SC01_shot001": {
                        "metadata": {"unused": {"value": "remove"}}
                    }
                }
            },
        }

    def setConfig(self, **kwargs):
        self.saved = kwargs


class _ServerCore:
    projectName = "show"

    def __init__(self):
        self.popups = []

    def popup(self, message, **_kwargs):
        self.popups.append(message)


class _ServerItem:
    @staticmethod
    def data(*_args):
        return {
            "type": "shot",
            "sequence": "EP01",
            "shot": "SC01_shot001",
        }


@unittest.skipUnless(BatchImportController, "Requires Prism Qt runtime")
class BatchImportControllerTests(unittest.TestCase):
    def test_mov_ingest_keeps_flat_playblast_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = os.path.join(tmp, "review.mov")
            Path(source).write_bytes(b"mov")
            output_dir = os.path.join(tmp, "media", "v0001")
            core = _Core(tmp, output_dir)
            controller = BatchImportController(core, object())
            entity = {
                "type": "shot",
                "sequence": "EP01",
                "shot": "SQ01_shot001",
            }

            controller.file_processor.import_media_files(
                entity, [source]
            )

            self.assertEqual(core.mediaProducts.identifier_call[1], "review")
            self.assertEqual(
                core.mediaProducts.identifier_call[2]["identifierType"],
                "playblasts",
            )
            context = core.mediaProducts.highest_context
            self.assertEqual(context["sequence"], "EP01")
            self.assertEqual(context["identifier"], "review")
            self.assertEqual(context["mediaType"], "playblasts")
            self.assertNotIn("entity", context)
            self.assertTrue(os.path.isfile(os.path.join(output_dir, "review.mov")))
            self.assertEqual(
                controller.file_processor._increment_version(None),
                "v0002",
            )

    def test_existing_shot_updates_only_frame_range(self):
        core = _ShotCore()
        controller = BatchImportController(core, object())
        item = {
            "project_code": "show",
            "episode": "EP01",
            "sequence": "SC01",
            "shot": "shot001",
            "frame_range": [1001, 1100],
        }

        controller._create_single_shot(
            item,
            shots_cache={"EP01": [dict(core.entities.entity)]},
        )

        self.assertEqual(core.entities.saved_range, (1001, 1100))
        self.assertIsNone(core.entities.saved_metadata)

    def test_fx_department_and_task_are_distinct(self):
        core = _DepartmentCore()
        controller = BatchImportController(core, object())
        controller._set_project_departments()

        fx = next(
            department
            for department in core.projects.departments
            if department["abbreviation"] == "Fx"
        )
        self.assertEqual(fx["name"], "Fx")
        self.assertEqual(fx["defaultTasks"], ["Effects"])

    def test_shot_info_keeps_only_frame_ranges(self):
        core = _ShotInfoCore()
        controller = BatchImportController(core, object())
        controller._keep_only_shot_ranges()

        self.assertEqual(
            core.saved["data"],
            {
                "shotRanges": {
                    "EP01": {"SC01_shot001": [1001, 1100]}
                }
            },
        )

    def test_server_path_no_longer_depends_on_shot_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            expected = (
                Path(directory)
                / "show"
                / "publish"
                / "shot"
                / "EP01"
                / "SC01"
                / "shot001"
                / "review"
            )
            expected.mkdir(parents=True)
            core = _ServerCore()
            plugin = type("_Plugin", (), {})()
            controller = BatchImportController(core, plugin)

            with mock.patch(
                "change_prism.config.get_server_root",
                return_value=directory,
            ), mock.patch(
                "change_prism.batch_import.controller."
                "QDesktopServices.openUrl"
            ) as open_url:
                controller._open_server_subdir(
                    [_ServerItem()], "review"
                )

            self.assertEqual(open_url.call_count, 1)
            self.assertFalse(core.popups)


if __name__ == "__main__":
    unittest.main()
