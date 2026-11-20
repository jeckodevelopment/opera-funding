import unittest
from datetime import date
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from status import effective_status, annotate

NOW=date(2026,11,16)

class FundingStatusTests(unittest.TestCase):
    def test_open_requires_both_issuer_window_and_reachable_link(self):
        row={"status":"aperto (fonte indice)","source_open_confirmed":True,"deadline":"2026-12-01","link_status":"raggiungibile"}
        self.assertEqual(effective_status(row,NOW),"APERTO")
        self.assertEqual(effective_status({**row,"link_status":"da verificare"},NOW),"DA VERIFICARE")
        self.assertEqual(effective_status({**row,"source_open_confirmed":False},NOW),"DA VERIFICARE")
    def test_future_deadline_alone_not_open(self):
        self.assertEqual(effective_status({"deadline":"2027-04-01","link_status":"raggiungibile"},NOW),"DA VERIFICARE")
    def test_expired_even_when_source_claims_open(self):
        row={"deadline":"2025-11-01","source_open_confirmed":True,"link_status":"raggiungibile"}
        self.assertEqual(effective_status(row,NOW),"CHIUSO")
    def test_closed_stays_closed_without_deadline(self):
        self.assertEqual(effective_status({"status":"chiuso"},NOW),"CHIUSO")
    def test_upcoming_and_rolling(self):
        row={"opening_date":"2026-12-01","opening_evidence":"https://example.org/avviso"}
        self.assertEqual(effective_status(row,NOW),"IN ARRIVO")
        row={"rolling_confirmed":True,"rolling_evidence":"https://example.org/info","source_open_confirmed":True,"link_status":"raggiungibile"}
        self.assertEqual(effective_status(row,NOW),"APERTO")
    def test_informational_catalogue_page_is_not_an_open_application(self):
        entry={"opportunity_type":"altro avviso","status":"aperto",
               "source_open_confirmed":True,"deadline":"2027-03-01",
               "link_status":"raggiungibile"}
        self.assertEqual(effective_status(entry,NOW),"INFORMATIVO")

    def test_closed_historical_notice_stays_closed(self):
        entry={"opportunity_type":"altro avviso","deadline":"2025-01-01"}
        self.assertEqual(effective_status(entry,NOW),"CHIUSO")

    def test_informative_is_not_open_even_with_issuer_flag(self):
        entry={"opportunity_type":"altro avviso","source_open_confirmed":True,
               "deadline":"2027-01-01","link_status":"raggiungibile"}
        self.assertEqual(annotate(entry,NOW)["funding_status"],"INFORMATIVO")

    def test_no_eligibility_penalty(self):
        row={"source_open_confirmed":True,"deadline":"2027-01-01","link_status":"raggiungibile","eligibility":"partner da reperire","relevance":98}
        self.assertEqual(annotate(row,NOW)["funding_status"],"APERTO")
        self.assertEqual(row["relevance"],98)
if __name__=="__main__":
    unittest.main()
