#!/usr/bin/env python3
"""2shell.waldemarenns.de, finale Fassung (Desi, 24.10.2026).
Vorschau:   python3 build.py         -> draft/*.html inkl. *.zustaende.html, mit Vorschau-Leiste und noindex
Produktion: python3 build.py --prod  -> draft/dist/ (ohne Leiste, ohne noindex, ohne Zustands-Seiten, absolute Pfade)
Rendert aus data/2shell.json (WaldemarEnns/2shell-data: PR #7 feat/display-ranges @ed8bcc0 und
PR #6 feat/curate-overlay @aa5c64d, lokal zusammengeführt, nicht gepusht) plus data/overlay.json
(nur noch für Lücken in den Daten, auf der Seite mit ◇ markiert). Kein JS, keine Tracker, keine externen Requests."""
import json, copy, html, pathlib, re, datetime as dt
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).parent
BER = ZoneInfo("Europe/Berlin")
CAL = "https://calendly.com/kontakt-waldemarenns"
PHPCHECK = "https://php-check.waldemarenns.de/"
MONTHS = ["Januar","Februar","März","April","Mai","Juni","Juli","August","September","Oktober","November","Dezember"]
SUFFIX = [""]
PROD = [False]
BASE = "https://2shell.waldemarenns.de"
# Umami, selbst gehostet (Coolify-Service umami-analytics auf Waldemars Server in Deutschland), cookielos.
UMAMI_HOST = "https://umami.alphabyte-solutions.com"
UMAMI_ID = "c6fb22c0-e934-48fc-bf0d-8c4d35c9e476"   # Website „2shell“ in Umami
UMAMI_DOMAIN = "2shell.waldemarenns.de"             # zählt nur auf der Live-Domain, nicht lokal oder in CI
NOW = [dt.datetime.now(dt.timezone.utc)]
OV_HTML = "<span class=\"ov\" title=\"Ergänzung, fehlt in 2shell.json\">◇</span>"
OV_USED = [0]
def _ov():
    if PROD[0]: return ""
    OV_USED[0] += 1
    return OV_HTML

def href(page):
    """Interne Links: Vorschau relativ auf Dateien, Produktion auf saubere URLs."""
    if PROD[0]: return "/" if page == "index" else f"/{page}"
    return f"{page}{SUFFIX[0]}.html"

def asset(path):
    return f"/{path}" if PROD[0] else path
SEV = {"CRITICAL": "kritisch", "HIGH": "hoch", "MEDIUM": "mittel", "LOW": "niedrig"}
HOSTS = {"nodejs.org": "Node.js", "imperva.com": "Imperva", "aikido.dev": "Aikido", "opensourcemalware.com": "OpenSourceMalware",
         "strobes.co": "Strobes", "github.com": "GitHub", "bun.com": "Bun", "vercel.com": "Vercel"}
e = html.escape

def parse(s): return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))

def fdt(s):
    if s is None: return ""
    if len(s) == 7: y, m = s.split("-"); return f"{MONTHS[int(m)-1]} {y}"
    if len(s) == 10: y, m, d = s.split("-"); return f"{d}.{m}.{y}"
    d = parse(s).astimezone(BER)
    return d.strftime("%d.%m.%Y, %H:%M Uhr") + (" (MESZ)" if d.dst() else " (MEZ)")

def num(x, p=1): return f"{x:.{p}f}".replace(".", ",")

def rng(s):
    """'>= 1.0.3, < 1.2.1' -> '1.0.3 bis vor 1.2.1'"""
    m = re.fullmatch(r">=\s*([\w.\-+~:]+),\s*<\s*([\w.\-+~:]+)", s.strip())
    if m: return f"{m.group(1)} bis vor {m.group(2)}"
    m = re.fullmatch(r"<\s*([\w.\-+~:]+)", s.strip())
    if m: return f"vor {m.group(1)}"
    return s

ARROW = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
WARN = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 2 21h20L12 3z"/><path d="M12 10v5M12 18v.01"/></svg>'

def load():
    data = json.loads((ROOT / "data/2shell.json").read_text())
    ov = json.loads((ROOT / "data/overlay.json").read_text())
    return data, ov

def adv(data, cid): return next(x for x in data["advisories"] if x["id"] == cid)

def uniq(seq):
    """Jeden Namen nur einmal, Reihenfolge bleibt, Groß-/Kleinschreibung zählt nicht."""
    seen, out = set(), []
    for n in seq:
        k = str(n).strip().casefold()
        if k and k not in seen:
            seen.add(k); out.append(n)
    return out

def lead_names(nick):
    """Hauptnamen, gleichrangig (Neo/Waldemar): Node2Shell und HTTP2Shell. Alle weiteren Namen gehören in extra."""
    return [n for n in ("Node2Shell", "HTTP2Shell") if n in nick] or nick[:2]

def alias_texts(data, ov):
    """Die freigegebenen Namens-Texte (texte.md). Hauptnamen stehen nur im Hauptteil, extra nur dahinter."""
    a = adv(data, "CVE-2026-111497")
    main, extra = names(data, ov)
    lead = lead_names(a["aliases"]["nicknames"])
    return {
        "desc_advisory": (f"CVE-2026-111497, bekannt als {' und '.join(lead)}, auch {' und '.join(extra)}: Fehler im Brotli-Decoder 1.0.3 bis 1.2.0. "
                          "Betroffene Versionen, Prüfbefehle und Updates für Node.js, Bun, Python und die PHP-Erweiterung brotli."),
        "h1_alias": f"{a['id']}, auch {' und '.join(extra)}",
        "aka": f"auch {', '.join(extra)}",
        "desc_overview_names": main,
    }

def names(data, ov):
    a = adv(data, "CVE-2026-111497")
    nick = a["aliases"]["nicknames"]          # Daten: Node2Shell, Python2Shell, HTTP2Shell, Broccoli2Shell
    lead = lead_names(nick)
    main = " / ".join(lead)
    lead_k = {n.casefold() for n in lead}
    extra = uniq(n for n in nick + ov.get("CVE-2026-111497", {}).get("extraNicknames", []) if n.casefold() not in lead_k)
    return main, extra

def head(title, desc, canonical):
    return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{'' if PROD[0] else '<!-- Vorschau (Desi, 24.10.2026). Produktion: python3 build.py --prod -->'}
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
{'' if PROD[0] else '<meta name="robots" content="noindex, nofollow">'}
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="article">
<meta property="og:locale" content="de_DE">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canonical}">
<meta name="theme-color" content="#F3F0E8">
<link rel="preload" href="{asset('fonts/plexsans.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{asset('fonts/fraunces.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{asset('style.css')}">
{umami_tag()}"""

def umami_tag():
    """Umami-Script nur in der Produktion. data-domains verhindert Zählung außerhalb der Live-Domain."""
    if not PROD[0]: return ""
    return f'<script defer src="{UMAMI_HOST}/script.js" data-website-id="{UMAMI_ID}" data-domains="{UMAMI_DOMAIN}"></script>\n'


def draftbar(data, label):
    if PROD[0]: return ""
    return f"""<div class="draft" role="note"><b>Finale Fassung</b><span>Vorschau, Rollout über Clay</span><span>{label}</span>{f'<span>{OV_HTML} = Ergänzung, fehlt noch in den Daten</span>' if OV_USED[0] else ''}</div>"""

def site_header(active, main):
    s = SUFFIX[0]
    return f"""<a class="skip" href="#main">Zum Inhalt springen</a>
