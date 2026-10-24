#!/usr/bin/env python3
"""Abnahme-Checks für dist/ (HANDOFF): kein noindex/ENTWURF, keine externen Ressourcen, nur JSON-LD als Script."""
import json, pathlib, re, sys

def alt_name_dupes(node, path="JSON-LD"):
    """Fehlermeldungen für doppelte Einträge in jedem alternateName (rekursiv)."""
    out = []
    if isinstance(node, dict):
        alt = node.get("alternateName")
        if isinstance(alt, list):
            seen = set()
            for n in alt:
                k = str(n).strip().casefold()
                if k in seen:
                    out.append(f"{path}.alternateName enthält '{n}' doppelt: {alt}")
                seen.add(k)
        for key, v in node.items():
            out += alt_name_dupes(v, f"{path}.{key}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out += alt_name_dupes(v, f"{path}[{i}]")
    return out

def name_dupes(text, where):
    """Fehlermeldungen, wenn ein *2Shell-Name in einem Text mehr als einmal vorkommt."""
    found = [m.group(0).casefold() for m in re.finditer(r"\b\w*2Shell\b", text, re.I)]
    return [f"{where}: '{n}' kommt {found.count(n)}x vor: {text[:160]}" for n in sorted(set(found)) if found.count(n) > 1]


NAME_TEXTS = [  # (Muster, Ort) für Texte, in denen jeder Name nur einmal stehen darf
    (r'<meta name="description" content="([^"]*)"', "meta description"),
    (r'<meta property="og:description" content="([^"]*)"', "og:description"),
    (r'<span class="alias">(.*?)</span>', "H1-Zusatz"),
    (r'<p class="aka">(.*?)</p>', "Karte (aka)"),
]


def main():
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
        for pat, where in NAME_TEXTS:
            for m in re.finditer(pat, t, re.S):
                errors += [f"{rel}: {x}" for x in name_dupes(m.group(1), where)]
        # JSON-LD: gültiges JSON, alternateName ohne doppelte Namen (Groß-/Kleinschreibung egal)
        for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', t, re.S):
            try:
                ld = json.loads(m.group(1))
            except ValueError as exc:
                errors.append(f"{rel}: JSON-LD ist kein gültiges JSON ({exc})"); continue
            errors += [f"{rel}: {e}" for e in alt_name_dupes(ld)]
        for m in re.finditer(r'url\(\s*["\']?(https?:)?//', t, re.I):
            errors.append(f"{rel}: externe url(): {t[m.start():m.start()+80]}")
    if errors:
        sys.exit("FEHLER in dist/:\n  " + "\n  ".join(errors))
    print("dist ok:", ", ".join(str(p.relative_to(dist)) for p in sorted(dist.rglob("*")) if p.is_file()))


if __name__ == "__main__":
    main()
