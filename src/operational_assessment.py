"""Operational applicant pathways; actions, not legal eligibility certificates.

Every opportunity gets a documented next step. Do not infer that Opera+ is
eligible simply because the source refers to cultural associations or because
the editorial adequacy is ALTA.
"""
from adequacy import PARTNERS_ALLOWED, PARTNERS_REQUIRED
from open_review_queue import review_tasks

DIRECT="verificare_candidatura_diretta"
PARTNER="verificare_candidatura_in_partenariato"
DOCUMENTS="integrare_verifica_documentale"
LOW="bassa_priorita_progettuale"
INACTIVE="non_attiva"


def operational_assessment(row):
    status=row.get("funding_status")
    adequacy=row.get("adequacy_label")
    if status!="APERTO":
        return {
            "path":INACTIVE,
            "reason":"Opportunità non classificata APERTA: non avviare una candidatura sulla sola base della scheda",
            "next_actions":["Verificare l'apertura effettiva sul sito ufficiale prima di qualsiasi candidatura"],
            "verified_eligibility":False,
        }
    tasks=review_tasks(row)
    conditions=row.get("eligibility_condition_status")
    comparison=row.get("applicant_requirement_comparison") or []
    beneficiaries=str(row.get("beneficiaries_excerpt") or "")
    requirements=str(row.get("requirements_excerpt") or "")
    terms=beneficiaries+" "+requirements
    mandatory_partner=bool(PARTNERS_REQUIRED.search(terms))
    allowed_partner=bool(PARTNERS_ALLOWED.search(terms))
    unresolved=any(isinstance(x,dict) and x.get("status") in (
        "da_verificare","potenzialmente_incompatibile") for x in comparison)
    complete=all(isinstance(row.get(k),str) and row[k].strip() for k in (
        "funded_activities_excerpt","beneficiaries_excerpt","requirements_excerpt"))
    strong_source=bool(row.get("assessment_source") or row.get("assessment_evidence_source"))
    disputes=bool(row.get("assessment_document_discrepancies"))
    if adequacy=="BASSA":
        path=LOW
        reason=("Adeguatezza progettuale BASSA; mantenere l'opportunità consultabile "
                "e verificare soltanto eventuali motivi concreti per rivalutarla")
        tasks.insert(0,"Valutare se esiste un progetto coerente prima di investire nella candidatura")
    elif mandatory_partner or (
        conditions=="potenzialmente_incompatibile" and allowed_partner):
        path=PARTNER
        reason=("La fonte indica un partenariato obbligatorio o una possibile "
                "partecipazione tramite partner; disponibilità a collaborare "
                "non equivale a un accordo formalizzato")
        tasks.insert(0,"Individuare capofila e partner idonei e verificare ruoli e accordi")
    elif complete and strong_source and not unresolved and not disputes and (
        conditions=="compatibilita_documentata") and not mandatory_partner:
        path=DIRECT
        reason=("La fonte menziona associazioni fra i possibili beneficiari, "
                "ma l'ammissibilità effettiva e tutte le condizioni vanno ancora confermate")
        tasks.insert(0,"Confermare nello statuto e nel bando la possibilità di domanda diretta")
    else:
        path=DOCUMENTS
        reason=("Prove insufficienti o condizioni non risolte: non è possibile "
                "stabilire in sicurezza la modalità di candidatura")
        if conditions=="potenzialmente_incompatibile":
            tasks.insert(0,"Verificare se il bando consente una partecipazione tramite capofila o partner")
        else:
            tasks.insert(0,"Recuperare bando integrale e requisiti ufficiali di candidatura")
    return {
        "path":path,
        "reason":reason,
        "next_actions":list(dict.fromkeys(tasks)),
        "verified_eligibility":False,
    }


def annotate_operational_assessment(row):
    result=operational_assessment(row)
    row["application_path"]=result["path"]
    row["application_path_reason"]=result["reason"]
    row["application_next_actions"]=result["next_actions"]
    row["application_eligibility_verified"]=False
    return row
