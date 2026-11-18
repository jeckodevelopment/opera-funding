import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from fit import explain

class FitTests(unittest.TestCase):
    def test_score_remains_unchanged_and_not_eligibility(self):
        item=explain({"title":"Bando musica lirica per scuole e formazione digitale","relevance":95,"eligibility":"da verificare"})
        self.assertEqual(item["relevance"],95)
        self.assertEqual(item["eligibility"],"da verificare")
        self.assertGreater(len(item["project_ideas"]),0)
        self.assertIn("Coerenza",item["score_explanation"])
        self.assertIn("bassa",item["score_confidence"])
    def test_partnership_check_is_not_a_claim_of_mandatory_partners(self):
        item=explain({"title":"Bando partnership culturale europea","relevance":75})
        self.assertTrue(any("partenariato" in x for x in item["eligibility_checks"]))
        self.assertEqual(item["eligibility"],"da verificare")
    def test_curated_ideas_survive_repeated_reconciliation(self):
        item={"title":"Bando Ordinarie – Arte e Cultura Fondazione CRT",
              "curated_project_ideas":["Videolezioni sull'opera e cultura musicale"],
              "relevance":55}
        explain(item)
        explain(item)
        self.assertEqual(item["project_ideas"],["Videolezioni sull'opera e cultura musicale"])
        self.assertEqual(item["relevance"],55)
    def test_inspected_description_adds_supported_thematic_reasons(self):
        item=explain({"title":"Bando progetti 2027","relevance":20,"detail_checked":True,
                      "detail_basis":"HTML della scheda",
                      "summary":"Finanziamento per videopodcast e formazione digitale dei giovani",
                      "beneficiaries_excerpt":"Beneficiari: enti culturali"})
        self.assertEqual(item["relevance"],20)
        self.assertIn("contenuto della scheda",item["score_explanation"])
        self.assertIn("punteggio calcolato in fase di scoperta",item["score_confidence"])
        self.assertEqual(item["score_explanation_basis"],"titolo e contenuti della scheda consultata")
        self.assertEqual(item["eligibility"],"da verificare")

    def test_uninspected_summary_never_counts_as_documented_evidence(self):
        item=explain({"title":"Avviso generico 2027","relevance":20,
                      "summary":"Sostegno a corsi di musica e video per le scuole"})
        self.assertNotIn("contenuto della scheda",item["score_explanation"])
        self.assertEqual(item["score_explanation_basis"],"solo titolo")

    def test_checks_distinguish_total_budget_and_rolling_hint(self):
        item=explain({"title":"Bando cultura", "amount_kind":"dotazione finanziaria",
                      "rolling_guidance":"Possibile procedura a sportello",
                      "eligibility":"da verificare"})
        joined=" ".join(item["eligibility_checks"])
        self.assertIn("dotazione complessiva",joined)
        self.assertIn("sportello",joined)
        self.assertEqual(item["eligibility"],"da verificare")

    def test_explain_reconciles_idempotently_without_duplicate_checks(self):
        item={"title":"Bando cultura", "relevance":25,
              "beneficiaries_excerpt":"Beneficiari: enti del terzo settore",
              "detail_checked":True, "detail_basis":"HTML della scheda"}
        explain(item)
        explain(item)
        self.assertEqual(len(item["eligibility_checks"]),len(set(item["eligibility_checks"])))
        self.assertEqual(item["relevance"],25)

    def test_all_types_receive_editorial_assessment_without_eligibility_claim(self):
        cases=[
          ("finanziamento potenziale",85,"ALTA AFFINITÀ"),
          ("call progettuale da verificare",55,"MEDIA AFFINITÀ"),
          ("finanziamento potenziale",20,"BASSA AFFINITÀ"),
          ("altro avviso",90,"INFORMATIVA"),
          ("pagina informativa",25,"INFORMATIVA"),
        ]
        for kind,points,label in cases:
            with self.subTest(kind=kind,points=points):
                row=explain({"title":"Iniziativa culturale", "relevance":points,
                             "opportunity_type":kind})
                self.assertEqual(row["assessment_label"],label)
                self.assertTrue(row["assessment_reason"])
                self.assertEqual(row["assessment_basis"],"solo titolo")
                self.assertEqual(row["relevance"],points)
                self.assertEqual(row["eligibility"],"da verificare")
                self.assertIn("non è confermato",row["assessment_opening_note"])

    def test_full_existing_catalog_gets_evaluated_without_dropping_rows(self):
        import json
        source=Path(__file__).resolve().parents[1]/"data/opportunities.json"
        catalog=json.loads(source.read_text(encoding="utf-8"))
        evaluated=[explain(dict(row)) for row in catalog]
        self.assertEqual(len(evaluated),len(catalog))
        self.assertEqual({r["id"] for r in evaluated},{r["id"] for r in catalog})
        self.assertTrue(all(r.get("assessment_label") and r.get("assessment_reason")
                            and r.get("assessment_basis") for r in evaluated))

    def test_irrelevant_title_has_no_invented_project(self):
        item=explain({"title":"Avviso selezione del personale tecnico","relevance":20})
        self.assertEqual(item["project_ideas"],[])
if __name__=="__main__":
    unittest.main()
