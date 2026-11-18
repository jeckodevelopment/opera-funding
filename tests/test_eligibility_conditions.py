"""Applicant signals are deliberately distinct from legal eligibility."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from eligibility_conditions import annotate_conditions, condition_signals

BASE={"opportunity_type":"finanziamento potenziale",
      "assessment_evidence_source":"https://example.org/bando",
      "funded_activities_excerpt":"Laboratori culturali"}

class ConditionTests(unittest.TestCase):
    def test_explicit_association_beneficiary_is_compatible_not_certified(self):
        row=annotate_conditions({**BASE,
            "beneficiaries_excerpt":"Beneficiari: associazioni culturali senza scopo di lucro regolarmente costituite"})
        self.assertEqual(row["eligibility_condition_status"],"compatibilita_documentata")
        self.assertIn("altri requisiti",row["eligibility_condition_reason"])
        self.assertEqual(row["eligibility_condition_sources"],["https://example.org/bando"])
        self.assertNotIn("eligibility",row)

    def test_mandatory_partnership_is_conditional(self):
        row=annotate_conditions({**BASE,
            "beneficiaries_excerpt":"Beneficiari: associazioni culturali",
            "requirements_excerpt":"Partenariato obbligatorio con due scuole"})
        self.assertEqual(row["eligibility_condition_status"],"condizionata")

    def test_cofinancing_optional_not_mandatory(self):
        row=annotate_conditions({**BASE,
            "beneficiaries_excerpt":"Beneficiari: associazioni culturali",
            "requirements_excerpt":"Cofinanziamento facoltativo per attività aggiuntive"})
        self.assertEqual(row["eligibility_condition_status"],"compatibilita_documentata")

    def test_exclusive_individual_applicants_flagged_without_certified_exclusion(self):
        row=annotate_conditions({**BASE,
            "beneficiaries_excerpt":"Solo persone fisiche possono presentare domanda"})
        self.assertEqual(row["eligibility_condition_status"],"potenzialmente_incompatibile")
        self.assertIn("partner",row["eligibility_condition_reason"])

    def test_negated_exclusivity_does_not_exclude(self):
        row=annotate_conditions({**BASE,
            "beneficiaries_excerpt":"Beneficiari: non solo persone fisiche ma anche associazioni culturali"})
        self.assertEqual(row["eligibility_condition_status"],"compatibilita_documentata")

    def test_generic_association_mention_without_eligibility_is_insufficient(self):
        row=annotate_conditions({**BASE,
            "beneficiaries_excerpt":"Un progetto racconta la storia delle associazioni culturali della regione"})
        self.assertEqual(row["eligibility_condition_status"],"informazioni_insufficienti")

    def test_lack_of_primary_source_is_insufficient(self):
        row=annotate_conditions({
            "opportunity_type":"finanziamento potenziale",
            "beneficiaries_excerpt":"Beneficiari: associazioni culturali"})
        self.assertEqual(row["eligibility_condition_status"],"informazioni_insufficienti")

    def test_unrelated_page_not_a_call(self):
        row=annotate_conditions({"opportunity_type":"altro avviso",
            "beneficiaries_excerpt":"Beneficiari: associazioni culturali"})
        self.assertEqual(row["eligibility_condition_status"],"non_applicabile")

    def test_official_document_field_source_provenance(self):
        row=annotate_conditions({**BASE,
            "assessment_field_sources":{"beneficiaries_excerpt":"https://example.org/bando.pdf",
                                        "requirements_excerpt":"https://example.org/faq.pdf"},
            "beneficiaries_excerpt":"Beneficiari: associazioni culturali",
            "requirements_excerpt":"Il partenariato è obbligatorio"})
        self.assertEqual(row["eligibility_condition_status"],"condizionata")
        self.assertEqual(row["eligibility_condition_sources"],
                         ["https://example.org/bando.pdf","https://example.org/faq.pdf"])

if __name__=="__main__":
    unittest.main()