<header class="site"><div class="wrap">
<a class="mark" href="{href('index')}">2shell <span>· Waldemar Enns</span></a>
<nav class="top" aria-label="Hauptnavigation">
<a href="{href('index')}"{' aria-current="page"' if active=="index" else ''}>Übersicht</a>
<a href="{href('cve-2026-111497')}"{' aria-current="page"' if active=="cve" else ''}>{e(main)}</a>
<a href="{PHPCHECK}">PHP2Shell</a>
<a class="btn btn-ink btn-sm" href="{CAL}">Notfall-Check buchen</a>
</nav></div></header>"""

def stale_banner(data):
    limit = data.get("meta", {}).get("bannerStaleAfterHours", 24)
    age = (NOW[0] - parse(data["stand"])).total_seconds() / 3600
    if age <= limit: return ""
    return f"""<div class="banner" role="status">{WARN}<p style="margin:0">Die Seite hat diese Daten zuletzt am {fdt(data["stand"])} aktualisiert. Maßgeblich sind die verlinkten Herstellerhinweise.</p></div>"""

def stand_line(data):
    return f'<span class="stand">Stand: <time datetime="{data["stand"]}">{fdt(data["stand"])}</time></span>'

def src(data, a, key):
    return (a.get("sources") or {}).get(key) or data["sources"].get(key, {})

def src_hint(data, a, key):
    s = src(data, a, key)
    if s.get("status") == "veraltet":
        return f'<small>Stand {fdt(s["fetchedAt"])}, Quelle zurzeit nicht erreichbar</small>'
    return ""

def kev_text(data, a):
    s = src(data, a, "cisaKev"); k = a["kev"]
    st = k.get("status") or ("unknown" if k.get("exploited") is None else ("listed" if k["exploited"] else "not_listed"))
    if s.get("status") == "fehlt" or st == "unknown":
        return '<span class="pill unk">unbekannt</span>', '<small>Abruf bei CISA fehlgeschlagen. Kein Wert heißt nicht „nein“.</small>'
    if st == "listed":
        return f'<span class="pill warn">gelistet seit {fdt(k["dateAdded"])}</span>', src_hint(data, a, "cisaKev")
    return '<span class="pill ok">nicht gelistet</span>', (src_hint(data, a, "cisaKev") or f'<small>Katalog {e(k.get("catalogVersion") or "")}</small>')

def epss_text(data, a):
    ep = a.get("epss")
    if not ep: return "keine Angabe", "<small>FIRST hat noch keinen Wert veröffentlicht.</small>"
    return f"{num(ep['score']*100,2)} %", f"<small>Perzentil {num(ep['percentile']*100,0)} · Stand {fdt(ep['date'])}</small>{src_hint(data,a,'firstEpss')}"

def pill(fs, ref=None):
    if fs == "fixed": return '<span class="pill ok">gepatcht</span>'
    if fs == "pending":
        r = f' <a href="{ref["url"]}">{e(ref["label"].split(" · ")[0])} ({"offen" if ref["state"]=="open" else e(ref["state"])})</a>' if ref else ""
        return f'<span class="pill warn">Fix in Arbeit</span>{r}'
    if fs == "none": return '<span class="pill warn">kein Fix</span>'
    if fs == "via_runtime":
        return f'<a class="pill rt" href="{ref["url"]}" title="{e(ref["label"])}">Fix über Node-Update</a>' if ref else '<span class="pill rt">Fix über Node-Update</span>'
    return '<span class="pill unk">kein Fix gelistet</span>'

def shown(x):
    """Betroffen-Zelle: displayRange (+ displayNote), sonst affectedRange."""
    dr = x.get("displayRange")
    r = e(dr) if dr else e(rng(x["affectedRange"]))
    t = f' title="Exakt: {e(x["affectedRange"])}"' if dr and dr != x["affectedRange"] else ""
    n = f'<span class="dn">{e(x["displayNote"])}</span>' if x.get("displayNote") else ""
    return f'<span{t}>{r}</span>{n}'

def src_name(url):
    h = re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
    return HOSTS.get(h, h)

def tested(x):
    t = x.get("testedBy")
    if not t: return ""
    return f' <a href="{t["sourceUrl"]}">Quelle: {e(t["name"])}, {fdt(t["date"])}</a>'

def recall_rows(data, ov, a):
    o = ov.get("CVE-2026-111497", {})
    core = [x for x in a["affected"] if x["ecosystem"] in ("library", "npm", "runtime", "PyPI", "PECL")]
    order = {"library": 0, "npm": 1, "runtime": 2, "PyPI": 3, "PECL": 4}
    core.sort(key=lambda x: order[x["ecosystem"]])
    rows = []
    def add(name, rg, fx, st, note, mark="", extra=""):
        n = f'<span class="note">{e(note)}{extra}</span>' if note else ""
        rows.append((order.get("_", 0), f'<tr><th scope="row">{e(name)}{mark}{n}</th><td class="v" data-l="Betroffen">{rg}</td><td class="v" data-l="Fix in">{fx}</td><td data-l="Status">{st}</td></tr>'))
    for x in [c for c in core if c["ecosystem"] == "library"]:
        key = f'{x["ecosystem"]}/{x["package"]}'
        on = o.get("notes", {})
        add(x.get("displayName") or x["package"], shown(x), ", ".join(f"<strong>{v}</strong>" for v in x["fixedVersions"]), pill(x["fixStatus"]), x.get("note") or on.get(key, ""), _ov() if not x.get("note") and key in on else "")
    node = [r for r in a["runtimes"] if r["product"] == "Node.js"]
    for r in [r for r in node if r["fixedIn"]]:
        add(f'Node.js {r["cycle"]}', f'vor {r["fixedIn"]}', f'<strong>{r["fixedIn"]}</strong>', '<span class="pill ok">gepatcht</span>', f'Support bis {fdt(r["eol"])}')
    eol = [r["cycle"] for r in node if not r["fixedIn"]]
    if eol:
        older = any(c["isEol"] and c["cycle"] not in eol for c in data.get("eolCycles", {}).get("nodejs", []))
        label = "Node.js " + ", ".join(eol) + (" und älter" if older else "")
        add(label, "alle Versionen", "–", '<span class="pill warn">kein Fix (EOL)</span>', "Diese Linien bekommen keine Updates mehr. Wechsle auf eine Linie mit Fix.")
    node_fix = [r["fixedIn"] for r in node if r["fixedIn"]]
    for x in sorted([c for c in core if c["ecosystem"] != "library"], key=lambda x: order[x["ecosystem"]]):
        key = f'{x["ecosystem"]}/{x["package"]}'
        dn = x.get("displayName") or o.get("displayNames", {}).get(key)
        mark = _ov() if not x.get("displayName") and key in o.get("displayNames", {}) else ""
        if x["fixStatus"] == "via_runtime":
            fx = "Node.js " + ", ".join(f"<strong>{v}</strong>" for v in sorted(node_fix, key=lambda v: [int(p) for p in v.split(".")]))
        else:
            fx = ", ".join(f"<strong>{v}</strong>" for v in x["fixedVersions"]) or "–"
        add(dn or x["package"], shown(x), fx, pill(x["fixStatus"], x.get("fixRef")), x.get("note") or "", mark, tested(x))
    return "\n".join(r for _, r in rows)

def distro_rows(a):
    d = [x for x in a["affected"] if x["ecosystem"] in ("Debian", "Ubuntu", "Alpine")]
    out = []
    for x in d:
        fx = ", ".join(x["fixedVersions"]) or "–"
        out.append(f'<tr><th scope="row">{e(x["ecosystem"])} {e((x.get("release") or "").replace(":LTS"," LTS"))}</th><td class="v" data-l="Paket">{e(x["package"])}</td><td class="v" data-l="Betroffen">{shown(x)}</td><td class="v" data-l="Fix in">{e(fx)}</td><td data-l="Status">{pill(x["fixStatus"])}</td></tr>')
    return len(d), "\n".join(out)

def exact_rows(a):
    rows = [x for x in a["affected"] if x["ecosystem"] in ("library", "npm", "runtime", "PyPI", "PECL")]
    order = {"library": 0, "npm": 1, "runtime": 2, "PyPI": 3, "PECL": 4}
    rows.sort(key=lambda x: order[x["ecosystem"]])
    return "\n".join(f'<tr><th scope="row">{e(x.get("displayName") or x["package"])}</th><td class="v" data-l="Angezeigt">{e(x.get("displayRange") or "–")}</td><td class="v" data-l="Exakt">{e(x["affectedRange"])}</td></tr>' for x in rows)

def range_note(data):
    n = data.get("meta", {}).get("displayRangeNote")
    if not n: return None
    return re.sub(r"\s*\((displayRange|affectedRange)\)", "", n)   # Feldnamen gehören nicht auf die Seite

def footer(data, active=None):
    facts = "" if active == "datenschutz" else f"""<p>{stand_line(data)}. Die Fakten in Tabellen, Zeitleiste und Quellen kommen aus OSV, NVD, GitHub Advisories, CISA KEV, FIRST EPSS, endoflife.date und den Herstellerhinweisen. Die Seite aktualisiert sie alle {data.get('refreshIntervalHours', 6)} Stunden.</p>
