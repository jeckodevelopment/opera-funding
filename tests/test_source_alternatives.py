import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from source_alternatives import delegated_source_status, rate_limit_due, rate_limited_source_status
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

 def test_http_429_partial_official_fallback_and_backoff(self):
  source={"id":"eucreative","name":"Creative Europe",
          "url":"https://culture.ec.europa.eu/funding/calls",
          "rate_limit_alternative_source_id":"eufunding"}
  upstream={"source_id":"eufunding","source_url":"https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/home",
            "ok":True,"discovered":12}
  now="2026-11-20T17:00:00+00:00"
  status=rate_limited_source_status(source,[upstream],now,now)
  self.assertTrue(status["ok"])
  self.assertFalse(status["direct_source_ok"])
  self.assertEqual(status["coverage_mode"],"official_alternative_partial")
  self.assertIn("parziale",status["coverage_note"])
  self.assertFalse(rate_limit_due(status,"2026-11-22T17:00:00+00:00"))
  self.assertTrue(rate_limit_due(status,"2026-11-23T17:00:00+00:00"))
 def test_no_fallback_if_upstream_unavailable(self):
  source={"id":"eucreative","name":"Creative Europe",
          "url":"https://culture.ec.europa.eu/funding/calls",
          "rate_limit_alternative_source_id":"eufunding"}
  status=rate_limited_source_status(source,[],"2026-11-20T17:00:00+00:00","2026-11-20T17:00:00+00:00")
  self.assertFalse(status["ok"])
  self.assertIn("error",status)
 def test_corrupt_rate_limit_timestamp_fails_open(self):
  self.assertTrue(rate_limit_due({"coverage_mode":"official_alternative_partial",
                                  "direct_last_429_at":"invalid"},"2026-11-20T17:00:00+00:00"))
if __name__=="__main__":unittest.main()
