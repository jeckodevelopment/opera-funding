import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from adequacy import apply_adequacy

class AdequacyTests(unittest.TestCase):
    def test_high_grade_requires_programme_activities_and_beneficiaries(self):
        row=apply_adequacy({
            "opportunity_type":"finanziamento potenziale","assessment_label":"ALTA AFFINITÀ",
            "assessment_evidence_source":"https://official.example/call",
            "programme_objectives_excerpt":"Sostegno alla cultura e all'educazione",
            "funded_activities_excerpt":"Laboratori culturali per scuole e giovani",
            "beneficiaries_excerpt":"Associazioni culturali ed enti scolastici",
            "requirements_excerpt":"Progetti culturali con partners ammessi",
        })
        self.assertEqual(row["adequacy_label"],"ALTA")
        self.assertEqual(row["adequacy_level"],3)

    def test_high_title_score_without_documents_is_capped(self):
        row=apply_adequacy({
            "assessment_label":"ALTA AFFINITÀ","relevance":99,
            "opportunity_type":"finanziamento potenziale"
        })
        self.assertEqual(row["adequacy_label"],"MEDIA")
        self.assertIn("documentazione",row["adequacy_reason"])

    def test_exclusive_individual_applicants_are_not_assumed_eligible(self):
        row=apply_adequacy({
            "assessment_label":"ALTA AFFINITÀ",
            "opportunity_type":"finanziamento potenziale",
            "assessment_evidence_source":"https://official.example/call",
            "funded_activities_excerpt":"Workshop culturali",
            "beneficiaries_excerpt":"Only individual artists may apply",
        })
        self.assertEqual(row["adequacy_label"],"BASSA")
        self.assertIn("diversi da un'associazione",row["adequacy_reason"])

    def test_school_project_is_not_excluded_due_to_lack_of_opera_keyword(self):
        row=apply_adequacy({
            "assessment_label":"MEDIA AFFINITÀ",
            "opportunity_type":"call progettuale da verificare",
            "assessment_evidence_source":"https://official.example/call",
            "funded_activities_excerpt":"Progetti di educazione nelle scuole",
            "beneficiaries_excerpt":"Associazioni e istituti scolastici",
            "requirements_excerpt":"Partenariato ammesso",
        })
        self.assertEqual(row["adequacy_label"],"MEDIA")

    def test_unresolved_beneficiary_evidence_caps_high_at_medium(self):
        row=apply_adequacy({
            "opportunity_type":"finanziamento potenziale",
            "assessment_label":"ALTA AFFINITÀ",
            "assessment_evidence_source":"https://example.org/bando",
            "programme_objectives_excerpt":"Educazione musicale",
            "funded_activities_excerpt":"Laboratori teatrali",
            "beneficiaries_excerpt":"Associazioni culturali ammesse",
            "requirements_excerpt":"Candidatura entro dicembre",
            "assessment_document_discrepancies":[{
                "field":"beneficiaries_excerpt",
                "first_source":"https://example.org/call.pdf",
                "other_source":"https://example.org/faq.pdf",
                "status":"testi_diversi_da_verificare"
            }]
        })
        self.assertEqual(row["adequacy_label"],"MEDIA")
        self.assertIn("fonti_requisiti_da_confrontare",row["adequacy_verification_flags"])
        self.assertIn("formulazioni differenti",row["adequacy_reason"])

    def test_difference_about_objectives_does_not_cap_eligibility(self):
        row=apply_adequacy({
            "opportunity_type":"finanziamento potenziale",
            "assessment_label":"ALTA AFFINITÀ",
            "assessment_evidence_source":"https://example.org/bando",
            "programme_objectives_excerpt":"Promozione culturale",
            "funded_activities_excerpt":"Laboratori musicali",
            "beneficiaries_excerpt":"Associazioni culturali",
            "requirements_excerpt":"Progetto artistico",
            "assessment_document_discrepancies":[{
                "field":"programme_objectives_excerpt",
                "first_source":"https://example.org/a.pdf",
                "other_source":"https://example.org/b.pdf"
            }]
        })
        self.assertEqual(row["adequacy_label"],"ALTA")
        self.assertEqual(row["adequacy_verification_flags"],[])

    def test_mention_not_only_individual_applicants_is_not_exclusive(self):
        row=apply_adequacy({
            "opportunity_type":"finanziamento potenziale",
            "assessment_label":"ALTA AFFINITÀ",
            "assessment_evidence_source":"https://example.org/bando",
            "programme_objectives_excerpt":"Promozione culturale",
            "funded_activities_excerpt":"Progetti culturali",
            "beneficiaries_excerpt":"Sono ammessi non solo persone fisiche ma anche enti culturali",
            "requirements_excerpt":"Progetto documentato"
        })
        self.assertEqual(row["adequacy_level"],3)
        self.assertNotIn("beneficiari_esclusivi",row["adequacy_verification_flags"])

    def test_missing_or_same_source_discrepancy_is_not_a_verified_conflict(self):
        row=apply_adequacy({
            "opportunity_type":"finanziamento potenziale",
            "assessment_label":"ALTA AFFINITÀ",
            "assessment_evidence_source":"https://example.org/bando",
            "programme_objectives_excerpt":"Promozione culturale",
            "funded_activities_excerpt":"Progetti culturali",
            "beneficiaries_excerpt":"Associazioni",
            "requirements_excerpt":"Cofinanziamento possibile",
            "assessment_document_discrepancies":[{"field":"requirements_excerpt",
                 "first_source":"https://example.org/a.pdf",
                 "other_source":"https://example.org/a.pdf"}]
        })
        self.assertEqual(row["adequacy_level"],3)

    def test_informational_record_not_misrepresented_as_grant(self):
        row=apply_adequacy({"opportunity_type":"altro avviso",
                             "assessment_label":"INFORMATIVA"})
        self.assertEqual(row["adequacy_level"],0)
        self.assertEqual(row["adequacy_label"],"INFORMATIVA")

if __name__=="__main__":
    unittest.main()
