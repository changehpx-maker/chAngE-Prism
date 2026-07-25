import os
import sys
import tempfile
import unittest
from pathlib import Path


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

            controller._ingest_mov_as_media(entity, [source])

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
            self.assertEqual(controller._increment_version(None), "v0002")


if __name__ == "__main__":
    unittest.main()
