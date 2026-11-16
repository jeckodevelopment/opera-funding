import sys
import unittest
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from issuer_sources import parse_issuer_window, apply_issuer_evidence

SPORT="""<body><h1>Fabbrica – Spazi Civici</h1><p>Apertura Piattaforma: 4 novembre 2026 ore 12:00</p>
<p>Chiusura Piattaforma: 18 dicembre 2026 ore 12:00</p>
<p>Le candidature dovranno essere presentate tramite Piattaforma Bandi.</p></body>"""
CATTOLICA="""<body><h2>FASE 1 ISCRIZIONE DEI PROGETTI</h2>
<p>Dal 16 novembre 2026 al 16 febbraio 2027 gli Enti interessati potranno candidare su questo sito i loro progetti, fornendo una descrizione degli stessi.</p></body>"""
CHECK={"source_id":"volto","match_path":"/bando-fabbrica-spazi-civici-per-la-gioventu",
"official_url":"https://www.sportesalute.eu/fabbrica","parser":"sport","label":"Fabbrica"}
class IssuerTests(unittest.TestCase):
    def test_sport_explicit_filing(self):
        self.assertEqual(parse_issuer_window(SPORT,"sport"),{"opening_date":"2026-11-04","deadline":"2026-12-18"})
    def test_cattolica_official_filing(self):
        self.assertEqual(parse_issuer_window(CATTOLICA,"cattolica"),{"opening_date":"2026-11-16","deadline":"2027-02-16"})
    def test_no_open_without_application_evidence(self):
        self.assertIsNone(parse_issuer_window("<p>Apertura Piattaforma: 4 novembre 2026</p><p>Chiusura Piattaforma: 18 dicembre 2026</p>","sport"))
    def test_issuer_provenance_and_status(self):
        original={"source_id":"volto","url":"https://infobandi.csvnet.it/bando-fabbrica-spazi-civici-per-la-gioventu/","deadline":"2026-12-18",
                  "link_status":"raggiungibile","funding_status":"DA VERIFICARE","documents":[]}
        response=Mock(url=CHECK["official_url"],headers={"Content-Type":"text/html"},text=SPORT)
        response.iter_content.return_value=[SPORT.encode()]
        session=Mock()
        session.get.return_value=response
        result=apply_issuer_evidence(original,None,[CHECK],session,lambda url,s:True,"2026-11-16T22:00:00+00:00")
        self.assertTrue(result["source_open_confirmed"])
        self.assertEqual(result["deadline_source"],CHECK["official_url"])
        self.assertEqual(result["opening_date"],"2026-11-04")
        self.assertEqual(result["link_status"],"raggiungibile")
        self.assertIn(CHECK["official_url"],[d["url"] for d in result["documents"]])
        response.close.assert_called_once()
    def test_cepell_explicit_official_filing_closure(self):
        html="<main><h1>Educare alla lettura</h1><p>Le proposte di progetto devono essere compilate e inviate esclusivamente on line attraverso la piattaforma bandi del Centro entro e non oltre le ore 13:00 del giorno 13 novembre 2026.</p></main>"
        self.assertEqual(parse_issuer_window(html,"cepell"),{"opening_date":None,"deadline":"2026-11-13"})
        self.assertIsNone(parse_issuer_window("<p>Evento del 13 novembre 2026</p>","cepell"))
    def test_cepell_official_deadline_marks_ended_without_fake_open(self):
        check={"source_id":"volto","match_path":"/bando-educare-alla-lettura-2026",
               "official_url":"https://centroperillibro.cultura.gov.it/educare-alla-lettura-online-la-9a-edizione-del-bando-scadenza-13-novembre/",
               "parser":"cepell"}
        html="<main>Le proposte di progetto devono essere compilate e inviate esclusivamente on line entro e non oltre le ore 13:00 del giorno 13 novembre 2026.</main>"
        response=Mock(url=check["official_url"],headers={"Content-Type":"text/html"},text=html)
        response.iter_content.return_value=[html.encode()]
        row={"source_id":"volto","url":"https://infobandi.csvnet.it/bando-educare-alla-lettura-2026/","funding_status":"DA VERIFICARE","documents":[]}
        session=Mock()
        session.get.return_value=response
        result=apply_issuer_evidence(row,None,[check],session,lambda url,s:True,"2026-11-17T00:00:00+00:00")
        self.assertEqual(result["deadline"],"2026-11-13")
        self.assertTrue(result["closure_confirmed"])
        self.assertFalse(result["source_open_confirmed"])
        self.assertEqual(result["deadline_source"],check["official_url"])
        self.assertNotIn("opening_evidence",result)
    def test_blocked_robots_keeps_unverified(self):
        item={"source_id":"volto","url":"https://infobandi.csvnet.it/bando-fabbrica-spazi-civici-per-la-gioventu/","funding_status":"DA VERIFICARE"}
        session=Mock()
        result=apply_issuer_evidence(item,None,[CHECK],session,lambda url,s:False,"2026-11-16T22:00:00+00:00")
        self.assertNotIn("source_open_confirmed",result)
        session.get.assert_not_called()
    def test_expired_filing_never_open(self):
        item={"source_id":"volto","url":"https://infobandi.csvnet.it/bando-fabbrica-spazi-civici-per-la-gioventu/","funding_status":"DA VERIFICARE"}
        response=Mock(url=CHECK["official_url"],headers={"Content-Type":"text/html"},text=SPORT)
        response.iter_content.return_value=[SPORT.encode()]
        session=Mock()
        session.get.return_value=response
        result=apply_issuer_evidence(item,None,[CHECK],session,lambda url,s:True,"2026-12-19T12:00:00+00:00")
        self.assertFalse(result["source_open_confirmed"])
        self.assertTrue(result["closure_confirmed"])
if __name__=="__main__":unittest.main()
