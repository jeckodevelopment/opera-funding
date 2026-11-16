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
    def test_irrelevant_title_has_no_invented_project(self):
        item=explain({"title":"Avviso selezione del personale tecnico","relevance":20})
        self.assertEqual(item["project_ideas"],[])
if __name__=="__main__":
    unittest.main()
