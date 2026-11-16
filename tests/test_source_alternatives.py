import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from source_alternatives import delegated_source_status
SOURCE={
 "id":"creativeitalia","name":"Europa Creativa Desk Italia",
 "url":"https://europacreativa.cultura.gov.it/",
 "official_alternative_source_id":"eucreative",
 "official_alternative_note":"Copertura tramite il catalogo della Commissione europea"
}
UPSTREAM={"source_id":"eucreative","ok":True,"discovered":4,
          "source_url":"https://culture.ec.europa.eu/funding/calls"}
class AlternativeTests(unittest.TestCase):
 def test_delegation_preserves_provenance(self):
  result=delegated_source_status(SOURCE,[UPSTREAM],"2026-11-16T22:00:00Z")
  self.assertTrue(result["ok"])
  self.assertEqual(result["discovered"],4)
  self.assertEqual(result["coverage_mode"],"official_alternative")
  self.assertEqual(result["source_url"],SOURCE["url"])
  self.assertEqual(result["alternative_url"],UPSTREAM["source_url"])
  self.assertNotIn("error",result)
 def test_upstream_unavailable_is_not_success(self):
  result=delegated_source_status(SOURCE,[{**UPSTREAM,"ok":False}],"2026-11-16T22:00:00Z")
  self.assertFalse(result["ok"])
  self.assertIn("error",result)
 def test_missing_upstream_is_not_success(self):
  result=delegated_source_status(SOURCE,[],"2026-11-16T22:00:00Z")
  self.assertFalse(result["ok"])
  self.assertEqual(result["discovered"],0)
if __name__=="__main__":unittest.main()
