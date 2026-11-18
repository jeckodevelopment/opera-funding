"""Regression checks: retired sources must never look currently OPEN."""
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from catalog_audit import load_retired_sources,mark_retired_source,audit_catalog
from status import annotate
from datetime import date
ROOT=Path(__file__).resolve().parents[1]

class CatalogAuditTests(unittest.TestCase):
 def test_alcotra_not_in_active_sources(self):
  active=json.loads((ROOT/"config/sources.json").read_text(encoding="utf-8"))
  retired=load_retired_sources(ROOT/"config/retired_sources.json")
  self.assertNotIn("alcotra",[s["id"] for s in active])
  self.assertIn("piemonte",[s["id"] for s in active])
  self.assertIn("alcotra",retired)
 def test_retired_status_not_false_open(self):
  retired={"alcotra":{"id":"alcotra"}}
  old={"source_id":"alcotra","url":"https://interreg-alcotra.eu/it/bando",
       "status":"aperto","source_open_confirmed":True,"link_status":"raggiungibile",
       "rolling_confirmed":True,"rolling_evidence":"precedente fonte"}
  mark_retired_source(old,retired)
  annotate(old,date(2026,11,19))
  self.assertTrue(old["source_retired"])
  self.assertFalse(old["source_open_confirmed"])
  self.assertNotEqual(old["funding_status"],"APERTO")
  self.assertEqual(old["status"],"non verificato")
 def test_retirement_preserves_history(self):
  old={"source_id":"alcotra","id":"historic","public_id":198,"title":"Bando 2025",
       "deadline":"2025-05-01","status":"chiuso"}
  mark_retired_source(old,{"alcotra":{"id":"alcotra"}})
  annotate(old,date(2026,11,19))
  self.assertEqual(old["public_id"],198)
  self.assertEqual(old["deadline"],"2025-05-01")
  self.assertEqual(old["funding_status"],"CHIUSO")
 def test_full_audit_flags_open_requirements_without_fabrication(self):
  rows=[
   {"public_id":1,"url":"https://example.org/one","source_id":"alcotra",
    "funding_status":"CHIUSO","adequacy_label":"BASSA","assessment_review_status":"PARZIALE"},
   {"public_id":2,"url":"https://example.org/call?edition=1","funding_status":"APERTO",
    "adequacy_label":"MEDIA","assessment_review_status":"PARZIALE",
    "beneficiaries_excerpt":"Associazioni","applicant_requirement_comparison":[{"status":"da_verificare"}]},
   {"public_id":3,"url":"https://example.org/call?edition=2","funding_status":"CHIUSO",
    "adequacy_label":"BASSA","assessment_review_status":"PARZIALE"}
  ]
  report=audit_catalog(rows,{"alcotra":{}})
  self.assertEqual(report["records_checked"],3)
  self.assertEqual(report["retired_sources"]["alcotra"],1)
  self.assertEqual(report["retired_open_ids"],[])
  self.assertEqual(report["duplicate_same_edition_urls"],[])
  self.assertEqual(report["priority_open_review_count"],1)
  self.assertEqual(report["priority_open_review"][0]["public_id"],2)
  self.assertIn("requisiti",report["priority_open_review"][0]["missing_evidence"])
 def test_audit_detects_duplicate_ids_and_no_assessment(self):
  rows=[{"public_id":5,"url":"https://example.org/a","funding_status":"CHIUSO"},
        {"public_id":5,"url":"https://example.org/a","funding_status":"CHIUSO"}]
  report=audit_catalog(rows,{})
  self.assertEqual(report["duplicate_public_ids"],[5])
  self.assertEqual(report["duplicate_same_edition_urls"],[[5,5]])
  self.assertEqual(report["unassessed_ids"],[5,5])

if __name__=="__main__":unittest.main()
