#!/usr/bin/env python3
"""Idempotent daily GitHub schedule gate for Opera+ Funding.

GitHub may delay or drop scheduled workflow events. Multiple morning triggers
are deliberately configured, but a successful scan is needed only once per
Europe/Rome calendar day. Push/dispatch still run immediately.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
ROME=ZoneInfo("Europe/Rome")


def should_run(event_name, report, now=None):
    """Unknown or corrupt timestamps fail open, never hide a missed daily run."""
    if event_name!="schedule":
        return True
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now=now.replace(tzinfo=timezone.utc)
    try:
        checked=report.get("checked_at") if isinstance(report,dict) else None
        last=datetime.fromisoformat(str(checked).replace("Z","+00:00"))
        if last.tzinfo is None:
            return True
        return last.astimezone(ROME).date()!=now.astimezone(ROME).date()
    except (TypeError,ValueError,OverflowError):
        return True


def main():
    try:
        report=json.loads((ROOT/"data/scan-status.json").read_text(encoding="utf-8"))
    except (OSError,ValueError):
        report={}
    event=os.environ.get("GITHUB_EVENT_NAME","")
    due=should_run(event,report)
    print("run_scan="+("true" if due else "false"))
    print("Opera+ Funding: "+("daily scan due" if due else "successful scan already recorded today"),
          file=sys.stderr)


if __name__=="__main__":
    main()
