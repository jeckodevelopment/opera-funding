"""Regression tests for evidence-backed editorial assessment."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from fit import explain


class EditorialAssessmentTests(unittest.TestCase):
    def test_no_evidence_is_transparently_title_only(self):
        row = explain({"title": "Bando cultura e formazione",
                       "opportunity_type": "non classificato", "relevance": 55})
        self.assertEqual(row["assessment_label"], "MEDIA AFFINITÀ")
        self.assertEqual(row["assessment_confidence"], "bassa")
        self.assertIn("soltanto sul titolo", row["assessment_reason"])

    def test_full_evidence_supports_high_affinity(self):
        row = explain({
            "title": "Sostegno culturale", "opportunity_type": "finanziamento potenziale",
            "relevance": 20,
            "programme_objectives_excerpt": "Promuovere l'educazione e l'accesso alla cultura.",
            "funded_activities_excerpt": "Sono finanziabili progetti didattici audiovisivi e musicali.",
            "beneficiaries_excerpt": "Possono partecipare associazioni culturali non profit.",
            "requirements_excerpt": "Obbligatoria una sede operativa nella regione.",
            "assessment_evidence_source": "https://example.org/bando",
        })
        self.assertEqual(row["assessment_label"], "ALTA AFFINITÀ")
        self.assertEqual(row["assessment_confidence"], "alta")
        self.assertIn("fonte ufficiale", row["assessment_basis"])
        self.assertEqual(row["assessment_source"], "https://example.org/bando")

    def test_school_cultural_workshops_high_affinity_without_opera_word(self):
        row = explain({
            "title": "Progetti educativi e culturali nelle scuole",
            "opportunity_type": "finanziamento potenziale", "relevance": 20,
            "programme_objectives_excerpt": "Accesso alla cultura per gli studenti.",
            "funded_activities_excerpt": "Laboratori culturali con scuole e associazioni.",
            "beneficiaries_excerpt": "Associazioni culturali e istituti scolastici.",
            "requirements_excerpt": "Partenariato educativo ammesso.",
        })
        self.assertEqual(row["assessment_label"], "ALTA AFFINITÀ")
        self.assertTrue(any("scuole" in p for p in row["project_ideas"]))

    def test_adult_cultural_education_can_be_relevant(self):
        row = explain({
            "title": "Educazione permanente per adulti",
            "opportunity_type": "finanziamento potenziale",
            "programme_objectives_excerpt": "Percorsi culturali accessibili alla popolazione adulta.",
            "funded_activities_excerpt": "Incontri di formazione culturale e workshop.",
        })
        self.assertEqual(row["assessment_label"], "MEDIA AFFINITÀ")
        self.assertTrue(any("adulti" in p for p in row["project_ideas"]))

    def test_generic_training_is_not_certified_high_without_beneficiaries(self):
        row = explain({
            "title": "Formazione",
            "opportunity_type": "finanziamento potenziale",
            "funded_activities_excerpt": "Laboratori culturali e didattici per giovani.",
            "programme_objectives_excerpt": "Educazione e inclusione territoriale.",
        })
        self.assertEqual(row["assessment_label"], "MEDIA AFFINITÀ")
        self.assertTrue(any("Beneficiari" in p for p in row["assessment_gaps"]))

    def test_title_only_high_score_does_not_override_evidence(self):
        row = explain({
            "title": "Musica e formazione per tutti",
            "opportunity_type": "call progettuale da verificare",
            "relevance": 100,
            "programme_objectives_excerpt": "Sostegno all'efficienza degli impianti industriali.",
            "funded_activities_excerpt": "Acquisto di macchinari per impianti di estrazione.",
        })
        self.assertEqual(row["assessment_label"], "BASSA AFFINITÀ")
        self.assertIn("solo nel titolo", row["assessment_reason"])

    def test_informational_notice_remains_informational(self):
        row = explain({"title": "Selezione personale musicisti",
                       "opportunity_type": "altro avviso", "relevance": 95,
                       "programme_objectives_excerpt": "Programma musicale culturale"})
        self.assertEqual(row["assessment_label"], "INFORMATIVA")

    def test_uncertain_individual_eligibility_is_not_asserted(self):
        row = explain({
            "title": "Mobilità artistica",
            "opportunity_type": "finanziamento potenziale", "relevance": 40,
            "beneficiaries_excerpt": "Only individual artists can apply to the programme.",
        })
        self.assertTrue(any("associazione" in gap for gap in row["assessment_gaps"]))
        self.assertNotIn("non ammissibile", row["assessment_reason"].lower())


if __name__ == "__main__":
    unittest.main()
