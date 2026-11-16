import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from pdf_dates import pdf_deadline_from_documents

class PdfDateTests(unittest.TestCase):
    def test_ignores_third_party_attachments(self):
        docs=[{"url":"https://official.example/bando"}, {"url":"https://external.example/other.pdf"}]
        session=Mock()
        deadline,source=pdf_deadline_from_documents(docs,"https://official.example/bando",session,lambda u,s: True)
        self.assertIsNone(deadline)
        self.assertIsNone(source)
        session.get.assert_not_called()

    def test_skips_attachments_when_robots_disallows(self):
        docs=[{"url":"https://official.example/bando"},{"url":"https://official.example/docs/call.pdf"}]
        session=Mock()
        result=pdf_deadline_from_documents(docs,"https://official.example/bando",session,lambda u,s: False)
        self.assertEqual(result,(None,None))
        session.get.assert_not_called()

    def test_uses_first_valid_source_pdf(self):
        docs=[{"url":"https://official.example/bando"},{"url":"https://official.example/docs/call.pdf"}]
        response=Mock(status_code=200,url="https://official.example/docs/call.pdf",
            headers={"Content-Type":"application/pdf"})
        response.iter_content.return_value=[b"%PDF-1.4\n"]
        with patch("pdf_dates.extract_pdf_deadline",return_value="2027-02-04"):
            session=Mock()
            session.get.return_value=response
            result=pdf_deadline_from_documents(docs,"https://official.example/bando",session,lambda u,s: True)
        self.assertEqual(result,("2027-02-04","https://official.example/docs/call.pdf"))
        response.close.assert_called_once()
if __name__=="__main__":
    unittest.main()
