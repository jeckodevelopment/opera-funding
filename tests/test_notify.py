import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from notify import run,candidates,make_message,is_open,MAX_DAILY,MAX_MONTHLY,parse_recipients

def item(key, status="APERTO", relevance=80, **kw):
    return {
        "id":key,"url":"https://example.org/call/"+key,
        "title":"Bando "+key,"issuer":"Ente culturale",
        "funding_status":status,
        "opportunity_type":"finanziamento potenziale",
        "source_open_confirmed":status=="APERTO",
        "link_status":"raggiungibile",
        "relevance":relevance,
        "adequacy_label":"MEDIA",
        "deadline":"2027-01-15",
        **kw,
    }

class NotifyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/"state.json"
        self.sent=[]
        def fake_sender(*args):
            self.sent.append(args)
            return "email_test_123"
        self.sender=fake_sender
    def tearDown(self):
        self.tmp.cleanup()
    def check(self,rows,day="2026-11-17",key="test_api_key",recipient="person@example.org"):
        return run(rows,self.path,day+"T06:00:00+00:00",key,recipient,self.sender)

    def test_initial_catalog_never_sends_historical_calls(self):
        self.assertEqual(self.check([item("old"),item("closed","CHIUSO")]),"bootstrapped")
        self.assertEqual(self.sent,[])
        self.assertEqual(self.check([item("old"),item("closed","CHIUSO")]),"no-news")
        self.assertEqual(self.sent,[])

    def test_one_digest_when_new_call_becomes_open_and_no_duplicates(self):
        self.check([item("x","DA VERIFICARE")])
        self.assertEqual(self.check([item("x"),item("y")]),"sent")
        self.assertEqual(len(self.sent),1)
        api,recipient,subject,html,plain,idempotency=self.sent[0]
        self.assertEqual(api,"test_api_key")
        self.assertEqual(recipient,"person@example.org")
        self.assertIn("2",subject)
        self.assertIn("Bando x",html)
        self.assertIn("Bando y",plain)
        self.assertTrue(idempotency.startswith("opera-funding-"))
        self.assertEqual(self.check([item("x"),item("y")]),"no-news")
        self.assertEqual(len(self.sent),1)

    def test_includes_all_new_grades_and_early_stage_without_inventing_opening(self):
        self.check([])
        rows=[item("info",opportunity_type="altro avviso"),
              item("low",relevance=40,adequacy_label="BASSA"),
              item("unconfirmed",source_open_confirmed=False),
              item("broken",link_status="non disponibile"),
              item("upcoming",status="IN ARRIVO",adequacy_label="ALTA"),
              item("verify",status="DA VERIFICARE",adequacy_label="MEDIA"),
              item("valid")]
        self.assertEqual(self.check(rows),"sent")
        self.assertEqual(len(self.sent),1)
        text_body=self.sent[0][4]
        for expected in ("low","unconfirmed","upcoming","verify","valid"):
            self.assertIn("Bando "+expected,text_body)
        for excluded in ("info","broken"):
            self.assertNotIn("Bando "+excluded,text_body)
        self.assertIn("IN ARRIVO",text_body)
        self.assertIn("Adeguatezza: ALTA",text_body)
        self.assertIn("DA VERIFICARE",text_body)

    def test_failure_never_marks_events_notified(self):
        self.check([])
        def fail(*args):
            raise RuntimeError("temporary send error")
        with self.assertRaises(RuntimeError):
            run([item("new")],self.path,"2026-11-17T06:00:00+00:00",
                "key","person@example.org",fail)
        self.assertEqual(self.check([item("new")]),"sent")

    def test_disabled_secrets_do_not_lose_pending_notification(self):
        self.check([])
        self.assertEqual(self.check([item("not-announced")],key="",recipient=""),"disabled")
        self.assertEqual(self.check([item("not-announced")]),"sent")
        self.assertEqual(len(self.sent),1)

    def test_free_quota_guard_does_not_mark_unsent(self):
        self.check([])
        state=json.loads(self.path.read_text())
        state["sent_days"]={"2026-11-17":MAX_DAILY}
        self.path.write_text(json.dumps(state))
        self.assertEqual(self.check([item("new")]),"quota")
        self.assertEqual(self.sent,[])
        self.assertEqual(self.check([item("new")],day="2026-11-18"),"sent")
        self.assertEqual(len(self.sent),1)

    def test_monthly_guard(self):
        self.check([])
        state=json.loads(self.path.read_text())
        state["sent_months"]={"2026-11":MAX_MONTHLY}
        self.path.write_text(json.dumps(state))
        self.assertEqual(self.check([item("new")]),"quota")
        self.assertEqual(self.sent,[])

    def test_html_escapes_untrusted_titles_and_https_only(self):
        self.check([])
        malicious=item("safe",title="<script>alert(1)</script>")
        self.assertEqual(self.check([malicious]),"sent")
        html=self.sent[0][3]
        self.assertIn("&lt;script&gt;",html)
        self.assertNotIn("<script>",html)
        self.assertEqual(candidates([item("bad",url="javascript:alert(1)")],{},set()),[])

    def test_title_links_to_numeric_detail_and_preserves_official_source(self):
        entry=item("linked",public_id=143,
                   title='Progetto <Rigoletto> & laboratorio')
        _,html,plain=make_message([entry])
        detail="https://jeckodevelopment.com/dev/funding/?opportunity=143"
        self.assertIn('href="'+detail+'"',html)
        self.assertIn("&lt;Rigoletto&gt; &amp; laboratorio</a>",html)
        self.assertIn("Scheda: "+detail,plain)
        self.assertIn('href="https://example.org/call/linked"',html)
        self.assertIn("Fonte ufficiale",html)

    def test_title_link_never_invents_public_id(self):
        _,html,plain=make_message([
            item("missing",public_id=None),
            item("unsafe",public_id="<script>alert(1)</script>"),
            item("bool",public_id=True),
        ])
        self.assertNotIn("opportunity=",html)
        self.assertNotIn("opportunity=",plain)
        self.assertNotIn("<script>",html)
        self.assertEqual(plain.count("Scheda: https://jeckodevelopment.com/dev/funding/"),3)

    def test_multiple_recipients_each_get_private_email(self):
        self.check([])
        addresses="one@example.org, two@example.org; THREE@example.org\nOne@example.org"
        self.assertEqual(self.check([item("multi")],recipient=addresses),"sent")
        self.assertEqual([x[1] for x in self.sent],["one@example.org","two@example.org","THREE@example.org"])
        self.assertEqual(len({x[5] for x in self.sent}),3)
        state=self.path.read_text()
        for address in ("one@example.org","two@example.org","THREE@example.org"):
            self.assertNotIn(address,state)
        self.assertEqual(self.check([item("multi")],recipient=addresses),"no-news")
        self.assertEqual(len(self.sent),3)

    def test_partial_failure_retries_only_missing_recipient(self):
        self.check([])
        calls=[]
        def partly_failing(*args):
            calls.append(args[1])
            if len(calls)==2:
                raise RuntimeError("provider error")
            return "ok"
        with self.assertRaises(RuntimeError):
            run([item("new")],self.path,"2026-11-17T06:00:00+00:00",
                "key","one@example.org,two@example.org",partly_failing)
        self.assertEqual(calls,["one@example.org","two@example.org"])
        self.assertNotIn("one@example.org",self.path.read_text())
        self.assertEqual(self.check([item("new")],recipient="one@example.org,two@example.org",key="key"),"sent")
        self.assertEqual([x[1] for x in self.sent],["two@example.org"])
        self.assertEqual(self.check([item("new")],recipient="one@example.org,two@example.org",key="key"),"no-news")

    def test_multiple_recipients_consume_daily_quota_individually(self):
        self.check([])
        state=json.loads(self.path.read_text())
        state["sent_days"]={"2026-11-17":MAX_DAILY-1}
        self.path.write_text(json.dumps(state))
        self.assertEqual(self.check([item("new")],recipient="one@example.org,two@example.org"),"quota")
        self.assertEqual([x[1] for x in self.sent],["one@example.org"])
        self.assertEqual(self.check([item("new")],day="2026-11-18",recipient="one@example.org,two@example.org"),"sent")
        self.assertEqual([x[1] for x in self.sent],["one@example.org","two@example.org"])

    def test_invalid_addresses_and_too_many_recipients(self):
        self.assertEqual(parse_recipients("a@example.org; b@example.org, A@example.org"),["a@example.org","b@example.org"])
        with self.assertRaises(ValueError):
            parse_recipients("valid@example.org, invalid entry")
        with self.assertRaises(ValueError):
            parse_recipients(",".join(f"u{i}@example.org" for i in range(11)))

    def test_branded_email_matches_dashboard_and_is_email_safe(self):
        subj,html,plain=make_message([item("a",title="Progetto <Opera & Cultura>",
                                              issuer="Ente <pubblico>",summary="Musica & formazione",
                                              deadline="2027-01-15")])
        self.assertIn("Opera+ Funding",subj)
        self.assertIn("Le opportunità da non perdere.",html)
        self.assertIn("#f7f6f3",html)
        self.assertIn("#b7dfc5",html)
        self.assertIn("operaplus-logo.png",html)
        self.assertIn('role="presentation"',html)
        self.assertIn("15 gennaio 2027",html)
        self.assertIn("&lt;Opera &amp; Cultura&gt;",html)
        self.assertIn("Ente &lt;pubblico&gt;",html)
        self.assertNotIn("<Opera & Cultura>",html)
        self.assertIn("Musica &amp; formazione",html)
        self.assertIn("https://example.org/call/a",html)
        self.assertIn("15 gennaio 2027",plain)
        self.assertIn("Esplora tutte le opportunità",html)
        self.assertNotIn("<script",html)
        self.assertNotIn("<style",html)
        self.assertNotIn("<link ",html)

    def test_transparent_logo_has_opaque_white_tile_in_dark_mode(self):
        _,html,_=make_message([item("logo")])
        start=html.index('alt="Opera+"')
        tile=html[max(0,start-480):start+250]
        self.assertIn('bgcolor="#ffffff"',tile)
        self.assertIn('background-color:#ffffff',tile)
        self.assertIn('background-image:linear-gradient(#ffffff,#ffffff)',tile)
        self.assertIn('border-radius:8px',tile)
        self.assertIn('operaplus-logo.png',tile)

    def test_branded_email_does_not_invent_missing_summary_or_dates(self):
        subject,html,plain=make_message([item("x",summary="",deadline=None),
                                           item("y",url="javascript:alert(1)")])
        self.assertIn("2 nuove opportunità",subject)
        self.assertIn("Da verificare",html)
        self.assertNotIn("javascript:",html)
        self.assertIn("https://jeckodevelopment.com/dev/funding/",html)

    def test_digest_includes_every_item_not_just_first_twelve(self):
        self.check([])
        rows=[item(f"extra-{i}",adequacy_label="ALTA" if i==14 else "MEDIA")
              for i in range(15)]
        self.assertEqual(self.check(rows),"sent")
        self.assertEqual(len(self.sent),2)
        bodies="\\n".join(call[4] for call in self.sent)
        for i in range(15):
            self.assertIn("Bando extra-"+str(i),bodies)
        self.assertEqual(self.check(rows),"no-news")

    def test_historical_v1_ledger_does_not_mass_alert_old_calls(self):
        historical=item("old")
        self.check([historical])
        state=json.loads(self.path.read_text())
        state["version"]=1
        state["statuses"][historical["id"]]="ALTRO"
        self.path.write_text(json.dumps(state))
        self.assertEqual(self.check([historical,item("brand-new")]),"sent")
        self.assertIn("Bando brand-new",self.sent[0][4])
        self.assertNotIn("Bando old",self.sent[0][4])

    def test_email_sorts_high_before_medium_before_low(self):
        self.check([])
        calls=[item("low",adequacy_label="BASSA"),
               item("med",adequacy_label="MEDIA"),
               item("high",adequacy_label="ALTA")]
        self.assertEqual(self.check(calls),"sent")
        body=self.sent[0][4]
        self.assertLess(body.index("Bando high"),body.index("Bando med"))
        self.assertLess(body.index("Bando med"),body.index("Bando low"))

    def test_one_unavailable_source_does_not_block_new_digest(self):
        from notify import main
        import os
        import sys as system
        with tempfile.TemporaryDirectory() as tmp:
            catalog=Path(tmp)/"catalog.json"
            report=Path(tmp)/"report.json"
            catalog.write_text(json.dumps([item("new-high",adequacy_label="ALTA")]))
            report.write_text(json.dumps({"sources":[
                {"source_id":"working","ok":True},
                {"source_id":"alcotra","ok":False}]}))
            with (patch.object(system,"argv",["notify.py","--catalog",str(catalog),
                                              "--report",str(report),"--state",str(self.path)]),
                  patch("notify.run") as mocked,
                  patch.dict(os.environ,{"RESEND_API_KEY":"dummy",
                                         "FUNDING_ALERT_RECIPIENT":"user@example.org"})):
                main()
                self.assertEqual(mocked.call_count,1)

    def test_failure_with_corrupt_state_is_explicit(self):
        self.path.write_text('{"version": 999, "statuses": {}}')
        with self.assertRaises(RuntimeError):
            self.check([item("x")])

if __name__=="__main__":
    unittest.main()
