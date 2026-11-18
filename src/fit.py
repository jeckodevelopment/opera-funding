"""Evidence-aware, explainable preliminary fit for Opera+.

Never infer eligibility, award probability, funding amounts or mandatory partners.
"""
import re

PROJECTS = [
    (re.compile(r"opera|liric|music|spettacol|teatr|festival|performing art",re.I),
     "Divulgazione dell'opera lirica con lezioni, incontri o attività dal vivo",
     "Coerenza con divulgazione musicale e spettacolo"),
    (re.compile(r"formazion|educazion|scuol|student|giovan|didattic|learning|education",re.I),
     "Percorso didattico digitale con il coinvolgimento di studenti e scuole",
     "Coerenza con formazione e coinvolgimento dei giovani"),
    (re.compile(r"digit|video|audiovis|media|podcast|innova",re.I),
     "Videolezioni e videopodcast per ampliare l'accesso alla cultura",
     "Coerenza con contenuti digitali e innovazione culturale"),
    (re.compile(r"accessib|inclus|partecip|comunit|pubblic|audience",re.I),
     "Attività divulgative per ampliare i pubblici dell'opera",
     "Coerenza con accesso, partecipazione e inclusione culturale"),
    (re.compile(r"interreg|cooperazion|transfront|europ|partner|partenariat",re.I),
     "Collaborazione culturale o formativa con enti partner",
     "Potenziale per una progettazione in partenariato")
]
PARTNER_PATTERN = re.compile(r"(?i)(?:obbligatori[oa]?)?\s*(?:partenariat|partner|partnership|consorzio|coordinatore|co-applicant)")
SPECIFIC = re.compile(r"(?i)\b(associazion|enti del terzo settore|ets|non profit|ong|fondazion)\b")

def explain(row):
    """Explain thematic suitability from identifiable evidence, never assert eligibility.

    The numeric score remains the discovery-time heuristic, not an assessment
    recalculated from official documents. Only text obtained from an inspected
    official/detail page is used as stronger thematic evidence.
    """
    title=str(row.get("title") or "")
    evidence_parts=[]
    if row.get("detail_checked") and row.get("detail_basis"):
        for field in ("summary", "beneficiaries_excerpt"):
            value=row.get(field)
            if isinstance(value,str) and value.strip():
                evidence_parts.append(value.strip()[:600])
    context=" ".join(evidence_parts)
    themes=[]
    projects=[]
    for pattern,project,reason in PROJECTS:
        if pattern.search(title):
            themes.append(reason + " (titolo)")
            projects.append(project)
        elif context and pattern.search(context):
            themes.append(reason + " (contenuto della scheda)")
            projects.append(project)
    row["score_explanation"] = (
        "; ".join(themes[:3])+"."
        if themes else
        "Non sono emerse corrispondenze tematiche esplicite nei contenuti analizzati; un punteggio basso non esclude opportunità progettuali."
    )
    row["score_confidence"] = (
        "indicativa — temi presenti anche nella scheda consultata; punteggio calcolato in fase di scoperta"
        if context else
        "bassa — analisi preliminare del titolo"
    )
    row["score_explanation_basis"] = (
        "titolo e contenuti della scheda consultata" if context else "solo titolo"
    )
    row["project_ideas"] = list(row.get("curated_project_ideas") or projects[:3])
    row["eligibility"] = row.get("eligibility") or "da verificare"
    beneficiary=str(row.get("beneficiaries_excerpt") or "")
    checks=["Verificare i beneficiari ammessi e la natura giuridica richiesta"]
    if PARTNER_PATTERN.search(title+" "+beneficiary):
        checks.append("Controllare se il partenariato è obbligatorio e con quali caratteristiche")
    if SPECIFIC.search(beneficiary):
        checks.append("Confrontare la categoria dei beneficiari con lo statuto e i requisiti di Opera+")
    if row.get("amount_kind") in ("dotazione finanziaria","budget complessivo"):
        checks.append("La cifra indicata può essere la dotazione complessiva, non il contributo ottenibile dal singolo progetto")
    if row.get("rolling_guidance"):
        checks.append("Verificare la disponibilità attuale dei fondi e le condizioni della procedura a sportello")
    checks.append("Verificare eventuali cofinanziamenti, vincoli e scadenze nella documentazione ufficiale")
    row["eligibility_checks"]=list(dict.fromkeys(checks))
    # Assign a substantive editorial reading to every record, including
    # informational pages. This is *not* evidence of current opening or legal
    # eligibility. Missing official facts remain explicit in the checks.
    point = max(0,min(100,int(row.get("relevance") or 0)))
    kind = row.get("opportunity_type") or ""
    if kind not in ("finanziamento potenziale","call progettuale da verificare"):
        label = "INFORMATIVA"
        reason = "Contenuto informativo o avviso non classificato come candidatura a finanziamento."
    elif point >= 70:
        label = "ALTA AFFINITÀ"
        reason = "Buona corrispondenza tematica per attività culturali o formative; verificare beneficiari e condizioni."
    elif point >= 45:
        label = "MEDIA AFFINITÀ"
        reason = "Alcuni temi coerenti con le attività dell'associazione; utilità progettuale da confermare nei requisiti."
    else:
        label = "BASSA AFFINITÀ"
        reason = "Corrispondenza tematica limitata nelle informazioni disponibili; conservata nel catalogo."
    row["assessment_label"] = label
    row["assessment_reason"] = reason
    row["assessment_basis"] = row["score_explanation_basis"]
    row["assessment_opening_note"] = (
        "Lo stato di apertura è distinto dalla pertinenza: senza evidenza ufficiale, non è confermato."
    )
    return row
