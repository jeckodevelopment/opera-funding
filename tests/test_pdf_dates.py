import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from pdf_dates import pdf_deadline_from_documents, extract_pdf_deadline
from datetime import date

class PdfDateTests(unittest.TestCase):
    def test_italian_written_month_and_no_publication_date(self):
        page=Mock()
        page.extract_text.return_value="Pubblicazione 15 gennaio 2026. Le domande devono essere presentate entro il 24 novembre 2026 alle ore 12."
        with patch("pdf_dates.PdfReader",return_value=Mock(pages=[page])):
            self.assertEqual(extract_pdf_deadline(b"%PDF",today=date(2026,11,16)),"2026-11-24")
    def test_explicit_submission_range_returns_closing_date(self):
        page=Mock()
        page.extract_text.return_value="Presentazione delle domande dal 01/02/2027 al 20/03/2027."
        with patch("pdf_dates.PdfReader",return_value=Mock(pages=[page])):
            self.assertEqual(extract_pdf_deadline(b"%PDF",today=date(2026,11,16)),"2027-03-20")
    def test_pub_date_without_filing_deadline_is_not_a_deadline(self):
        page=Mock()
        page.extract_text.return_value="Data pubblicazione 10/11/2026. Attività dal 01/01/2027 al 31/12/2027."
        with patch("pdf_dates.PdfReader",return_value=Mock(pages=[page])):
            self.assertIsNone(extract_pdf_deadline(b"%PDF",today=date(2026,11,16)))
    def test_try_second_official_pdf_when_first_has_no_deadline(self):
        docs=[{"url":"https://official.example/grant"},
              {"url":"https://official.example/guide.pdf"},
              {"url":"https://official.example/bando.pdf"}]
        response_a=Mock(url=docs[1]["url"],headers={"Content-Type":"application/pdf"})
        response_a.iter_content.return_value=[b"one"]
        response_b=Mock(url=docs[2]["url"],headers={"Content-Type":"application/pdf"})
        response_b.iter_content.return_value=[b"two"]
        session=Mock()
        session.get.side_effect=[response_a,response_b]
        with patch("pdf_dates.extract_pdf_deadline",side_effect=[None,"2027-02-20"]):
            result=pdf_deadline_from_documents(docs,"https://official.example",session,lambda u,s:True)
        self.assertEqual(result,("2027-02-20",docs[2]["url"]))
        self.assertEqual(session.get.call_count,2)
        response_a.close.assert_called_once()
        response_b.close.assert_called_once()
    def test_direct_pdf_can_be_inspected_as_first_document(self):
        url="https://official.example/call.pdf"
        response=Mock(url=url,headers={"Content-Type":"application/pdf"})
        response.iter_content.return_value=[b"pdf"]
        session=Mock()
        session.get.return_value=response
        with patch("pdf_dates.extract_pdf_deadline",return_value="2027-03-05"):
            result=pdf_deadline_from_documents([{"url":url}],"https://official.example",session,lambda u,s:True,include_first=True)
        self.assertEqual(result,("2027-03-05",url))
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
