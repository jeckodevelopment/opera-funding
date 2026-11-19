"""Source-based corrections for five priority calls and Opera+ applicability.

Allianz 2026 is a legitimate open call but Opera+ lacks demonstrated sector experience
and financial/operational capability: editorial suitability stays LOW, not legal exclusion.
"""
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
CALLS={
113:("eufunding","https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/CREA-MEDIA-2027-AUDFILMEDU","BASSA"),
146:("volto","https://infobandi.csvnet.it/bando-una-mano-a-chi-sostiene-nuova-edizione-2026-27/","MEDIA"),
148:("volto","https://infobandi.csvnet.it/erase-indifference-challenge-2026/?utm_source=rss&utm_medium=rss&utm_campaign=erase-indifference-challenge-2026","BASSA"),
254:("volto","https://infobandi.csvnet.it/bando-2027-del-fondo-nazionale-per-la-rievocazione-storica/?utm_source=rss&utm_medium=rss&utm_campaign=bando-2027-del-fondo-nazionale-per-la-rievocazione-storica","BASSA"),
255:("volto","https://infobandi.csvnet.it/call-for-ideas-2026-di-fondazione-allianz-umanamente/?utm_source=rss&utm_medium=rss&utm_campaign=call-for-ideas-2026-di-fondazione-allianz-umanamente","BASSA"),
}

class PriorityGrantReviewsTests(unittest.TestCase):
    def test_evidence_changes_grade_without_certifying_applicant(self):
        for identifier,(source,url,expected) in CALLS.items():
            with self.subTest(identifier=identifier):
                row={"public_id":identifier,"source_id":source,"url":url,
                     "opportunity_type":"finanziamento potenziale",
                     "funding_status":"APERTO"}
                apply_assessment_reviews([row],REVIEWS)
                self.assertTrue(row.get("assessment_reviewed_at"))
                for field in ("beneficiaries_excerpt","requirements_excerpt",
                              "funded_activities_excerpt","programme_objectives_excerpt"):
                    self.assertTrue(row.get(field),field)
                apply_adequacy(row)
                annotate_operational_assessment(row)
                self.assertEqual(row["adequacy_label"],expected)
                self.assertFalse(row["application_eligibility_verified"])
                self.assertTrue(row["application_next_actions"])

    def test_five_year_history_excludes_new_association_rievocazione(self):
        entry=next(x for x in REVIEWS if x.get("public_id")==254)
        self.assertIn("cinque anni",entry["requirements_excerpt"])
        self.assertIn("spettacolo.cultura.gov.it",entry["evidence_url"])

    def test_catholic_fund_has_real_cofinancing_and_delayed_reimbursement(self):
        entry=next(x for x in REVIEWS if x.get("public_id")==146)
        self.assertIn("80%",entry["requirements_excerpt"])
        self.assertIn("rendicontazione",entry["funded_activities_excerpt"])

    def test_film_only_grant_is_not_generic_education(self):
        entry=next(x for x in REVIEWS if x.get("public_id")==113)
        self.assertIn("film education",entry["assessment_reason"])
        self.assertIn("ec.europa.eu",entry["evidence_url"])

    def test_experience_required_for_implemented_initiatives(self):
        entry=next(x for x in REVIEWS if x.get("public_id")==148)
        self.assertIn("già",entry["requirements_excerpt"])
        self.assertIn("eraseindifference.org",entry["evidence_url"])

if __name__=="__main__":
    unittest.main()
