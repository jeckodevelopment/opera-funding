import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from assessment_reviews import apply_assessment_reviews
from verification import pick_for_review

class ReviewedAssessmentTests(unittest.TestCase):
    def test_persist_explicit_review_without_changing_open_state(self):
        url="https://example.org/opportunities/a"
        row={"url":url,"source_id":"issuer","title":"Progetto", "funding_status":"APERTO","assessment_label":"ALTA AFFINITÀ"}
        review={"source_id":"issuer","url":url,"assessment_label":"BASSA AFFINITÀ",
                "assessment_reason":"Non corrisponde alle attività","reviewed_at":"2026-11-18"}
        result=apply_assessment_reviews([row],[review])[0]
        self.assertEqual(result["assessment_label"],"BASSA AFFINITÀ")
        self.assertEqual(result["funding_status"],"APERTO")
        self.assertEqual(result["assessment_source"],url)

    def test_unclassified_records_are_assessed_in_queue(self):
        record={"id":"x","title":"Grant","relevance":65,
                "opportunity_type":"non classificato","funding_status":"APERTO"}
        self.assertEqual(pick_for_review([record],{},1),{"x"})

    def test_different_host_does_not_inherit_review(self):
        row={"url":"https://example.org/bando","source_id":"a"}
        review={"source_id":"a","url":"https://another.org/bando","assessment_label":"MEDIA AFFINITÀ",
                "reviewed_at":"2026-11-18"}
        self.assertNotIn("assessment_label",apply_assessment_reviews([row],[review])[0])

if __name__=="__main__":
    unittest.main()
