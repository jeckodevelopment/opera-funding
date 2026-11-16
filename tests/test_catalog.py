import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from catalog import deduplicate_catalog

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
    def test_does_not_merge_without_verifiable_deadline(self):
        a={"source_id":"volto","url":A,"title":TITLE}
        b={"source_id":"volto","url":B,"title":TITLE}
        self.assertEqual(len(deduplicate_catalog([a,b])),2)
if __name__=="__main__":
    unittest.main()
