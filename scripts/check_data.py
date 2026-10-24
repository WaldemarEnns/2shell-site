#!/usr/bin/env python3
"""Prüft data/2shell.json vor dem Build. Bricht ab, wenn die Daten fehlen oder unbrauchbar sind."""
import json, pathlib, sys

p = pathlib.Path(__file__).resolve().parent.parent / "data" / "2shell.json"
try:
    d = json.loads(p.read_text(encoding="utf-8"))
except Exception as exc:  # fehlt, leer, kein JSON
    sys.exit(f"FEHLER: {p} ist nicht lesbar ({exc}). Ohne Daten wird nicht gebaut.")
ids = [a.get("id") for a in d.get("advisories", []) if isinstance(a, dict)]
if not d.get("stand") or "CVE-2026-111497" not in ids:
    sys.exit(f"FEHLER: {p} hat kein 'stand' oder keinen Eintrag CVE-2026-111497 (gefunden: {ids}).")
print(f"Daten ok: stand={d['stand']}, advisories={ids}")
