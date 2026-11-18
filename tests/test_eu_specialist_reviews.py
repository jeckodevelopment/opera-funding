"""Regressions: specialised EU calls are not generic opera education grants."""
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
  116:("eufunding","https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/CREA-MEDIA-2027-DEVVGIM"),
  34:("eucreative","https://culture.ec.europa.eu/funding/calls/circulation-of-european-literary-works-5"),
  114:("eufunding","https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/CREA-MEDIA-2027-CODEV"),
  115:("eufunding","https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/CREA-MEDIA-2027-DEVSLATE"),
  117:("eufunding","https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/CREA-MEDIA-2027-FILMOVE"),
}

class EuEditorialReviewsTests(unittest.TestCase):
    def test_all_five_have_documented_restrictions_and_noncertified_low_priority(self):
        for ident,(source,url) in CASES.items():
            with self.subTest(ident=ident):
                row={"public_id":ident,"source_id":source,"url":url,
                     "funding_status":"APERTO","opportunity_type":"finanziamento potenziale"}
                apply_assessment_reviews([row],REVIEWS)
                self.assertTrue(row.get("assessment_reviewed_at"))
                self.assertTrue(row.get("assessment_gaps"))
                self.assertTrue(str(row.get("assessment_source")).startswith("https://"))
                for field in ("programme_objectives_excerpt","funded_activities_excerpt",
                              "beneficiaries_excerpt","requirements_excerpt"):
                    self.assertTrue(row.get(field),field)
                apply_adequacy(row)
                annotate_operational_assessment(row)
                self.assertEqual(row["adequacy_label"],"BASSA")
                self.assertEqual(row["application_path"],"bassa_priorita_progettuale")
                self.assertFalse(row["application_eligibility_verified"])

    def test_not_relabeling_specialist_film_calls_as_general_cultural_courses(self):
        for ident in (116,114,115,117):
            entry=next(x for x in REVIEWS if x.get("public_id")==ident)
            self.assertIn("audiovisiv",entry["assessment_reason"].lower()+
                          " "+entry["programme_objectives_excerpt"].lower()+
                          " "+entry["requirements_excerpt"].lower()) if ident!=116 else self.assertIn("videogiochi",entry["assessment_reason"].lower())

if __name__=="__main__":
    unittest.main()
