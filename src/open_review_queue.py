"""Prioritized documentary review queue for genuinely open grant opportunities.

The queue never infers an OPEN status and never changes eligibility or adequacy.
It is an internal scan-status report, not a new visual assessment.
"""
from collections import Counter
from datetime import date

CATEGORY_LABELS={
    "territorio":"Verificare sede e ambito territoriale",
    "natura_giuridica":"Verificare natura giuridica e iscrizioni richieste",
    "anzianita":"Verificare anzianità e data di riferimento",
    "condizioni_economiche":"Verificare cofinanziamento, bilancio o soglie economiche",
    "partenariato":"Verificare requisiti e accordi di partenariato",
    "esperienza_pregressa":"Verificare esperienza e attività pregresse",
}

def _deadline(row, as_of):
    value=row.get("deadline")
    if not isinstance(value,str):
        return None
    try:
        d=date.fromisoformat(value)
        return (d-as_of).days if d>=as_of else None
    except ValueError:
        return None

def review_tasks(row):
    """Stable actionable tasks, based only on existing extracted evidence."""
    tasks=[]
    seen=set()
    def add(text):
        if text not in seen:
            seen.add(text)
            tasks.append(text)
    missing=set(row.get("assessment_missing_fields") or [])
    if "Beneficiari ammessi" in missing or not row.get("beneficiaries_excerpt"):
        add("Accertare quali soggetti possono presentare domanda e in quale ruolo")
    if "Attività finanziabili" in missing or not row.get("funded_activities_excerpt"):
        add("Verificare le attività effettivamente finanziabili")
    if "Vincoli e requisiti" in missing or not row.get("requirements_excerpt"):
        add("Leggere condizioni e requisiti completi del bando")
    comparison=row.get("applicant_requirement_comparison") or []
    for item in comparison:
        if not isinstance(item,dict):
            continue
        label=CATEGORY_LABELS.get(item.get("category"))
        if label and item.get("status") != "compatibile":
            add(label)
    if row.get("eligibility_condition_status")=="potenzialmente_incompatibile":
        add("Verificare l'eventuale partecipazione come partner prima di escludere la candidatura")
    elif row.get("eligibility_condition_status")=="condizionata":
        add("Chiarire gli obblighi di partenariato o cofinanziamento")
    if row.get("assessment_document_discrepancies"):
        add("Confrontare le fonti ufficiali che riportano requisiti differenti")
    for issue in row.get("assessment_document_issues") or []:
        if isinstance(issue,dict) and issue.get("reason") not in ("testi_diversi_da_verificare",):
            add("Recuperare documentazione ufficiale non letta completamente")
            break
    if not row.get("assessment_evidence_source") and not row.get("assessment_source"):
        add("Consultare una fonte ufficiale per confermare i requisiti")
    # Individually reviewed source gaps are the most actionable checks.
    # Do not drop them just because all four evidence excerpts are populated.
    for gap in row.get("assessment_gaps") or []:
        if isinstance(gap,str) and gap.strip():
            add(" ".join(gap.split())[:380])
    if not tasks:
        add("Confermare i requisiti sulla versione aggiornata del bando")
    return tasks

def build_open_review_queue(rows, as_of=None, limit=None):
    """Return counts and a sorted set of actionable open opportunities.

    Counts cover all rows, while only records explicitly marked APERTO are in
    the queue. No open-ness is guessed from titles, expiration or edit timestamps.
    """
    as_of=as_of or date.today()
    if isinstance(as_of,str):
        as_of=date.fromisoformat(as_of)
    items=[]
    statuses=Counter()
    categories=Counter()
    paths=Counter()
    for row in rows:
        if row.get("funding_status")!="APERTO":
            continue
        status=row.get("eligibility_condition_status") or "informazioni_insufficienti"
        paths[row.get("application_path") or "integrare_verifica_documentale"]+=1
        statuses[status]+=1
        comparisons=row.get("applicant_requirement_comparison") or []
        for c in comparisons:
            if isinstance(c,dict) and c.get("category") in CATEGORY_LABELS:
                categories[c["category"]]+=1
        days=_deadline(row,as_of)
        tasks=review_tasks(row)
        sources=[]
        for url in [row.get("assessment_source"),row.get("assessment_evidence_source"),
                    row.get("url")]:
            if isinstance(url,str) and url.startswith("https://") and url not in sources:
                sources.append(url)
        for c in comparisons:
            if isinstance(c,dict) and isinstance(c.get("source"),str) and c["source"].startswith("https://") and c["source"] not in sources:
                sources.append(c["source"])
        items.append({
            "public_id":row.get("public_id"),
            "title":str(row.get("title") or "Opportunità senza titolo")[:220],
            "deadline":row.get("deadline") if days is not None else None,
            "days_remaining":days,
            "adequacy":row.get("adequacy_label") or "NON DETERMINATA",
            "application_path":row.get("application_path") or "integrare_verifica_documentale",
            "application_path_reason":row.get("application_path_reason") or "Modalità di candidatura non ancora valutata",
            "application_next_actions":row.get("application_next_actions") or tasks,
            "condition_status":status,
            "review_status":row.get("assessment_review_status") or "NON ESAMINATA",
            "pending_conditions":sum(1 for c in comparisons if isinstance(c,dict) and c.get("status")=="da_verificare"),
            "tasks":tasks,
            "sources":sources[:5],
        })
    def sort_key(item):
        urgent= item["days_remaining"] is not None and item["days_remaining"]<=14
        condition= item["condition_status"] in ("potenzialmente_incompatibile","condizionata")
        return (0 if urgent else 1, 0 if condition else 1,
                item["days_remaining"] if item["days_remaining"] is not None else 999999,
                -item["pending_conditions"], str(item["title"]).casefold())
    items.sort(key=sort_key)
    total=len(items)
    if limit is not None:
        items=items[:limit]
    return {
        "as_of":as_of.isoformat(),
        "open_total":total,
        "in_queue":len(items),
        "condition_status_counts":dict(sorted(statuses.items())),
        "specific_requirement_category_counts":dict(sorted(categories.items())),
        "application_path_counts":dict(sorted(paths.items())),
        "items":items,
    }
