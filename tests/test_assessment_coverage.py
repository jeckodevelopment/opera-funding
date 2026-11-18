"""Every grant gets an explainable opinion and an independent evidence status."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from assessment_coverage import annotate_assessment_coverage,assessment_coverage
from verification import pick_for_review,backlog_candidates

class AssessmentCoverageTests(unittest.TestCase):
    def test_new_record_is_always_prioritized_over_old_unreviewed(self):
        old={"old":{"id":"old","title":"Cultura","opportunity_type":"finanziamento potenziale",
                    "detail_checked":False}}
        candidates=[old["old"],{"id":"new","title":"Altra call","opportunity_type":"non classificato"}]
        self.assertEqual(pick_for_review(candidates,old,1),{"new"})

    def test_expired_and_informational_backlog_is_not_excluded(self):
        old={"a":{"id":"a","source_id":"iss","funding_status":"CHIUSO","opportunity_type":"finanziamento potenziale"},
             "b":{"id":"b","source_id":"iss","funding_status":"DA VERIFICARE","opportunity_type":"altro avviso"}}
        self.assertEqual({x["id"] for x in backlog_candidates(old,"iss",set())},{"a","b"})

    def test_unread_record_has_a_rating_but_no_document_review(self):
        row=annotate_assessment_coverage({"assessment_label":"MEDIA AFFINITÀ"})
        self.assertEqual(row["assessment_review_status"],"NON ESAMINATA")
        self.assertEqual(row["assessment_evidence_count"],0)
        self.assertEqual(len(row["assessment_missing_fields"]),4)

    def test_attempt_without_evidence_does_not_count_as_verified(self):
        row=annotate_assessment_coverage({"assessment_label":"BASSA AFFINITÀ",
                                           "detail_attempted_at":"2026-11-18T00:00:00Z"})
        self.assertEqual(row["assessment_review_status"],"FONTE NON SUFFICIENTE")

    def test_all_required_fields_do_not_certify_legal_eligibility(self):
        row=annotate_assessment_coverage({
            "detail_checked":True,"assessment_evidence_source":"https://example.org/",
            "programme_objectives_excerpt":"Promuovere la musica.",
            "funded_activities_excerpt":"Laboratori musicali.",
            "beneficiaries_excerpt":"Associazioni culturali.",
            "requirements_excerpt":"Richiesta sede in Italia.",
        })
        self.assertEqual(row["assessment_review_status"],"EVIDENZE RACCOLTE")
        self.assertEqual(assessment_coverage([row])["completely_verified_applicability"],0)

    def test_manual_source_review_remains_traceable(self):
        row=annotate_assessment_coverage({"assessment_reviewed_at":"2026-11-18",
                                           "assessment_label":"MEDIA AFFINITÀ"})
        self.assertEqual(row["assessment_review_status"],"REVISIONE DOCUMENTALE")

if __name__=="__main__":
    unittest.main()
