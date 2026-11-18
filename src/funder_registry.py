"""Public funder/program register with conservative source-ID reconciliation."""
import json
from pathlib import Path
from urllib.parse import urlparse

def load_registry(path):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    funders=data["funders"]; programs=data["programs"]
    funder_ids=[f["id"] for f in funders]
    program_ids=[p["id"] for p in programs]
    if len(set(funder_ids))!=len(funder_ids) or len(set(program_ids))!=len(program_ids):
        raise ValueError("Duplicate registry identifiers")
    if any(p["funder_id"] not in funder_ids for p in programs):
        raise ValueError("Unknown funder referenced by programme")
    for entry in [*funders,*programs]:
        url=entry.get("url") or entry.get("website")
        if url and (urlparse(url).scheme!="https" or not urlparse(url).hostname):
            raise ValueError("Registry URLs must be HTTPS")
    source_ids=[p["source_id"] for p in programs if p.get("source_id")]
    if len(set(source_ids))!=len(source_ids):
        raise ValueError("Ambiguous source-to-program mapping")
    return data

def link_opportunities(rows,registry):
    """Map only explicitly configured discovery sources; never infer from issuer text."""
    programs={p["source_id"]:p for p in registry["programs"] if p.get("source_id")}
    for row in rows:
        p=programs.get(row.get("source_id"))
        if p:
            row["funder_id"]=p["funder_id"]
            row["program_id"]=p["id"]
        elif not str(row.get("source_id") or "").startswith("programme:"):
            row.pop("funder_id",None)
            row.pop("program_id",None)
    return rows

def public_monitoring(registry,source_statuses,checked_at,direct_status=None):
    by_source={s["source_id"]:s for s in source_statuses}
    direct_status=direct_status or {}
    public_funders=[dict(f) for f in registry["funders"]]
    public_programs=[]
    for p in registry["programs"]:
        status=by_source.get(p.get("source_id"))
        direct=direct_status.get(p["id"]) if p.get("monitoring")=="direct" else None
        public_programs.append({**p,"monitoring_status":(
            "reference_only" if p.get("monitoring")=="reference-only" else
            direct["status"] if direct else
            "ok" if status and status.get("ok") else
            "error" if status and not status.get("ok") else
            "not_configured"
        ),"last_checked_at":(direct.get("last_checked_at") if direct else status.get("checked_at") if status else None),
            "changed":bool(direct.get("changed")) if direct else False,
            "candidate_count":len(direct.get("candidate_links",[])) if direct else None})
    return {"checked_at":checked_at,"funders":public_funders,"programs":public_programs}
