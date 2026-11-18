import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from funder_registry import load_registry,link_opportunities,public_monitoring

ROOT=Path(__file__).resolve().parents[1]
class TestFunderRegistry(unittest.TestCase):
 def test_registry(self):
  data=load_registry(ROOT/"config/funders.json")
  self.assertGreaterEqual(len(data["funders"]),49)
  self.assertGreaterEqual(len(data["programs"]),29)
  self.assertEqual(len([p for p in data["programs"] if p["monitoring"]=="direct"]),11)
  self.assertTrue(all(p["funder_id"] for p in data["programs"]))
 def test_links_are_strict(self):
  data=load_registry(ROOT/"config/funders.json")
  rows=[{"source_id":"crt"},{"source_id":"volto","issuer":"Fondazione CRT"}]
  link_opportunities(rows,data)
  self.assertEqual(rows[0]["funder_id"],"crt")
  self.assertNotIn("funder_id",rows[1])
 def test_monitoring_not_faked(self):
  data=load_registry(ROOT/"config/funders.json")
  results=public_monitoring(data,[{"source_id":"crt","ok":True,"checked_at":"2026-11-18"}],"2026-11-18")
  by_id={p["id"]:p for p in results["programs"]}
  self.assertEqual(by_id["crt-bandi"]["monitoring_status"],"ok")
  self.assertEqual(by_id["enelcuore-progetti"]["monitoring_status"],"not_configured")
  self.assertEqual(by_id["iren-contributi"]["monitoring_status"],"reference_only")
  self.assertEqual(by_id["provincia-cuneo-contributi"]["monitoring_status"],"reference_only")
  self.assertEqual(by_id["settimo-associazioni"]["monitoring_status"],"not_configured")
  self.assertIsNone(by_id["iren-contributi"]["last_checked_at"])
if __name__=="__main__":unittest.main()