"""   # auf der Datenschutzseite ohne Stand-/Fakten-Zeile (Desi)
    cur = ' aria-current="page"' if active == "datenschutz" else ""
    return f"""<footer class="site"><div class="wrap">
<div>{facts}<p>Diese Seite ist unabhängig. Sie gehört weder zu Google noch zum Node.js-Projekt, zu Bun, zum PHP-Projekt oder zur Python Software Foundation. Im Zweifel gelten die Herstellerhinweise.</p>
<p>Gesetzt in Fraunces und IBM Plex. Keine Cookies. Seitenaufrufe zähle ich anonym mit Umami auf meinem eigenen Server.</p></div>
<nav aria-label="Rechtliches"><a href="https://waldemarenns.de">Über Waldemar Enns</a><a href="https://waldemarenns.de/imprint">Impressum</a><a href="{href('datenschutz')}"{cur}>Datenschutz</a></nav>
</div></footer>"""

def offer_block(main):
    return f"""<div class="offer" id="notfall-check">
<div>
<p class="label" style="color:#B9B3A6">Notfall-Check {e(main)}</p>
<h2>Ich prüfe deine Server und spiele die Updates ein.</h2>
<p>Ich suche jede Node.js-, Bun- und Python-Installation auf deinem Server, auch in Containern und Images. Dann aktualisiere ich Runtime und Pakete, starte die Prozesse neu und sehe die Logs auf Auffälligkeiten durch. Du bekommst ein schriftliches Kurzprotokoll.</p>
<ul><li>In der Regel fertig 48 Stunden nach Erhalt der Zugänge, an Werktagen.</li><li>Von Freitagabend bis Samstagabend arbeite ich nicht.</li><li>Finde ich Spuren eines Angriffs, halte ich an und bespreche mit dir das weitere Vorgehen.</li></ul>
<p style="font-size:.875rem;color:#B9B3A6">Gleicher Umfang und gleiche Preise wie beim PHP-Notfall-Check.</p>
</div>
<div>
<p class="price">149&nbsp;€ pro Website<br>299&nbsp;€ pro Server</p>
<p class="tax">Server heißt: eigener Server, VPS oder Docker-Host. Ab 3 Systemen 15 % Rabatt je System. Du kennst den Preis, bevor ich anfange. Gemäß § 19 UStG wird keine Umsatzsteuer berechnet.</p>
<p style="margin-top:1.5rem"><a class="btn btn-ink" href="{CAL}">Notfall-Check buchen {ARROW}</a></p>
<p style="font-size:.9375rem">Oder schreib mir an <a href="mailto:kontakt@waldemarenns.de?subject=Notfall-Check%20Node2Shell%20%2F%20HTTP2Shell">kontakt@waldemarenns.de</a>, um welche Server es geht.</p>
<p style="font-size:.9375rem">Läuft deine Website mit PHP? Für PHP2Shell gibt es den <a href="{PHPCHECK}">PHP-Notfall-Check ab 149 €</a>.</p>
</div></div>"""

ROLE = {"reporter": "Gemeldet von", "fix": "Fix in Node.js", "exploit_research": "Exploit-Forschung", "analysis": "Analyse für Python"}
# Redaktionelle Texte zu exploitation[].kind (Daten liefern Datum, Art, Quelle; die Sätze gibt Waldemar frei)
EXPL = {"poc_public": "Öffentlicher Proof of Concept. Er bringt laut Aikido nur einen absichtlich geschwächten Build dazu, fremden Code auszuführen.",
        "rce_lab": "Imperva führt im Labor Code auf dem offiziellen Node.js 24.22.0 (Linux arm64) aus, nicht bei jedem Versuch.",
        "none_reported": "Laut Strobes keine bestätigten Angriffe in freier Wildbahn."}

def cvss31(a):
    """CVSS 3.1 aus cvss.additional, falls vorhanden."""
    return [c for c in (a["cvss"].get("additional") or []) if c.get("version") == "3.1"]

def advisory(data, ov, label):
    a = adv(data, "CVE-2026-111497"); o = ov.get("CVE-2026-111497", {})
    main, extra = names(data, ov)
    title = f"{main} (CVE-2026-111497): Brotli-Lücke in Node.js, Bun und Python prüfen"
    at = alias_texts(data, ov)
    desc = at["desc_advisory"]
    kev, kevsub = kev_text(data, a); ep, epsub = epss_text(data, a)
    vr = (a["cvss"].get("vendorRatings") or [None])[0]
    pending = [x for x in a["affected"] if x["fixStatus"] == "pending"]
    # Zeitleiste: echte Daten + Overlay
    tl_items = [(t, False) for t in a["timeline"]] + [(t, True) for t in o.get("timeline", [])]
    tl_items.sort(key=lambda p: p[0]["date"] if len(p[0]["date"]) > 10 else p[0]["date"] + ("T12:00:00Z" if len(p[0]["date"]) == 10 else "-01T00:00:00Z"))
    tl = "\n".join(f'<li><time datetime="{t["date"]}">{fdt(t["date"])}</time><span>{e(t["event"])}{_ov() if isov else ""} <a href="{t["sourceUrl"]}">Quelle</a></span></li>' for t, isov in tl_items)
    cn = o.get("creditNames", {})
    cr_items = [(dict(c, name=cn.get(c["name"], c["name"])), c["name"] in cn) for c in a["credits"]] + [(c, True) for c in o.get("credits", [])]
    nrep = sum(1 for c, _ in cr_items if c["role"] == "reporter")
    def cr_dt(c):
        r = ROLE.get(c["role"], c["role"])
        return f'{r} · laut {src_name(c["sourceUrl"])}' if c["role"] == "reporter" and nrep > 1 else r
    cr = "\n".join(f'<div><dt>{cr_dt(c)}</dt><dd><a href="{c["sourceUrl"]}">{e(c["name"])}</a>{_ov() if isov else ""}{f"<small>{e(c[chr(110)+chr(111)+chr(116)+chr(101)])}</small>" if c.get("note") else ""}</dd></div>' for c, isov in cr_items)
    refs_items = [(r, False) for r in a["references"]] + [(r, True) for r in o.get("references", [])]
    refs = "\n".join(f'<li><a href="{r["url"]}">{e(r["label"])}</a>{_ov() if isov else ""}{f"<span class=d>{fdt(r.get(chr(100)+chr(97)+chr(116)+chr(101)))}</span>" if r.get("date") else ""}</li>' for r, isov in refs_items)
    expl_src = a["exploitation"] or o.get("exploitation", [])
    expl_ov = not a["exploitation"]
    def expl_txt(x):
        t = x.get("note") or EXPL.get(x["kind"])
        return (e(t) if t else e(x["kind"]) + _ov()) + (_ov() if expl_ov else "")
    expl = "\n".join(f'<li><strong>{fdt(x["date"])}:</strong> {expl_txt(x)} <a href="{x["sourceUrl"]}">Bericht von {e(x["sourceLabel"])}</a></li>' for x in expl_src)
    wild = next((x for x in expl_src if x["kind"] == "none_reported"), None)
    wild_html = (f'keine gemeldet<small>Stand {fdt(wild["date"])} laut <a href="{wild["sourceUrl"]}">{e(wild["sourceLabel"])}</a></small>' if wild
                 else f'keine Angabe{_ov()}<small>Die Daten nennen noch keine Quelle.</small>')
    c31 = cvss31(a)
    c31_html = "".join(f'<dt>CVSS 3.1</dt><dd>{num(c["score"])} {SEV.get(c["severity"], e(c["severity"]))}, {e(c["source"])}</dd>' for c in c31)
    rnote = range_note(data)
    def _vk(c): return [int(p) for p in c.split(".")]
    def _join(xs): return ", ".join(xs[:-1]) + " und " + xs[-1] if len(xs) > 1 else "".join(xs)
    nrt = [r for r in a["runtimes"] if r["product"] == "Node.js"]
    node_eol_txt = _join(sorted([r["cycle"] for r in nrt if not r["fixedIn"]], key=_vk))
    ok = sorted([r["cycle"] for r in nrt if r["fixedIn"]], key=_vk)
    node_ok_txt = ", ".join(ok[:-1]) + " oder " + ok[-1] if len(ok) > 1 else "".join(ok)
    bun = next((x for x in a["affected"] if x["ecosystem"] == "runtime" and x["package"] == "bun"), None)
    bun_rng = e(bun["displayRange"]) if bun and bun.get("displayRange") else "bis einschließlich 1.4.3"
    pend_rows = "\n".join(f'<tr><th scope="row">{e(x.get("displayName") or x["package"])}<span class="note">{e(x.get("note") or "")}</span></th><td class="v" data-l="Kopie">{shown(x)}</td><td data-l="Stand">{pill("pending", x.get("fixRef"))}<span class="note">geprüft {fdt(x["fixRef"]["checkedAt"])}</span></td></tr>' for x in pending)
    nd, drows = distro_rows(a)
    canonical = "https://2shell.waldemarenns.de/cve-2026-111497"
    jsonld = {"@context": "https://schema.org", "@type": "TechArticle", "headline": title, "inLanguage": "de",
              "about": {"@type": "Thing", "name": "CVE-2026-111497", "alternateName": uniq(a["aliases"]["nicknames"] + extra)},
              "dateModified": data["stand"], "author": {"@type": "Person", "name": "Waldemar Enns", "url": "https://waldemarenns.de"}}
    s = SUFFIX[0]
    vr_html = f'<dt>Node.js</dt><dd>stuft als <a href="{vr["url"]}">„{e(vr["rating"])}“</a> ein</dd>' if vr else ""
    return head(title, desc, canonical) + f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>\n</head><body>' + draftbar(data, label) + site_header("cve", main) + f"""
