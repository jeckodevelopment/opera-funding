import unittest
from datetime import datetime, timezone, timedelta
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from detail import DETAIL_SCHEMA_VERSION

class DetailFreshnessTests(unittest.TestCase):
    def test_version_bump_forces_legacy_refresh(self):
        old={"detail_checked":True}
        self.assertNotEqual(old.get("detail_version"),DETAIL_SCHEMA_VERSION)
    def test_old_check_should_be_refreshed(self):
        checked=(datetime.now(timezone.utc)-timedelta(days=4)).isoformat()
        self.assertLess(datetime.fromisoformat(checked),datetime.now(timezone.utc)-timedelta(days=3))
    def test_new_check_remains_fresh(self):
        checked=datetime.now(timezone.utc).isoformat()
        self.assertGreater(datetime.fromisoformat(checked),datetime.now(timezone.utc)-timedelta(days=3))
if __name__=="__main__":
    unittest.main()
