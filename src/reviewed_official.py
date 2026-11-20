"""Bounded, human-reviewed official evidence for unresolved catalog entries.

These dated snapshots are not a substitute for rechecking issuer sites.
A time-limited OPEN flag expires unless renewed with fresh official evidence.
"""
from datetime import date
from urllib.parse import urlparse

def apply_reviewed_facts(rows, facts, now):
    today=date.fromisoformat(now[:10])
    for row in rows:
        for fact in facts:
            if row.get("source_id")!=fact["source_id"]:
                continue
            url=urlparse(row.get("url") or "")
            if (url.scheme!="https" or url.hostname!=fact["match_host"] or url.port not in (None,443)
                    or url.path.rstrip("/").lower()!=fact["match_path"].rstrip("/").lower()):
                continue
            evidence=urlparse(fact["official_url"])
            if evidence.scheme!="https" or not evidence.hostname:
                continue
            deadline=date.fromisoformat(fact["deadline"]) if fact.get("deadline") else None
            if deadline is None and not fact.get("rolling"):
                continue
            # Preserve fresher live facts and do not overwrite contradictory dates.
            if (deadline and row.get("deadline") and row["deadline"]!=deadline.isoformat()
                    and not fact.get("supersede_inferred_deadline")):
                continue
            if deadline:
                row["deadline"]=deadline.isoformat()
                row["deadline_source"]=fact["official_url"]
            row["reviewed_official_at"]="2026-11-17"
            row["reviewed_official_basis"]=fact["evidence"]
            row["status_evidence"]=fact["official_url"]
            row["deadline_verified_at"]=now
            if fact.get("opening_date"):
                row["opening_date"]=fact["opening_date"]
                row["opening_evidence"]=fact["official_url"]
            recent=not fact.get("review_valid_until") or today<=date.fromisoformat(fact["review_valid_until"])
            open_confirmed=bool(recent and (deadline is None or today<=deadline)
                                and fact["evidence"]!="official_expired_application_deadline")
            row["source_open_confirmed"]=open_confirmed
            row["closure_confirmed"]=bool(deadline and today>deadline)
            if fact.get("rolling"):
                row["rolling_confirmed"]=bool(open_confirmed)
                row["rolling_evidence"]=fact["official_url"] if open_confirmed else None
                row["status_basis"]="Richieste su base continuativa nel 2026; stato basato su verifica ufficiale datata"
            elif fact["evidence"]=="official_expired_application_deadline":
                row["status_basis"]="Scadenza di candidatura pubblicata dall'ente, già trascorsa"
            else:
                row["status_basis"]="Apertura dichiarata da ente o portale istituzionale; verifica valida per periodo limitato"
            docs=list(row.get("documents") or [])
            if not any(d.get("url")==fact["official_url"] for d in docs):
                docs.append({"label":"Fonte ufficiale della verifica","url":fact["official_url"]})
            row["documents"]=docs
            # A broken syndication URL does not invalidate an issuer-dated close.
            break
    return rows
