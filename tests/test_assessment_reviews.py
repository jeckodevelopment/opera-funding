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

    def test_every_open_record_has_a_reasoned_editorial_assessment(self):
        # The open set changes after each discovery; it cannot be hard-coded
        # to the finite set of manually reviewed URLs.
        import json
        root=Path(__file__).resolve().parents[1]
        catalog=json.loads((root/"data/opportunities.json").read_text(encoding="utf-8"))
        unrated=[str(x.get("public_id")) for x in catalog
                 if x.get("funding_status")=="APERTO"
                 and (not x.get("assessment_label") or not x.get("assessment_reason"))]
        self.assertFalse(unrated,"Open grants missing editorial assessment: "+", ".join(unrated))

    def test_unclassified_records_are_assessed_in_queue(self):
        record={"id":"x","title":"Grant","relevance":65,
                "opportunity_type":"non classificato","funding_status":"APERTO"}
        self.assertEqual(pick_for_review([record],{},1),{"x"})

    def test_stable_id_reconciles_review_after_source_url_changes(self):
        row={"public_id":146,"url":"https://aggregator.example/new-edition","source_id":"volto","title":"Bando"}
        review={"public_id":146,"source_id":"volto","url":"https://another.example/old-edition",
                "assessment_label":"MEDIA AFFINITÀ","reviewed_at":"2026-11-18"}
        result=apply_assessment_reviews([row],[review])[0]
        self.assertEqual(result["assessment_label"],"MEDIA AFFINITÀ")

    def test_generic_button_title_replaced_with_documented_name(self):
        row={"public_id":183,"url":"https://example.org/bando","source_id":"issuer","title":"SCOPRI IL BANDO"}
        review={"public_id":183,"source_id":"issuer","url":"https://example.org/bando",
                "catalog_title":"Buoni formazione per la cultura","reviewed_at":"2026-11-18"}
        self.assertEqual(apply_assessment_reviews([row],[review])[0]["title"],"Buoni formazione per la cultura")

    def test_seven_priority_calls_have_current_documented_assessments(self):
        import json
        from adequacy import apply_adequacy
        reviews=json.loads((Path(__file__).resolve().parents[1]/"config/assessment_reviews.json").read_text(encoding="utf-8"))
        expected={176:"BASSA",23:"MEDIA",182:"BASSA",183:"MEDIA",19:"BASSA",143:"BASSA",255:"BASSA"}
        blocked={176,182,19,143}
        for number,label in expected.items():
            with self.subTest(public_id=number):
                record=next(r for r in reviews if r.get("public_id")==number)
                self.assertEqual(record["reviewed_at"],"2026-11-19")
                self.assertTrue(record.get("evidence_url","").startswith("https://"))
                self.assertTrue(record.get("requirements_excerpt"))
                self.assertTrue(record.get("assessment_gaps"))
                row={"source_id":record["source_id"],"url":record["url"],"public_id":number,
                     "opportunity_type":"finanziamento potenziale","funding_status":"APERTO",
                     "applicant_requirement_comparison":[]}
                result=apply_assessment_reviews([row],reviews)[0]
                apply_adequacy(result)
                self.assertEqual(result["adequacy_label"],label)
                self.assertEqual(bool(result.get("direct_application_blocker")),number in blocked)
                self.assertEqual(result["funding_status"],"APERTO")

    def test_official_allianz_review_does_not_invent_local_seat_or_minimum_age(self):
        import json
        reviews=json.loads((Path(__file__).resolve().parents[1]/"config/assessment_reviews.json").read_text(encoding="utf-8"))
        record=next(r for r in reviews if r.get("public_id")==255)
        self.assertEqual(record["source_id"],"volto")
        self.assertIn("umanamente.allianz.it",record["evidence_url"])
        self.assertNotIn("comune di",record["requirements_excerpt"].lower())
        self.assertNotIn("almeno due anni",record["requirements_excerpt"].lower())

    def test_documented_festival_first_edition_blocker_is_applied(self):
        import json
        root=Path(__file__).resolve().parents[1]
        review=next(x for x in json.loads((root/"config/assessment_reviews.json").read_text(encoding="utf-8"))
                    if x.get("public_id")==190)
        row={"public_id":190,"source_id":review["source_id"],"url":review["url"],
             "title":"Festival partecipativi 2027","funding_status":"APERTO"}
        out=apply_assessment_reviews([row],[review])[0]
        self.assertEqual(out["assessment_label"],"BASSA AFFINITÀ")
        self.assertIn("prime edizioni",out["assessment_reason"])\n        self.assertIn("precedente",out["direct_application_blocker"])
        self.assertTrue(out["assessment_evidence_source"].startswith("https://"))

    def test_circ7_conditions_are_supported_by_official_pdf(self):
        import json
        root=Path(__file__).resolve().parents[1]
        review=next(x for x in json.loads((root/"config/assessment_reviews.json").read_text(encoding="utf-8"))
                    if x.get("public_id")==8)
        self.assertIn("comunità locale",review["beneficiaries_excerpt"])
        self.assertIn("26 novembre 2026",review["requirements_excerpt"])
        self.assertTrue(review["evidence_url"].endswith("13_Avviso_Eventi_Culturali_2027.pdf"))

    def test_different_host_does_not_inherit_review(self):
        row={"url":"https://example.org/bando","source_id":"a"}
        review={"source_id":"a","url":"https://another.org/bando","assessment_label":"MEDIA AFFINITÀ",
                "reviewed_at":"2026-11-18"}
        self.assertNotIn("assessment_label",apply_assessment_reviews([row],[review])[0])

if __name__=="__main__":
    unittest.main()
