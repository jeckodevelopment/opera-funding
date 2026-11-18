"""Only explicitly open calls enter the operational review queue."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from open_review_queue import build_open_review_queue, review_tasks

def row(ident, **fields):
    return {
        "public_id":ident, "title":"Bando "+str(ident),
        "url":"https://example.org/bando/"+str(ident),
        "funding_status":"APERTO",
        "assessment_review_status":"PARZIALE",
        "eligibility_condition_status":"informazioni_insufficienti",
        **fields
    }

class OpenReviewQueueTests(unittest.TestCase):
    def test_excludes_closed_and_unconfirmed_without_guessing(self):
        rows=[
            row(1, funding_status="CHIUSO",deadline="2026-11-20"),
            row(2, funding_status="DA VERIFICARE",deadline="2026-11-21"),
            row(3, deadline="2026-11-22"),
        ]
        result=build_open_review_queue(rows,"2026-11-18")
        self.assertEqual(result["open_total"],1)
        self.assertEqual(result["items"][0]["public_id"],3)

    def test_urgent_deadline_first_then_eligibility_condition(self):
        rows=[
            row(1,deadline="2027-02-01"),
            row(2,deadline="2026-11-23",eligibility_condition_status="condizionata"),
            row(3,deadline="2026-12-07",eligibility_condition_status="potenzialmente_incompatibile"),
            row(4,deadline="2026-11-22"),
        ]
        result=build_open_review_queue(rows,"2026-11-18")
        self.assertEqual([x["public_id"] for x in result["items"]],[2,4,3,1])
        self.assertEqual(result["items"][0]["days_remaining"],5)

    def test_ambiguous_deadline_is_not_invented(self):
        rows=[row(1,deadline="rolling"),row(2,deadline="2025-02-01")]
        result=build_open_review_queue(rows,"2026-11-18")
        self.assertEqual([x["deadline"] for x in result["items"]],[None,None])
        self.assertTrue(all(x["days_remaining"] is None for x in result["items"]))

    def test_relevant_tasks_for_operaplus_and_source_citations(self):
        data=row(143,
            assessment_evidence_source="https://example.org/bando",
            beneficiaries_excerpt="Associazioni culturali",
            eligibility_condition_status="condizionata",
            eligibility_specific_requirements=[{"category":"partenariato"}],
            applicant_requirement_comparison=[
                {"category":"partenariato","status":"da_verificare",
                 "source":"https://example.org/bando.pdf"}],
            assessment_missing_fields=["Attività finanziabili","Vincoli e requisiti"],
            assessment_document_issues=[{"source":"https://example.org/faq.pdf",
                                         "reason":"testo_non_estratto"}],
        )
        result=build_open_review_queue([data],"2026-11-18")
        entry=result["items"][0]
        self.assertEqual(entry["public_id"],143)
        self.assertEqual(entry["pending_conditions"],1)
        self.assertEqual(entry["condition_status"],"condizionata")
        self.assertTrue(any("partenariato" in t for t in entry["tasks"]))
        self.assertTrue(any("documentazione ufficiale" in t for t in entry["tasks"]))
        self.assertTrue(any("attività effettivamente" in t for t in entry["tasks"]))
        self.assertIn("https://example.org/bando.pdf",entry["sources"])
        self.assertEqual(result["specific_requirement_category_counts"]["partenariato"],1)

    def test_limit_never_changes_aggregate_counts(self):
        result=build_open_review_queue([row(1),row(2),row(3)],"2026-11-18",limit=1)
        self.assertEqual(result["open_total"],3)
        self.assertEqual(result["in_queue"],1)
        self.assertEqual(result["condition_status_counts"]["informazioni_insufficienti"],3)

    def test_missing_evidence_is_not_presented_as_verified(self):
        tasks=review_tasks(row(1))
        self.assertTrue(any("soggetti possono" in x for x in tasks))
        self.assertTrue(any("fonte ufficiale" in x for x in tasks))

if __name__=="__main__":
    unittest.main()
