import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from catalog_changes import track_changes

NOW="2026-11-17T22:40:00+00:00"
LATER="2026-11-18T07:00:00+00:00"

def row(id="a",**kwargs):
    return {"id":id,"title":"Sostegno alla cultura","deadline":"2027-01-31",
            "documents":[{"label":"Bando","url":"https://example.org/bando.pdf"}],**kwargs}

class CatalogChangeTests(unittest.TestCase):
    def test_existing_records_receive_first_baseline_without_mass_new_tags(self):
        previous=[row("a"),row("b",title="Musica") if False else {"id":"b","title":"Musica"}]
        current=[row("a"),row("b")]
        out=track_changes(current,previous,NOW)
        self.assertTrue(all("catalog_new_at" not in x for x in out))
        self.assertTrue(all("catalog_updated_at" not in x for x in out))
        self.assertTrue(all(x["catalog_tracking_version"]==1 for x in out))
    def test_new_record_only_after_baseline(self):
        old=track_changes([row("a")],[row("a")],NOW)
        current=[row("a"),row("b")]
        tracked=track_changes(current,old,LATER)
        self.assertNotIn("catalog_new_at",tracked[0])
        self.assertEqual(tracked[1]["catalog_new_at"],LATER)
    def test_real_fact_change_gets_updated_at_and_stable_scans_do_not(self):
        previous=track_changes([row("a")],[row("a")],NOW)
        changed=track_changes([{"id":"a","title":"Sostegno alla cultura","deadline":"2027-02-12",
                  "documents":[{"label":"Bando","url":"https://example.org/bando.pdf"}]}],previous,LATER)
        self.assertEqual(changed[0]["catalog_updated_at"],LATER)
        again=track_changes([dict(changed[0],last_seen="future",score_explanation="Un'altra spiegazione")],changed,"2026-11-19T07:00:00+00:00")
        self.assertEqual(again[0]["catalog_updated_at"],LATER)
    def test_operational_status_does_not_mark_updated(self):
        previous=track_changes([row("a")],[row("a")],NOW)
        latest=dict(row("a"),link_status="non disponibile",status="chiuso",relevance=80,
                    detail_attempted_at=LATER)
        latest=track_changes([latest],previous,LATER)
        self.assertNotIn("catalog_updated_at",latest[0])
    def test_doc_order_does_not_count_as_change(self):
        a=row("a");a["documents"].append({"label":"FAQ","url":"https://example.org/faq.pdf"})
        before=track_changes([a],[a],NOW)
        b=dict(a,documents=list(reversed(a["documents"])))
        self.assertNotIn("catalog_updated_at",track_changes([b],before,LATER)[0])
    def test_new_tag_stable_and_update_timestamp_separate(self):
        baseline=track_changes([row("a")],[row("a")],NOW)
        introduced=track_changes([row("a"),row("b")],baseline,LATER)
        future=track_changes([row("a"),row("b")],introduced,"2026-11-19T07:00:00+00:00")
        self.assertEqual(future[1]["catalog_new_at"],LATER)
        self.assertNotIn("catalog_updated_at",future[1])
    def test_never_drops_opportunities(self):
        original=[row(str(i)) for i in range(30)]
        tracked=track_changes(original,[],NOW)
        self.assertEqual(len(tracked),30)

if __name__=="__main__":
    unittest.main()