<main id="main">
<div class="wrap">
<p class="meta"><span><span class="sq" aria-hidden="true"></span>Sicherheitshinweis</span><span>{a['id']}</span><span>{a['aliases']['ids'][0]}</span>{stand_line(data)}</p>
{stale_banner(data)}
<div class="hero">
<div>
<h1>{e(main)}: Lücke im Brotli-Decoder<span class="alias">{e(at["h1_alias"])}</span></h1>
<p class="lead">Präparierte, komprimierte Daten können den Brotli-Decoder von Google über das Ende eines Puffers hinausschreiben lassen. Das trifft Node.js, Bun, Python-Pakete und jede Software, die den C-Decoder in Version 1.0.3 bis 1.2.0 nutzt.</p>
<div class="actions"><a class="btn btn-ink" href="#rueckruf">Betroffene Versionen ansehen</a><a class="btn btn-line" href="#notfall-check">Notfall-Check buchen</a></div>
</div>
<aside class="plaque" aria-label="Schweregrad">
<div><div class="score">{num(a['cvss']['score'])}</div><span class="sev">{SEV.get(a['cvss']['severity'], e(a['cvss']['severity']))}</span></div>
<dl><dt>CVSS {a['cvss']['version']}</dt><dd>{e(a['cvss']['source'])}</dd>{c31_html}{vr_html}</dl>
</aside>
</div>
</div>

