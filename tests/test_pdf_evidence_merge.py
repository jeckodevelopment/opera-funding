import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pdf_evidence import official_pdf_evidence


def response(url):
    r = Mock()
    r.url = url
    r.headers = {"Content-Type": "application/pdf"}
    r.iter_content.return_value = [b"%PDF-1.4 test bytes"]
    return r


class PdfEvidenceMergeTests(unittest.TestCase):
    def test_complementary_documents_preserve_each_fields_origin(self):
        base = "https://example.org/"
        documents = [{"url": base + "call.pdf"}, {"url": base + "faq.pdf"}]
        session = Mock()
        session.get.side_effect = [response(documents[0]["url"]), response(documents[1]["url"])]
        first = {"beneficiaries_excerpt": "Associazioni culturali ammesse alla candidatura"}
        second = {"requirements_excerpt": "Richiesto partenariato con ente educativo"}
        with patch("pdf_evidence.pdf_extract_evidence", side_effect=[first, second]):
            facts = official_pdf_evidence(documents, base + "bando", session, lambda url, s: True)
        self.assertEqual(facts["beneficiaries_excerpt"], first["beneficiaries_excerpt"])
        self.assertEqual(facts["requirements_excerpt"], second["requirements_excerpt"])
        self.assertEqual(facts["assessment_field_sources"], {
            "beneficiaries_excerpt": documents[0]["url"],
            "requirements_excerpt": documents[1]["url"]})
        self.assertEqual(facts["assessment_evidence_source"], documents[0]["url"])
        self.assertEqual(session.get.call_count, 2)

    def test_first_official_document_wins_conflicting_values(self):
        base = "https://example.org/"
        documents = [{"url": base + "call.pdf"}, {"url": base + "faq.pdf"}]
        session = Mock()
        session.get.side_effect = [response(x["url"]) for x in documents]
        with patch("pdf_evidence.pdf_extract_evidence", side_effect=[
            {"beneficiaries_excerpt": "Soltanto associazioni"},
            {"beneficiaries_excerpt": "Solo imprese", "requirements_excerpt": "Obbligo di cofinanziamento"}
        ]):
            facts = official_pdf_evidence(documents, base + "bando", session, lambda url, s: True)
        self.assertEqual(facts["beneficiaries_excerpt"], "Soltanto associazioni")
        self.assertEqual(facts["assessment_field_sources"]["beneficiaries_excerpt"], documents[0]["url"])
        self.assertEqual(facts["requirements_excerpt"], "Obbligo di cofinanziamento")

    def test_external_and_disallowed_documents_not_downloaded(self):
        session = Mock()
        facts = official_pdf_evidence([
            {"url": "https://external.org/bando.pdf"},
            {"url": "https://example.org/bando.pdf"},
        ], "https://example.org/info", session, lambda url, s: False)
        self.assertEqual(facts, {})
        session.get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
