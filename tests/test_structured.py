import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from structured import structured_facts
from priority import check_priority

PAGE="""<html><main>
<h1>L.R. 14/2016 art. 20 – contributi ad associazioni</h1>
<p>Stato Aperto</p>
<p>Domande dal Lun, 02/11/2026 - 09:00</p>
<p>Scadenza Mar, 24/11/2026 - 12:00</p>
<p>Rivolto a Enti pubblici Terzo settore</p>
</main></html>"""
URL="https://bandi.regione.piemonte.it/contributi-finanziamenti/manifestazioni"

class StructuredTests(unittest.TestCase):
    def test_official_page_with_weekdays(self):
        info=structured_facts(PAGE,URL)
        self.assertEqual(info["deadline"],"2026-11-24")
        self.assertEqual(info["opening_date"],"2026-11-02")
        self.assertTrue(info["source_open_confirmed"])
        self.assertFalse(info["closure_confirmed"])
        self.assertEqual(info["deadline_source"],URL)

    def test_no_open_without_explicit_label(self):
        info=structured_facts("<main>Scadenza 24/11/2026. Un evento aperto al pubblico.</main>",URL)
        self.assertFalse(info["source_open_confirmed"])
        self.assertEqual(info["deadline"],"2026-11-24")

    def test_verified_priority_page(self):
        response=Mock(url=URL,status_code=200,headers={"Content-Type":"text/html"},text=PAGE)
        response.iter_content.return_value=[PAGE.encode()]
        session=Mock()
        session.get.return_value=response
        source={"name":"Regione Piemonte","id":"piemonte","url":"https://bandi.regione.piemonte.it/"}
        target={"url":URL,"title":"Contributi eventi e manifestazioni culturali"}
        result=check_priority(target,source,session,lambda u,s:True,"2026-11-16T19:00:00+00:00")
        self.assertIsNotNone(result)
        self.assertEqual(result["funding_status"],"APERTO")
        self.assertEqual(result["deadline"],"2026-11-24")
        self.assertEqual(result["link_status"],"raggiungibile")
        self.assertEqual(result["eligibility"],"da verificare")

if __name__=="__main__":unittest.main()
