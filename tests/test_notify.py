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

    def test_filter_information_low_relevance_and_unconfirmed(self):
        self.check([])
        rows=[item("info",opportunity_type="altro avviso"),
              item("low",relevance=40),
              item("unconfirmed",source_open_confirmed=False),
              item("broken",link_status="non disponibile"),
              item("valid")]
        self.assertEqual(self.check(rows),"sent")
        self.assertEqual(len(self.sent),1)
        self.assertIn("valid",self.sent[0][4])
        for bad in ("info","low","unconfirmed","broken"):
            self.assertNotIn("Bando "+bad,self.sent[0][4])

    def test_failure_never_marks_events_notified(self):
        self.check([])
        def fail(*args):
            raise RuntimeError("temporary send error")
        with self.assertRaises(RuntimeError):
            run([item("new")],self.path,"2026-11-17T06:00:00+00:00",
                "key","person@example.org",fail)
        self.assertEqual(self.check([item("new")]),"sent")

    def test_disabled_secrets_never_send_and_advance_baseline(self):
        self.check([])
        self.assertEqual(self.check([item("not-announced")],key="",recipient=""),"disabled")
        self.assertEqual(self.check([item("not-announced")]),"no-news")
        self.assertEqual(self.sent,[])

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

    def test_multiple_recipients_each_get_private_email(self):
        self.check([])
        addresses="one@example.org, two@example.org; THREE@example.org\\nOne@example.org"
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

    def test_failure_with_corrupt_state_is_explicit(self):
        self.path.write_text('{"version": 999, "statuses": {}}')
        with self.assertRaises(RuntimeError):
            self.check([item("x")])

if __name__=="__main__":
    unittest.main()
