import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from detail import extract, safe_same_origin

class DetailTests(unittest.TestCase):
    def test_explicit_deadline_and_official_links(self):
        html='''<html><main><h1>Bando musica</h1><p>Scadenza: 25/12/2027</p><p>Contributo massimo: € 20.000</p><a href="/files/bando.pdf">Testo del bando</a><a href="/faq">FAQ</a></main></html>'''
        info=extract(html,"https://example.org/opportunities/1")
        self.assertEqual(info["deadline"],"2027-12-25")
        self.assertEqual(len(info["documents"]),3)
        self.assertIn("20.000",info["amount"])
    def test_publication_date_is_not_deadline(self):
        info=extract("<main>Pubblicato il 02/03/2026</main>","https://example.org/bando")
        self.assertIsNone(info["deadline"])
    def test_external_and_insecure_documents_not_stored(self):
        html='<main><a href="https://evil.example/bando.pdf">Bando</a><a href="http://example.org/faq">FAQ</a></main>'
        info=extract(html,"https://example.org/bando")
        self.assertEqual(len(info["documents"]),1)
        self.assertFalse(safe_same_origin("https://another.org/", "https://example.org/"))
    def test_page_links_only(self):
        self.assertTrue(safe_same_origin("https://example.org/faq","https://example.org/bando"))
        self.assertFalse(safe_same_origin("https://example.org.evil.test/file","https://example.org/bando"))
if __name__=="__main__":
    unittest.main()
