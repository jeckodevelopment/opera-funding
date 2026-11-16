import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from quality import reconcile_status, check_link

class QualityTests(unittest.TestCase):
    def test_expired_open_is_closed(self):
        row={"status":"aperto (fonte indice)","deadline":"2025-05-01"}
        self.assertEqual(reconcile_status(row,date(2026,11,16))["status"],"chiuso")
    def test_undated_open_is_unverified(self):
        row={"status":"aperto (fonte indice)","deadline":None}
        self.assertEqual(reconcile_status(row,date(2026,11,16))["status"],"non verificato")
    def test_link_404(self):
        reply=Mock(status_code=404,url="https://example.org/old-bando")
        reply.__enter__=Mock(return_value=reply)
        reply.__exit__=Mock(return_value=False)
        session=Mock()
        session.get.return_value=reply
        row=check_link({"url":"https://example.org/old-bando"},session,"2026-11-16T18:00:00Z")
        self.assertEqual(row["link_status"],"non disponibile")
        self.assertEqual(row["link_http_status"],404)
    def test_connection_error_does_not_mark_missing(self):
        import requests
        session=Mock()
        session.get.side_effect=requests.Timeout()
        row=check_link({"url":"https://example.org/bando"},session,"2026-11-16T18:00:00Z")
        self.assertEqual(row["link_status"],"da verificare")
if __name__=="__main__":
    unittest.main()
