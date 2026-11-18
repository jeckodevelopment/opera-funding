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
        session.get.return_value=Mock(status_code=200,text="User-agent: *\\nDisallow: /private/\\nAllow: /")
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

    def test_new_origin_requires_separate_policy(self):
        session=Mock()
        session.get.return_value=Mock(status_code=404)
        self.assertTrue(eligible_to_fetch("https://one.example/a",session))
        self.assertTrue(eligible_to_fetch("https://two.example/b",session))
        self.assertEqual(session.get.call_count,2)

if __name__=="__main__":
    unittest.main()
