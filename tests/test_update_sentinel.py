import unittest
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import update_sentinel


class TestUpdateSentinel(unittest.TestCase):
    def test_parse_semver(self):
        self.assertEqual(update_sentinel.parse_semver("2.1.1"), (2, 1, 1))
        self.assertEqual(update_sentinel.parse_semver("v2.10.0"), (2, 10, 0))
        self.assertTrue(update_sentinel.parse_semver("2.2.0") > update_sentinel.parse_semver("2.1.1"))
        self.assertTrue(update_sentinel.parse_semver("3.0.0") > update_sentinel.parse_semver("2.9.9"))

    def test_get_local_version(self):
        ver = update_sentinel.get_local_version()
        self.assertTrue(isinstance(ver, str))
        self.assertTrue(len(ver.split(".")) >= 2)

    def test_check_cache_rw(self):
        test_data = {"test_key": "val", "last_check_timestamp": 12345}
        orig_cache_file = update_sentinel.CACHE_FILE
        test_cache = os.path.join(TOOLS_DIR, "test_cache_tmp.json")
        try:
            update_sentinel.CACHE_FILE = test_cache
            update_sentinel.write_update_cache(test_data)
            read_back = update_sentinel.read_update_cache()
            self.assertEqual(read_back.get("test_key"), "val")
        finally:
            update_sentinel.CACHE_FILE = orig_cache_file
            if os.path.exists(test_cache):
                os.remove(test_cache)


if __name__ == "__main__":
    unittest.main()
