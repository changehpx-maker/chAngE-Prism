import io
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))

from change_prism.houdini_archive import cli


def _plan():
    return {
        "source_hip": "scene.hip",
        "archive_root": "Archives",
        "proposed_version": "v0001",
        "houdini_version": "21.0.631",
        "hython_executable": "hython.exe",
        "version_warning": "",
        "estimated_total_bytes": 10,
        "estimated_file_count": 2,
        "summary": {
            "reference_count": 4,
            "package_input_count": 2,
            "skipped_cache_count": 1,
            "skipped_missing_count": 1,
            "skipped_unsupported_count": 1,
        },
    }


class HoudiniArchiveCliTests(unittest.TestCase):
    def test_yes_executes_and_returns_zero(self):
        output = io.StringIO()
        with mock.patch.object(
            cli, "build_package_plan", return_value=_plan()
        ), mock.patch.object(
            cli,
            "execute_package",
            return_value={
                "version": "v0001",
                "version_path": "Archives/v0001",
            },
        ) as execute:
            code = cli.main(
                [
                    "scene.hip",
                    "--archive-root",
                    "Archives",
                    "--yes",
                ],
                output=output,
            )
        self.assertEqual(code, 0)
        execute.assert_called_once()
        self.assertIn("Created v0001", output.getvalue())
        self.assertIn(
            "1 unavailable /mnt/nas reference(s)",
            output.getvalue(),
        )

    def test_declined_confirmation_returns_two(self):
        output = io.StringIO()
        with mock.patch.object(
            cli, "build_package_plan", return_value=_plan()
        ), mock.patch.object(cli, "execute_package") as execute:
            code = cli.main(
                ["scene.hip", "--archive-root", "Archives"],
                input_func=lambda _prompt: "n",
                output=output,
            )
        self.assertEqual(code, 2)
        execute.assert_not_called()

    def test_preflight_failure_returns_one(self):
        output = io.StringIO()
        with mock.patch.object(
            cli,
            "build_package_plan",
            side_effect=cli.ArchiveError("missing input"),
        ):
            code = cli.main(
                [
                    "scene.hip",
                    "--archive-root",
                    "Archives",
                    "--yes",
                ],
                output=output,
            )
        self.assertEqual(code, 1)
        self.assertIn("missing input", output.getvalue())


if __name__ == "__main__":
    unittest.main()
