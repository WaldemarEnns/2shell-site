#!/usr/bin/env python3
"""Abnahme-Checks für dist/ (HANDOFF): kein noindex/ENTWURF, keine externen Ressourcen, nur JSON-LD als Script."""
import pathlib, re, sys

dist = pathlib.Path(__file__).resolve().parent.parent / "dist"
need = ["index.html", "cve-2026-111497/index.html", "style.css"]
errors = [f"fehlt: dist/{n}" for n in need if not (dist / n).is_file()]
if not list((dist / "fonts").glob("*.woff2")):
    errors.append("fehlt: dist/fonts/*.woff2")
for f in sorted(dist.rglob("*")):
    if f.suffix not in (".html", ".css"):
        continue
    t = f.read_text(encoding="utf-8")
    rel = f.relative_to(dist)
    for bad in ("noindex", "nofollow", "ENTWURF", "Entwurf", "zustaende"):
        if bad in t:
            errors.append(f"{rel}: enthält '{bad}'")
    # externe Ressourcen (Links <a href> zu anderen Seiten sind erlaubt, Laden von Dritten nicht)
    for m in re.finditer(r'<(script|img|iframe|link|source|video|audio|embed|object)\b[^>]*>', t, re.I):
        tag = m.group(0)
        if re.search(r'rel="canonical"', tag):
            continue
        if re.search(r'(src|href|srcset|data)="(https?:)?//', tag, re.I):
            errors.append(f"{rel}: externe Ressource {tag[:120]}")
    for m in re.finditer(r'<script\b([^>]*)>', t, re.I):
        if 'type="application/ld+json"' not in m.group(1):
            errors.append(f"{rel}: Script ohne JSON-LD-Typ: {m.group(0)}")
    for m in re.finditer(r'url\(\s*["\']?(https?:)?//', t, re.I):
        errors.append(f"{rel}: externe url(): {t[m.start():m.start()+80]}")
if errors:
    sys.exit("FEHLER in dist/:\n  " + "\n  ".join(errors))
print("dist ok:", ", ".join(str(p.relative_to(dist)) for p in sorted(dist.rglob("*")) if p.is_file()))