<section class="block" id="rueckruf" aria-labelledby="h-rueckruf"><div class="wrap">
<div class="recall">
<div class="recall-head"><span class="tag" id="h-rueckruf">Rückrufhinweis</span>
<p><strong>Brotli-Decoder 1.0.3 bis 1.2.0.</strong> Ein Schreibzugriff außerhalb des Puffers kann den Prozess abstürzen lassen, Speicherinhalte preisgeben und möglicherweise fremden Code ausführen. Ein Login braucht der Angreifer dafür nicht.</p></div>
<table class="data"><caption>Betroffene Versionen und Updates</caption>
<thead><tr><th scope="col">Produkt</th><th scope="col">Betroffen</th><th scope="col">Fix in</th><th scope="col">Status</th></tr></thead>
<tbody>
{recall_rows(data, ov, a)}
</tbody></table>
<details class="distro"><summary>Exakte Versionsbereiche{f'<span class="sum-note">{e(rnote)}</span>' if rnote else ''}</summary>
<table class="data"><caption>Angezeigter und exakter Bereich laut Quellen</caption><thead><tr><th scope="col">Produkt</th><th scope="col">Angezeigt</th><th scope="col">Exakt</th></tr></thead>
<tbody>{exact_rows(a)}</tbody></table>
</details>
<details class="distro"><summary>Pakete der Distributionen ({nd} Einträge aus Debian, Ubuntu und Alpine)</summary>
<table class="data"><thead><tr><th scope="col">Distribution</th><th scope="col">Paket</th><th scope="col">Betroffen</th><th scope="col">Fix in</th><th scope="col">Status</th></tr></thead>
<tbody>{drows}</tbody></table>
<p class="recall-foot" style="border-top:1px solid var(--rule)">„Kein Fix gelistet“ heißt: Der Tracker nennt noch keine Version mit Fix. Die Node.js-Pakete der Distributionen nutzen oft die System-Bibliothek, dann zählt die brotli-Zeile.</p>
</details>
<p class="recall-foot">Das Update allein reicht nicht. Ein laufender Prozess behält den alten Decoder, bis du ihn neu startest. Container-Images baust du auf einer gepatchten Basis neu und rollst sie aus.</p>
</div>
</div></section>

<section class="block" id="betroffen" aria-labelledby="h-betroffen"><div class="wrap">
<h2 id="h-betroffen">Wer ist betroffen?</h2>
<div class="prose"><p>Gefährdet bist du, wenn dein Code oder eine Bibliothek darin Brotli-Daten entpackt, die von außen kommen. Viele HTTP-Clients entpacken Antworten selbstständig, deshalb trifft das mehr Anwendungen als gedacht.</p></div>
<div class="paths">
<article><h3>Deine Anwendung ruft URLs ab</h3>
<p><code>fetch()</code> in Node.js und Bun entpackt Antworten mit <code>Content-Encoding: br</code> automatisch.</p>
<p>In Python tun das urllib3 und damit requests sowie aiohttp, sobald Brotli oder brotlicffi installiert ist. httpx nur mit dem Extra <code>httpx[brotli]</code>.</p>
<p>Typische Wege: Webhooks, Link-Vorschauen, Crawler, Import per URL.</p></article>
<article><h3>Deine Anwendung nimmt Request-Bodys an</h3>
<p>Express 5.0.0 bis 5.3.0 mit body-parser 2.0.0 bis 2.3.0 entpackt <code>br</code>-Bodys, zum Beispiel hinter <code>express.json()</code>.</p>
<p>Express 4 mit body-parser 1.x lehnt <code>br</code> mit 415 ab. Ein reiner <code>node:http</code>-Server entpackt Bodys nicht selbst.</p></article>
<article><h3>Dein Code ruft den Decoder direkt auf</h3>
<p><code>zlib.brotliDecompress()</code> und <code>createBrotliDecompress()</code> in Node.js, <code>brotli.decompress()</code> in Python, <code>brotli_uncompress()</code> in der PHP-Erweiterung brotli.</p>
<p>Dazu zählen Bibliotheken, die damit Archive, Caches oder Queue-Nachrichten lesen.</p></article>
</div>
<p class="aside">Express und body-parser enthalten den Fehler nicht. Sie reichen die Daten nur an den Decoder weiter. Ein Express-Update hilft deshalb nicht, das Node.js-Update schon. Hast du Node.js aus den Paketen deiner Distribution, nutzt es eventuell die System-Bibliothek. Dann kommt der Fix über das Brotli-Paket der Distribution.</p>
</div></section>

<section class="block" id="bug" aria-labelledby="h-bug"><div class="wrap prose">
<h2 id="h-bug">Der Fehler im Decoder</h2>
<p>Ein Brotli-Datenstrom besteht aus Blöcken, und der Decoder wechselt beim Lesen zwischen Blocktypen. Vor dem Fix meldete die Funktion <code>DecodeBlockTypeAndLength()</code> in <code>c/dec/decode.c</code> nur „ja“ oder „nein“. Ein unmöglicher Blockwechsel sah für den Aufrufer aus wie „brauche mehr Daten“.</p>
<p>Der Decoder hängte darauf weitere Bytes des Angreifers an einen internen Puffer von acht Byte an und schrieb über dessen Ende hinaus. So überschreibt er benachbarten Speicher.</p>
<p>Der Fix (Brotli-Commit <a href="https://github.com/google/brotli/commit/0ed4268a4401abcb4472096340477cf4af7d1a2b"><code>0ed4268</code></a>) bricht in diesem Fall mit dem Fehler <code>BROTLI_DECODER_ERROR_FORMAT_BLOCK_SWITCH</code> ab. Der CVE-Eintrag nennt CWE-252 und CWE-787. Quellen: <a href="https://nodejs.org/en/blog/vulnerability/october-2026-security-releases">Node.js-Hinweis zu CVE-2026-111497</a>, <a href="https://osv.dev/vulnerability/CVE-2026-111497">CVE-Eintrag bei OSV</a>.</p>
</div></section>

<section class="block" id="pruefen" aria-labelledby="h-pruefen"><div class="wrap">
<h2 id="h-pruefen">Versionen prüfen</h2>
<div class="prose"><p>Prüf überall, wo Code läuft: Produktion, Staging, CI-Runner, Build-Images, Serverless-Funktionen und Laptops. Schick dabei keinen Angriffs-Traffic an Produktivsysteme.</p></div>
<div class="stacks">
<div class="stack"><h3>Node.js</h3><pre><code>node --version
<span class="c"># betroffen unter 22.23.4, 24.22.1, 26.12.1 und auf Linien ohne Support</span>
node -p "process.versions.brotli"
<span class="c"># wer entpackt Request-Bodys?</span>
npm ls express body-parser</code></pre></div>
<div class="stack"><h3>Bun</h3><pre><code>bun --version
<span class="c"># betroffen {bun_rng}</span></code></pre>
<p>Mit <code>bun build --compile</code> gebaute Programme enthalten die alte Runtime, bis du sie neu baust.</p></div>
<div class="stack"><h3>Python</h3><pre><code>pip show Brotli brotlicffi
<span class="c"># wer zieht Brotli nach?</span>
pipdeptree -r -p Brotli
grep -i brotli poetry.lock uv.lock requirements*.txt</code></pre>
<p>pip-audit, Dependabot und Safety haben die PyPI-Pakete anfangs nicht zuverlässig gemeldet. Prüf von Hand.</p></div>
<div class="stack"><h3>PHP-Erweiterung brotli</h3><pre><code>php -m | grep -i brotli
<span class="c"># Details zur geladenen Erweiterung</span>
php --ri brotli</code></pre>
<p>PHP selbst ist von dieser Lücke nicht betroffen, nur die Erweiterung.</p></div>
<div class="stack"><h3>System-Bibliothek</h3><pre><code>dpkg -l | grep -i brotli      <span class="c"># Debian, Ubuntu</span>
rpm -qa | grep -i brotli      <span class="c"># RHEL, Fedora</span>
apk info -v | grep -i brotli  <span class="c"># Alpine</span></code></pre>
<p>Distributionen liefern den Fix teils als Backport mit alter Versionsnummer. Vergleich mit der Tabelle oben oder dem Sicherheitshinweis deiner Distribution.</p></div>
<div class="stack"><h3>Container</h3><pre><code>docker run --rm --entrypoint node &lt;image&gt; --version
docker run --rm --entrypoint pip &lt;image&gt; show Brotli brotlicffi</code></pre>
<p>Eine Paketliste übersieht leicht die Runtime, die im Image steckt.</p></div>
</div>
</div></section>

