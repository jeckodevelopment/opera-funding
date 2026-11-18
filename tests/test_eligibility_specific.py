"""Specific source-backed requirements never certify an applicant's eligibility."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from eligibility_specific import annotate_specific_requirements, extract_specific_requirements

BASE = {"opportunity_type":"finanziamento potenziale",
        "assessment_evidence_source":"https://official.example/call"}

class SpecificRequirementTests(unittest.TestCase):
    def test_all_five_constraints_with_attributed_evidence(self):
        text = ("È richiesta la sede legale in Piemonte. "
                "Iscritti al RUNTS sono ammessi. "
                "Costituiti da almeno 2 anni alla data del bando. "
                "Cofinanziamento obbligatorio del 20%. "
                "Partenariato richiesto con almeno una scuola.")
        row = annotate_specific_requirements({**BASE,"requirements_excerpt":text})
        self.assertEqual({x["category"] for x in row["eligibility_specific_requirements"]},
                         {"territorio","natura_giuridica","anzianita",
                          "condizioni_economiche","partenariato"})
        self.assertEqual(row["eligibility_specific_unchecked"], 5)
        self.assertTrue(all(x["source"] == "https://official.example/call"
                            for x in row["eligibility_specific_requirements"]))
        self.assertTrue(all(x["status"] == "requisito_documentato_da_verificare"
                            for x in row["eligibility_specific_requirements"]))
        self.assertNotIn("eligibility",row)

    def test_merely_named_place_or_partner_is_not_mandatory(self):
        row=annotate_specific_requirements({**BASE,
            "requirements_excerpt":"Evento a Torino con partner culturali. Budget 12000 euro."})
        self.assertEqual(row["eligibility_specific_requirements"], [])

    def test_optional_cofinancing_does_not_look_mandatory(self):
        row=annotate_specific_requirements({**BASE,
            "requirements_excerpt":"Cofinanziamento facoltativo, partenariato ammesso."})
        self.assertEqual(row["eligibility_specific_unchecked"],0)

    def test_missing_source_is_not_documented(self):
        row=annotate_specific_requirements({
            "opportunity_type":"finanziamento potenziale",
            "requirements_excerpt":"Sede legale in Piemonte e partenariato obbligatorio."})
        self.assertEqual(row["eligibility_specific_requirements"], [])

    def test_per_field_pdf_source_takes_precedence(self):
        row=annotate_specific_requirements({**BASE,
            "requirements_excerpt":"Almeno 2 anni di attività certificata.",
            "beneficiaries_excerpt":"Sede legale in Piemonte.",
            "assessment_field_sources":{
                "requirements_excerpt":"https://official.example/rules.pdf",
                "beneficiaries_excerpt":"https://official.example/applicants.pdf"}})
        origin={x["category"]:x["source"] for x in row["eligibility_specific_requirements"]}
        self.assertEqual(origin["anzianita"],"https://official.example/rules.pdf")
        self.assertEqual(origin["territorio"],"https://official.example/applicants.pdf")

    def test_explicit_prior_experience_required_not_merely_discussed(self):
        eligible=annotate_specific_requirements({**BASE,
            "requirements_excerpt":"Esperienza pregressa obbligatoria nella gestione di progetti culturali."})
        self.assertEqual([x["category"] for x in eligible["eligibility_specific_requirements"]],
                         ["esperienza_pregressa"])
        generic=annotate_specific_requirements({**BASE,
            "requirements_excerpt":"Il progetto valorizza le esperienze culturali e la creatività."})
        self.assertEqual(generic["eligibility_specific_unchecked"],0)

    def test_informational_records_not_assessed(self):
        row=annotate_specific_requirements({**BASE,"opportunity_type":"altro avviso",
            "requirements_excerpt":"Partenariato obbligatorio."})
        self.assertEqual(row["eligibility_specific_unchecked"],0)

if __name__=="__main__":
    unittest.main()
