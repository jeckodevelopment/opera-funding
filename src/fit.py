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
    title=str(row.get("title") or "")
    themes=[]
    projects=[]
    for pattern, project, reason in PROJECTS:
        if pattern.search(title):
            projects.append(project)
            themes.append(reason)
    # Preserve the original numeric relevance rather than fabricating
    # precision from unknown applicant rules.
    row["score_explanation"] = (
        "; ".join(themes[:3])+"."
        if themes else
        "Pertinenza preliminare: dal titolo non emergono elementi sufficienti per collegare il bando ai progetti Opera+."
    )
    row["score_confidence"] = "bassa — analisi preliminare del titolo"
    row["project_ideas"] = list(row.get("curated_project_ideas") or projects[:3])
    row["eligibility"] = row.get("eligibility") or "da verificare"
    beneficiary=str(row.get("beneficiaries_excerpt") or "")
    checks=["Verificare i beneficiari ammessi e la natura giuridica richiesta"]
    if PARTNER_PATTERN.search(title+" "+beneficiary):
        checks.append("Controllare se il partenariato è obbligatorio e con quali caratteristiche")
    if SPECIFIC.search(beneficiary):
        checks.append("Confrontare la categoria dei beneficiari con lo statuto e i requisiti di Opera+")
    checks.append("Verificare eventuali cofinanziamenti, vincoli e scadenze nella documentazione ufficiale")
    row["eligibility_checks"] = checks
    return row
