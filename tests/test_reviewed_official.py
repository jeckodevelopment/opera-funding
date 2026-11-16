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
    return {"source_id":fact["source_id"],"url":"https://example.org"+fact["match_path"]+"?utm_source=feed",
            "deadline":deadline,"funding_status":"DA VERIFICARE","link_status":"raggiungibile",
            "opportunity_type":"finanziamento potenziale"}

class VerifiedFactsTests(unittest.TestCase):
    def test_all_five_match_official_sourced_records(self):
        rows=[row(f) for f in FACTS]
        apply_reviewed_facts(rows,FACTS,"2026-11-17T09:00:00+00:00")
        self.assertEqual(len(rows),5)
        for rec,fact in zip(rows,FACTS):
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

    def test_official_evidence_expires_without_fake_future_open(self):
        rows=[row(f) for f in FACTS]
        apply_reviewed_facts(rows,FACTS,"2026-11-25T09:00:00+00:00")
        self.assertEqual(effective_status(rows[1],date(2026,11,25)),"DA VERIFICARE")
        self.assertEqual(effective_status(rows[2],date(2026,11,25)),"CHIUSO")
        self.assertEqual(effective_status(rows[3],date(2026,11,25)),"CHIUSO")
        self.assertEqual(effective_status(rows[4],date(2026,11,25)),"DA VERIFICARE")

    def test_does_not_override_conflicting_deadline_or_other_path(self):
        first=row(FACTS[1],"2027-03-05")
        other={"source_id":"volto","url":"https://example.org/other-bando","link_status":"raggiungibile"}
        apply_reviewed_facts([first,other],FACTS,"2026-11-17T09:00:00+00:00")
        self.assertEqual(first["deadline"],"2027-03-05")
        self.assertNotIn("status_evidence",first)
        self.assertNotIn("deadline",other)

    def test_rolling_period_ends_without_inventing_next_cycle(self):
        rec=row(FACTS[4])
        apply_reviewed_facts([rec],FACTS,"2027-01-01T00:00:00+00:00")
        self.assertFalse(rec["rolling_confirmed"])
        self.assertEqual(effective_status(rec,date(2027,1,1)),"CHIUSO")

if __name__=="__main__":
    unittest.main()
