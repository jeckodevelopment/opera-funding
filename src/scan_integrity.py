#!/usr/bin/env python3
"""Fail closed when the output of a funding scan is incomplete or inconsistent.

Runs after scanning and before notifications/publication. This verifies integrity,
not the truth of source websites or the legal eligibility of applicants.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from catalog_admission import admission_reasons
from archive_consolidation import load_archive_reviews,archive_review_summary

ROOT=Path(__file__).resolve().parents[1]
REQUIRED_REVIEW=("assessment_review_status","adequacy_label",
                 "eligibility_condition_status")
REQUIRED_LISTS=("eligibility_specific_requirements",
                "applicant_requirement_comparison")
VALID_STATES={"APERTO","CHIUSO","IN ARRIVO","DA VERIFICARE","INFORMATIVO"}


def _integer(value):
    return isinstance(value,int) and not isinstance(value,bool)


def validate_scan(rows, report, now=None, max_age_minutes=30, pending_rows=None):
    """Return actionable errors; no network and no mutation of source data."""
    problems=[]
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone aware")
    if not isinstance(rows,list) or not rows:
        return ["Catalogo assente, vuoto o non valido"]
    if not isinstance(report,dict):
        return ["Report scansione mancante o non valido"]
    stamp=report.get("checked_at")
    try:
        checked=datetime.fromisoformat(stamp.replace("Z","+00:00"))
        if checked.tzinfo is None:
            raise ValueError("timestamp senza timezone")
        age=(now-checked).total_seconds()/60
        if age < -5 or age > max_age_minutes:
            problems.append("Timestamp scansione non recente: "+str(stamp))
    except (ValueError,TypeError,AttributeError):
        problems.append("Timestamp scansione mancante o non interpretabile")

    coverage=report.get("coverage")
    coverage_totals=coverage.get("totals") if isinstance(coverage,dict) else None
    assessment=report.get("assessment_coverage")
    queue=report.get("open_eligibility_review")
    if not isinstance(coverage_totals,dict):
        problems.append("Copertura del catalogo assente")
        coverage_totals={}
    if not isinstance(assessment,dict):
        problems.append("Copertura documentale assente")
        assessment={}
    if not isinstance(queue,dict):
        problems.append("Coda di verifica ammissibilità assente")
        queue={}

    for label,reported in (
        ("coverage.totals.all",coverage_totals.get("all")),
        ("assessment_coverage.total",assessment.get("total")),
    ):
        if not _integer(reported) or reported!=len(rows):
            problems.append(label+": atteso "+str(len(rows))+", trovato "+str(reported))

    seen=set()
    open_ids=set()
    state_totals={}
    incomplete=[]
    for i,row in enumerate(rows):
        if not isinstance(row,dict):
            problems.append("Record non valido in posizione "+str(i))
            continue
        identifier=row.get("public_id")
        if not _integer(identifier) or identifier<=0 or identifier in seen:
            problems.append("ID numerico pubblico mancante, errato o duplicato: "+str(identifier))
        else:
            seen.add(identifier)
        status=row.get("funding_status")
        state_totals[status]=state_totals.get(status,0)+1
        if status not in VALID_STATES:
            problems.append("Stato temporale sconosciuto per "+str(identifier)+": "+str(status))
        if status=="APERTO" and _integer(identifier) and identifier>0:
            open_ids.add(identifier)
        if (any(not isinstance(row.get(key),str) or not row[key].strip()
                for key in REQUIRED_REVIEW)
            or any(not isinstance(row.get(key),list) for key in REQUIRED_LISTS)
            or not isinstance(row.get("applicant_comparison_counts"),dict)):
            incomplete.append(identifier)
    missing_operational=[]
    for row in rows:
        if not isinstance(row,dict):
            continue
        if (not isinstance(row.get("application_path"),str)
            or not row.get("application_path")
            or not isinstance(row.get("application_next_actions"),list)
            or not row["application_next_actions"]
            or row.get("application_eligibility_verified") is not False):
            missing_operational.append(row.get("public_id"))
    if missing_operational:
        problems.append("Percorso operativo mancante o non prudenziale su "
                        +str(len(missing_operational))+" record")
    reconciliation=report.get("catalog_reconciliation")
    if not isinstance(reconciliation,dict):
        problems.append("Riconciliazione catalogo assente")
    else:
        sections=reconciliation.get("coverage")
        if not isinstance(sections,dict):
            problems.append("Riconciliazione catalogo priva di coperture")
        else:
            expected={"catalogo":len(rows),
                      "aperte":sum(isinstance(r,dict) and r.get("funding_status")=="APERTO" for r in rows),
                      "aperte_alta_media":sum(isinstance(r,dict) and r.get("funding_status")=="APERTO"
                                              and r.get("adequacy_label") in ("ALTA","MEDIA") for r in rows)}
            for name,total in expected.items():
                part=sections.get(name)
                if not isinstance(part,dict) or part.get("total")!=total:
                    problems.append("Riconciliazione "+name+" non coerente")
    requirements=report.get("requirement_reconciliation")
    if requirements is not None:
        sections=requirements.get("coverage") if isinstance(requirements,dict) else None
        if not isinstance(sections,dict):
            problems.append("Riconciliazione requisiti priva di coperture")
        else:
            from catalog_reconciliation import summarize_requirement_coverage
            expected=summarize_requirement_coverage(rows)
            for name,section in expected["coverage"].items():
                if sections.get(name)!=section:
                    problems.append("Riconciliazione requisiti incoerente: "+name)
            if requirements.get("open_without_comparable_requirements")!=expected[
                "open_without_comparable_requirements"]:
                problems.append("Coda requisiti non confrontabili incoerente")
        if any(not isinstance(r.get("requirement_coverage_status"),str)
               for r in rows if isinstance(r,dict)):
            problems.append("Stato di copertura requisiti mancante")
    quality=report.get("catalog_quality")
    if quality is not None:
        from catalog_quality import catalog_quality
        expected_quality=catalog_quality(rows)
        if quality!=expected_quality:
            problems.append("Diagnostica qualità catalogo non coerente con le schede")
    admission=report.get("catalog_admission")
    if admission is not None:
        if not isinstance(pending_rows,list):
            problems.append("Registro istruttorie mancante o non valido")
        else:
            public_identifiers={r.get("id") for r in rows if isinstance(r,dict)}
            pending_identifiers=[r.get("id") for r in pending_rows if isinstance(r,dict)]
            if (len(pending_identifiers)!=len(pending_rows)
                    or len(pending_identifiers)!=len(set(pending_identifiers))
                    or public_identifiers.intersection(pending_identifiers)):
                problems.append("Schede istruttorie duplicate o già pubblicate")
            if (admission.get("in_review")!=len(pending_rows)
                    or admission.get("pending_ids")!=pending_identifiers):
                problems.append("Riepilogo istruttorie non coerente")
            if any(not admission_reasons(r) for r in pending_rows if isinstance(r,dict)):
                problems.append("Scheda completa trattenuta in istruttoria")
            if any(not r.get("admission_reasons") for r in pending_rows if isinstance(r,dict)):
                problems.append("Istruttoria priva dei motivi espliciti")
            ids=admission.get("published_ids")
            if not isinstance(ids,list) or len(ids)!=admission.get("new_published"):
                problems.append("Identificativi delle nuove schede non coerenti")
            else:
                just_published={x.get("public_id"):x for x in rows if isinstance(x,dict)
                                and x.get("public_id") in ids}
                if len(just_published)!=len(ids):
                    problems.append("Nuove schede mancanti o duplicate")
                if any(admission_reasons(record) for record in just_published.values()):
                    problems.append("Pubblicazione di nuova scheda priva di valutazione completa")
    archive_report=report.get("archival_consolidation")
    if archive_report is not None:
        reviews=load_archive_reviews(ROOT/"config/archive_catalog_reviews.json")
        if archive_report!=archive_review_summary(rows,reviews):
            problems.append("Consolidamento archivio non coerente con 39 schede")
    audit=report.get("catalog_audit")
    if isinstance(audit,dict):
        if audit.get("records_checked")!=len(rows):
            problems.append("Audit catalogo non coerente con numero schede")
        if audit.get("unassessed_ids"):
            problems.append("Audit catalogo: schede senza valutazione")
        if audit.get("retired_open_ids"):
            problems.append("Audit catalogo: fonte ritirata ancora marcata APERTA")
        if audit.get("duplicate_public_ids"):
            problems.append("Audit catalogo: identificativi pubblici duplicati")
        status_in_audit=audit.get("status_counts") or {}
        if status_in_audit!={key:sum(r.get("funding_status")==key for r in rows) for key in status_in_audit}:
            problems.append("Audit catalogo: riepilogo stati non coerente")
    if incomplete:
        problems.append("Valutazioni/requisiti mancanti su "+str(len(incomplete))+
                        " record; esempi: "+", ".join(str(x) for x in incomplete[:5]))

    for label,state in (("open","APERTO"),("closed","CHIUSO"),
                        ("upcoming","IN ARRIVO"),("unverified","DA VERIFICARE"),("informational","INFORMATIVO")):
        count=coverage_totals.get(label)
        if count is None and label=="informational" and state_totals.get(state,0)==0:
            continue  # compatibility with historical reports with no information bucket
        if not _integer(count) or count!=state_totals.get(state,0):
            problems.append("coverage.totals."+label+" non coerente con le righe")
    if _integer(coverage_totals.get("all")) and sum(
        state_totals.get(x,0) for x in VALID_STATES)!=len(rows):
        problems.append("Ripartizione stati non esaustiva")

    if queue:
        items=queue.get("items")
        if not isinstance(items,list):
            problems.append("Coda operativa priva di items")
        else:
            queue_ids=[x.get("public_id") for x in items if isinstance(x,dict)]
            if len(items)!=len(queue_ids) or len(set(queue_ids))!=len(queue_ids):
                problems.append("Coda operativa contiene elementi non validi o duplicati")
            if set(queue_ids)!=open_ids:
                problems.append("Coda operativa non coincide con le opportunità APERTO")
            for entry in items:
                if not isinstance(entry,dict):
                    continue
                if not isinstance(entry.get("tasks"),list) or not entry["tasks"]:
                    problems.append("Coda operativa senza verifiche per "+str(entry.get("public_id")))
        for label,expected in (("open_total",len(open_ids)),("in_queue",len(open_ids))):
            if queue.get(label)!=expected:
                problems.append("Coda "+label+" non coerente con opportunità APERTO")
        status_counts=queue.get("condition_status_counts")
        if not isinstance(status_counts,dict) or sum(
            x for x in status_counts.values() if _integer(x))!=len(open_ids):
            problems.append("Totali dei segnali di ammissibilità non coerenti")
    return problems


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--catalog",type=Path,default=ROOT/"data/opportunities.json")
    parser.add_argument("--report",type=Path,default=ROOT/"data/scan-status.json")
    parser.add_argument("--max-age-minutes",type=int,default=30)
    args=parser.parse_args()
    try:
        rows=json.loads(args.catalog.read_text(encoding="utf-8"))
        report=json.loads(args.report.read_text(encoding="utf-8"))
        pending_path=ROOT/"data/pending-opportunities.json"
        pending_rows=json.loads(pending_path.read_text(encoding="utf-8")) if pending_path.exists() else []
        problems=validate_scan(rows,report,max_age_minutes=args.max_age_minutes,pending_rows=pending_rows)
    except (OSError,UnicodeError,json.JSONDecodeError,ValueError) as exc:
        problems=["Impossibile leggere o validare i dati: "+str(exc)]
    if problems:
        print("INTEGRITÀ SCANSIONE FALLITA:",file=sys.stderr)
        for p in problems:
            print(" - "+p,file=sys.stderr)
        return 1
    print("Integrità scansione OK: "+str(len(rows))+" record, "
          +str(sum(r.get("funding_status")=="APERTO" for r in rows))+
          " aperti, valutazioni complete e coda coerente")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
