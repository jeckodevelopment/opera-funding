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

    def test_review_can_cite_primary_source_when_catalog_uses_aggregator(self):
        row={"url":"https://aggregator.example/bandi/one?ref=rss","source_id":"volto"}
        review={"source_id":"volto","url":"https://aggregator.example/bandi/one",
                "evidence_url":"https://issuer.example/official-bando",
                "assessment_label":"MEDIA AFFINITÀ","reviewed_at":"2026-11-18"}
        result=apply_assessment_reviews([row],[review])[0]
        self.assertEqual(result["assessment_source"],"https://issuer.example/official-bando")

    def test_open_catalog_snapshot_has_individual_review(self):
        import json
        root=Path(__file__).resolve().parents[1]
        catalog=json.loads((root/"data/opportunities.json").read_text(encoding="utf-8"))
        reviews=json.loads((root/"config/assessment_reviews.json").read_text(encoding="utf-8"))
        reviewed={(x["source_id"],x["url"].split("?")[0].rstrip("/")) for x in reviews}
        missing=[str(x.get("public_id")) for x in catalog
                 if x.get("funding_status")=="APERTO"
                 and (x.get("source_id"),x.get("url","").split("?")[0].rstrip("/")) not in reviewed]
        self.assertFalse(missing,"Open opportunities with no evidence review: "+", ".join(missing))

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
