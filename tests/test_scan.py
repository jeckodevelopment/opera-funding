import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from scan import score
class ScoreTests(unittest.TestCase):
    def test_culture_and_training(self):
        s,themes=score("Bando per cultura, musica e formazione giovani")
        self.assertGreaterEqual(s,70)
        self.assertIn("cultura e spettacolo",themes)
    def test_generic_is_not_automatically_high(self):
        s,_=score("Bando generale contributi")
        self.assertEqual(s,20)
if __name__=="__main__":
    unittest.main()
