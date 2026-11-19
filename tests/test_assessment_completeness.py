import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from catalog_reconciliation import (reconcile_catalog_assessments, validate_catalog_assessments,
                                    annotate_requirement_coverage, summarize_requirement_coverage)

class AssessmentCompletenessTests(unittest.TestCase):
    def test_existing_judgement_is_preserved(self):
        row={"public_id":1,"adequacy_label":"MEDIA","adequacy_level":2,
             "adequacy_reason":"Coerenza culturale","assessment_reason":"Attività educative"}
        self.assertEqual(reconcile_catalog_assessments([row]),0)
        self.assertEqual(row["adequacy_label"],"MEDIA")
        self.assertNotIn("assessment_fallback",row)

    def test_incomplete_opportunity_gets_low_rating_and_remains_in_catalog(self):
        rows=[{"public_id":17,"adequacy_label":"MEDIA","adequacy_reason":"Preliminare",
               "funding_status":"APERTO","url":"https://example.org/grant"}]
        self.assertEqual(validate_catalog_assessments(rows),1)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["adequacy_label"],"BASSA")
        self.assertEqual(rows[0]["adequacy_level"],1)
        self.assertTrue(rows[0]["assessment_fallback"])
        self.assertIn("prudenziale",rows[0]["assessment_reason"])
        self.assertEqual(rows[0]["funding_status"],"APERTO")
        self.assertEqual(rows[0]["url"],"https://example.org/grant")

    def test_informational_record_remains_informational(self):
        row={"public_id":19,"opportunity_type":"altro avviso"}
        reconcile_catalog_assessments([row])
        self.assertEqual(row["adequacy_label"],"INFORMATIVA")
        self.assertTrue(row["adequacy_reason"])

    def test_all_records_are_retained_and_mixed_ratings_allowed(self):
        rows=[{"id":"a"}, {"id":"b","adequacy_label":"ALTA",
               "adequacy_reason":"Progetto coerente","assessment_reason":"Attività ammesse"}]
        self.assertEqual(reconcile_catalog_assessments(rows),1)
        self.assertEqual(len(rows),2)
        self.assertEqual([r["adequacy_label"] for r in rows],["BASSA","ALTA"])

    def test_reconcile_full_catalog_without_inventing_requirements(self):
        rows=[
            {"public_id":1,"funding_status":"APERTO","adequacy_label":"MEDIA",
             "applicant_requirement_comparison":[
                 {"status":"da_verificare","requirement":"Sede in Piemonte",
                  "source":"https://official.example/call"}]},
            {"public_id":2,"funding_status":"APERTO","adequacy_label":"BASSA",
             "requirements_excerpt":"Beneficiari da confermare",
             "applicant_requirement_comparison":[]},
            {"public_id":3,"funding_status":"CHIUSO","opportunity_type":"altro avviso"},
            {"public_id":4,"funding_status":"APERTO","adequacy_label":"BASSA",
             "direct_application_blocker":"Registro obbligatorio mancante"},
        ]
        for row in rows: annotate_requirement_coverage(row)
        report=summarize_requirement_coverage(rows)
        self.assertEqual(report["coverage"]["catalogo"]["total"],4)
        self.assertEqual(sum(report["coverage"]["catalogo"]["coverage_status_counts"].values()),4)
        self.assertEqual(report["coverage"]["aperte"]["requirements_compared"],1)
        self.assertEqual(report["coverage"]["aperte_alta_media"]["total"],1)
        self.assertEqual([r["public_id"] for r in report[
            "open_without_comparable_requirements"]],[2])
        self.assertEqual(rows[1]["requirement_coverage_status"],"senza_requisiti_confrontabili")
        self.assertEqual(rows[3]["requirement_coverage_status"],"ostacolo_documentato")

    def test_informative_editorial_review_has_no_grant_coverage(self):
        row={"public_id":270,"funding_status":"APERTO",
             "opportunity_type":"finanziamento potenziale",
             "adequacy_label":"INFORMATIVA",
             "applicant_requirement_comparison":[]}
        annotate_requirement_coverage(row)
        self.assertEqual(row["requirement_coverage_status"],"avviso_informativo")

    def test_unverified_eligibility_is_not_automatically_ineligible(self):
        row={"public_id":20,"eligibility":"da verificare"}
        reconcile_catalog_assessments([row])
        self.assertEqual(row["eligibility"],"da verificare")
        self.assertNotIn("application_eligibility_verified",row)

if __name__=="__main__":unittest.main()
