import sys
import unittest
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from classify import classify, parse_deadline, parse_status, clean_title
from scan import discover

class ClassificationTests(unittest.TestCase):
    def test_relevant_but_not_project_grant(self):
        item=classify("Bando di Selezione per Formazione di Graduatorie per incarichi di docenza")
        self.assertEqual(item["opportunity_type"],"altro avviso")
        self.assertGreaterEqual(item["relevance"],45)

    def test_rural_land_lease_auction_is_not_grant(self):
        result=classify("AVVISO DI GARA PER L’ASSEGNAZIONE IN AFFITTO DI FONDI RUSTICI")
        self.assertEqual(result["opportunity_type"],"altro avviso")
        result=classify("Assegnazione in affitto terreni agricoli regionali")
        self.assertEqual(result["opportunity_type"],"altro avviso")

    def test_financing_and_dates(self):
        item=classify("Contributi per festival musicali",
            "Contributi per festival musicali Attivo Pubblicato il 12/10/2026 Scadenza 05/04/2027 12:00")
        self.assertEqual(item["opportunity_type"],"finanziamento potenziale")
        self.assertEqual(item["deadline"],"2027-04-05")
        self.assertEqual(item["status"],"aperto (fonte indice)")

    def test_closed_listing_kept_visible(self):
        item=classify("Avviso pubblico Festival Musicali 2026",
            "Avviso pubblico Festival Musicali 2026 Chiuso Pubblicato il 16/07/2025 Scadenza 30/09/2025")
        self.assertEqual(item["status"],"chiuso")
        self.assertEqual(item["opportunity_type"],"call progettuale da verificare")
        self.assertEqual(item["deadline"],"2025-09-30")

    def test_unlabeled_dates_not_deadline(self):
        self.assertIsNone(parse_deadline("Pubblicato il 16/07/2025"))
        self.assertEqual(parse_status("Festival aperto al pubblico"),"non verificato")

    def test_invalid_date_ignored(self):
        self.assertIsNone(parse_deadline("Scadenza 31/02/2027"))

    def test_clean_title(self):
        self.assertEqual(clean_title("Bando culturale Attivo Pubblicato il 11/10/2026 Scadenza 15/11/2026"),"Bando culturale")

    def test_source_discovery_no_eligibility_filter(self):
        source={"id":"f","name":"Fondazione","url":"https://example.org/bandi"}
        session=Mock()
        reply=Mock(status_code=200,headers={"Content-Type":"text/html"},url=source["url"],
            text='<a href="/call-1">Contributi per festival musicali Chiuso Pubblicato il 10/10/2025 Scadenza 11/11/2025</a>')
        session.get.return_value=reply
        from unittest.mock import patch
        with patch("scan.eligible_to_fetch", return_value=True):
            rows=discover(source,session,"2026-11-16T19:00:00+00:00")
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["status"],"chiuso")
        self.assertEqual(rows[0]["eligibility"],"da verificare")

if __name__=="__main__":
    unittest.main()
