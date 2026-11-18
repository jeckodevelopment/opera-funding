"""Official Piemonte ECG grant review: no fabricated direct eligibility."""
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from assessment_reviews import apply_assessment_reviews
from eligibility_conditions import annotate_conditions
from eligibility_specific import annotate_specific_requirements
from applicant_comparison import annotate_applicant_comparison,load_applicant_profile
from adequacy import apply_adequacy
from operational_assessment import annotate_operational_assessment

ROOT=Path(__file__).resolve().parents[1]
URL="https://volontariatotorino.it/bandi/educazione-alla-cittadinanza-globale-per-la-sostenibilita-e-la-solidarieta-internazionale-bando-2026/"

class PiemonteECGTests(unittest.TestCase):
    def test_partner_only_investigation_not_direct_application(self):
        reviews=json.loads((ROOT/"config/assessment_reviews.json").read_text(encoding="utf-8"))
        row={"public_id":176,"source_id":"volto","url":URL,
             "funding_status":"APERTO","opportunity_type":"finanziamento potenziale"}
        apply_assessment_reviews([row],reviews)
        self.assertIn("3 anni",row["requirements_excerpt"])
        self.assertIn("RUNTS",row["requirements_excerpt"])
        self.assertIn("partner",row["beneficiaries_excerpt"])
        annotate_conditions(row)
        annotate_specific_requirements(row)
        annotate_applicant_comparison(row,load_applicant_profile(),"2026-11-18")
        apply_adequacy(row)
        annotate_operational_assessment(row)
        self.assertEqual(row["adequacy_label"],"BASSA")
        self.assertEqual(row["application_path"],"integrare_verifica_documentale")
        self.assertIn("Capofila",row["direct_application_blocker"])
        self.assertTrue(any("partner" in task for task in row["application_next_actions"]))
        self.assertFalse(row["application_eligibility_verified"])
        self.assertIn("bandi.regione.piemonte.it",row["assessment_source"])
        self.assertIn("Autorità Locale",row["requirements_excerpt"])

if __name__=="__main__":
    unittest.main()
