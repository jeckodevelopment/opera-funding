import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from assessment_reviews import apply_assessment_reviews
from verification import pick_for_review

class ReviewedAssessmentTests(unittest.TestCase):
    def test_urgent_torino_and_piemonte_reviews_are_actionable(self):
        import json
        reviews=json.loads((Path(__file__).resolve().parents[1]/"config/assessment_reviews.json").read_text(encoding="utf-8"))
        c7=next(x for x in reviews if x.get("public_id")==8)
        region=next(x for x in reviews if x.get("public_id")==23)
        self.assertIn("EVENTI CULTURALI ANNO 2027",c7["requirements_excerpt"])
        self.assertIn("26/11/2026",c7["requirements_excerpt"])
        self.assertIn("soglia minima",c7["assessment_gaps"][-1])
        self.assertTrue(any("registro" in gap for gap in c7["assessment_gaps"]))
        self.assertTrue(any("FINDOM" in gap and "Allegato B" in gap for gap in region["assessment_gaps"]))
        self.assertTrue(any("manifestazione" in gap and "non" in gap for gap in region["assessment_gaps"]))

    def test_persist_explicit_review_without_changing_open_state(self):
        url="https://example.org/opportunities/a"
        row={"url":url,"source_id":"issuer","title":"Progetto", "funding_status":"APERTO","assessment_label":"ALTA AFFINITÀ"}
        review={"source_id":"issuer","url":url,"assessment_label":"BASSA AFFINITÀ",
                "assessment_reason":"Non corrisponde alle attività","reviewed_at":"2026-11-18"}
        result=apply_assessment_reviews([row],[review])[0]
        self.assertEqual(result["assessment_label"],"BASSA AFFINITÀ")
        self.assertEqual(result["funding_status"],"APERTO")
        self.assertEqual(result["assessment_source"],url)

    def test_review_can_cite_primary_source_when_catalog_uses_aggregator(self):
        row={"url":"https://aggregator.example/bandi/one?ref=rss","source_id":"volto"}
        review={"source_id":"volto","url":"https://aggregator.example/bandi/one",
                "evidence_url":"https://issuer.example/official-bando",
                "assessment_label":"MEDIA AFFINITÀ","reviewed_at":"2026-11-18"}
        result=apply_assessment_reviews([row],[review])[0]
        self.assertEqual(result["assessment_source"],"https://issuer.example/official-bando")

    def test_every_open_record_has_a_reasoned_editorial_assessment(self):
        # The open set changes after each discovery; it cannot be hard-coded
        # to the finite set of manually reviewed URLs.
        import json
        root=Path(__file__).resolve().parents[1]
        catalog=json.loads((root/"data/opportunities.json").read_text(encoding="utf-8"))
        unrated=[str(x.get("public_id")) for x in catalog
                 if x.get("funding_status")=="APERTO"
                 and (not x.get("assessment_label") or not x.get("assessment_reason"))]
        self.assertFalse(unrated,"Open grants missing editorial assessment: "+", ".join(unrated))

    def test_unclassified_records_are_assessed_in_queue(self):
        record={"id":"x","title":"Grant","relevance":65,
                "opportunity_type":"non classificato","funding_status":"APERTO"}
        self.assertEqual(pick_for_review([record],{},1),{"x"})

    def test_stable_id_reconciles_review_after_source_url_changes(self):
        row={"public_id":146,"url":"https://aggregator.example/new-edition","source_id":"volto","title":"Bando"}
        review={"public_id":146,"source_id":"volto","url":"https://another.example/old-edition",
                "assessment_label":"MEDIA AFFINITÀ","reviewed_at":"2026-11-18"}
        result=apply_assessment_reviews([row],[review])[0]
        self.assertEqual(result["assessment_label"],"MEDIA AFFINITÀ")

    def test_five_source_verified_direct_application_blockers(self):
        import json
        from operational_assessment import operational_assessment
        reviews=json.loads((Path(__file__).resolve().parents[1]/"config/assessment_reviews.json").read_text(encoding="utf-8"))
        for public_id in (25,32,148,162,254):
            with self.subTest(public_id=public_id):
                review=next(r for r in reviews if r.get("public_id")==public_id)
                self.assertTrue(review["evidence_url"].startswith("https://"))
                self.assertTrue(review["direct_application_blocker"])
                row={"public_id":public_id,"source_id":review["source_id"],
                     "url":review["url"],"funding_status":"APERTO",
                     "adequacy_label":"BASSA"}
                applied=apply_assessment_reviews([row],[review])[0]
                self.assertEqual(operational_assessment(applied)["path"],
                                 "integrare_verifica_documentale")

    def test_european_literacy_consortium_has_source_backed_requirement(self):
        import json
        from eligibility_specific import extract_specific_requirements
        reviews=json.loads((Path(__file__).resolve().parents[1]/"config/assessment_reviews.json").read_text(encoding="utf-8"))
        review=next(r for r in reviews if r.get("public_id")==120)
        row=apply_assessment_reviews([{"public_id":120,"source_id":review["source_id"],"url":review["url"]}],[review])[0]
        extracted=extract_specific_requirements(row)
        self.assertIn("partenariato",{r["category"] for r in extracted})
        self.assertTrue(all(r["source"].startswith("https://") for r in extracted))

    def test_agricultural_and_regional_direct_blockers(self):
        import json
        from operational_assessment import operational_assessment
        reviews=json.loads((Path(__file__).resolve().parents[1]/"config/assessment_reviews.json").read_text(encoding="utf-8"))
        for ident in (22,185):
            with self.subTest(public_id=ident):
                review=next(x for x in reviews if x.get("public_id")==ident)
                row={"public_id":ident,"source_id":review["source_id"],
                     "url":review["url"],"funding_status":"APERTO",
                     "adequacy_label":"BASSA"}
                applied=apply_assessment_reviews([row],[review])[0]
                self.assertEqual(operational_assessment(applied)["path"],
                                 "integrare_verifica_documentale")
                self.assertTrue(review["evidence_url"].startswith("https://"))

    def test_partnership_experience_for_early_childhood_is_not_absolute_blocker(self):
        import json
        from eligibility_specific import extract_specific_requirements
        reviews=json.loads((Path(__file__).resolve().parents[1]/"config/assessment_reviews.json").read_text(encoding="utf-8"))
        review=next(x for x in reviews if x.get("public_id")==188)
        self.assertFalse(review.get("direct_application_blocker"))
        self.assertIn("almeno un partner",review["requirements_excerpt"])
        row=apply_assessment_reviews([{
            "public_id":188,"source_id":review["source_id"],"url":review["url"],
            "opportunity_type":"finanziamento potenziale"}],[review])[0]
        extracted=extract_specific_requirements(row)
        self.assertIn("esperienza_pregressa",{x["category"] for x in extracted})

    def test_rural_lease_auction_kept_as_informative_notice(self):
        import json
        from adequacy import apply_adequacy
        reviews=json.loads((Path(__file__).resolve().parents[1]/"config/assessment_reviews.json").read_text(encoding="utf-8"))
        entry=next(x for x in reviews if x.get("public_id")==270)
        row={"public_id":270,"source_id":entry["source_id"],"url":entry["url"],
             "funding_status":"APERTO","opportunity_type":"finanziamento potenziale"}
        result=apply_assessment_reviews([row],[entry])[0]
        apply_adequacy(result)
        self.assertEqual(result["adequacy_label"],"INFORMATIVA")
        self.assertEqual(result["funding_status"],"APERTO")
        self.assertIn("NON un bando",result["assessment_reason"])

    def test_last_twelve_open_calls_have_individually_attributed_requirements(self):
        import json
        from eligibility_specific import extract_specific_requirements
        from applicant_comparison import compare_applicant_requirements
        path=Path(__file__).resolve().parents[1]/"config/assessment_reviews.json"
        reviews=json.loads(path.read_text(encoding="utf-8"))
        ids=(144,115,18,117,34,189,116,119,149,113,114,145)
        for ident in ids:
            with self.subTest(public_id=ident):
                review=next(x for x in reviews if x.get("public_id")==ident)
                self.assertGreaterEqual(len(review["reviewed_requirements"]),1)
                self.assertEqual(review["assessment_label"],"BASSA AFFINITÀ")
                row=apply_assessment_reviews([{
                    "public_id":ident,"source_id":review["source_id"],
                    "url":review["url"],"funding_status":"APERTO",
                    "opportunity_type":"finanziamento potenziale"
                }],[review])[0]
                extracted=extract_specific_requirements(row)
                self.assertGreaterEqual(len(extracted),1)
                self.assertTrue(all(x["source"].startswith("https://") for x in extracted))
                row["eligibility_specific_requirements"]=extracted
                outcomes=compare_applicant_requirements(row,{"profile_fields":{}})
                self.assertGreaterEqual(len(outcomes),1)
                self.assertTrue(all(x["status"]=="da_verificare" for x in outcomes))

    def test_generic_button_title_replaced_with_documented_name(self):
        row={"public_id":183,"url":"https://example.org/bando","source_id":"issuer","title":"SCOPRI IL BANDO"}
        review={"public_id":183,"source_id":"issuer","url":"https://example.org/bando",
                "catalog_title":"Buoni formazione per la cultura","reviewed_at":"2026-11-18"}
        self.assertEqual(apply_assessment_reviews([row],[review])[0]["title"],"Buoni formazione per la cultura")

    def test_seven_priority_calls_have_current_documented_assessments(self):
        import json
        from adequacy import apply_adequacy
        reviews=json.loads((Path(__file__).resolve().parents[1]/"config/assessment_reviews.json").read_text(encoding="utf-8"))
        expected={176:"BASSA",23:"MEDIA",182:"BASSA",183:"MEDIA",19:"BASSA",143:"BASSA",255:"BASSA"}
        blocked={176,182,19,143}
        for number,label in expected.items():
            with self.subTest(public_id=number):
                record=next(r for r in reviews if r.get("public_id")==number)
                self.assertEqual(record["reviewed_at"],"2026-11-19")
                self.assertTrue(record.get("evidence_url","").startswith("https://"))
                self.assertTrue(record.get("requirements_excerpt"))
                self.assertTrue(record.get("assessment_gaps"))
                row={"source_id":record["source_id"],"url":record["url"],"public_id":number,
                     "opportunity_type":"finanziamento potenziale","funding_status":"APERTO",
                     "applicant_requirement_comparison":[]}
                result=apply_assessment_reviews([row],reviews)[0]
                apply_adequacy(result)
                self.assertEqual(result["adequacy_label"],label)
                self.assertEqual(bool(result.get("direct_application_blocker")),number in blocked)
                self.assertEqual(result["funding_status"],"APERTO")

    def test_official_allianz_review_does_not_invent_local_seat_or_minimum_age(self):
        import json
        reviews=json.loads((Path(__file__).resolve().parents[1]/"config/assessment_reviews.json").read_text(encoding="utf-8"))
        record=next(r for r in reviews if r.get("public_id")==255)
        self.assertEqual(record["source_id"],"volto")
        self.assertIn("umanamente.allianz.it",record["evidence_url"])
        self.assertNotIn("comune di",record["requirements_excerpt"].lower())
        self.assertNotIn("almeno due anni",record["requirements_excerpt"].lower())

    def test_documented_festival_first_edition_blocker_is_applied(self):
        import json
        root=Path(__file__).resolve().parents[1]
        review=next(x for x in json.loads((root/"config/assessment_reviews.json").read_text(encoding="utf-8"))
                    if x.get("public_id")==190)
        row={"public_id":190,"source_id":review["source_id"],"url":review["url"],
             "title":"Festival partecipativi 2027","funding_status":"APERTO"}
        out=apply_assessment_reviews([row],[review])[0]
        self.assertEqual(out["assessment_label"],"BASSA AFFINITÀ")
        self.assertIn("prime edizioni",out["assessment_reason"])
        self.assertIn("festival esistente",out["direct_application_blocker"])
        self.assertTrue(out["assessment_evidence_source"].startswith("https://"))

    def test_circ7_conditions_are_supported_by_official_pdf(self):
        import json
        root=Path(__file__).resolve().parents[1]
        review=next(x for x in json.loads((root/"config/assessment_reviews.json").read_text(encoding="utf-8"))
                    if x.get("public_id")==8)
        self.assertIn("comunità locale",review["beneficiaries_excerpt"])
        self.assertIn("26 novembre 2026",review["requirements_excerpt"])
        self.assertTrue(review["evidence_url"].endswith("13_Avviso_Eventi_Culturali_2027.pdf"))

    def test_23_and_183_are_conditionally_relevant_without_invented_projects(self):
        import json
        reviews=json.loads((Path(__file__).resolve().parents[1]/"config/assessment_reviews.json").read_text(encoding="utf-8"))
        for public_id in (23,183):
            with self.subTest(public_id=public_id):
                item=next(r for r in reviews if r.get("public_id")==public_id)
                self.assertEqual(item["assessment_label"],"MEDIA AFFINITÀ")
                self.assertTrue(item.get("assessment_gaps"))
                self.assertTrue(item.get("requirements_excerpt"))
                self.assertNotIn("23/04/2026",item["assessment_reason"])
        event=next(r for r in reviews if r.get("public_id")==23)
        self.assertIn("24/11/2026",event["requirements_excerpt"])
        self.assertIn("FINDOM",event["requirements_excerpt"])
        self.assertIn("non ha documentato",event["assessment_reason"])
        voucher=next(r for r in reviews if r.get("public_id")==183)
        self.assertIn("Linea A",voucher["requirements_excerpt"])
        self.assertIn("ROL",voucher["requirements_excerpt"])
        self.assertIn("promotore",voucher["assessment_gaps"][2])
        self.assertIn("2.000-10.000",voucher["requirements_excerpt"])
        self.assertIn("non ha documentato",voucher["assessment_reason"])

    def test_official_eligibility_for_medium_calls(self):
        import json
        root=Path(__file__).resolve().parents[1]
        reviews={x.get("public_id"):x for x in json.loads(
            (root/"config/assessment_reviews.json").read_text(encoding="utf-8"))}
        self.assertIn("anche di recente costituzione",reviews[33]["beneficiaries_excerpt"])
        self.assertIn("RUNTS non è obbligatorio",reviews[177]["beneficiaries_excerpt"])
        self.assertIn("enti privati senza scopo di lucro",reviews[252]["beneficiaries_excerpt"])
        self.assertIn("20%",reviews[252]["assessment_reason"])
        for ident in (33,177,252):
            self.assertTrue(reviews[ident]["evidence_url"].startswith("https://"))
            self.assertGreaterEqual(len(reviews[ident]["assessment_gaps"]),3)

    def test_different_host_does_not_inherit_review(self):
        row={"url":"https://example.org/bando","source_id":"a"}
        review={"source_id":"a","url":"https://another.org/bando","assessment_label":"MEDIA AFFINITÀ",
                "reviewed_at":"2026-11-18"}
        self.assertNotIn("assessment_label",apply_assessment_reviews([row],[review])[0])

if __name__=="__main__":
    unittest.main()
