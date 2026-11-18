"""Regression tests: every discovered record receives an editorial assessment."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from fit import explain


class EditorialAssessmentTests(unittest.TestCase):
    def test_unclassified_funding_like_record_is_not_information_only(self):
        row = explain({
            "title": "Bando cultura e formazione",
            "opportunity_type": "non classificato",
            "relevance": 55,
        })
        self.assertEqual(row["assessment_label"], "MEDIA AFFINITÀ")
        self.assertIn("tipologia non è ancora accertata", row["assessment_reason"])

    def test_other_notice_is_informational(self):
        row = explain({
            "title": "Selezione del personale del teatro",
            "opportunity_type": "altro avviso",
            "relevance": 90,
        })
        self.assertEqual(row["assessment_label"], "INFORMATIVA")

    def test_unclassified_low_affinity_has_explicit_rating(self):
        row = explain({
            "title": "Bando generico",
            "opportunity_type": "non classificato",
            "relevance": 20,
        })
        self.assertEqual(row["assessment_label"], "BASSA AFFINITÀ")


if __name__ == "__main__":
    unittest.main()
