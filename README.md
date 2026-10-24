# 2shell-site

Statische Seite für **https://2shell.waldemarenns.de**: Übersicht und Sicherheitshinweis zu Node2Shell / HTTP2Shell (CVE-2026-111497) und PHP2Shell. Design und Texte von Desi, von Waldemar freigegeben. Die Fakten kommen aus [2shell-data](https://github.com/WaldemarEnns/2shell-data).

Keine Tracker, keine Cookies, kein JavaScript außer JSON-LD, keine Anfragen an Dritte.

## Bauen

```sh
curl -fsSL -o data/2shell.json https://raw.githubusercontent.com/WaldemarEnns/2shell-data/main/data/2shell.json
python3 build.py --prod        # Python 3.9+, keine Abhängigkeiten
python3 scripts/check_dist.py  # Abnahme-Checks (u. a. alternateName im JSON-LD ohne Dubletten)
python3 -m unittest discover -s tests
```

Ausgabe: `dist/` (`index.html`, `cve-2026-111497/index.html`, `style.css`, `fonts/`). `python3 build.py` ohne `--prod` baut die Vorschau mit Leiste und noindex.

## Docker

`Dockerfile` im Repo-Root, zweistufig:

1. `python:3.13-slim` lädt `2shell.json` von 2shell-data `main` (Build-Arg `DATA_URL`), prüft die Daten und baut `dist/`. Fehlen die Daten oder sind sie kaputt, bricht der Build ab. Ohne Daten wird nichts ausgeliefert.
2. `nginx:alpine` liefert `dist/` auf **Port 80** aus. Zur Laufzeit gibt es kein Python und kein Node.

```sh
docker build -t 2shell-site .
docker run --rm -p 8080:80 2shell-site
./scripts/smoke.sh http://127.0.0.1:8080
```

nginx (`nginx/`): `/cve-2026-111497` (Canonical, ohne Schrägstrich) liefert direkt 200, `/cve-2026-111497/` leitet per 301 dorthin um. Dazu Sicherheits-Header (CSP, nosniff, Referrer-Policy), gzip, Cache-Header (HTML 5 min, CSS 1 Tag, Schriften 1 Jahr) und ein Zugriffslog ohne IP-Adressen.

## Deploy über Coolify

- Coolify-App mit Build Pack **Dockerfile**, Port **80**, Domain `https://2shell.waldemarenns.de`.
- `.github/workflows/redeploy.yml` löst alle 6 Stunden (`30 */6 * * *` UTC, 30 min nach dem Datenlauf von 2shell-data) und per Hand einen Neubau über die Coolify-API aus. Sonst zeigt die Seite nach 24 h das Veraltet-Banner.
- Repo-Secrets (setzt Roman): `COOLIFY_URL` (z. B. `https://coolify.example.de`, ohne `/api`), `COOLIFY_APP_UUID`, `COOLIFY_DEPLOY_TOKEN` (API-Token mit Deploy-Recht). Fehlen sie, überspringt der Workflow den Lauf mit einem Hinweis.
- `.github/workflows/live-data-check.yml` (Name `live-data-check`) prüft alle 6 Stunden (`15 */6 * * *` UTC, zwischen Datenlauf und Redeploy) und per Hand die Seite gegen 2shell-data `main`: Daten, freigegebene Texte, Abnahme-Checks. Ohne Deploy, ohne Secrets. Rot heißt: Daten oder Texte prüfen.
- `.github/workflows/ci.yml` baut bei jedem PR und Push das Image und testet es mit `scripts/smoke.sh`.

## Schriften

Fraunces und IBM Plex (Sans, Mono), selbst gehostet unter der SIL Open Font License 1.1, siehe `fonts/OFL-Fraunces.txt` und `fonts/OFL-IBM-Plex.txt`.
