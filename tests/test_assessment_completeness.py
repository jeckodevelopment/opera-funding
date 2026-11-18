import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from catalog_reconciliation import validate_catalog_assessments

class AssessmentCompletenessTests(unittest.TestCase):
    def test_all_rows_have_judgement_and_reason(self):
        rows=[{"public_id":1,"adequacy_label":"MEDIA","adequacy_reason":"Coerenza culturale","assessment_reason":"Attività educative"},
              {"public_id":2,"adequacy_label":"BASSA","adequacy_reason":"Evidenze limitate","assessment_reason":"Solo titolo"}]
        self.assertEqual(validate_catalog_assessments(rows),2)

    def test_missing_assessment_prevents_publication(self):
        row={"public_id":17,"adequacy_label":"MEDIA","adequacy_reason":"Preliminare"}
        with self.assertRaisesRegex(ValueError,"17"):
            validate_catalog_assessments([row])

    def test_unverified_eligibility_is_separate(self):
        row={"public_id":20,"adequacy_label":"BASSA","adequacy_reason":"Documentazione insufficiente",
             "assessment_reason":"Compatibilità limitata","eligibility":"da verificare"}
        self.assertEqual(validate_catalog_assessments([row]),1)

if __name__=="__main__":unittest.main()
