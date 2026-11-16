import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from catalog import deduplicate_catalog,reconcile_official_equivalents

ROOT="https://infobandi.csvnet.it/"
A=ROOT+"bando-una-mano-a-chi-sostiene-2026/?utm_source=rss"
B=ROOT+"bando-una-mano-a-chi-sostiene-nuova-edizione-2026-27/?utm_source=rss"
TITLE="Bando Una mano a chi sostiene – nuova edizione 2026/27"

class CatalogTests(unittest.TestCase):
    def test_deduplicate_same_grant_with_same_deadline(self):
        old={"id":A,"url":A,"source_id":"volto","title":TITLE,"deadline":"2027-02-16",
             "deadline_source":B,"first_seen":"2026-11-10"}
        canonical={"id":B,"url":B,"source_id":"volto","title":TITLE,"deadline":"2027-02-16",
                   "deadline_source":B,"first_seen":"2026-11-12"}
        rows=deduplicate_catalog([old,canonical])
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["id"],B)
        self.assertEqual(rows[0]["first_seen"],"2026-11-10")
        self.assertIn(A,rows[0]["alternative_urls"])
    def test_distinct_windows_never_merge(self):
        a={"source_id":"volto","url":A,"title":TITLE,"deadline":"2027-02-16","window_key":"phase-1"}
        b={"source_id":"volto","url":B,"title":TITLE,"deadline":"2027-02-16","window_key":"phase-2"}
        self.assertEqual(len(deduplicate_catalog([a,b])),2)
    def test_distinct_deadline_and_issuer_never_merge(self):
        a={"source_id":"volto","url":A,"title":TITLE,"deadline":"2027-02-16"}
        b={"source_id":"volto","url":B,"title":TITLE,"deadline":"2027-06-16"}
        c={"source_id":"torino","url":"https://bandi.comune.torino.it/avviso/x","title":TITLE,"deadline":"2027-02-16"}
        self.assertEqual(len(deduplicate_catalog([a,b,c])),3)
    def test_culture_moves_volto_syndication_reconciled_with_verified_official_call(self):
        official={"source_id":"eucreative","url":"https://culture.ec.europa.eu/culture-moves-europe/call-for-individual-mobility",
                  "deadline":"2027-04-30","funding_status":"APERTO","first_seen":"2026-10-01"}
        synd={"source_id":"volto","url":"https://infobandi.csvnet.it/culture-moves-europe-bando-per-la-mobilita-individuale-di-artisti-e-professionisti-della-cultura-2/?utm_source=rss",
              "deadline":"2027-04-30","funding_status":"DA VERIFICARE","first_seen":"2026-11-01"}
        rows=reconcile_official_equivalents([synd,official])
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["source_id"],"eucreative")
        self.assertEqual(rows[0]["funding_status"],"APERTO")
        self.assertIn(synd["url"],rows[0]["alternative_urls"])

    def test_circoscrizione_7_synced_notice_is_same_official_call(self):
        official={"source_id":"torino","url":"https://bandi.comune.torino.it/avviso/invito-presentare-progetti-iniziative-varie-anno-2027-circoscrizione-7",
                  "deadline":"2026-11-26","funding_status":"APERTO","first_seen":"2026-10-12"}
        synd={"source_id":"volto","url":"https://volontariatotorino.it/bandi/circoscrizione-7-invito-a-presentare-progetti-per-iniziative-varie-anno-2027/",
              "deadline":"2026-11-26","funding_status":"DA VERIFICARE","first_seen":"2026-11-01"}
        result=reconcile_official_equivalents([synd,official])
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["source_id"],"torino")
        self.assertEqual(result[0]["funding_status"],"APERTO")
        self.assertIn(synd["url"],result[0]["alternative_urls"])
    def test_do_not_merge_unconfirmed_or_mismatched_synced_notice(self):
        official={"source_id":"torino","url":"https://bandi.comune.torino.it/avviso/invito-presentare-progetti-iniziative-varie-anno-2027-circoscrizione-7",
                  "deadline":"2026-11-26"}
        syndicated={"source_id":"volto","url":"https://volontariatotorino.it/bandi/circoscrizione-7-invito-a-presentare-progetti-per-iniziative-varie-anno-2027/",
                    "deadline":"2026-11-27"}
        self.assertEqual(len(reconcile_official_equivalents([official,syndicated])),2)
        syndicated["deadline"]=None
        self.assertEqual(len(reconcile_official_equivalents([official,syndicated])),2)
    def test_does_not_merge_without_verifiable_deadline(self):
        a={"source_id":"volto","url":A,"title":TITLE}
        b={"source_id":"volto","url":B,"title":TITLE}
        self.assertEqual(len(deduplicate_catalog([a,b])),2)
if __name__=="__main__":
    unittest.main()
