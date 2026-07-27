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

    def test_process_removes_new_product_version_on_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            product = Path(directory) / "products" / "published_ref"
            processor = FileProcessor(_Core(product))
            with mock.patch.object(
                processor,
                "build_product_data",
                side_effect=OSError("copy failed"),
            ):
                with self.assertRaises(OSError):
                    processor.process(
                        {
                            "episode": "EP01",
                            "sequence": "SC01",
                            "shot": "shot001",
                        },
                        {"type": "shot"},
                        "show",
                        copy_to_local=True,
                    )

            self.assertFalse((product / "v0001").exists())

    def test_review_copy_failure_removes_only_files_created_by_run(self):
        processor = FileProcessor(_Core("unused"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.mov"
            source.write_bytes(b"review")
            missing = root / "missing.mov"
            destination_root = root / "review"
            destination_root.mkdir()
            first_destination = destination_root / "first.mov"
            protected_destination = destination_root / "protected.mov"
            protected_destination.write_bytes(b"existing")

            with self.assertRaises(FileNotFoundError):
                processor.execute_review_copies(
                    [
                        (str(source), str(first_destination)),
                        (
                            str(missing),
                            str(destination_root / "second.mov"),
                        ),
                    ]
                )

            self.assertFalse(first_destination.exists())
            self.assertEqual(
                protected_destination.read_bytes(), b"existing"
            )

            with self.assertRaises(FileExistsError):
                processor.execute_review_copies(
                    [(str(source), str(protected_destination))]
                )
            self.assertEqual(
                protected_destination.read_bytes(), b"existing"
            )

    def test_xml_context_redacts_personal_fields(self):
        entry = FileProcessor._make_step_entry(
            {},
            xml_path="description.xml",
            xml_attributes={
                "sequence_frame": 10,
                "user_name": "top-level artist",
                "context": {
                    "project_code": "show",
                    "user_phone": "secret",
                    "user_name": "artist",
                    "user_icon": "https://example.invalid/avatar",
                    "status_code": "inprogress",
                },
            },
            frame_range=[1001, 1010],
        )

        attributes = entry["xml"]["attributes"]
        self.assertEqual(attributes["project_code"], "show")
        self.assertEqual(
            attributes["context"]["status_code"], "inprogress"
        )
        self.assertNotIn("user_phone", attributes["context"])
        self.assertNotIn("user_name", attributes["context"])
        self.assertNotIn("user_icon", attributes["context"])
        self.assertNotIn("user_name", attributes)
