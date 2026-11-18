"""Operational actions stay explicitly non-certifying and evidence-backed."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from operational_assessment import operational_assessment,annotate_operational_assessment
from catalog_reconciliation import summarize_catalog_reconciliation

def row(**opts):
    return {
        "public_id":17,
        "funding_status":"APERTO",
        "adequacy_label":"MEDIA",
        "assessment_source":"https://official.example/call",
        "funded_activities_excerpt":"Progetti di divulgazione culturale",
        "beneficiaries_excerpt":"Beneficiari: associazioni culturali",
        "requirements_excerpt":"Requisiti generali di progetto",
        "eligibility_condition_status":"compatibilita_documentata",
        "applicant_requirement_comparison":[],
        **opts
    }

class OperationalAssessmentTests(unittest.TestCase):
    def test_direct_is_review_only_never_certification(self):
        result=operational_assessment(row())
        self.assertEqual(result["path"],"verificare_candidatura_diretta")
        self.assertFalse(result["verified_eligibility"])
        self.assertTrue(any("Confermare" in x for x in result["next_actions"]))

    def test_missing_requirements_never_claims_direct(self):
        result=operational_assessment(row(requirements_excerpt=""))
        self.assertEqual(result["path"],"integrare_verifica_documentale")
        self.assertTrue(any("requisiti" in x.lower() for x in result["next_actions"]))

    def test_unresolved_constraints_never_direct(self):
        result=operational_assessment(row(applicant_requirement_comparison=[
            {"category":"natura_giuridica","status":"da_verificare"}]))
        self.assertEqual(result["path"],"integrare_verifica_documentale")

    def test_mandatory_partnership_explained(self):
        result=operational_assessment(row(requirements_excerpt="Partenariato obbligatorio con scuole"))
        self.assertEqual(result["path"],"verificare_candidatura_in_partenariato")
        self.assertFalse(result["verified_eligibility"])

    def test_exclusive_beneficiaries_without_partner_evidence_still_unresolved(self):
        result=operational_assessment(row(eligibility_condition_status="potenzialmente_incompatibile",
            beneficiaries_excerpt="Solo persone fisiche possono presentare domanda"))
        self.assertEqual(result["path"],"integrare_verifica_documentale")
        self.assertTrue(any("partner" in a.lower() for a in result["next_actions"]))

    def test_possible_partner_role_needs_validation(self):
        result=operational_assessment(row(eligibility_condition_status="potenzialmente_incompatibile",
            beneficiaries_excerpt="Solo imprese, associazioni ammesse come partner"))
        self.assertEqual(result["path"],"verificare_candidatura_in_partenariato")

    def test_low_adequacy_remains_visible_and_deprioritized(self):
        result=operational_assessment(row(adequacy_label="BASSA"))
        self.assertEqual(result["path"],"bassa_priorita_progettuale")
        self.assertFalse(result["verified_eligibility"])

    def test_closed_status_never_has_application(self):
        result=annotate_operational_assessment(row(funding_status="CHIUSO"))
        self.assertEqual(result["application_path"],"non_attiva")
        self.assertFalse(result["application_eligibility_verified"])

    def test_reconciliation_covers_every_record_and_focuses_on_open_high_medium(self):
        records=[
            row(public_id=1),
            row(public_id=2,adequacy_label="ALTA",requirements_excerpt=""),
            row(public_id=3,adequacy_label="BASSA",beneficiaries_excerpt=""),
            row(public_id=4,funding_status="CHIUSO",requirements_excerpt=""),
        ]
        result=summarize_catalog_reconciliation(records)
        self.assertEqual(result["coverage"]["catalogo"]["total"],4)
        self.assertEqual(result["coverage"]["aperte"]["total"],3)
        self.assertEqual(result["coverage"]["aperte_alta_media"]["total"],2)
        self.assertEqual(result["coverage"]["aperte_alta_media"]["missing_documentation"]["requisiti"],1)
        self.assertEqual(result["priority_open_ids"],[1,2])

if __name__=="__main__":
    unittest.main()
