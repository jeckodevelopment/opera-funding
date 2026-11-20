import unittest
from datetime import datetime, timezone, timedelta
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from verification import pick_for_review,coverage,needs_review,backlog_candidates,classify_crt_information,classify_informational_page

NOW=datetime(2026,11,16,21,0,tzinfo=timezone.utc)
def row(key, **props):
    return {"id":key,"title":key,"relevance":60,
            "opportunity_type":"finanziamento potenziale",**props}

class VerificationTests(unittest.TestCase):
    def test_piemonte_avvisi_index_is_informational_not_grant(self):
        item={"id":"https://bandi.regione.piemonte.it/avvisi-beni-regionali",
              "source_id":"piemonte",
              "url":"https://bandi.regione.piemonte.it/avvisi-beni-regionali",
              "title":"Avvisi pubblici e per beni regionali",
              "opportunity_type":"finanziamento potenziale"}
        result=classify_informational_page(item)
        self.assertEqual(result["opportunity_type"],"altro avviso")
        self.assertIn("informativa",result["type_reason"].lower())

    def test_piemonte_individual_calls_are_not_hidden(self):
        item={"id":"https://bandi.regione.piemonte.it/avvisi-beni-regionali/grandi-eventi",
              "source_id":"piemonte",
              "url":"https://bandi.regione.piemonte.it/avvisi-beni-regionali/grandi-eventi",
              "title":"Contributi per grandi eventi culturali",
              "opportunity_type":"finanziamento potenziale"}
        result=classify_informational_page(item)
        self.assertEqual(result["opportunity_type"],"finanziamento potenziale")

    def test_unvisited_first_and_fair_rotation(self):
        found=[row("a"),row("b"),row("c")]
        initial=pick_for_review(found,{},1,NOW)
        self.assertEqual(initial,{"a"})
        previous={"a":row("a",detail_attempted_at=NOW.isoformat())}
        subsequent=pick_for_review(found,previous,1,NOW)
        self.assertEqual(subsequent,{"b"})
        previous["b"]=row("b",detail_attempted_at=NOW.isoformat())
        self.assertEqual(pick_for_review(found,previous,1,NOW),{"c"})
    def test_open_urgent_incomplete_outweighs_older_routine_refresh(self):
        old_date=(NOW-timedelta(days=6)).isoformat()
        def old(key,**kwargs):
            return row(key,detail_checked=True,detail_version=9,
                       detail_checked_at=old_date,detail_attempted_at=old_date,
                       **kwargs)
        older=old("routine",funding_status="APERTO",deadline="2027-01-20",
                  funded_activities_excerpt="Attività",beneficiaries_excerpt="Associazioni",
                  requirements_excerpt="Requisiti documentati")
        urgent=old("urgent",funding_status="APERTO",deadline="2026-11-20",
                   beneficiaries_excerpt="Associazioni")
        previous={x["id"]:x for x in (older,urgent)}
        self.assertEqual(pick_for_review([row("routine"),row("urgent")],previous,1,NOW),{"urgent"})

    def test_upcoming_opening_within_14_days_gets_review_priority(self):
        past=(NOW-timedelta(days=4)).isoformat()
        def old(key,**kw):
            return row(key,detail_checked=True,detail_version=9,
                       detail_checked_at=past,detail_attempted_at=past,**kw)
        imminent=old("upcoming",funding_status="IN ARRIVO",
                     opening_date="2026-11-22",
                     funded_activities_excerpt="Attività",
                     beneficiaries_excerpt="Associazioni",
                     requirements_excerpt="Requisiti")
        routine=old("open",funding_status="APERTO",deadline="2027-05-20",
                    funded_activities_excerpt="Attività",
                    beneficiaries_excerpt="Associazioni",
                    requirements_excerpt="Requisiti")
        previous={x["id"]:x for x in (imminent,routine)}
        chosen=pick_for_review([row("open"),row("upcoming")],previous,1,NOW)
        self.assertEqual(chosen,{"upcoming"})

    def test_upcoming_is_rechecked_daily_even_with_complete_excerpts(self):
        yesterday=(NOW-timedelta(hours=26)).isoformat()
        entry=row("early",funding_status="IN ARRIVO",opening_date="2026-12-01",
                  detail_checked=True,detail_version=9,detail_checked_at=yesterday,
                  funded_activities_excerpt="Attività",
                  beneficiaries_excerpt="Associazioni",
                  requirements_excerpt="Requisiti")
        self.assertTrue(needs_review(entry,NOW))
        self.assertFalse(needs_review({**entry,"funding_status":"CHIUSO"},NOW))

    def test_open_incomplete_revisited_daily_not_complete(self):
        yesterday=(NOW-timedelta(hours=26)).isoformat()
        incomplete=row("incomplete",detail_checked=True,detail_version=9,
                       detail_checked_at=yesterday,funding_status="APERTO",
                       beneficiaries_excerpt="Associazioni")
        complete={**incomplete,"funded_activities_excerpt":"Laboratori",
                  "requirements_excerpt":"Regolamento"}
        self.assertTrue(needs_review(incomplete,NOW))
        self.assertFalse(needs_review(complete,NOW))

    def test_new_opportunities_still_first_and_archived_not_accelerated(self):
        old_date=(NOW-timedelta(days=5)).isoformat()
        existing={"old":row("old",funding_status="APERTO",
                            deadline="2026-11-18",
                            detail_checked=True,detail_version=9,
                            detail_checked_at=old_date,detail_attempted_at=old_date)}
        self.assertEqual(pick_for_review([row("old"),row("new")],existing,1,NOW),{"new"})
        closed=row("closed",funding_status="CHIUSO",
                   detail_checked=True,detail_version=9,
                   detail_checked_at=(NOW-timedelta(hours=26)).isoformat())
        self.assertFalse(needs_review(closed,NOW))

    def test_previous_source_schema_is_refreshed(self):
        previous={"old":row("old",detail_checked=True,detail_version=5,
                              detail_checked_at=NOW.isoformat())}
        self.assertEqual(pick_for_review([row("old")],previous,1,NOW),{"old"})
    def test_old_parser_version_forces_revisit(self):
        previous={"a":row("a",detail_checked=True,detail_version=1,
                  detail_checked_at=NOW.isoformat())}
        self.assertEqual(pick_for_review([row("a")],previous,1,NOW),{"a"})
    def test_three_day_revisit(self):
        old=row("a",detail_checked=True,detail_version=9,
                detail_checked_at=(NOW-timedelta(days=4)).isoformat())
        fresh={**old,"detail_checked_at":NOW.isoformat()}
        self.assertTrue(needs_review(old,NOW))
        self.assertFalse(needs_review(fresh,NOW))
    def test_previous_detail_parser_version_is_rechecked_after_new_format(self):
        previous={"torino":row("torino",source_id="torino",detail_checked=True,detail_version=6,
                                  detail_checked_at=NOW.isoformat())}
        self.assertEqual(pick_for_review([row("torino",source_id="torino")],previous,1,NOW),{"torino"})

    def test_mic_consuntivi_and_volto_navigation_are_not_grants(self):
        cases=[
          ("mic","https://spettacolo.cultura.gov.it/bando-jazz-attivazione-dei-consuntivi-2026/","Bando per la PROMOZIONE DELLA MUSICA JAZZ – Attivazione della..."),
          ("mic","https://spettacolo.cultura.gov.it/contributi-fnsv-fondo-nazionale-per-lo-spettacolo-dal-vivo/","Contributi FNSV"),
          ("volto","https://volontariatotorino.it/progetti-volto/","Progetti Vol.To"),
          ("volto","https://volontariatotorino.it/progetti-servizio-civile/","Progetti di Servizio Civile")
        ]
        for sid,url,title in cases:
            self.assertEqual(classify_informational_page(row("x",source_id=sid,url=url,title=title))["opportunity_type"],"altro avviso")
    def test_four_source_informational_pages_not_funding(self):
        cases=[
          ("mic","https://spettacolo.cultura.gov.it/bando-jazz-2027-assegnazione/","Bando Jazz 2027 – Assegnazione contributi"),
          ("mic","https://spettacolo.cultura.gov.it/category/contributi-fus/","Contributi extra FNSV"),
          ("alcotra","https://interreg-alcotra.eu/it/i-progetti-finanziati-2021-2027","I progetti finanziati"),
          ("torino","https://bandi.comune.torino.it/avviso/contributo-servizi","Approvazione contributo straordinario per museo"),
        ]
        for sid,url,title in cases:
            with self.subTest(sid=sid,title=title):
                row_in=row("x",source_id=sid,url=url,title=title)
                self.assertEqual(classify_informational_page(row_in)["opportunity_type"],"altro avviso")
        actual=row("y",source_id="alcotra",url="https://interreg-alcotra.eu/it/terzo-bando-progetti-singoli",title="Terzo bando progetti singoli")
        self.assertEqual(classify_informational_page(actual)["opportunity_type"],"finanziamento potenziale")
    def test_navigation_and_awards_cannot_be_open_applications(self):
        cases=[
          ("mic","https://spettacolo.cultura.gov.it/bando-festival-cori-e-bande-2026-assegnazione-dei-contributi/","Bando FESTIVAL, CORI E BANDE / 2026 – Assegnazione dei contributi"),
          ("mic","https://spettacolo.cultura.gov.it/bando-teatro-urbano-sociale-e-di-strada-2026-assegnazione-dei-contributi/","Bando TEATRO URBANO / 2026"),
          ("piemonte","https://bandi.regione.piemonte.it/pre-informazione-fondi-ue","Pre informazione"),
          ("piemonte","https://www.regione.piemonte.it/web/bandi-pnrr-per-enti-locali","Bandi Enti Locali"),
          ("piemonte","https://www.regione.piemonte.it/web/bandi-per-enti-locali","Bandi Enti Locali"),
          ("torino","https://bandi.comune.torino.it/","Bandi - Appalti"),
          ("erasmus","https://erasmus-plus.ec.europa.eu/opportunities","Opportunities"),
        ]
        for sid,url,title in cases:
            with self.subTest(url=url):
                result=classify_informational_page(row("x",source_id=sid,url=url,title=title))
                self.assertEqual(result["opportunity_type"],"altro avviso")

    def test_erasmus_documentation_is_not_an_open_call(self):
        cases=[
            ("https://www.erasmusplus.it/wp-content/uploads/2024/05/CORRIGENDUM-Disposizioni-nazionali-HE_2024.pdf", "Corrigendum Disposizioni Nazionali 2024"),
            ("https://www.erasmusplus.it/educazione_adulti/esiti/", "Esiti e candidature"),
            ("https://www.erasmusplus.it/programma/per-partecipare/come-fare-domanda/", "Moduli di candidatura"),
        ]
        for url,title in cases:
            with self.subTest(url=url):
                self.assertEqual(classify_informational_page(row("doc",source_id="erasmusitalia",url=url,title=title))["opportunity_type"],"altro avviso")
        real=row("call",source_id="erasmusitalia",url="https://www.erasmusplus.it/educazione_adulti/bando-2027/",title="Bando Erasmus+ 2027")
        self.assertEqual(classify_informational_page(real)["opportunity_type"],"finanziamento potenziale")
    def test_regional_health_appointments_are_not_grants(self):
        record=row("health",source_id="piemonte",
                   url="https://bandi.regione.piemonte.it/avvisi-beni-regionali/avviso-individuazione-soggetti-idonei-alle-direzioni-ssr",
                   title="Avviso per individuazione di soggetti idonei alle direzioni del SSR")
        result=classify_informational_page(record)
        self.assertEqual(result["opportunity_type"],"altro avviso")

    def test_information_status_has_separate_coverage_bucket(self):
        rows=[row("information",source_id="piemonte",opportunity_type="altro avviso",funding_status="INFORMATIVO"),
              row("unverified",source_id="piemonte",funding_status="DA VERIFICARE")]
        report=coverage(rows,[])
        self.assertEqual(report["totals"]["informational"],1)
        self.assertEqual(report["totals"]["unverified"],1)
        self.assertEqual(report["totals"]["candidate_unverified"],1)

    def test_quality_report_separates_candidate_backlog_from_information(self):
        rows=[row("candidate",source_id="erasmusitalia",funding_status="DA VERIFICARE"),
              row("guide",source_id="erasmusitalia",opportunity_type="altro avviso",funding_status="DA VERIFICARE"),
              row("open",source_id="crt",funding_status="APERTO",deadline="2026-12-01")]
        report=coverage(rows,[{"source_id":"erasmusitalia","ok":True},{"source_id":"crt","ok":True}])
        self.assertEqual(report["totals"]["unverified"],2)
        self.assertEqual(report["totals"]["candidate_unverified"],1)
        self.assertEqual(report["totals"]["informational_unverified"],1)
        self.assertEqual(report["totals"]["candidate_missing_deadline"],1)
        self.assertEqual(report["by_source"]["erasmusitalia"]["informational_unverified"],1)

    def test_navigation_and_project_showcases_are_not_new_funding_calls(self):
        cases=[
          ("sanpaolo","https://www.compagniadisanpaolo.it/it/i-progetti/progetti-di-sviluppo/","Progetti di sviluppo"),
          ("piemonte","https://bandi.regione.piemonte.it/contributi-finanziamenti","Contributi e finanziamenti"),
          ("piemonte","https://bandi.regione.piemonte.it/crowdfunding","Vai alla sezione Crowdfunding"),
          ("eucreative","https://culture.ec.europa.eu/cultural-heritage/funding-opportunities-for-cultural-heritage","Funding sources for cultural heritage"),
          ("erasmusitalia","https://www.erasmusplus.it/istruzione_superiore/partenariati-strategici-ka2-3/","Progetti di Cooperazione"),
        ]
        for sid,url,title in cases:
            with self.subTest(url=url):
                classified=classify_informational_page(row("nav",source_id=sid,url=url,title=title))
                self.assertEqual(classified["opportunity_type"],"altro avviso")
                self.assertNotEqual(classified.get("funding_status"),"CHIUSO")
        for sid,url in [
          ("sanpaolo","https://www.compagniadisanpaolo.it/it/contributi/festival-partecipativi-2027/"),
          ("piemonte","https://bandi.regione.piemonte.it/contributi-finanziamenti/aiuti-allo-spettacolo-dal-vivo"),
          ("eucreative","https://culture.ec.europa.eu/culture-moves-europe/call-for-residency-hosts"),
          ("erasmusitalia","https://www.erasmusplus.it/educazione_adulti/bando-2027/"),
        ]:
            with self.subTest(grant=url):
                self.assertEqual(classify_informational_page(row("call",source_id=sid,url=url,title="Call for proposals 2027"))["opportunity_type"],"finanziamento potenziale")

    def test_guidance_and_preinformation_are_not_active_applications(self):
        cases=[
            ("torino","https://bandi.comune.torino.it/avviso/linee-guida-concessione-lerogazione-contributi-ordinari-altri-benefici-economici-lanno-2027","Linee Guida per contributi 2027"),
            ("piemonte","https://bandi.regione.piemonte.it/pre-informazione-fondi-ue/sistema-regionale-standard-formativi-contributo-funzionamento-commissioni-tecniche","Pre informazione contributi")
        ]
        for sid,url,title in cases:
            with self.subTest(source=sid):
                result=classify_informational_page(row("info",source_id=sid,url=url,title=title))
                self.assertEqual(result["opportunity_type"],"altro avviso")
                self.assertNotEqual(result.get("funding_status"),"CHIUSO")
        live=row("live",source_id="torino",url="https://bandi.comune.torino.it/avviso/circ-4-secondo-avviso-concessione-contributi-ordinari-2026",title="Secondo avviso contributi 2026")
        self.assertEqual(classify_informational_page(live)["opportunity_type"],"finanziamento potenziale")

    def test_revisit_not_in_current_index(self):
        old={"one":row("one",source_id="volto",funding_status="DA VERIFICARE"),
             "expired":row("expired",source_id="volto",funding_status="CHIUSO"),
             "other":row("other",source_id="crt",funding_status="DA VERIFICARE")}
        pending=backlog_candidates(old,"volto",set())
        self.assertEqual([x["id"] for x in pending],["one","expired"])
        self.assertEqual([x["id"] for x in backlog_candidates(old,"volto",{"one"})],["expired"])
    def test_crt_news_is_not_an_application(self):
        old=row("press",source_id="crt",url="https://www.fondazionecrt.it/fondazione-crt-per-la-scuola/")
        result=classify_crt_information(old)
        self.assertEqual(result["opportunity_type"],"altro avviso")
        self.assertNotEqual(result.get("funding_status"),"CHIUSO")
        grant=row("grant",source_id="crt",url="https://www.fondazionecrt.it/bandi-progetti/note-sipari/")
        self.assertEqual(classify_crt_information(grant)["opportunity_type"],"finanziamento potenziale")
    def test_count_evidences_without_inventing(self):
        rows=[row("a",source_id="piemonte",funding_status="APERTO",deadline="2026-12-02",
                  deadline_source="https://example.org/bando",detail_checked_at=NOW.isoformat(),
                  link_status="raggiungibile"),
              row("b",source_id="piemonte",funding_status="DA VERIFICARE")]
        report=coverage(rows,[{"source_id":"piemonte","ok":True}])
        self.assertEqual(report["totals"]["all"],2)
        self.assertEqual(report["totals"]["open"],1)
        self.assertEqual(report["totals"]["unverified"],1)
        self.assertEqual(report["totals"]["dated_with_source"],1)
        self.assertEqual(report["by_source"]["piemonte"]["total"],2)
if __name__=="__main__":
    unittest.main()
