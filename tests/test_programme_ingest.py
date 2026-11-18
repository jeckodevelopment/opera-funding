import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from programme_ingest import ingest_programme_calls,qualified_candidate
from funder_registry import link_opportunities

PROGRAM={"id":"sample-call","funder_id":"private","funder_name":"Fondazione Esempio","name":"Contributi","monitoring":"direct","url":"https://example.org/contributi"}
CANDIDATE={"url":"https://example.org/bandi/cultura-2027","title":"Bando cultura e musica 2027"}
class ProgrammeIngestTests(unittest.TestCase):
 def test_reject_generic_or_offsite(self):
  self.assertTrue(qualified_candidate(CANDIDATE,PROGRAM))
  self.assertFalse(qualified_candidate({"url":"https://elsewhere.test/bandi/2027","title":"Bando cultura 2027"},PROGRAM))
  self.assertFalse(qualified_candidate({"url":"https://example.org/bandi","title":"Bandi aperti"},PROGRAM))
 def test_promote_verified_call_only(self):
  state={"sample-call":{"status":"ok","candidate_links":[CANDIDATE]}}
  def details(row,*args):
   row.update({"detail_checked":True,"beneficiaries_excerpt":"Associazioni culturali",
               "deadline":"2027-02-10","status":"non verificato"})
   return row
  def live(row,*args):
   row["link_status"]="raggiungibile"
   return row
  entries={}
  with patch("programme_ingest.enrich",side_effect=details),patch("programme_ingest.check_link",side_effect=live):
   stats=ingest_programme_calls([PROGRAM],state,entries,None,lambda u,s:True,"2026-11-18T12:00:00Z")
  self.assertEqual(stats[0]["new"],1)
  row=next(iter(entries.values()))
  self.assertEqual(row["funder_id"],"private")
  self.assertEqual(row["program_id"],"sample-call")
  self.assertNotEqual(row["funding_status"],"APERTO")
  link_opportunities([row],{"programs":[]})
  self.assertEqual(row["program_id"],"sample-call")
  with patch("programme_ingest.enrich",side_effect=details),patch("programme_ingest.check_link",side_effect=live):
   again=ingest_programme_calls([PROGRAM],state,entries,None,lambda u,s:True,"2026-11-19T12:00:00Z")
  self.assertEqual(again[0]["new"],0)
 def test_no_detail_no_catalogue(self):
  state={"sample-call":{"status":"ok","candidate_links":[CANDIDATE]}}
  entries={}
  with patch("programme_ingest.enrich",side_effect=lambda row,*args:row):
   stats=ingest_programme_calls([PROGRAM],state,entries,None,lambda u,s:True,"2026-11-18T12:00:00Z")
  self.assertEqual(stats[0]["new"],0)
  self.assertEqual(entries,{})
if __name__=="__main__":unittest.main()
