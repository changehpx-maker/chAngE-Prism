import tempfile
import unittest
from pathlib import Path
from unittest import mock

from change_prism.batch_import.file_processor import FileProcessor


class _Products:
    def __init__(self, root):
        self.root = str(root)

    def createProduct(self, _entity, _product):
        return self.root

    @staticmethod
    def getNextAvailableVersion(_entity, _product):
        return "v0001"


class _Entities:
    range = None
    metadata = {}

    def setShotRange(self, _entity, start, end):
        self.range = (start, end)

    def getMetaData(self, _entity):
        return {}

    def setMetaData(self, entity=None, metaData=None):
        del entity
        self.metadata = metaData


class _Media:
    def createIdentifier(self, *args, **kwargs):
        pass

    def getHighestMediaVersion(self, *args, **kwargs):
        return "v0001"

    def createVersion(self, *args, **kwargs):
        return ""


class _Core:
    def __init__(self, root):
        self.products = _Products(root)
        self.entities = _Entities()
        self.mediaProducts = _Media()
        self.username = "tester"
        self.user = "tester"
        self.saved = None

    def saveVersionInfo(self, filepath, details):
        self.saved = (filepath, details)


class FileProcessorTests(unittest.TestCase):
    def test_process_records_product_version_and_normalized_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            product = root / "products" / "published_ref"
            server = root / "server" / "shot001"
            fbx = (
                server
                / "shot_motion"
                / "shot_animation"
                / "fbx"
                / "camera.fbx"
            )
            fbx.parent.mkdir(parents=True)
            fbx.touch()
            item = {
                "episode": "EP01",
                "sequence": "SC01",
                "shot": "shot001",
                "server_dir": str(server),
                "frame_range": [1001, 1100],
                "steps": [
                    {
                        "label": "Animation",
                        "files": {"fbx_files": [str(fbx)]},
                    }
                ],
            }
            core = _Core(product)
            data = FileProcessor(core).process(
                item,
                {
                    "type": "shot",
                    "sequence": "EP01",
                    "shot": "SC01_shot001",
                },
                "show",
                copy_to_local=False,
            )

        self.assertEqual(data["product_version"], "v0001")
        self.assertEqual(data["steps"]["Animation"]["fbx"], [str(fbx)])
        self.assertEqual(
            core.saved[1]["products_path"],
            str(product / "v0001"),
        )

    def test_copy_to_local_retargets_file_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            product = root / "products" / "published_ref"
            server = root / "server" / "shot001"
            fbx = (
                server
                / "shot_motion"
                / "shot_animation"
                / "fbx"
                / "camera.fbx"
            )
            fbx.parent.mkdir(parents=True)
            fbx.touch()
            item = {
                "episode": "EP01",
                "sequence": "SC01",
                "shot": "shot001",
                "server_dir": str(server),
                "steps": [],
            }
            data = FileProcessor(_Core(product)).process(
                item, {"type": "shot"}, "show", copy_to_local=True
            )

        self.assertEqual(
            data["source_file_root"], str(product / "v0001")
        )
        self.assertTrue(
            data["steps"]["Animation"]["fbx"][0].endswith(
                "camera.fbx"
            )
        )

    def test_copy_reuses_scanned_paths_without_rescanning_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            product = root / "products" / "published_ref"
            server = root / "server" / "shot001"
            source = (
                server
                / "shot_motion"
                / "shot_animation"
                / "fbx"
                / "camera.fbx"
            )
            source.parent.mkdir(parents=True)
            source.write_bytes(b"fbx")
            item = {
                "episode": "EP01",
                "sequence": "SC01",
                "shot": "shot001",
                "server_dir": str(server),
                "frame_range": [1001, 1100],
                "steps": [
                    {
                        "label": "Animation",
                        "files": {"fbx_files": [str(source)]},
                    }
                ],
            }

            with mock.patch(
                "change_prism.batch_import.file_processor.collect_step_files",
                side_effect=AssertionError("unexpected rescan"),
            ):
                data = FileProcessor(_Core(product)).process(
                    item,
                    {"type": "shot"},
                    "show",
                    copy_to_local=True,
                )

            copied = data["steps"]["Animation"]["fbx"][0]
            self.assertTrue(Path(copied).is_file())
            self.assertTrue(
                copied.startswith(str(product / "v0001"))
            )
