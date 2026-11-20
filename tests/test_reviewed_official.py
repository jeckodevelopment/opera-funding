import json
import sys
import unittest
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from reviewed_official import apply_reviewed_facts
from status import effective_status

ROOT=Path(__file__).resolve().parents[1]
FACTS=json.loads((ROOT/"config"/"reviewed_official_facts.json").read_text(encoding="utf-8"))

def row(fact, deadline=None):
    # exact, curated URL path identity; extra query parameters never change it.
    return {"source_id":fact["source_id"],"url":"https://"+fact["match_host"]+fact["match_path"]+"?utm_source=feed",
            "deadline":deadline,"funding_status":"DA VERIFICARE","link_status":"raggiungibile",
            "opportunity_type":"finanziamento potenziale"}

class VerifiedFactsTests(unittest.TestCase):
    def test_all_five_match_official_sourced_records(self):
        rows=[row(f) for f in FACTS[:5]]
        apply_reviewed_facts(rows,FACTS,"2026-11-17T09:00:00+00:00")
        self.assertEqual(len(rows),5)
        for rec,fact in zip(rows,FACTS[:5]):
            with self.subTest(fact=fact["match_path"]):
                self.assertEqual(rec["deadline"],fact["deadline"])
                self.assertEqual(rec["deadline_source"],fact["official_url"])
                self.assertEqual(rec["status_evidence"],fact["official_url"])
                self.assertIn(fact["official_url"],[x["url"] for x in rec["documents"]])
        self.assertEqual([effective_status(r,date(2026,11,17)) for r in rows],
                         ["CHIUSO","APERTO","APERTO","APERTO","APERTO"])
        self.assertTrue(rows[4]["rolling_confirmed"])
        self.assertEqual(rows[4]["rolling_evidence"],FACTS[4]["official_url"])
        self.assertNotIn("opening_date",rows[2])

    def test_new_issuer_verified_reconciliations(self):
        by_path={f["match_path"]:f for f in FACTS}
        checked=[row(f) for f in FACTS[5:15]]
        apply_reviewed_facts(checked,FACTS,"2026-11-18T20:00:00+00:00")
        states=[effective_status(r,date(2026,11,18)) for r in checked]
        self.assertEqual(states,["CHIUSO","APERTO","IN ARRIVO","APERTO","APERTO","APERTO","APERTO","APERTO","APERTO","APERTO"])
        self.assertIsNone(checked[7].get("deadline"))
        self.assertTrue(checked[7]["rolling_confirmed"])
        self.assertEqual(checked[2]["opening_date"],"2027-01-07")
        self.assertIn("buoni-formazione",checked[7]["rolling_evidence"])

    def test_actual_volto_bandi_urls_are_matched(self):
        rows=[
            {"source_id":"volto","url":"https://volontariatotorino.it/bandi/dora-in-avanti-bando-per-lo-sviluppo-delle-comunita-a-torino-nord/",
             "deadline":"2026-11-20","link_status":"raggiungibile"},
            {"source_id":"volto","url":"https://volontariatotorino.it/bandi/linee-guida-2025-2026-per-le-richieste-di-contributo-al-fondo-di-beneficenza-di-intesa-sanpaolo/",
             "deadline":"2026-12-31","link_status":"raggiungibile"}
        ]
        apply_reviewed_facts(rows,FACTS,"2026-11-17T00:00:00+00:00")
        self.assertEqual([effective_status(r,date(2026,11,17)) for r in rows],["APERTO","APERTO"])
        self.assertEqual(rows[0]["reviewed_official_basis"],"official_issuer_statement")
        self.assertEqual(rows[1]["reviewed_official_basis"],"official_rolling_application_process")
        self.assertTrue(rows[1]["rolling_confirmed"])
        self.assertIn("linkedin.com",rows[0]["status_evidence"])
        self.assertIn("intesasanpaolo.com",rows[1]["status_evidence"])


    def test_eight_unverified_source_reconciliation(self):
        from verification import classify_informational_page
        expected={
            "programme:cmtorino-giovani":3,
            "programme:rivoli-associazioni":1,
            "volto":1,
        }
        selected=[f for f in FACTS if f["source_id"] in expected and
                  f["match_path"] in {
                    "/sites/default/files/pagina/ra6/documenti/politiche%20giovanili/avviso%20pubblico%20amare.pdf",
                    "/sites/default/files/pagina/ra6/documenti/politiche%20giovanili/avviso%20pubblico.pdf",
                    "/sites/default/files/pagina/ra6/documenti/politiche%20giovanili/festival%20giovani/avviso%20di%20manifestazione%20di%20interesse%20festival%20giovani.pdf",
                    "/ocmultibinary/download/5839/124709/5/c8fede5d77292d746efa498315c98a33.pdf/file/avviso%2bcontributi.pdf",
                    "/bandi/contributi-a-sostegno-di-iniziative-rilevanti-ai-fini-della-promozione-delleconomia-provinciale-anno-2027"
                  }]
        self.assertEqual(len(selected),5)
        records=[row(f) for f in selected]
        apply_reviewed_facts(records,FACTS,"2026-11-20T09:00:00+00:00")
        states={f["match_path"]:effective_status(r,date(2026,11,20))
                for f,r in zip(selected,records)}
        self.assertEqual(list(states.values()).count("CHIUSO"),4)
        self.assertEqual(list(states.values()).count("APERTO"),1)
        for path in (
            "/comunicazione/contributi-il-contrasto-delle-discriminazioni",
            "/istruzione-e-sviluppo-sociale/servizio-civile/servizio-civile-bandi",
            "/sites/default/files/pagina/ra6/documenti/politiche%20giovanili/esito%20avviso%20pubblico%20amare.pdf",
            "/sites/default/files/pagina/ra6/documenti/politiche%20giovanili/esito%20avviso%20pubblico%20guida%20sicura.pdf",
            "/sites/default/files/pagina/ra6/documenti/politiche%20giovanili/guida%20sicura%2026/dd_363_2026%20-%20determina%20approvazione%20avviso.pdf",
        ):
            info=classify_informational_page({"source_id":"programme:cmtorino-giovani",
                "url":"https://www.cittametropolitana.torino.it"+path,
                "opportunity_type":"finanziamento potenziale"})
            self.assertEqual(info["opportunity_type"],"altro avviso",path)

    def test_explicit_official_close_supersedes_inferred_pdf_date(self):
        fact=next(f for f in FACTS if f["source_id"]=="programme:rivoli-associazioni")
        rec=row(fact,"2026-12-31")
        apply_reviewed_facts([rec],FACTS,"2026-11-20T09:00:00+00:00")
        self.assertEqual(rec["deadline"],"2026-09-30")
        self.assertEqual(effective_status(rec,date(2026,11,20)),"CHIUSO")

    def test_no_broad_path_suffix_matching_for_unrelated_pages(self):
        r={"source_id":"volto","url":"https://volontariatotorino.it/archivio/bandi/dora-in-avanti-bando-per-lo-sviluppo-delle-comunita-a-torino-nord",
           "deadline":"2026-11-20","link_status":"raggiungibile"}
        apply_reviewed_facts([r],FACTS,"2026-11-17T00:00:00+00:00")
        self.assertNotIn("reviewed_official_basis",r)

    def test_official_evidence_expires_without_fake_future_open(self):
        rows=[row(f) for f in FACTS]
        apply_reviewed_facts(rows,FACTS,"2026-11-25T09:00:00+00:00")
        self.assertEqual(effective_status(rows[1],date(2026,11,25)),"DA VERIFICARE")
        self.assertEqual(effective_status(rows[2],date(2026,11,25)),"CHIUSO")
        self.assertEqual(effective_status(rows[3],date(2026,11,25)),"CHIUSO")
        self.assertEqual(effective_status(rows[4],date(2026,11,25)),"DA VERIFICARE")

    def test_does_not_override_conflicting_deadline_or_other_path(self):
        first=row(FACTS[1],"2027-03-05")
        forged={"source_id":FACTS[1]["source_id"],"url":"https://example.org"+FACTS[1]["match_path"],"link_status":"raggiungibile"}
        other={"source_id":"volto","url":"https://example.org/other-bando","link_status":"raggiungibile"}
        apply_reviewed_facts([first,other,forged],FACTS,"2026-11-17T09:00:00+00:00")
        self.assertEqual(first["deadline"],"2027-03-05")
        self.assertNotIn("status_evidence",first)
        self.assertNotIn("deadline",other)
        self.assertNotIn("deadline",forged)

    def test_rolling_period_ends_without_inventing_next_cycle(self):
        rec=row(FACTS[4])
        apply_reviewed_facts([rec],FACTS,"2027-01-01T00:00:00+00:00")
        self.assertFalse(rec["rolling_confirmed"])
        self.assertEqual(effective_status(rec,date(2027,1,1)),"CHIUSO")

if __name__=="__main__":
    unittest.main()
