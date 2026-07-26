import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))

from change_prism import heavy_jobs


class HeavyJobTests(unittest.TestCase):
    def tearDown(self):
        heavy_jobs._ACTIVE_JOBS.clear()

    def test_group_allows_one_owner_until_release(self):
        first = object()
        second = object()
        self.assertTrue(heavy_jobs.acquire("archive_package", first))
        self.assertTrue(heavy_jobs.acquire("archive_package", first))
        self.assertFalse(heavy_jobs.acquire("archive_package", second))
        heavy_jobs.release("archive_package", second)
        self.assertTrue(heavy_jobs.is_active("archive_package"))
        heavy_jobs.release("archive_package", first)
        self.assertTrue(heavy_jobs.acquire("archive_package", second))


if __name__ == "__main__":
    unittest.main()
