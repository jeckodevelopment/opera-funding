import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from catalog_reconciliation import reconcile_catalog_assessments, validate_catalog_assessments

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

    def test_unverified_eligibility_is_not_automatically_ineligible(self):
        row={"public_id":20,"eligibility":"da verificare"}
        reconcile_catalog_assessments([row])
        self.assertEqual(row["eligibility"],"da verificare")
        self.assertNotIn("application_eligibility_verified",row)

if __name__=="__main__":unittest.main()
