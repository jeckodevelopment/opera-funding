import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from structured import structured_facts
from priority import check_priority

PAGE="""<html><main>
<h1>L.R. 14/2016 art. 20 – contributi ad associazioni</h1>
<p>Stato Aperto</p>
<p>Domande dal Lun, 02/11/2026 - 09:00</p>
<p>Scadenza Mar, 24/11/2026 - 12:00</p>
<p>Rivolto a Enti pubblici Terzo settore</p>
</main></html>"""
URL="https://bandi.regione.piemonte.it/contributi-finanziamenti/manifestazioni"

class StructuredTests(unittest.TestCase):
    def test_volto_explicit_deadline_of_grant(self):
        html="<main><h1>Dora in Avanti</h1><p>Scadenza del bando: 20 Novembre 2026</p><p>Entro il 7 dicembre la fondazione selezionerà i candidati.</p></main>"
        facts=structured_facts(html,"https://volontariatotorino.it/bandi/dora-in-avanti/")
        self.assertEqual(facts["deadline"],"2026-11-20")
        self.assertFalse(facts["source_open_confirmed"])
    def test_mic_online_filing_window(self):
        html="<main><h1>Rievocazione storica 2027</h1><p>Dalle ore 16:00 del 3 novembre 2026 fino alle ore 16:00 del 31 gennaio 2027 è disponibile, sulla piattaforma telematica DOS-Cultura, la modulistica per la compilazione e l’invio delle domande di contributo.</p></main>"
        facts=structured_facts(html,"https://spettacolo.cultura.gov.it/bando-rievocazione-storica-2027/")
        self.assertEqual(facts["opening_date"],"2026-11-03")
        self.assertEqual(facts["deadline"],"2027-01-31")
        self.assertTrue(facts["source_open_confirmed"])
        self.assertTrue(facts["status_evidence"])
    def test_mic_dates_without_filing_not_open(self):
        html="<main>Dal 3 novembre 2026 fino al 31 gennaio 2027 si svolgerà il festival.</main>"
        facts=structured_facts(html,"https://spettacolo.cultura.gov.it/festival/")
        self.assertIsNone(facts["deadline"])
        self.assertFalse(facts["source_open_confirmed"])
    def test_alcotra_closed_written_month(self):
        html="<main><h1>Terzo bando</h1><h2>Bando chiuso il 31 gennaio 2025 alle ore 12:00</h2></main>"
        facts=structured_facts(html,"https://interreg-alcotra.eu/it/terzo-bando-progetti-singoli")
        self.assertEqual(facts["deadline"],"2025-01-31")
        self.assertTrue(facts["closure_confirmed"])
    def test_csvnet_explicit_italian_deadline(self):
        html="<main><h1>Bando lettura</h1><div>SCADENZA</div><div>13 novembre 2026 alle ore 13:00</div><div>Pubblicato il 25 ottobre 2026</div></main>"
        facts=structured_facts(html,"https://infobandi.csvnet.it/bando-educare-alla-lettura-2026/")
        self.assertEqual(facts["deadline"],"2026-11-13")
        self.assertFalse(facts["source_open_confirmed"])
    def test_alcotra_explicit_open_and_close_fields(self):
        html="<main><h1>Quarto bando progetti maturi</h1><p>Data di apertura 01/07/2025</p><p>Data di chiusura 31/10/2025</p></main>"
        facts=structured_facts(html,"https://interreg-alcotra.eu/it/quarto-bando-progetti-singoli-finestra-1-progetti-maturi")
        self.assertEqual(facts["opening_date"],"2025-07-01")
        self.assertEqual(facts["deadline"],"2025-10-31")
    def test_torino_youth_climate_official_submission_deadline(self):
        html="<main><h1>Torino Youth Climate Action Fund</h1><p>Termine di presentazione delle proposte progettuali: ore 12.00 del 8 ottobre 2026</p></main>"
        result=structured_facts(html,"https://bandi.comune.torino.it/avviso/avviso-pubblico-torino-youth-climate-action-fund-lassegnazione-contributi-sostegno-della")
        self.assertEqual(result["deadline"],"2026-10-08")
        self.assertFalse(result["source_open_confirmed"])
    def test_torino_official_submission_but_no_date(self):
        html="<main>Termine di presentazione delle proposte progettuali da definire</main>"
        self.assertIsNone(structured_facts(html,"https://bandi.comune.torino.it/avviso/clima")["deadline"])
    def test_torino_application_range_textual_dates(self):
        html="<main><p>Dal 15 ottobre 2026 al 2 novembre 2026 entro le ore 18:00 è possibile presentare la richiesta.</p></main>"
        facts=structured_facts(html,"https://bandi.comune.torino.it/avviso/3deg-avviso-pubblico-concessione-contributi-ordinari-altri-benefici-economici")
        self.assertEqual(facts["deadline"],"2026-11-02")
        self.assertEqual(facts["opening_date"],"2026-10-15")
    def test_not_generic_project_period(self):
        html="<main><p>Il progetto si svolge dal 15 ottobre 2026 al 2 novembre 2026</p></main>"
        facts=structured_facts(html,"https://bandi.comune.torino.it/avviso/evento")
        self.assertIsNone(facts["deadline"])
    def test_official_description_for_card(self):
        html='<html><head><meta name="description" content="Sostegno a progetti culturali che coinvolgono giovani e comunità locali del Piemonte."></head><body><main>Stato: Aperto</main></body></html>'
        facts=structured_facts(html,"https://bandi.regione.piemonte.it/contributi-finanziamenti/progetti")
        self.assertIn("progetti culturali", facts["summary"])

    def test_crt_multiple_windows_select_latest(self):
        html="<main><p>1° scadenza chiusa il 27 febbraio 2026</p><p>2° scadenza: 15 settembre 2026</p></main>"
        facts=structured_facts(html,"https://www.fondazionecrt.it/bandi-progetti/note-sipari/")
        self.assertEqual(facts["deadline"],"2026-09-15")
    def test_crt_date_range_uses_closing_date(self):
        html="<main><p>Seconda scadenza: tra il 01/07/2026 e il 15/10/2026</p></main>"
        facts=structured_facts(html,"https://www.fondazionecrt.it/bandi-progetti/arte-cultura-ordinarie/")
        self.assertEqual(facts["deadline"],"2026-10-15")
    def test_crt_special_rule_not_applied_to_unrelated_domain(self):
        html="<main>2° scadenza: 15 settembre 2026</main>"
        facts=structured_facts(html,"https://other.example/bando")
        self.assertIsNone(facts["deadline"])
    def test_eu_english_status_dates(self):
        page="<html><main><p>Opportunity status: open</p><h1>Residency hosts</h1><p>Opening date: 15 October 2026, 9:00 CEST</p><p>Deadline: 18 January 2027, 23:59 CET</p></main></html>"
        facts=structured_facts(page,"https://culture.ec.europa.eu/culture-moves-europe/call-for-residency-hosts")
        self.assertTrue(facts["source_open_confirmed"])
        self.assertEqual(facts["opening_date"],"2026-10-15")
        self.assertEqual(facts["deadline"],"2027-01-18")
        self.assertTrue(facts["status_evidence"])
    def test_eu_closed_status(self):
        page="<main><p>Opportunity status: closed</p><p>Deadline: 5 May 2026</p></main>"
        facts=structured_facts(page,"https://culture.ec.europa.eu/funding/calls/closed")
        self.assertTrue(facts["closure_confirmed"])
        self.assertFalse(facts["source_open_confirmed"])
        self.assertEqual(facts["deadline"],"2026-05-05")
    def test_festival_two_windows_earliest_upcoming(self):
        html="<html><main><p>Stato: IN CORSO</p><p>Data scadenza: 05/04/2027</p><p>Per i festival da aprile ad agosto 2027 le proposte dovranno pervenire entro il 03 dicembre 2026 alle ore 15:00.</p><p>Per i festival da settembre 2027 a marzo 2028 le proposte dovranno pervenire entro il 5 aprile 2027 alle ore 15:00.</p></main></html>"
        facts=structured_facts(html,"https://www.compagniadisanpaolo.it/it/contributi/linee-guida-per-i-festival-partecipativi-2027/")
        self.assertEqual(facts["deadline"],"2026-12-03")
        self.assertEqual(facts["application_windows"],["2026-12-03","2027-04-05"])
        self.assertTrue(facts["source_open_confirmed"])
    def test_san_paolo_in_corso_and_data_scadenza(self):
        html="<body><main><p>Stato: IN CORSO</p><p>Data pubblicazione: 21/10/2026</p><p>Data scadenza: 05/04/2027</p></main></body>"
        facts=structured_facts(html,"https://www.compagniadisanpaolo.it/it/contributi/festival")
        self.assertTrue(facts["source_open_confirmed"])
        self.assertEqual(facts["deadline"],"2027-04-05")
    def test_turin_active_dal_al(self):
        html="<html><main><div>Attivo</div><div>dal:</div><div>12/10/2026</div><div>al:</div><div>26/11/2026</div></main></html>"
        facts=structured_facts(html,"https://bandi.comune.torino.it/avviso/circoscrizione-7")
        self.assertTrue(facts["source_open_confirmed"])
        self.assertEqual(facts["opening_date"],"2026-10-12")
        self.assertEqual(facts["deadline"],"2026-11-26")
    def test_turin_window_not_inferred_for_other_host(self):
        html="<html><main>Attivo dal 12/10/2026 al 26/11/2026</main></html>"
        facts=structured_facts(html,"https://example.org/notice")
        self.assertFalse(facts["source_open_confirmed"])
        self.assertIsNone(facts["deadline"])
    def test_official_page_with_weekdays(self):
        info=structured_facts(PAGE,URL)
        self.assertEqual(info["deadline"],"2026-11-24")
        self.assertEqual(info["opening_date"],"2026-11-02")
        self.assertTrue(info["source_open_confirmed"])
        self.assertFalse(info["closure_confirmed"])
        self.assertEqual(info["deadline_source"],URL)

    def test_drupal_metadata_outside_main(self):
        html="""<html><body><main><h1>Bando contributi</h1></main>
        <aside class="field-list"><div>Stato</div><div>Aperto</div>
        <div>Domande dal</div><div>Lun, 02/11/2026 - 09:00</div>
        <div>Scadenza</div><div>Mar, 24/11/2026 - 12:00</div></aside></body></html>"""
        facts=structured_facts(html,URL)
        self.assertTrue(facts["source_open_confirmed"])
        self.assertEqual(facts["deadline"],"2026-11-24")

    def test_no_open_without_explicit_label(self):
        info=structured_facts("<main>Scadenza 24/11/2026. Un evento aperto al pubblico.</main>",URL)
        self.assertFalse(info["source_open_confirmed"])
        self.assertEqual(info["deadline"],"2026-11-24")

    def test_verified_priority_page(self):
        response=Mock(url=URL,status_code=200,headers={"Content-Type":"text/html"},text=PAGE)
        response.iter_content.return_value=[PAGE.encode()]
        session=Mock()
        session.get.return_value=response
        source={"name":"Regione Piemonte","id":"piemonte","url":"https://bandi.regione.piemonte.it/"}
        target={"url":URL,"title":"Contributi eventi e manifestazioni culturali"}
        result=check_priority(target,source,session,lambda u,s:True,"2026-11-16T19:00:00+00:00")
        self.assertIsNotNone(result)
        self.assertEqual(result["funding_status"],"APERTO")
        self.assertEqual(result["deadline"],"2026-11-24")
        self.assertEqual(result["link_status"],"raggiungibile")
        self.assertEqual(result["eligibility"],"da verificare")

if __name__=="__main__":unittest.main()
