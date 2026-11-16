import unittest
from datetime import datetime, timezone, timedelta
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from verification import pick_for_review,coverage,needs_review

NOW=datetime(2026,11,16,21,0,tzinfo=timezone.utc)
def row(key, **props):
    return {"id":key,"title":key,"relevance":60,
            "opportunity_type":"finanziamento potenziale",**props}

class VerificationTests(unittest.TestCase):
    def test_unvisited_first_and_fair_rotation(self):
        found=[row("a"),row("b"),row("c")]
        initial=pick_for_review(found,{},1,NOW)
        self.assertEqual(initial,{"a"})
        previous={"a":row("a",detail_attempted_at=NOW.isoformat())}
        subsequent=pick_for_review(found,previous,1,NOW)
        self.assertEqual(subsequent,{"b"})
        previous["b"]=row("b",detail_attempted_at=NOW.isoformat())
        self.assertEqual(pick_for_review(found,previous,1,NOW),{"c"})
    def test_old_parser_version_forces_revisit(self):
        previous={"a":row("a",detail_checked=True,detail_version=1,
                  detail_checked_at=NOW.isoformat())}
        self.assertEqual(pick_for_review([row("a")],previous,1,NOW),{"a"})
    def test_three_day_revisit(self):
        old=row("a",detail_checked=True,detail_version=3,
                detail_checked_at=(NOW-timedelta(days=4)).isoformat())
        fresh={**old,"detail_checked_at":NOW.isoformat()}
        self.assertTrue(needs_review(old,NOW))
        self.assertFalse(needs_review(fresh,NOW))
    def test_count_evidences_without_inventing(self):
        rows=[row("a",source_id="piemonte",funding_status="APERTO",deadline="2026-12-02",
                  deadline_source="https://example.org/bando",detail_checked_at=NOW.isoformat(),
                  link_status="raggiungibile"),
              row("b",source_id="piemonte",funding_status="DA VERIFICARE")]
        report=coverage(rows,[{"source_id":"piemonte","ok":True}])
        self.assertEqual(report["totals"]["all"],2)
        self.assertEqual(report["totals"]["open"],1)
        self.assertEqual(report["totals"]["unverified"],1)
        self.assertEqual(report["totals"]["dated_with_source"],1)
        self.assertEqual(report["by_source"]["piemonte"]["total"],2)
if __name__=="__main__":
    unittest.main()
