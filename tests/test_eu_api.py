import sys
import unittest
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from eu_api import fetch_creative_europe,api_result_to_opportunity
SOURCE={"id":"eufunding","url":"https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/home"}
NOW="2026-11-16T22:00:00+00:00"
RECORD={"reference":"123","metadata":{
 "title":["Creative Europe – Artistic European cooperation"],
 "topicAbbreviation":["CREA-CULT-2027-COOP"],
 "openingDate":["2026-11-01T00:00:00Z"],
 "deadlineDate":["2027-02-24T17:00:00Z"],
 "status":["open for submission"]
}}
class APITests(unittest.TestCase):
 def test_official_metadata_preserves_provenance(self):
  row=api_result_to_opportunity(RECORD,SOURCE,NOW)
  self.assertEqual(row["deadline"],"2027-02-24")
  self.assertTrue(row["source_open_confirmed"])
  self.assertEqual(row["source_id"],"eufunding")
  self.assertIn("CREA-CULT-2027-COOP",row["url"])
  self.assertEqual(row["link_status"],"non verificato")
 def test_past_deadline_never_open(self):
  record={"metadata":{**RECORD["metadata"],"deadlineDate":["2025-01-01"]}}
  row=api_result_to_opportunity(record,SOURCE,NOW)
  self.assertFalse(row["source_open_confirmed"])
 def test_missing_metadata_rejected(self):
  self.assertIsNone(api_result_to_opportunity({"metadata":{"title":["X"]}},SOURCE,NOW))
  self.assertIsNone(api_result_to_opportunity({"metadata":{"title":["X"],"topicAbbreviation":["../../bad"]}},SOURCE,NOW))
 def test_official_api_request_and_result(self):
  session=Mock()
  response=Mock()
  response.json.return_value={"results":[RECORD],"totalResults":1}
  session.post.return_value=response
  rows=fetch_creative_europe(session,SOURCE,NOW)
  self.assertEqual(len(rows),1)
  args,kwargs=session.post.call_args
  self.assertEqual(kwargs["params"]["apiKey"],"SEDIA")
  self.assertIn("43251814",kwargs["files"]["query"][1])
  self.assertLessEqual(kwargs["timeout"],30)
 def test_invalid_response_fails_loudly(self):
  session=Mock()
  session.post.return_value.json.return_value={"unexpected":[]}
  with self.assertRaises(ValueError):fetch_creative_europe(session,SOURCE,NOW)
if __name__=="__main__":unittest.main()
