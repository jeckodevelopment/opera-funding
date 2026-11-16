#!/usr/bin/env python3
"""Package the static dashboard with the latest public data."""
import json
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / "dist"
if out.exists():
    shutil.rmtree(out)
shutil.copytree(root / "web", out)
(out / "data").mkdir(exist_ok=True)
for name in ("opportunities.json", "scan-status.json"):
    path = root / "data" / name
    json.loads(path.read_text(encoding="utf-8"))
    shutil.copy2(path, out / "data" / name)
print(f"Built {out}")
