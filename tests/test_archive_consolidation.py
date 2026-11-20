"""Archival case decisions are explicit, conservative and stable."""
import sys
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from archive_consolidation import (NON_FUNDING,HISTORICAL,load_archive_reviews,
                                   apply_archive_reviews,archive_review_summary)

class ArchiveConsolidationTests(unittest.TestCase):
    def test_full_known_case_registry_is_nonduplicated_and_explained(self):
        reviews=load_archive_reviews(ROOT/"config/archive_catalog_reviews.json")
        self.assertEqual(len(reviews),39)
        self.assertEqual(sum(len(x["observed_issue_signatures"]) for x in reviews),57)
        self.assertEqual(sum(x["disposition"]==NON_FUNDING for x in reviews),25)
        self.assertEqual(sum(x["disposition"]==HISTORICAL for x in reviews),14)

    def test_rebuild_diagnostics_before_reviewing_archival_fingerprint(self):
        from assessment_coverage import annotate_assessment_coverage
        review=load_archive_reviews(ROOT/"config/archive_catalog_reviews.json")
        entry=next(x for x in review if x["public_id"]==16)
        reason,url,field=entry["observed_issue_signatures"][0].split("|")
        self.assertEqual(reason,"testi_diversi_da_verificare")
        row={"public_id":16,"url":entry["url"],"source_id":entry["source_id"],
             "funding_status":"CHIUSO","opportunity_type":"finanziamento potenziale",
             "assessment_document_issues":[],
             "assessment_document_discrepancies":[
                 {"other_source":url,"field":field}]}
        annotate_assessment_coverage(row)
        apply_archive_reviews([row],review,"2026-11-20")
        self.assertEqual(row["archive_case_review"]["disposition"],NON_FUNDING)
        self.assertEqual(len(row["assessment_document_issues"]),1)
        self.assertEqual(row["opportunity_type"],"altro avviso")

    def test_real_archival_reference_is_not_funding_and_diagnostic_is_preserved(self):
        review=load_archive_reviews(ROOT/"config/archive_catalog_reviews.json")
        entry=next(x for x in review if x["public_id"]==16)
        original=entry["observed_issue_signatures"][0].split("|")
        row={"public_id":16,"url":entry["url"],"source_id":entry["source_id"],
             "funding_status":"CHIUSO","opportunity_type":"finanziamento potenziale",
             "assessment_document_issues":[{"reason":original[0],"source":original[1],
                                           "field":original[2] or None}]}
        apply_archive_reviews([row],review,"2026-11-20")
        self.assertEqual(row["opportunity_type"],"altro avviso")
        self.assertEqual(row["archive_case_review"]["disposition"],NON_FUNDING)
        self.assertFalse(row["archive_case_review"]["pdf_contents_verified"])
        self.assertEqual(len(row["assessment_document_issues"]),1)

    def test_historical_grant_remains_a_grant_with_raw_issues(self):
        review=load_archive_reviews(ROOT/"config/archive_catalog_reviews.json")
        entry=next(x for x in review if x["public_id"]==24)
        parts=[x.split("|") for x in entry["observed_issue_signatures"]]
        row={"public_id":24,"url":entry["url"],"source_id":entry["source_id"],
             "funding_status":"CHIUSO","opportunity_type":"finanziamento potenziale",
             "assessment_document_issues":[dict(reason=x[0],source=x[1],field=x[2] or None)
                                            for x in parts]}
        apply_archive_reviews([row],review,"2026-11-20")
        self.assertEqual(row["opportunity_type"],"finanziamento potenziale")
        self.assertEqual(row["archive_case_review"]["disposition"],HISTORICAL)
        self.assertEqual(len(row["assessment_document_issues"]),len(parts))

    def test_reopened_or_revised_document_revokes_archival_decision(self):
        review=load_archive_reviews(ROOT/"config/archive_catalog_reviews.json")
        entry=next(x for x in review if x["public_id"]==16)
        row={"public_id":16,"url":entry["url"],"source_id":entry["source_id"],
             "funding_status":"APERTO","opportunity_type":"finanziamento potenziale",
             "assessment_document_issues":[]}
        apply_archive_reviews([row],review,"2026-11-20")
        self.assertEqual(row["opportunity_type"],"finanziamento potenziale")
        self.assertEqual(row["archive_case_review"]["disposition"],"riesame_necessario")

    def test_new_issue_is_not_hidden_by_closed_archival_register(self):
        review=load_archive_reviews(ROOT/"config/archive_catalog_reviews.json")
        row={"public_id":999,"assessment_document_issues":[{"reason":"pdf_non_interpretabile"}]}
        result=archive_review_summary([row],review)
        self.assertEqual(result["new_unreviewed_ids"],[999])
        self.assertEqual(result["missing_registry_ids"],sorted(x["public_id"] for x in review))

if __name__=="__main__":
    unittest.main()
