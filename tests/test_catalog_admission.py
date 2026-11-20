import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from catalog_admission import admission_reasons,split_new_catalogue

def complete(**kw):
    row={
        "id":"https://example.org/call","url":"https://example.org/call",
        "public_id":300,"title":"Bando internazionale per progetti culturali",
        "source_id":"piemonte","opportunity_type":"finanziamento potenziale",
        "funding_status":"APERTO","link_status":"raggiungibile",
        "source_open_confirmed":True,"deadline":"2027-03-01",
        "deadline_source":"https://example.org/call",
        "detail_checked":True,
        "assessment_evidence_source":"https://example.org/call",
        "programme_objectives_excerpt":"Supporto a laboratori artistici.",
        "funded_activities_excerpt":"Laboratori di musica per studenti.",
        "beneficiaries_excerpt":"Enti culturali riconosciuti.",
        "requirements_excerpt":"Progetto culturale e bilancio preventivo.",
        "assessment_reason":"Pertinenza documentata ma requisiti da confermare.",
        "adequacy_reason":"Coerenza con attività culturali.",
        "adequacy_label":"MEDIA",
        **kw
    }
    return row

class AdmissionTests(unittest.TestCase):
    def test_full_evidence_admitted_once(self):
        row=complete()
        published,pending,report=split_new_catalogue([row],set())
        self.assertEqual(len(published),1)
        self.assertEqual(pending,[])
        self.assertEqual(report["new_published"],1)
        self.assertEqual(row["catalog_admission_status"],"valutata_prima_pubblicazione")

    def test_uninspected_entry_never_public(self):
        row=complete(detail_checked=False,requirements_excerpt="")
        published,pending,report=split_new_catalogue([row],set())
        self.assertEqual(published,[])
        self.assertEqual(report["in_review"],1)
        self.assertIn("fonte_non_esaminata",pending[0]["admission_reasons"])
        self.assertIn("evidenza_mancante:requirements_excerpt",pending[0]["admission_reasons"])

    def test_aggregator_without_primary_source_is_held(self):
        row=complete(source_id="volto",assessment_evidence_source="https://infobandi.csvnet.it/one")
        self.assertIn("fonte_ente_erogatore_non_verificata",admission_reasons(row))

    def test_rolling_call_no_invented_deadline(self):
        row=complete(deadline=None,deadline_source=None,
                     rolling_confirmed=True,rolling_evidence="https://example.org/sportello")
        self.assertEqual(admission_reasons(row),[])

    def test_disputed_documents_block_admission(self):
        row=complete(assessment_document_issues=[{"reason":"testi_diversi_da_verificare"}])
        self.assertIn("documenti_con_anomalie",admission_reasons(row))

    def test_legacy_record_not_suppressed(self):
        row=complete(detail_checked=False,requirements_excerpt="")
        pub,pending,report=split_new_catalogue([row],{row["id"]})
        self.assertEqual(len(pub),1)
        self.assertEqual(len(pending),0)
        self.assertEqual(report["new_published"],0)

    def test_informative_requires_provenance_and_type(self):
        row=complete(opportunity_type="altro avviso",funding_status="INFORMATIVO",
                     type_reason="Pagina di informazioni non candidabile")
        self.assertEqual(admission_reasons(row),[])
        row.pop("type_reason")
        self.assertIn("natura_informativa_non_documentata",admission_reasons(row))

    def test_unverified_state_must_not_be_published(self):
        row=complete(funding_status="DA VERIFICARE")
        self.assertIn("stato_candidatura_non_verificato",admission_reasons(row))

    def test_no_fallback_assessment_can_pass(self):
        row=complete(assessment_fallback=True)
        self.assertIn("valutazione_non_motivata",admission_reasons(row))