<section class="block" id="offen" aria-labelledby="h-offen"><div class="wrap">
<h2 id="h-offen">Noch ohne Fix</h2>
<div class="prose"><p>Manche Projekte bringen eine eigene Kopie des Decoders mit. Ein Update deiner Distribution ändert daran nichts. Jedes Projekt muss seine Kopie selbst aktualisieren.</p></div>
<div class="recall" style="margin-top:1.25rem">
<table class="data"><caption>Gebündelte Kopien ohne Release mit Fix</caption>
<thead><tr><th scope="col">Projekt</th><th scope="col">Gebündelte Kopie</th><th scope="col">Stand</th></tr></thead>
<tbody>{pend_rows or '<tr><td colspan="3">Die Daten nennen zurzeit kein Projekt ohne Fix.</td></tr>'}</tbody></table></div>
<p class="prose" style="margin-top:1rem">Weitere Projekte mit eigener Kopie, darunter .NET, das Ruby-Gem brotli und DuckDB, führt die <a href="https://broccoli2shell.com/#vendored">Liste gebündelter Brotli-Kopien auf broccoli2shell.com</a>.</p>
</div></section>

<section class="block" id="update" aria-labelledby="h-update"><div class="wrap">
<h2 id="h-update">Updates einspielen</h2>
<div class="stacks">
<div class="stack"><pre><code><span class="c"># Node.js, z. B. mit nvm</span>
nvm install 24.22.1   <span class="c"># oder 22.23.4 / 26.12.1</span>
<span class="c"># Dockerfile</span>
FROM node:24.22.1-slim
<span class="c"># Bun</span>
bun upgrade</code></pre></div>
<div class="stack"><pre><code><span class="c"># Python</span>
pip install -U "Brotli&gt;=1.2.1" "brotlicffi&gt;=1.2.1.0"
<span class="c"># Debian, Ubuntu</span>
sudo apt update &amp;&amp; sudo apt upgrade</code></pre></div>
</div>
<ul class="plain" style="margin-top:1.5rem">
<li>Starte danach jeden Prozess neu, der Brotli lädt.</li>
<li>Bau Container-Images neu. Ein auf <code>node:24.22.0</code> festgelegtes Image bleibt verwundbar, egal wie oft du es neu baust.</li>
<li>Heb die Versionen in <code>package-lock.json</code>, <code>poetry.lock</code>, <code>uv.lock</code> oder <code>requirements.txt</code> an. Sonst installiert der nächste Build die alte Version.</li>
<li>Zieh von Node.js {node_eol_txt} auf {node_ok_txt} um. Für diese Linien kommt kein Fix.</li>
</ul>
</div></section>

<section class="block" id="uebergang" aria-labelledby="h-uebergang"><div class="wrap">
<h2 id="h-uebergang">Wenn du noch nicht updaten kannst</h2>
<div class="prose"><p>Node.js nennt keinen Workaround. Die folgenden Schritte verkleinern die Angriffsfläche bis zum Update.</p></div>
<ul class="plain">
<li><strong>Python:</strong> Deinstalliere Brotli und brotlicffi, wo du Brotli nicht brauchst. urllib3, requests und aiohttp nutzen dann gzip und deflate. Entferne auch Extras wie <code>httpx[brotli]</code>, sonst kommt das Paket beim nächsten Install zurück.</li>
<li><strong>Eingehende Anfragen:</strong> Lehn Request-Bodys mit <code>Content-Encoding: br</code> an Proxy, Load Balancer oder WAF ab. Vercel hat dafür am 21.10.2026 Firewall-Regeln geschaltet.</li>
<li><strong>Express 5:</strong> <code>express.json({{ inflate: false }})</code> schaltet das Entpacken ab. Dann lehnt der Server auch gzip-Bodys ab, teste deine Clients vorher.</li>
<li><strong>Bun:</strong> <code>fetch(url, {{ decompress: false }})</code> verhindert das Entpacken, aber nur für diesen einen Aufruf.</li>
<li><strong>Ausgehende Abrufe:</strong> Eine WAF sieht die Antworten nicht, die dein Code von fremden Servern holt. Diesen Weg schließt nur das Update.</li>
</ul>
</div></section>

<section class="block" id="ausnutzung" aria-labelledby="h-ausnutzung"><div class="wrap">
<h2 id="h-ausnutzung">Ausnutzungsstand</h2>
<dl class="facts">
<div><dt>CISA KEV</dt><dd>{kev}{kevsub}</dd></div>
<div><dt>EPSS (FIRST)</dt><dd>{ep}{epsub}</dd></div>
<div><dt>Angriffe in freier Wildbahn</dt><dd>{wild_html}</dd></div>
</dl>
<ul class="plain">{expl}</ul>
</div></section>

<section class="block" id="zeitleiste" aria-labelledby="h-zeit"><div class="wrap">
<h2 id="h-zeit">Zeitleiste</h2>
<ol class="time">{tl}</ol>
<p style="font-size:.875rem;color:var(--ink-3);margin-top:1rem">Uhrzeiten in deutscher Zeit.</p>
</div></section>

<section class="block" id="dank" aria-labelledby="h-dank"><div class="wrap">
<h2 id="h-dank">Wer die Arbeit gemacht hat</h2>
<div class="prose"><p>Ich habe die Lücke weder gefunden noch behoben. Die Arbeit haben andere gemacht:</p></div>
<dl class="credits">{cr}</dl>
</div></section>

<section class="block" aria-label="Angebot"><div class="wrap">{offer_block(main)}</div></section>

