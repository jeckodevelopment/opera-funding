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
    # A title is discovery metadata, not a substantive examination of a call.
    # Prefer source-backed programme, activity, beneficiaries and conditions.
    evidence_fields = (
        ("attività finanziabili", "funded_activities_excerpt"),
        ("destinatari", "beneficiaries_excerpt"),
        ("finalità del bando", "programme_objectives_excerpt"),
        ("vincoli e condizioni", "requirements_excerpt"),
        ("contenuto della scheda", "summary"),
    )
    supplied = [(label, str(row.get(key) or "").strip()) for label, key in evidence_fields
                if isinstance(row.get(key), str) and row.get(key).strip()]
    evidence_text = " ".join(value for _, value in supplied)
    evidence_kinds = [label for label, _ in supplied]
    kind = row.get("opportunity_type") or ""
    informational = kind not in ("finanziamento potenziale", "call progettuale da verificare", "non classificato")
    # Never use title-derived themes to fabricate evidence in the source text.
    matches = [
        ("musica, opera e spettacolo", r"opera liric|\bliric|\boperist|\bmusic|spettacol|\bteatr|performing arts"),
        ("educazione e formazione", r"formazion|didattic|educazion|education|learning|student|scuol"),
        ("produzione audiovisiva e digitale", r"digit|audiovis|videolezion|videopodcast|podcast|multimedia"),
        ("accesso alla cultura e partecipazione", r"accessib|inclus|partecip|pubblic|audience|comunit"),
    ]
    supported = [label for label, pattern in matches if re.search(pattern, evidence_text, re.I)]
    unsupported = [label for label, pattern in matches if re.search(pattern, title, re.I)
                   and label not in supported]
    beneficiary = str(row.get("beneficiaries_excerpt") or "")
    requirements = str(row.get("requirements_excerpt") or "")
    # Negative indicators are stated as cautions rather than as an eligibility verdict.
    issues = []
    if re.search(r"(?i)solo (?:persone fisiche|individui|singoli artisti)|individual (?:artists|applicants)", beneficiary):
        issues.append("La fonte menziona beneficiari individuali: verificare se un'associazione può candidarsi.")
    if re.search(r"(?i)partenariat|consorzio|co-applicant|partner obbligat", requirements):
        issues.append("La candidatura può dipendere da requisiti di partenariato indicati nella fonte.")
    if not beneficiary:
        issues.append("Beneficiari ammessi non documentati.")
    if not row.get("funded_activities_excerpt"):
        issues.append("Attività finanziabili non documentate.")
    if not row.get("requirements_excerpt"):
        issues.append("Vincoli di candidatura non documentati.")
    if informational:
        label = "INFORMATIVA"
        reason = "Avviso informativo o procedura diversa da una candidatura a finanziamento."
    elif supplied:
        # Source-supported thematic overlap outweighs title-only hints; a generic
        # introductory paragraph cannot by itself justify an 'alta affinità'.
        if len(supported) >= 2 and (row.get("funded_activities_excerpt") or row.get("programme_objectives_excerpt")):
            label = "ALTA AFFINITÀ"
        elif supported:
            label = "MEDIA AFFINITÀ"
        else:
            label = "BASSA AFFINITÀ"
        reason = ("Dalla documentazione consultata emergono: " + ", ".join(supported) + "."
                  if supported else "Nei contenuti disponibili non emergono attività direttamente coerenti con Opera+.")
    else:
        # Explicitly provisional judgement, not a fake full assessment.
        point = max(0, min(100, int(row.get("relevance") or 0)))
        label = ("ALTA AFFINITÀ" if point >= 70 else "MEDIA AFFINITÀ" if point >= 45 else "BASSA AFFINITÀ")
        reason = "Valutazione provvisoria basata soltanto sul titolo; il testo ufficiale non è ancora disponibile nel catalogo."
    if kind == "non classificato":
        reason += " La tipologia della procedura non è ancora accertata."
    if supplied and unsupported:
        reason += " Temi presenti solo nel titolo: " + ", ".join(unsupported) + "."
    row["assessment_label"] = label
    row["assessment_reason"] = reason
    row["assessment_basis"] = ("fonte ufficiale: " + ", ".join(evidence_kinds) if supplied else "solo titolo, evidenze insufficienti")
    row["assessment_confidence"] = (
        "alta" if (row.get("funded_activities_excerpt") and row.get("beneficiaries_excerpt") and row.get("requirements_excerpt"))
        else "media" if (row.get("funded_activities_excerpt") and row.get("beneficiaries_excerpt"))
        else "limitata" if supplied else "bassa"
    )
    row["assessment_gaps"] = issues
    row["assessment_source"] = row.get("assessment_evidence_source") or (row.get("url") if supplied else None)
    row["assessment_opening_note"] = (
        "L'affinità non implica ammissibilità o apertura: verificare i requisiti e lo stato sulla fonte ufficiale."
    )
    return row
