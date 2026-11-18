import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from applicant_comparison import (
    load_applicant_profile, compare_applicant_requirements, annotate_applicant_comparison
)

def profile(**entries):
    values={name:{"value":value,"verification":verified,"source":source}
            for name,(value,verified,source) in entries.items()}
    return {"profile_fields":values}

def requirement(category,excerpt):
    return {"category":category,"excerpt":excerpt,
            "source":"https://example.org/avviso.pdf",
            "status":"requisito_documentato_da_verificare"}

class ApplicantComparisonTests(unittest.TestCase):
    def test_declared_profile_never_certifies_an_requirement(self):
        actual=load_applicant_profile()
        self.assertEqual(actual["profile_fields"]["legal_form"]["verification"],"dichiarato")
        row={"eligibility_specific_requirements":[
            requirement("natura_giuridica","Iscrizione al RUNTS obbligatoria"),
            requirement("territorio","Sede legale in Piemonte"),
            requirement("partenariato","Partenariato obbligatorio"),
        ]}
        out=annotate_applicant_comparison(row,actual,"2026-11-18")
        self.assertEqual(out["applicant_comparison_counts"]["da_verificare"],3)
        self.assertNotIn("eligibility",out)

    def test_documented_registration_only_for_exact_runts_obligation(self):
        row={"eligibility_specific_requirements":[
            requirement("natura_giuridica","Iscrizione al RUNTS obbligatoria")]}
        yes=profile(runts_registration=(True,"documentato","Registro RUNTS"))
        no=profile(runts_registration=(False,"documentato","Registro RUNTS"))
        unknown=profile(runts_registration=(True,"dichiarato","Autodichiarazione"))
        self.assertEqual(compare_applicant_requirements(row,yes)[0]["status"],"compatibile")
        self.assertEqual(compare_applicant_requirements(row,no)[0]["status"],"potenzialmente_incompatibile")
        self.assertEqual(compare_applicant_requirements(row,unknown)[0]["status"],"da_verificare")

    def test_runts_mentioned_as_optional_does_not_imply_exclusion(self):
        row={"eligibility_specific_requirements":[
            requirement("natura_giuridica","Iscritti al RUNTS sono ammessi")]}
        no=profile(runts_registration=(False,"documentato","Registro RUNTS"))
        self.assertEqual(compare_applicant_requirements(row,no)[0]["status"],"da_verificare")

    def test_age_uses_verified_date_at_specific_day(self):
        row={"eligibility_specific_requirements":[
            requirement("anzianita","Costituiti da almeno 2 anni")]}
        p=profile(constitution_date=("2024-11-19","documentato","Atto costitutivo"))
        self.assertEqual(compare_applicant_requirements(row,p,date(2026,11,18))[0]["status"],"da_verificare")
        self.assertEqual(compare_applicant_requirements(row,p,date(2026,11,19))[0]["status"],"compatibile")

    def test_unknown_territory_cofinancing_partners_remain_open_even_with_some_profile(self):
        row={"eligibility_specific_requirements":[
            requirement("territorio","Sede legale in Piemonte"),
            requirement("condizioni_economiche","Cofinanziamento obbligatorio"),
            requirement("partenariato","Almeno 3 partner")]}
        p=profile(registered_region=("Piemonte","documentato","Statuto"),
                  available_cofinancing_eur=(20000,"documentato","Delibera"),
                  confirmed_partners=(["Teatro"],"documentato","Accordo"))
        self.assertEqual([x["status"] for x in compare_applicant_requirements(row,p)],
                         ["da_verificare"]*3)

    def test_profile_validation_rejects_unattributed_documented_fact(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/"profile.json"
            p.write_text(json.dumps(profile(runts_registration=(True,"documentato",None))),encoding="utf-8")
            with self.assertRaises(ValueError):
                load_applicant_profile(p)

    def test_operaplus_declared_facts_inform_checks_without_certifying_eligibility(self):
        actual=load_applicant_profile()
        fields=actual["profile_fields"]
        self.assertEqual(fields["constitution_date"]["value"],"2026-04-23")
        self.assertEqual(fields["registered_municipality"]["value"],"Torino")
        self.assertEqual(fields["registered_region"]["value"],"Piemonte")
        self.assertEqual(fields["runts_registration"]["value"],"in_corso")
        self.assertEqual(fields["tax_code_exists"]["value"],True)
        self.assertEqual(fields["completed_activities"]["value"],False)
        self.assertEqual(fields["partnership_willingness"]["value"],True)
        self.assertEqual(fields["cofinancing_policy"]["value"],"da_valutare_per_progetto")
        self.assertTrue(all(v["verification"]=="dichiarato" for v in fields.values()
                            if v.get("value") is not None))
        row={"eligibility_specific_requirements":[
            requirement("natura_giuridica","Iscrizione al RUNTS obbligatoria"),
            requirement("anzianita","Costituiti da almeno 2 anni"),
            requirement("territorio","Sede legale in Piemonte"),
            requirement("condizioni_economiche","Cofinanziamento obbligatorio del 10%"),
            requirement("partenariato","Partenariato obbligatorio"),
            requirement("esperienza_pregressa","Esperienza pregressa obbligatoria")
        ]}
        out=annotate_applicant_comparison(row,actual,"2026-11-18")
        self.assertEqual(out["applicant_comparison_counts"]["da_verificare"],6)
        reasons=" ".join(x["reason"] for x in out["applicant_requirement_comparison"])
        for phrase in ("in corso","anzianità dichiarata","Torino","singolo progetto",
                       "partner e accordi","Nessuna attività precedente"):
            self.assertIn(phrase,reasons)
        self.assertEqual(out["applicant_comparison_counts"]["compatibile"],0)
        self.assertEqual(out["applicant_comparison_counts"]["potenzialmente_incompatibile"],0)

    def test_preliminary_age_warning_does_not_reject_future_deadline(self):
        actual=load_applicant_profile()
        row={"eligibility_specific_requirements":[
            requirement("anzianita","Costituiti da almeno 1 anno")]}
        result=compare_applicant_requirements(row,actual,"2026-11-18")[0]
        self.assertEqual(result["status"],"da_verificare")
        self.assertIn("inferiore al minimo",result["reason"])

    def test_record_keeps_opportunity_and_adequacy_unchanged(self):
        row={"adequacy_label":"ALTA","funding_status":"APERTO",
             "eligibility_specific_requirements":[requirement("territorio","Sede legale in Piemonte")]}
        result=annotate_applicant_comparison(row,profile(),"2026-11-18")
        self.assertEqual(result["adequacy_label"],"ALTA")
        self.assertEqual(result["funding_status"],"APERTO")
        self.assertEqual(result["applicant_comparison_counts"]["da_verificare"],1)

if __name__=="__main__":
    unittest.main()
