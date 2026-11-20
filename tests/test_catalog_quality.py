import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from catalog_quality import catalog_quality, diagnostic_review_class


class CatalogQualityTests(unittest.TestCase):
    def test_result_pdf_is_flagged_not_silently_cleared(self):
        issue={"reason":"nessuna_evidenza_estratta",
               "source":"https://example.org/Graduatoria-2026.pdf"}
        self.assertEqual(diagnostic_review_class(issue),
                         "verifica_allegato_potenzialmente_accessorio")
        row={"public_id":20,"funding_status":"CHIUSO",
             "assessment_document_issues":[issue]}
        result=catalog_quality([row])["document_issues"]
        self.assertEqual(result["total_records"],1)
        self.assertEqual(result["review_classes"]["verifica_allegato_potenzialmente_accessorio"],1)

    def test_different_texts_always_require_comparison(self):
        item={"reason":"testi_diversi_da_verificare",
              "source":"https://example.org/FAQ.pdf"}
        self.assertEqual(diagnostic_review_class(item),
                         "confrontare_documenti_e_priorita")

    def test_separates_source_backed_rolling_from_real_deadline_gap(self):
        rows=[
          {"public_id":1,"source_id":"sanpaolo","funding_status":"APERTO",
           "opportunity_type":"finanziamento potenziale","rolling_confirmed":True,
           "rolling_evidence":"https://example.org/sportello","url":"https://example.org/1"},
          {"public_id":2,"source_id":"piemonte","funding_status":"IN ARRIVO",
           "opportunity_type":"call progettuale da verificare",
           "opening_evidence":"https://example.org/apertura","url":"https://example.org/2"},
          {"public_id":3,"source_id":"test","funding_status":"CHIUSO",
           "opportunity_type":"finanziamento potenziale","url":"https://example.org/3"},
          {"public_id":4,"source_id":"test","funding_status":"INFORMATIVO",
           "opportunity_type":"altro avviso"}]
        report=catalog_quality(rows)["missing_deadline"]
        self.assertEqual(report["total"],3)
        self.assertEqual(report["by_classification"],{
          "apertura_futura":1,"scadenza_da_documentare":1,"sportello_verificato":1})
        self.assertEqual([x["public_id"] for x in report["cases"]],[1,2,3])

    def test_diagnostics_are_preserved_and_prioritized_without_fabrication(self):
        rows=[
          {"public_id":13,"source_id":"x","funding_status":"CHIUSO",
           "assessment_document_issues":[{"source":"https://example.org/old.pdf",
                                           "reason":"testo_non_estratto"}]},
          {"public_id":5,"source_id":"y","funding_status":"IN ARRIVO",
           "assessment_document_issues":[{"source":"https://example.org/new.pdf",
                                           "reason":"download_non_riuscito"},
                                          {"source":"https://example.org/faq.pdf",
                                           "reason":"testi_diversi_da_verificare",
                                           "field":"beneficiaries_excerpt"}]}]
        report=catalog_quality(rows)["document_issues"]
        self.assertEqual(report["total_records"],2)
        self.assertEqual(report["total_diagnostics"],3)
        self.assertEqual([x["public_id"] for x in report["cases"]],[5,13])
        self.assertEqual(report["reasons"]["download_non_riuscito"],1)
        self.assertEqual(report["cases"][0]["issues"][1]["field"],"beneficiaries_excerpt")

    def test_missing_end_date_does_not_make_informative_notice_a_candidate(self):
        rows=[{"public_id":1,"opportunity_type":"altro avviso",
               "funding_status":"INFORMATIVO"}]
        self.assertEqual(catalog_quality(rows)["missing_deadline"]["total"],0)


if __name__=="__main__":
    unittest.main()
