"""Conservative catalog-wide reconciliation and a reproducible audit trail.

Never infer eligibility, merge distinct application windows, or delete historic
opportunities. Source retirement invalidates stale live-application claims only.
"""
from collections import Counter, defaultdict
import json
from pathlib import Path
from urllib.parse import urlsplit

REQUIRED_EVIDENCE=(
    ("programme_objectives_excerpt","finalita"),
    ("funded_activities_excerpt","attivita_finanziabili"),
    ("beneficiaries_excerpt","beneficiari"),
    ("requirements_excerpt","requisiti"),
)

def load_retired_sources(path):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    entries=data.get("retired_sources",[])
    if len({r["id"] for r in entries})!=len(entries):
        raise ValueError("Retired source IDs must be unique")
    return {r["id"]:r for r in entries}

def mark_retired_source(row,retired):
    source=retired.get(row.get("source_id"))
    if source is None:
        row.pop("source_retired",None)
        row.pop("source_retirement_note",None)
        return row
    row["source_retired"]=True
    row["source_retirement_note"]=(
        "Fonte non più monitorata automaticamente; storico conservato. "
        "L'apertura attuale non è verificabile da questo canale."
    )
    # Without a permitted current fetch, an old OPEN badge cannot prove
    # that applications are still accepted. Preserve dates and identifiers.
    row["source_open_confirmed"]=False
    row["reopened_confirmed"]=False
    if row.get("status","").lower().startswith("aperto"):
        row["status"]="non verificato"
        row["status_basis"]="Fonte ritirata: apertura non riconfermata"
    return row

def audit_catalog(rows,retired):
    """Audit every record; return counts and actionable case IDs, not fake certainty."""
    records=list(rows)
    public_ids=Counter(r.get("public_id") for r in records if isinstance(r.get("public_id"),int))
    identity=defaultdict(list)
    for row in records:
        url=str(row.get("url") or "").strip()
        if not url:continue
        parsed=urlsplit(url)
        # Do not collapse query strings, application windows, or editions.
        canonical=(parsed.scheme.lower(),parsed.netloc.lower(),
                   parsed.path.rstrip("/").lower(),parsed.query,
                   str(row.get("window_key") or ""),str(row.get("edition_year") or ""))
        identity[canonical].append(row.get("public_id"))
    collisions=[sorted(ids,key=lambda v:str(v)) for ids in identity.values() if len(ids)>1]
    priority=[]
    for row in records:
        if row.get("funding_status")!="APERTO":
            continue
        gaps=[name for field,name in REQUIRED_EVIDENCE
              if not isinstance(row.get(field),str) or not row[field].strip()]
        checks=sum(isinstance(c,dict) and c.get("status") in (
            "da_verificare","potenzialmente_incompatibile")
            for c in (row.get("applicant_requirement_comparison") or []))
        if gaps or checks or row.get("assessment_document_issues"):
            priority.append({"public_id":row.get("public_id"),
                             "adequacy":row.get("adequacy_label") or "NON VALUTATA",
                             "missing_evidence":gaps,"unresolved_checks":checks,
                             "document_issues":bool(row.get("assessment_document_issues"))})
    priority.sort(key=lambda item:(0 if item["adequacy"] in ("ALTA","MEDIA") else 1,
                                   -len(item["missing_evidence"]),
                                   -item["unresolved_checks"],
                                   int(item["public_id"] or 0)))
    return {
        "records_checked":len(records),
        "status_counts":dict(sorted(Counter(str(r.get("funding_status") or "SCONOSCIUTO")
                                            for r in records).items())),
        "adequacy_counts":dict(sorted(Counter(str(r.get("adequacy_label") or "NON VALUTATA")
                                              for r in records).items())),
        "unassessed_ids":[r.get("public_id") for r in records
                          if not r.get("adequacy_label") or not r.get("assessment_review_status")],
        "duplicate_public_ids":sorted(x for x,n in public_ids.items() if n>1),
        "duplicate_same_edition_urls":collisions,
        "retired_sources":{sid:sum(r.get("source_id")==sid for r in records)
                           for sid in retired},
        "retired_open_ids":[r.get("public_id") for r in records
                            if r.get("source_id") in retired and r.get("funding_status")=="APERTO"],
        "priority_open_review":priority,
        "priority_open_review_count":len(priority),
        "coverage_note":"Controllo automatico dell'intero catalogo: non certifica ammissibilità o contenuti non disponibili."
    }
