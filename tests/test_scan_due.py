import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from scan_due import should_run


class ScheduledScanFreshnessTests(unittest.TestCase):
    def test_scheduled_scan_skips_when_success_already_today_in_rome(self):
        report={"checked_at":"2026-11-20T05:50:00+00:00"}
        now=datetime(2026,11,20,7,20,tzinfo=timezone.utc)
        self.assertFalse(should_run("schedule",report,now))

    def test_scheduled_scan_runs_when_yesterday_even_if_late_utc(self):
        report={"checked_at":"2026-11-19T15:54:37+00:00"}
        now=datetime(2026,11,20,7,15,tzinfo=timezone.utc)
        self.assertTrue(should_run("schedule",report,now))

    def test_day_boundary_uses_rome_not_utc(self):
        report={"checked_at":"2026-11-19T23:30:00+00:00"}
        now=datetime(2026,11,20,6,23,tzinfo=timezone.utc)
        self.assertFalse(should_run("schedule",report,now))

    def test_summer_day_boundary_and_dst(self):
        report={"checked_at":"2026-07-19T22:30:00+00:00"}
        now=datetime(2026,7,20,6,23,tzinfo=timezone.utc)
        self.assertFalse(should_run("schedule",report,now))

    def test_invalid_or_missing_report_fails_open(self):
        now=datetime(2026,11,20,6,23,tzinfo=timezone.utc)
        for report in ({},{"checked_at":"bogus"},{"checked_at":None},None):
            self.assertTrue(should_run("schedule",report,now))

    def test_push_and_manual_dispatch_are_never_skipped(self):
        report={"checked_at":"2026-11-20T06:05:00+00:00"}
        now=datetime(2026,11,20,6,23,tzinfo=timezone.utc)
        for event in ("push","workflow_dispatch"):
            self.assertTrue(should_run(event,report,now))

    def test_yaml_has_staggered_windows_gate_and_integrity(self):
        yml=(Path(__file__).resolve().parents[1]/".github/workflows/scan.yml").read_text(encoding="utf-8")
        for t in ("'41 5 * * *'","'23 6 * * *'","'11 7 * * *'"):
            self.assertIn(t,yml)
        self.assertIn("group: funding-scan",yml)
        self.assertLess(yml.index("git reset --hard origin/main"),
                        yml.index("python src/scan_due.py"))
        self.assertLess(yml.index("python src/scan_due.py"),
                        yml.index("python src/scan.py"))
        self.assertIn("if: steps.due.outputs.run_scan == 'true'",yml)
        self.assertLess(yml.index("run: python src/scan_integrity.py"),
                        yml.index("run: python src/notify.py"))


if __name__=="__main__":
    unittest.main()
