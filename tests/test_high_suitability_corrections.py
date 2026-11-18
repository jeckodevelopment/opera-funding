"""Prevent false high suitability for recently founded association."""
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from assessment_reviews import apply_assessment_reviews
from adequacy import apply_adequacy
from operational_assessment import annotate_operational_assessment

ROOT=Path(__file__).resolve().parents[1]
REVIEWS=json.loads((ROOT/"config/assessment_reviews.json").read_text(encoding="utf-8"))
CASES={
    149:("volto","https://infobandi.csvnet.it/supporto-a-organizzazioni-della-societa-civile-per-promuovere-i-valori-dellue/?utm_source=rss&utm_medium=rss&utm_campaign=supporto-a-organizzazioni-della-societa-civile-per-promuovere-i-valori-dellue","BASSA"),
    183:("sanpaolo","https://www.compagniadisanpaolo.it/it/contributi/buoni-formazione-per-la-cultura/","MEDIA")
}

class HighSuitabilityCorrectionTests(unittest.TestCase):
    def test_documented_conditions_avoid_high_label(self):
        for ident,(source,url,expected) in CASES.items():
            with self.subTest(ident=ident):
                row={"public_id":ident,"source_id":source,"url":url,
                     "opportunity_type":"finanziamento potenziale","funding_status":"APERTO"}
                apply_assessment_reviews([row],REVIEWS)
                self.assertTrue(row.get("assessment_reviewed_at"))
                self.assertTrue(row["funded_activities_excerpt"])
                self.assertTrue(row["beneficiaries_excerpt"])
                self.assertTrue(row["requirements_excerpt"])
                apply_adequacy(row)
                annotate_operational_assessment(row)
                self.assertEqual(row["adequacy_label"],expected)
                self.assertFalse(row["application_eligibility_verified"])
                self.assertTrue(row["application_next_actions"])

    def test_cerv_funding_to_intermediaries_not_local_direct_grant(self):
        entry=next(x for x in REVIEWS if x.get("public_id")==149)
        self.assertIn("2,5",entry["requirements_excerpt"])
        self.assertIn("3 anni",entry["requirements_excerpt"])
        self.assertIn("a cascata",entry["assessment_reason"])

    def test_training_voucher_not_public_cultural_courses(self):
        entry=next(x for x in REVIEWS if x.get("public_id")==183)
        self.assertIn("dipendenti",entry["beneficiaries_excerpt"])
        self.assertIn("pubblico",entry["assessment_reason"])
        self.assertIn("compagniadisanpaolo.it",entry["evidence_url"])

if __name__=="__main__":
    unittest.main()
