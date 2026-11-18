import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from public_ids import assign_public_ids, attach_public_aliases

class PublicIdTests(unittest.TestCase):
    def test_initial_ids_are_deterministic_and_positive(self):
        registry={"ids":{},"next_id":1}
        rows=[{"id":"https://b"},{"id":"https://a"},{"id":"https://c"}]
        assign_public_ids(rows,registry)
        self.assertEqual({r["id"]:r["public_id"] for r in rows},
                         {"https://a":1,"https://b":2,"https://c":3})
        self.assertEqual(registry["next_id"],4)
    def test_same_ids_after_rerank_scan_and_title_change(self):
        registry={"ids":{},"next_id":1}
        old=assign_public_ids([{"id":"https://z","relevance":90},{"id":"https://a"}],registry)
        newer=assign_public_ids([{"id":"https://a","title":"Nuova intestazione"},
                                 {"id":"https://z","relevance":10}],registry)
        self.assertEqual({r["id"]:r["public_id"] for r in old},
                         {r["id"]:r["public_id"] for r in newer})
    def test_deleted_ids_are_never_reused(self):
        registry={"ids":{},"next_id":1}
        assign_public_ids([{"id":"a"},{"id":"b"}],registry)
        new=assign_public_ids([{"id":"b"},{"id":"c"}],registry)
        self.assertEqual({r["id"]:r["public_id"] for r in new},{"b":2,"c":3})
        self.assertEqual(registry["ids"]["a"],1)
    def test_conflict_rejected(self):
        registry={"ids":{"a":10},"next_id":11}
        with self.assertRaises(ValueError):
            assign_public_ids([{"id":"a","public_id":11}],registry)
    def test_recovery_keeps_existing_number(self):
        registry={"ids":{},"next_id":1}
        rows=assign_public_ids([{"id":"url-1","public_id":143},{"id":"url-2"}],registry)
        self.assertEqual({r["id"]:r["public_id"] for r in rows},{"url-1":143,"url-2":144})
    def test_duplicate_registry_rejected(self):
        with self.assertRaises(ValueError):
            assign_public_ids([{"id":"a"}],{"ids":{"a":1,"b":1},"next_id":2})
    def test_alias_redirects_old_numeric_id_without_reassignment(self):
        registry={"ids":{"old-rss":146,"old-syndicated":147,"official":32,
                           "new-rss":252},"next_id":253}
        rows=[{"id":"official","public_id":32,"alternative_urls":["old-syndicated"]},
              {"id":"new-rss","public_id":252,"alternative_urls":["old-rss"]}]
        attach_public_aliases(rows,registry)
        self.assertEqual(rows[0]["public_id_aliases"],[147])
        self.assertEqual(rows[1]["public_id_aliases"],[146])
        self.assertEqual(registry["ids"]["old-rss"],146)

    def test_no_rows_removed(self):
        registry={"ids":{},"next_id":1}
        rows=[{"id":f"entry-{i}"} for i in range(250)]
        self.assertEqual(len(assign_public_ids(rows,registry)),250)
        self.assertEqual(len({r["public_id"] for r in rows}),250)

if __name__=="__main__":unittest.main()
