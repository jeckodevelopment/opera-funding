"""Changes to eligibility modules must trigger a catalog rescan on main."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=ROOT/".github/workflows/scan.yml"

class ScanTriggerTests(unittest.TestCase):
    def test_all_eligibility_dependencies_trigger_scan(self):
        yaml=WORKFLOW.read_text(encoding="utf-8")
        required=(
            "src/adequacy.py",
            "src/eligibility_conditions.py",
            "src/eligibility_specific.py",
            "src/applicant_comparison.py",
            "src/open_review_queue.py",
            "config/applicant_profile.json",
            "src/assessment_coverage.py",
            "src/assessment_reviews.py",
            "src/scan.py",
        )
        for path in required:
            with self.subTest(path=path):
                self.assertIn("- '"+path+"'",yaml)

    def test_scan_is_runnable_manually_and_daily(self):
        yaml=WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:",yaml)
        self.assertIn("schedule:",yaml)
        self.assertIn("python src/scan.py",yaml)
        self.assertIn("data/scan-status.json",yaml)

if __name__=="__main__":
    unittest.main()