<section class="block" id="quellen" aria-labelledby="h-quellen"><div class="wrap">
<h2 id="h-quellen">Quellen</h2>
<ol class="refs">{refs}</ol>
</div></section>
</main>""" + footer(data) + "\n</body></html>\n"

def overview(data, ov, label):
    h = adv(data, "CVE-2026-111497"); p1 = adv(data, "CVE-2026-109618"); p2 = adv(data, "CVE-2026-109619")
    main, extra = names(data, ov)
    title = f"PHP2Shell und {main}: Sicherheitslücken prüfen und schließen lassen"
    desc = (f"Aktuelle 2shell-Lücken mit betroffenen Versionen und Fixes: PHP2Shell ({p1['id']}, {p2['id']}) "
            f"und {alias_texts(data, ov)['desc_overview_names']} ({h['id']}). Notfall-Check zum Festpreis von Waldemar Enns.")
    kev_h, kevs_h = kev_text(data, h); kev_p, kevs_p = kev_text(data, p1)
    ep_h, _ = epss_text(data, h)
    ep_p = "keine Angabe" if not (p1.get("epss") and p2.get("epss")) else f"{num(p1['epss']['score']*100,2)} % und {num(p2['epss']['score']*100,2)} %"
    pend = [x for x in h["affected"] if x["fixStatus"] == "pending"]
    pend_txt = "; ".join(f'<span class="pill warn">Fix in Arbeit</span> {e(x.get("displayName") or x["package"])}, <a href="{x["fixRef"]["url"]}">{e(x["fixRef"]["label"].split(" · ")[0])} {"offen" if x["fixRef"]["state"]=="open" else e(x["fixRef"]["state"])}</a>' for x in pend)
    node_fix = ", ".join(r["fixedIn"] for r in h["runtimes"] if r["product"] == "Node.js" and r["fixedIn"])
    bun_fix = ", ".join(r["fixedIn"] for r in h["runtimes"] if r["product"] == "Bun" and r["fixedIn"])
    py_fix = " · ".join(f'{"Brotli" if x["package"]=="brotli" else x["package"]} {", ".join(x["fixedVersions"])}' for x in h["affected"] if x["ecosystem"] == "PyPI")
    php_fix = ", ".join(r["fixedIn"] for r in p1["runtimes"] if r["fixedIn"])
    php_eol = [c["cycle"] for c in data.get("eolCycles", {}).get("php", []) if c["isEol"]]
    php_eol_txt = f" · {php_eol[0]} und älter ohne Update" if php_eol else ""
    def cvss_line(a):
        c = a["cvss"]; return f"{num(c['score'])} {SEV.get(c['severity'], e(c['severity']))} (CVSS {c['version']})"
    def c31_line(advs):
        vals = [cvss31(x) for x in advs]
        if not all(vals): return ""
        src = vals[0][0]["source"]
        return f' · CVSS 3.1 ({e(src)}): ' + " und ".join(f'{num(v[0]["score"])} {SEV.get(v[0]["severity"], "")}' for v in vals)
    seen = set(); php_refs = []
    for x in (p1, p2):
        for r in x["references"]:
            if r["type"] in ("vendor", "advisory", "analysis", "news") and r["url"] not in seen and not r["label"].startswith(("oss-security", "php/php-src")):
                seen.add(r["url"]); php_refs.append(r)
    php_src = " · ".join(f'<a href="{r["url"]}" title="{e(r["label"])}">{e(r["label"].split(" · ")[0])}</a>' for r in php_refs)
    s = SUFFIX[0]
    canonical = "https://2shell.waldemarenns.de/"
    return head(title, desc, canonical) + '</head><body>' + draftbar(data, label) + site_header("index", main) + f"""
<main id="main">
<div class="wrap">
<p class="meta"><span><span class="sq" aria-hidden="true"></span>Notfall-Check</span><span>PHP · Node.js · Bun · Python</span>{stand_line(data)}</p>
{stale_banner(data)}
<div class="hero" style="grid-template-columns:minmax(0,1fr)">
<div>
<h1>PHP2Shell und {e(main)}: Sicherheitslücken prüfen und schließen<span class="alias">Aktuelle Lücken, über die Angreifer ohne Login an deinen Server kommen können</span></h1>
<p class="lead">Hier stehen nur die aktuellen „2Shell“-Lücken mit betroffenen Versionen, Fixes und Ausnutzungsstand. Ich prüfe deine Server zum Festpreis und spiele die Updates ein.</p>
<div class="actions"><a class="btn btn-ink" href="{CAL}">Notfall-Check buchen {ARROW}</a><a class="btn btn-line" href="#luecken">Aktuelle Lücken ansehen</a></div>
</div></div>
</div>

<section class="block" id="luecken" aria-labelledby="h-luecken"><div class="wrap">
<h2 id="h-luecken">Aktuelle Lücken</h2>
<div class="vulns">
<article class="vuln">
<div><h3>{e(main)}</h3><p class="ids">{h['id']}</p><p class="aka">{e(alias_texts(data, ov)["aka"])}</p></div>
<dl>
<dt>Betrifft</dt><dd>Brotli-Decoder 1.0.3 bis 1.2.0 in Node.js, Bun, Python-Paketen und gebündelten Kopien</dd>
<dt>Fix</dt><dd>Node.js {node_fix} · Bun {bun_fix} · {py_fix}</dd>
{f'<dt>Offen</dt><dd>{pend_txt}</dd>' if pend_txt else ''}
<dt>CVSS</dt><dd>{cvss_line(h)}{c31_line([h])}{', Node.js: „' + e(h['cvss']['vendorRatings'][0]['rating']) + '“' if h['cvss'].get('vendorRatings') else ''}</dd>
<dt>CISA KEV</dt><dd>{kev_h} {kevs_h}</dd>
<dt>EPSS</dt><dd>{ep_h}</dd>
</dl>
<a class="btn btn-line btn-sm" href="{href('cve-2026-111497')}">Hinweis zu {e(main)} lesen {ARROW}</a>
</article>
<article class="vuln">
<div><h3>PHP2Shell</h3><p class="ids">{p1['id']}<br>{p2['id']}</p><p class="aka">zwei Lücken im PHP-Kern</p></div>
<dl>
<dt>Betrifft</dt><dd>PHP-FPM, mod_php, php-cgi, FrankenPHP, LiteSpeed</dd>
<dt>Fix</dt><dd>PHP {php_fix}{php_eol_txt}</dd>
<dt>CVSS</dt><dd>je {cvss_line(p1)}{c31_line([p1, p2])}</dd>
<dt>CISA KEV</dt><dd>{kev_p} {kevs_p}</dd>
<dt>EPSS</dt><dd>{ep_p}</dd>
{f'<dt>Quellen</dt><dd class="srcs">{php_src}</dd>' if php_src else ''}
</dl>
<a class="btn btn-line btn-sm" href="{PHPCHECK}">PHP2Shell-Check öffnen {ARROW}</a>
</article>
</div>
<p style="font-size:.875rem;color:var(--ink-3);margin-top:1rem">Keine allgemeine CVE-Datenbank: Hier stehen nur Lücken, für die ich einen Notfall-Check anbiete.</p>
</div></section>

