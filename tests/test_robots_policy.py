"""Robots policy cached by origin without bypassing path-based disallow rules."""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from scan import eligible_to_fetch

class RobotsPolicyTests(unittest.TestCase):
    def test_one_robots_request_for_many_pages_and_pdfs(self):
        session=Mock()
        session.get.return_value=Mock(status_code=200,text="""User-agent: *
Disallow: /private/
""")
        self.assertTrue(eligible_to_fetch("https://example.org/bandi/call",session))
        self.assertFalse(eligible_to_fetch("https://example.org/private/bando.pdf",session))
        self.assertTrue(eligible_to_fetch("https://example.org/bandi/other",session))
        self.assertEqual(session.get.call_count,1)

    def test_denied_policy_is_cached_without_bypassing_disallow(self):
        session=Mock()
        session.get.return_value=Mock(status_code=403)
        self.assertFalse(eligible_to_fetch("https://example.org/a",session))
        self.assertFalse(eligible_to_fetch("https://example.org/b",session))
        self.assertEqual(session.get.call_count,1)

    def test_403_is_reported_as_http_failure_not_a_confirmed_disallow(self):
        session=Mock()
        session.get.return_value=Mock(status_code=403)
        self.assertFalse(eligible_to_fetch("https://example.org/bandi",session))
        diagnostic=session._funding_robots_diagnostics[("https","example.org")]
        self.assertIn("HTTP 403",diagnostic)
        self.assertNotIn("non consentito",diagnostic)

    def test_explicit_disallow_is_distinguished_from_unreachable_robots(self):
        session=Mock()
        session.get.return_value=Mock(status_code=200,text="""User-agent: *
Disallow: /private/
""")
        self.assertFalse(eligible_to_fetch("https://example.org/private/doc.pdf",session))
        diagnostic=session._funding_robots_diagnostics[("https","example.org")]
        self.assertIn("non consentito",diagnostic)

    def test_new_origin_requires_separate_policy(self):
        session=Mock()
        session.get.return_value=Mock(status_code=404)
        self.assertTrue(eligible_to_fetch("https://one.example/a",session))
        self.assertTrue(eligible_to_fetch("https://two.example/b",session))
        self.assertEqual(session.get.call_count,2)

if __name__=="__main__":
    unittest.main()
