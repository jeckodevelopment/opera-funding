"""Regression coverage for post-scan integrity gate."""
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from scan_integrity import validate_scan

NOW=datetime(2026,11,18,22,0,tzinfo=timezone.utc)

def example():
    rows=[
        {"public_id":1,"funding_status":"APERTO","adequacy_label":"ALTA",
         "assessment_review_status":"PARZIALE",
         "eligibility_condition_status":"informazioni_insufficienti",
         "eligibility_specific_requirements":[],
         "applicant_requirement_comparison":[],
         "applicant_comparison_counts":{"compatibile":0,"potenzialmente_incompatibile":0,"da_verificare":0},"application_path":"integrare_verifica_documentale",
         "application_next_actions":["Verificare condizioni"],"application_eligibility_verified":False},
        {"public_id":2,"funding_status":"CHIUSO","adequacy_label":"BASSA",
         "assessment_review_status":"FONTE NON SUFFICIENTE",
         "eligibility_condition_status":"informazioni_insufficienti",
         "eligibility_specific_requirements":[],
         "applicant_requirement_comparison":[],
         "applicant_comparison_counts":{"compatibile":0,"potenzialmente_incompatibile":0,"da_verificare":0},"application_path":"integrare_verifica_documentale",
         "application_next_actions":["Verificare condizioni"],"application_eligibility_verified":False},
    ]
    report={"checked_at":"2026-11-18T21:55:30+00:00",
            "coverage":{"totals":{"all":2,"open":1,"closed":1,"upcoming":0,"unverified":0}},
            "assessment_coverage":{"total":2},
            "catalog_reconciliation":{"coverage":{"catalogo":{"total":2},"aperte":{"total":1},
                "aperte_alta_media":{"total":1}}},
            "open_eligibility_review":{
                "open_total":1,"in_queue":1,
                "condition_status_counts":{"informazioni_insufficienti":1},
                "items":[{"public_id":1,"tasks":["Verificare beneficiari"]}]
            }}
    return rows,report

