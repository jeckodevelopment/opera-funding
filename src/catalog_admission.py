"""Fail-closed admission gate for *new* public catalogue records.

Discovery is not publication. Hold incomplete candidates in a persistent
internal queue; accept only source-backed, meaningfully assessed records.
Legacy public records remain visible and preserve stable numeric IDs.
"""
from collections import Counter
from urllib.parse import urlparse

EVIDENCE=("programme_objectives_excerpt","funded_activities_excerpt",
          "beneficiaries_excerpt","requirements_excerpt")
CANDIDATES={"finanziamento potenziale","call progettuale da verificare","non classificato"}
ACTIVE={"APERTO","IN ARRIVO","CHIUSO"}


def _https(value):
    if not isinstance(value,str):
        return False
    parsed=urlparse(value)
    return parsed.scheme=="https" and bool(parsed.hostname) and not parsed.username and not parsed.password


def has_verified_window(row):
    """A deadline or confirmed rolling window, with official HTTPS evidence."""
    return bool(
        (row.get("deadline") and _https(row.get("deadline_source"))) or
        (row.get("rolling_confirmed") is True and _https(row.get("rolling_evidence")))
    )


def admission_reasons(row):
    """Return explicit reasons, never a false attestation of legal eligibility."""
    reasons=[]
    informative=row.get("opportunity_type")=="altro avviso"
    if not _https(row.get("url")):
        reasons.append("url_non_valida")
    if not isinstance(row.get("title"),str) or len(row["title"].strip())<12:
        reasons.append("titolo_non_specifico")
    if row.get("link_status")!="raggiungibile":
        reasons.append("link_non_verificato")
    if informative:
        if not str(row.get("type_reason") or "").strip():
            reasons.append("natura_informativa_non_documentata")
        if row.get("funding_status") not in ("INFORMATIVO","CHIUSO"):
            reasons.append("stato_informativo_incoerente")
        return reasons
    if row.get("opportunity_type") not in CANDIDATES:
        reasons.append("tipologia_non_classificata")
    if row.get("funding_status") not in ACTIVE:
        reasons.append("stato_candidatura_non_verificato")
    if not row.get("detail_checked") and not row.get("assessment_reviewed_at"):
        reasons.append("fonte_non_esaminata")
    for field in EVIDENCE:
        if not isinstance(row.get(field),str) or not row[field].strip():
            reasons.append("evidenza_mancante:"+field)
    if not (_https(row.get("assessment_evidence_source")) or
            _https(row.get("assessment_source"))):
        reasons.append("provenienza_requisiti_mancante")
    # A mere thematic rank/fallback is never a completed editorial judgement.
    if (row.get("assessment_fallback") is True
            or not str(row.get("assessment_reason") or "").strip()
            or not str(row.get("adequacy_reason") or "").strip()
            or row.get("adequacy_label") not in ("ALTA","MEDIA","BASSA")):
        reasons.append("valutazione_non_motivata")
    if row.get("assessment_document_issues"):
        reasons.append("documenti_con_anomalie")
    if row.get("funding_status")=="APERTO":
        if not row.get("source_open_confirmed"):
            reasons.append("apertura_non_confermata")
        if not has_verified_window(row):
            reasons.append("finestra_candidatura_non_documentata")
    if row.get("funding_status")=="IN ARRIVO" and not (
            row.get("opening_date") and _https(row.get("opening_evidence"))):
        reasons.append("apertura_futura_non_documentata")
    if row.get("funding_status")=="IN ARRIVO" and not has_verified_window(row):
        reasons.append("finestra_candidatura_non_documentata")
    if row.get("funding_status")=="CHIUSO" and not (
            row.get("deadline") and _https(row.get("deadline_source")) or
            row.get("closure_confirmed") and _https(row.get("status_evidence"))):
        reasons.append("chiusura_non_documentata")
    # An aggregator may aid discovery, but cannot prove primary-source grant
    # terms merely by being reachable. Manual/source-backed review or issuer URL.
    if row.get("source_id")=="volto" and not (
            _https(row.get("issuer_official_url")) or
            _https(row.get("assessment_source")) and
            urlparse(row["assessment_source"]).hostname not in
                ("volontariatotorino.it","infobandi.csvnet.it")):
        reasons.append("fonte_ente_erogatore_non_verificata")
    return reasons


def split_new_catalogue(rows, public_ids):
    """Keep legacy public IDs; new records enter only after full gate."""
    published=[]
    pending=[]
    failures=Counter()
    admitted=[]
    for row in rows:
        # Historical cards with an unconfirmed application window are not
        # exempt from the pre-publication gate. Preserve the same public_id
        # in the persistent review queue for a future verified re-admission.
        legacy=row.get("id") in public_ids
        uncertain_legacy=(legacy and row.get("funding_status")=="DA VERIFICARE"
                          and row.get("opportunity_type") in CANDIDATES)
        if legacy and not uncertain_legacy:
            published.append(row)
            continue
        reasons=admission_reasons(row)
        if reasons:
            candidate=dict(row)
            candidate.pop("catalog_admission_status",None)
            candidate["admission_reasons"]=reasons
            pending.append(candidate)
            failures.update(reasons)
        else:
            row.pop("admission_reasons",None)
            row["catalog_admission_status"]="valutata_prima_pubblicazione"
            admitted.append(row.get("public_id"))
            published.append(row)
    return published,pending,{
        "new_published":len(admitted),
        "published_ids":admitted,
        "in_review":len(pending),
        "reasons":dict(sorted(failures.items())),
        "pending_ids":[x.get("id") for x in pending],
        "note":"Nuove schede ammesse solo dopo verifica documentale; nessuna ammissibilità legale certificata."
    }
