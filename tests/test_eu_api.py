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
 def test_eu_api_uses_only_explicit_substantive_metadata(self):
  data={"metadata":{**RECORD["metadata"],
    "topicDescription":["Support for international cultural collaboration in Europe."],
    "eligibleActivities":["Grants for cross-border performing arts projects."],
    "eligibleApplicants":["Registered non-profit cultural organisations."],
    "eligibilityConditions":["Applications must include an international partner."]}}
  row=api_result_to_opportunity(data,SOURCE,NOW)
  self.assertIn("cultural collaboration",row["programme_objectives_excerpt"])
  self.assertIn("performing arts",row["funded_activities_excerpt"])
  self.assertIn("non-profit",row["beneficiaries_excerpt"])
  self.assertIn("international partner",row["requirements_excerpt"])
  self.assertEqual(row["assessment_evidence_source"],row["url"])

 def test_eu_api_does_not_invent_missing_beneficiary_conditions(self):
  row=api_result_to_opportunity(RECORD,SOURCE,NOW)
  self.assertFalse(row.get("beneficiaries_excerpt"))
  self.assertFalse(row.get("requirements_excerpt"))

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
 def test_archived_topic_is_consulted_via_official_details_api(self):
  from eu_api import fetch_topic_evidence
  topic="CREA-CULT-2024-LIT"
  item={"url":"https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/"+topic,
        "title":"Circulation of European literary works","source_id":"eufunding"}
  record={"metadata":{"topicAbbreviation":[topic],
       "topicDescription":["Support for circulation of translated literary works across Europe."],
       "eligibleApplicants":["Publishing organisations capable of translating and distributing European literature."]}}
  session=Mock()
  session.post.return_value.json.return_value={"results":[record]}
  result=fetch_topic_evidence(item,session,NOW)
  self.assertIn("translated literary works",result["programme_objectives_excerpt"])
  self.assertIn("Publishing organisations",result["beneficiaries_excerpt"])
  self.assertTrue(result["detail_checked"])
  self.assertEqual(result["detail_attempted_at"],NOW)
  self.assertEqual(session.post.call_args.kwargs["params"]["text"],'"'+topic+'"')

 def test_topic_missing_from_official_response_is_marked_insufficient(self):
  from eu_api import fetch_topic_evidence
  item={"url":"https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/CREA-MEDIA-2021-TRAINING"}
  session=Mock()
  session.post.return_value.json.return_value={"results":[]}
  result=fetch_topic_evidence(item,session,NOW)
  self.assertEqual(result["detail_attempted_at"],NOW)
  self.assertFalse(result["detail_checked"])
  self.assertFalse(result.get("beneficiaries_excerpt"))

 def test_eu_service_failure_remains_eligible_for_retry(self):
  from eu_api import fetch_topic_evidence
  item={"url":"https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/CREA-MEDIA-2021-TRAINING"}
  session=Mock()
  session.post.side_effect=RuntimeError("offline")
  self.assertNotIn("detail_attempted_at",fetch_topic_evidence(item,session,NOW))

 def test_invalid_response_fails_loudly(self):
  session=Mock()
  session.post.return_value.json.return_value={"unexpected":[]}
  with self.assertRaises(ValueError):fetch_creative_europe(session,SOURCE,NOW)
if __name__=="__main__":unittest.main()