<section class="block" id="preise" aria-labelledby="h-preise"><div class="wrap">
<h2 id="h-preise">Notfall-Check zum Festpreis</h2>
<div class="prose"><p>Du kennst den Preis, bevor ich anfange. Im Protokoll steht, was vorher lief und was ich geändert habe.</p></div>
<div class="prices">
<article><h3>PHP2Shell</h3><p>PHP-Version prüfen, Update einspielen, Logs durchsehen, Kurzprotokoll.</p>
<p class="amount">149&nbsp;€ pro Website<br>299&nbsp;€ pro Server</p><p>Ab 3 Systemen 15 % Rabatt je System.</p>
<a class="btn btn-line btn-sm" href="{PHPCHECK}#preise">Leistungen im PHP-Check ansehen</a></article>
<article><h3>{e(main)}</h3><p>Node.js-, Bun- und Python-Installationen finden, Updates einspielen, Prozesse neu starten, Logs durchsehen, Kurzprotokoll.</p>
<p class="amount">149&nbsp;€ pro Website<br>299&nbsp;€ pro Server</p><p>Server heißt: eigener Server, VPS oder Docker-Host. Ab 3 Systemen 15 % Rabatt je System.</p>
<a class="btn btn-ink btn-sm" href="{CAL}">Notfall-Check buchen</a></article>
</div>
<p style="font-size:.875rem;color:var(--ink-2);margin-top:1rem">Alle Preise sind Endpreise. Gemäß § 19 UStG wird keine Umsatzsteuer berechnet.</p>
</div></section>

<section class="block" id="ablauf" aria-labelledby="h-ablauf"><div class="wrap">
<h2 id="h-ablauf">Vom Kurztermin zum Protokoll</h2>
<ol class="steps">
<li><span class="when">Heute</span><h3>Kurztermin oder E-Mail</h3><p>Du buchst einen Kurztermin oder schreibst mir, um welche Server es geht. Ich schicke dir ein Festpreisangebot, du gibst mir Zugang.</p></li>
<li><span class="when">In der Regel 48 Stunden</span><h3>Prüfen und updaten</h3><p>Ich prüfe Versionen und Setup, spiele die Updates ein und sehe die Logs durch. Die 48 Stunden zählen ab Erhalt der Zugänge, an Werktagen.</p></li>
<li><span class="when">Abschluss</span><h3>Protokoll</h3><p>Du liest schriftlich nach, was vorher lief, was ich geändert habe und was ich dir empfehle.</p></li>
</ol>
</div></section>

<section class="block" aria-labelledby="h-wer"><div class="wrap prose">
<h2 id="h-wer">Wer den Check macht</h2>
<p>Ich bin Waldemar Enns, Webentwickler aus Rastatt mit 9 Jahren Erfahrung in Laravel und PHP, Vue und Nuxt sowie Node. Meine eigenen Server betreibe ich mit Docker. Von Freitagabend bis Samstagabend arbeite ich nicht. <a href="https://waldemarenns.de">Mehr über mich auf waldemarenns.de</a></p>
</div></section>

<section class="block" aria-label="Termin"><div class="wrap">
<div class="offer" style="grid-template-columns:minmax(0,1.5fr) auto;align-items:center">
<div><h2>Lass deine Server prüfen.</h2><p style="margin:0">Nenn mir Server, Stack und Hoster. Du bekommst ein Festpreisangebot, bevor ich etwas anfasse.</p></div>
<div><a class="btn btn-ink" href="{CAL}">Notfall-Check buchen {ARROW}</a></div>
</div></div></section>
</main>""" + footer(data) + "\n</body></html>\n"

def states(data):
    d = copy.deepcopy(data)
    d["stand"] = "2026-10-23T04:24:51Z"
    for s in d["sources"].values():
        s["status"] = "veraltet"; s["fetchedAt"] = "2026-10-23T04:24:51Z"
    d["sources"]["cisaKev"] = {"status": "fehlt", "fetchedAt": None, "lastAttemptAt": "2026-10-24T10:24:51Z", "lastError": "HTTP 503", "staleAfterHours": 12}
    for a in d["advisories"]:
        a["sources"] = {k: copy.deepcopy(v) for k, v in d["sources"].items()}
        a["kev"].update(exploited=None, status="unknown")
        if a["id"] == "CVE-2026-111497": a["epss"] = None
    return d

def privacy(data, ov, label):
    """Datenschutzerklärung (Text in legal/datenschutz.html, Entwurf bis zu Waldemars Freigabe)."""
    main, _ = names(data, ov)
    body = re.sub(r"^\s*<!--.*?-->\s*", "", (ROOT / "legal/datenschutz.html").read_text(), flags=re.S)
    title = "Datenschutzerklärung: 2shell-Notfall-Check von Waldemar Enns"
    desc = "Datenschutzerklärung von 2shell.waldemarenns.de: Hosting bei Hetzner in Deutschland, selbst gehostete Schriften, cookielose Statistik mit selbst gehostetem Umami."
    return head(title, desc, f"{BASE}/datenschutz") + '</head><body>' + draftbar(data, label) + site_header("datenschutz", main) + f"""
<main id="main">
<div class="wrap prose legal">
<h1>Datenschutzerklärung</h1>
{body}
</div>
</main>""" + footer(data, "datenschutz") + "\n</body></html>\n"

def build_prod(data, ov):
    import shutil, sys
    dist = ROOT / "dist"
    if dist.exists(): shutil.rmtree(dist)
    (dist / "cve-2026-111497").mkdir(parents=True)
    PROD[0] = True; SUFFIX[0] = ""; NOW[0] = dt.datetime.now(dt.timezone.utc)
    (dist / "index.html").write_text(overview(data, ov, ""))
    (dist / "cve-2026-111497" / "index.html").write_text(advisory(data, ov, ""))
    (dist / "datenschutz").mkdir()
    (dist / "datenschutz" / "index.html").write_text(privacy(data, ov, ""))
    shutil.copy(ROOT / "style.css", dist / "style.css")
    shutil.copytree(ROOT / "fonts", dist / "fonts")
    print("gebaut (prod):", ", ".join(str(p.relative_to(ROOT)) for p in sorted(dist.rglob("*")) if p.is_file()))

if __name__ == "__main__":
    import sys
    data, ov = load()
    if "--prod" in sys.argv:
        build_prod(data, ov); raise SystemExit
    st = states(data)
    (ROOT / "data/2shell.zustaende.json").write_text(json.dumps(st, ensure_ascii=False, indent=1))
    real = f"Daten: 2shell-data #7 @90c8e30 + #6 @0f58a99 (lokal zusammengeführt), Stand {fdt(data['stand'])}"
    sim = "Daten: Zustände simuliert (älter als 24 h, KEV unbekannt, EPSS fehlt)"
    out = {}
    for suf, d, lab in [("", data, real), (".zustaende", st, sim)]:
        SUFFIX[0] = suf
        NOW[0] = dt.datetime.now(dt.timezone.utc) if suf == "" else dt.datetime(2026, 10, 24, 11, 0, tzinfo=dt.timezone.utc)
        for name, fn in ((f"index{suf}.html", overview), (f"cve-2026-111497{suf}.html", advisory), (f"datenschutz{suf}.html", privacy)):
            OV_USED[0] = 0
            fn(d, ov, lab)              # erster Lauf zählt ◇, zweiter Lauf rendert die Legende passend
            out[name] = fn(d, ov, lab)
    for k, v in out.items(): (ROOT / k).write_text(v)
    print("gebaut:", ", ".join(out))
