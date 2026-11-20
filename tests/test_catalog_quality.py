import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from catalog_quality import catalog_quality


class CatalogQualityTests(unittest.TestCase):
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
