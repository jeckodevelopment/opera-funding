import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from evidence import official_evidence
from detail import extract

URL="https://funding.example.org/avviso"

class EvidenceTests(unittest.TestCase):
    def test_explicit_beneficiaries_follow_heading(self):
        html="<main><h2>Beneficiari</h2><p>Associazioni culturali senza scopo di lucro con sede in Piemonte.</p></main>"
        result=official_evidence(html,URL)
        self.assertIn("Associazioni culturali",result["beneficiaries_excerpt"])
        self.assertEqual(result["beneficiaries_source"],URL)

    def test_inline_beneficiaries_and_amount_kind(self):
        html="<main><p>Soggetti ammissibili: Enti del Terzo Settore iscritti al RUNTS</p><p>Dotazione finanziaria: euro 250.000</p></main>"
        facts=official_evidence(html,URL)
        self.assertIn("Terzo Settore",facts["beneficiaries_excerpt"])
        self.assertEqual(facts["amount_kind"],"dotazione finanziaria")
        self.assertIn("250.000",facts["amount"])
        self.assertEqual(facts["amount_source"],URL)

    def test_no_eligibility_claim_on_unrelated_prose(self):
        facts=official_evidence("<main><p>Le associazioni culturali sono diffuse in Piemonte.</p><p>Pubblicato il 12 novembre 2026</p></main>",URL)
        self.assertIsNone(facts["beneficiaries_excerpt"])
        self.assertIsNone(facts["amount"])
        self.assertIsNone(facts["rolling_guidance"])

    def test_rolling_is_advisory_not_confirmed_open(self):
        info=extract("<main><p>Le domande si presentano a sportello fino ad esaurimento fondi.</p></main>",URL)
        self.assertIn("a sportello",info["rolling_guidance"])
        self.assertEqual(info["rolling_guidance_source"],URL)
        self.assertNotIn("source_open_confirmed",info)
        self.assertNotIn("rolling_confirmed",info)
        self.assertIsNone(info["deadline"])

    def test_funding_amount_and_beneficiaries_are_not_invented(self):
        info=extract("<main><h1>Progetti culturali</h1><p>Pubblicazione 16/11/2026</p></main>",URL)
        self.assertIsNone(info["beneficiaries_excerpt"])
        self.assertIsNone(info["amount"])
        self.assertIsNone(info["amount_kind"])
        self.assertIsNone(info["rolling_guidance"])

    def test_wrong_context_does_not_become_budget(self):
        info=official_evidence("<main>Fatturato aziendale € 1.500.000.</main>",URL)
        self.assertIsNone(info["amount"])

if __name__=="__main__":
    unittest.main()
