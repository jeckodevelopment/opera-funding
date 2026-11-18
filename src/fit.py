"""Evidence-aware, explainable preliminary fit for Opera+.

Never infer eligibility, award probability, funding amounts or mandatory partners.
"""
import re

# Possible Opera+ formats, not keyword matches for the art form alone.
# A cultural, educational or community call may support a project even when it
# does not mention music or opera in its title.
PROJECTS = [
    (re.compile(r"cultur|artistic|heritage|patrimon|muse|bibliotec|creative|audience",re.I),
     "Incontri e percorsi di divulgazione culturale per ampliare i pubblici",
     "Coerenza con accesso e promozione della cultura"),
    (re.compile(r"educazion|formazion|scuol|student|giovan|didattic|learning|education|pcto|pon\\b|pn\\s*scuola|fse\\+?|erasmus",re.I),
     "Laboratori nelle scuole, percorsi formativi e progetti educativi con partner",
     "Coerenza con didattica e attività culturali nelle scuole"),
    (re.compile(r"adult|lifelong|apprendimento permanente|educazione permanente|invecchiamento attivo",re.I),
     "Percorsi culturali per adulti, educazione permanente e incontri introduttivi",
     "Coerenza con formazione culturale degli adulti"),
    (re.compile(r"comunit|territor|partecip|inclus|fragilit|accessib|rigeneraz|cittadin|coesion",re.I),
     "Eventi di divulgazione, laboratori partecipativi e progetti culturali inclusivi",
     "Coerenza con partecipazione territoriale e inclusione"),
    (re.compile(r"music|opera|liric|spettacol|teatr|festival|performing art",re.I),
     "Workshop, masterclass e preparazione all'opera in collaborazione con teatri",
     "Coerenza con attività culturali e spettacolo dal vivo"),
    (re.compile(r"digit|video|audiovis|media|podcast|innova",re.I),
     "Videolezioni, videopodcast e strumenti di accesso digitale alla cultura",
     "Coerenza con contenuti culturali digitali"),
    (re.compile(r"partner|partenariat|cooperazion|transfront|europ|network",re.I),
     "Progetti culturali con scuole, teatri, enti locali o altri partner",
     "Possibilità progettuale in partenariato")
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
        ("promozione e accesso alla cultura",
         r"cultur|heritage|patrimon|artistic|creative|audience|muse|bibliotec"),
        ("educazione, scuole e giovani",
         r"formazion|didattic|educazion|education|learning|student|scuol|giovan|youth|pcto|\\bpon\\b|fse\\+"),
        ("formazione e attività culturali per adulti",
         r"adult|lifelong|apprendimento permanente|educazione permanente|invecchiamento attivo"),
        ("comunità, inclusione e partecipazione",
         r"accessib|inclus|partecip|pubblic|comunit|territor|rigeneraz|coesion"),
        ("musica, teatro e spettacolo",
         r"opera liric|\\bliric|\\boperist|\\bmusic|spettacol|\\bteatr|performing arts"),
        ("produzione audiovisiva e digitale",
         r"digit|audiovis|videolezion|videopodcast|podcast|multimedia"),
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
                  if supported else "Nelle evidenze disponibili non emergono attività finanziabili compatibili con i possibili progetti culturali ed educativi di Opera+.")
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
    row["assessment_basis"] = ("fonte ufficiale: " + ", ".join(evidence_kinds) if supplied else "solo titolo")
    row["assessment_confidence"] = (
        "alta" if (row.get("funded_activities_excerpt") and row.get("beneficiaries_excerpt") and row.get("requirements_excerpt"))
        else "media" if (row.get("funded_activities_excerpt") and row.get("beneficiaries_excerpt"))
        else "limitata" if supplied else "bassa"
    )
    row["assessment_gaps"] = issues
    row["assessment_source"] = row.get("assessment_evidence_source") or (row.get("url") if supplied else None)
    row["assessment_opening_note"] = (
        "L'affinità non implica ammissibilità; senza evidenza ufficiale lo stato di apertura non è confermato."
    )
    return row