class ScanIntegrityTests(unittest.TestCase):
    def check(self, rows, report):
        return validate_scan(rows,report,now=NOW)

    def test_consistent_report_passes(self):
        self.assertEqual(self.check(*example()),[])

    def test_missing_operational_path_fails(self):
        rows,report=example()
        del rows[0]["application_path"]
        self.assertTrue(any("Percorso operativo" in x for x in self.check(rows,report)))

    def test_reconciliation_mismatch_fails(self):
        rows,report=example()
        report["catalog_reconciliation"]["coverage"]["aperte_alta_media"]["total"]=2
        self.assertTrue(any("Riconciliazione" in x for x in self.check(rows,report)))

    def test_stale_report_fails(self):
        rows,report=example()
        report["checked_at"]="2026-11-17T21:55:30+00:00"
        self.assertTrue(any("Timestamp" in x for x in self.check(rows,report)))

    def test_missing_queue_fails(self):
        rows,report=example()
        del report["open_eligibility_review"]
        self.assertTrue(any("Coda" in x for x in self.check(rows,report)))

    def test_missing_assessment_fails(self):
        rows,report=example()
        del rows[0]["adequacy_label"]
        self.assertTrue(any("Valutazioni" in x for x in self.check(rows,report)))

    def test_catalog_audit_detects_stale_retired_open(self):
        rows,report=example()
        report["catalog_audit"]={
            "records_checked":2,"status_counts":{"APERTO":1,"CHIUSO":1},
            "unassessed_ids":[],"duplicate_public_ids":[],
            "retired_open_ids":[1]}
        self.assertTrue(any("fonte ritirata" in x for x in self.check(rows,report)))

    def test_catalog_audit_reconciles_all_records(self):
        rows,report=example()
        report["catalog_audit"]={
            "records_checked":3,"status_counts":{"APERTO":1,"CHIUSO":1},
            "unassessed_ids":[],"duplicate_public_ids":[],
            "retired_open_ids":[]}
        self.assertTrue(any("Audit catalogo" in x for x in self.check(rows,report)))

    def test_missing_applicant_comparison_fails(self):
        rows,report=example()
        del rows[0]["applicant_requirement_comparison"]
        self.assertTrue(any("Valutazioni" in x for x in self.check(rows,report)))

    def test_public_id_duplicate_fails(self):
        rows,report=example()
        rows[1]["public_id"]=1
        self.assertTrue(any("duplicato" in x for x in self.check(rows,report)))

    def test_open_queue_mismatch_fails(self):
        rows,report=example()
        report["open_eligibility_review"]["items"][0]["public_id"]=2
        self.assertTrue(any("non coincide" in x for x in self.check(rows,report)))

    def test_counts_mismatch_fails(self):
        rows,report=example()
        report["coverage"]["totals"]["open"]=2
        self.assertTrue(any("coverage.totals.open" in x for x in self.check(rows,report)))

    def test_information_bucket_is_accepted_and_reconciled(self):
        rows,report=example()
        rows[1]["funding_status"]="INFORMATIVO"
        report["coverage"]["totals"]["closed"]=0
        report["coverage"]["totals"]["informational"]=1
        self.assertEqual(self.check(rows,report),[])

    def test_catalog_quality_is_reconciled_against_real_rows(self):
        from catalog_quality import catalog_quality
        rows,report=example()
        rows[1]["assessment_document_issues"]=[{"reason":"download_non_riuscito",
                                                  "source":"https://example.org/bando.pdf"}]
        report["catalog_quality"]=catalog_quality(rows)
        self.assertEqual(self.check(rows,report),[])
        report["catalog_quality"]["document_issues"]["total_records"]=0
        self.assertTrue(any("qualità catalogo" in p for p in self.check(rows,report)))

    def test_admission_queue_integrity(self):
        from catalog_admission import split_new_catalogue
        rows,report=example()
        pending_row={"id":"https://example.org/new","url":"https://example.org/new",
                     "title":"Bando culturale da esaminare",
                     "opportunity_type":"finanziamento potenziale"}
        _,pending,entry=split_new_catalogue([pending_row],set())
        report["catalog_admission"]=entry
        self.assertEqual(validate_scan(rows,report,now=NOW,pending_rows=pending),[])
        report["catalog_admission"]["in_review"]=0
        errors=validate_scan(rows,report,now=NOW,pending_rows=pending)
        self.assertTrue(any("Riepilogo istruttorie" in x for x in errors))

    def test_historical_record_temporarily_unavailable_does_not_break_gate(self):
        rows,report=example()
        rows[0]["catalog_admission_status"]="valutata_prima_pubblicazione"
        rows[0]["link_status"]="da verificare"
        report["catalog_admission"]={
            "new_published":0,"published_ids":[],"in_review":0,"pending_ids":[]}
        self.assertEqual(validate_scan(rows,report,now=NOW,pending_rows=[]),[])

    def test_unknown_state_fails(self):
        rows,report=example()
        rows[1]["funding_status"]="BOH"
        self.assertTrue(any("Stato temporale" in x for x in self.check(rows,report)))

    def test_empty_catalog_fails(self):
        _,report=example()
        self.assertTrue(self.check([],report))

    def test_queue_missing_tasks_fails(self):
        rows,report=example()
        report["open_eligibility_review"]["items"][0]["tasks"]=[]
        self.assertTrue(any("senza verifiche" in x for x in self.check(rows,report)))

    def test_ordinary_scan_resyncs_after_queue_before_processing(self):
        workflow=(Path(__file__).resolve().parents[1]/".github/workflows/scan.yml").read_text()
        self.assertIn("group: funding-scan",workflow)
        self.assertIn("git fetch origin main",workflow)
        self.assertIn("git reset --hard origin/main",workflow)
        self.assertLess(workflow.index("git reset --hard origin/main"),
                        workflow.index("run: python src/scan.py"))
        self.assertLess(workflow.index("git reset --hard origin/main"),
                        workflow.index("run: python src/notify.py"))

    def test_historical_backfill_uses_fresh_main_and_stages_generated_data(self):
        workflow=(Path(__file__).resolve().parents[1]/".github/workflows/history-backfill.yml").read_text()
        self.assertIn("git reset --hard origin/main",workflow)
        self.assertIn("git add -A -- data/",workflow)
        self.assertLess(workflow.index("git reset --hard origin/main"),
                        workflow.index("python -u src/scan.py --history-backfill"))
        self.assertLess(workflow.index("git add -A -- data/"),
                        workflow.index("git rebase origin/main"))
        self.assertIn("group: funding-scan",workflow)
        # The one-off scan must not fire again on every ordinary src/scan.py edit.
        self.assertNotIn("      - 'src/scan.py'",workflow)

    def test_gate_runs_before_publication_and_notification(self):
        workflow=(Path(__file__).resolve().parents[1]/".github/workflows/scan.yml").read_text()
        integrity=workflow.index("run: python src/scan_integrity.py")
        publish=workflow.index("name: Commit updated public catalogue before notifications")
        notify=workflow.index("run: python src/notify.py")
        ledger=workflow.index("name: Commit notification delivery ledger")
        self.assertLess(integrity,publish)
        self.assertLess(publish,notify)
        self.assertLess(notify,ledger)
        self.assertIn("steps.integrity.outcome == 'success'",workflow)
        self.assertIn("steps.publish.outcome == 'success'",workflow)
        self.assertIn("always() && !cancelled()",workflow)

if __name__=="__main__":
    unittest.main()
