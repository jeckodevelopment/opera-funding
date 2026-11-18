import sys
import unittest
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from programme_monitor import _snapshot,check_programmes,public_status
from funder_registry import public_monitoring

URL="https://example.org/contributi"
class TestProgrammeMonitoring(unittest.TestCase):
 def test_snapshot_stable_against_navigation_and_script(self):
  html='<html><header>menu A</header><main><p>Fondo per enti</p><a href="/bandi/2027">Bando cultura 2027</a><a href="https://evil.test/bandi">Bando esterno</a></main><footer>footer</footer><script>volatile</script></html>'
  snap=_snapshot(html,URL)
  self.assertEqual(len(snap["candidate_links"]),1)
  self.assertEqual(snap["candidate_links"][0]["url"],"https://example.org/bandi/2027")
  self.assertEqual(snap["digest"],_snapshot(html.replace("menu A","menu B").replace("volatile","different"),URL)["digest"])
 def test_silent_baseline_and_change(self):
  response=Mock()
  response.url=URL
  response.headers={"Content-Type":"text/html"}
  response.encoding="utf-8"
  response.iter_content=lambda _:iter([b"<main>Contributi associazioni</main>"])
  session=Mock()
  session.get.return_value=response
  registry={"programs":[{"id":"p","monitoring":"direct","url":URL}]}
  first=check_programmes(registry,{},session,lambda u,s:True,"2026-11-18")
  self.assertFalse(first["p"]["changed"])
  self.assertTrue(first["p"]["baseline_created"])
  response.iter_content=lambda _:iter([b"<main>Contributi associazioni - aggiornamento</main>"])
  second=check_programmes(registry,first,session,lambda u,s:True,"2026-11-19")
  self.assertTrue(second["p"]["changed"])
  self.assertNotIn("digest",public_status(second)["p"])
 def test_denied_robots_preserves_baseline(self):
  registry={"programs":[{"id":"p","monitoring":"direct","url":URL}]}
  existing={"p":{"digest":"123","candidate_links":[],"last_success_at":"2026-11-17"}}
  results=check_programmes(registry,existing,Mock(),lambda u,s:False,"2026-11-18")
  self.assertEqual(results["p"]["status"],"error")
  self.assertEqual(results["p"]["digest"],"123")
 def test_registry_monitoring_consistent(self):
  registry={"funders":[{"id":"x"}],"programs":[{"id":"p","funder_id":"x","monitoring":"direct"}]}
  value=public_monitoring(registry,[],"2026-11-18",{"p":{"status":"ok","changed":True,"candidate_links":[],"last_checked_at":"2026-11-18"}})
  self.assertEqual(value["programs"][0]["monitoring_status"],"ok")
  self.assertTrue(value["programs"][0]["changed"])
if __name__=="__main__":unittest.main()
