import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from crt_windows import extract_ordinarie_windows

URL="https://www.fondazionecrt.it/bandi-progetti/arte-cultura-ordinarie/"
HTML="""<html><body><main>
<h1>Ordinarie: Arte e Cultura</h1>
<p>Progetto – Bando Ordinarie 2026</p>
<p>Prima scadenza: tra il 02/02/2026 e il 30/04/2026, ore 15.00</p>
<p>Seconda scadenza: tra il 01/07/2026 e il 15/10/2026, ore 15.00</p>
<p>Sostegno attività – Bando Ordinarie 2026</p>
<p>Unica scadenza: tra il 02/02/2026 e il 04/03/2026, ore 15.00</p>
</main></body></html>"""

class CRTEditionTests(unittest.TestCase):
    def test_three_distinct_2026_deadlines(self):
        rows=extract_ordinarie_windows(HTML,URL)
        self.assertEqual(len(rows),3)
        self.assertEqual(set(x["deadline"] for x in rows),{"2026-03-04","2026-04-30","2026-10-15"})
        self.assertEqual(len(set(x["window_key"] for x in rows)),3)
        self.assertEqual(sum(x["application_type"]=="Progetto" for x in rows),2)
        self.assertEqual(sum(x["application_type"]=="Sostegno attività" for x in rows),1)
        self.assertTrue(all(x["deadline_source"]==URL for x in rows))
    def test_no_duplicate_mobile_markup(self):
        rows=extract_ordinarie_windows(HTML+HTML,URL)
        self.assertEqual(len(rows),3)
    def test_new_edition_keeps_distinct_ids(self):
        rows2026=extract_ordinarie_windows(HTML,URL)
        rows2027=extract_ordinarie_windows(HTML.replace("2026","2027"),URL)
        self.assertFalse(set(x["window_key"] for x in rows2026)&set(x["window_key"] for x in rows2027))
    def test_not_other_crt_pages(self):
        self.assertEqual(extract_ordinarie_windows(HTML,"https://www.fondazionecrt.it/bandi-progetti/note-sipari/"),[])
if __name__=="__main__":unittest.main()
