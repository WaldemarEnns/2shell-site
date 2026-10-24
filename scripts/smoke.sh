#!/usr/bin/env bash
# Smoke-Test gegen einen laufenden Container: ./scripts/smoke.sh http://127.0.0.1:8080
set -euo pipefail
B="${1:-http://127.0.0.1:8080}"
fail() { echo "FEHLER: $*" >&2; exit 1; }
code() { curl -s -o /dev/null -w '%{http_code}' "$B$1"; }

for i in $(seq 1 30); do curl -sf -o /dev/null "$B/" && break; sleep 1; done

[ "$(code /)" = 200 ] || fail "/ liefert nicht 200"
[ "$(code /cve-2026-111497)" = 200 ] || fail "/cve-2026-111497 liefert nicht 200"
[ "$(code /style.css)" = 200 ] || fail "/style.css liefert nicht 200"
[ "$(code /fonts/plexsans.woff2)" = 200 ] || fail "/fonts/plexsans.woff2 liefert nicht 200"
[ "$(code /gibt-es-nicht)" = 404 ] || fail "unbekannte URL liefert nicht 404"

[ "$(code /cve-2026-111497/)" = 301 ] || fail "/cve-2026-111497/ leitet nicht per 301 um"
loc=$(curl -sI "$B/cve-2026-111497/" | tr -d '\r' | awk 'tolower($1)=="location:"{print $2}')
[ "$loc" = "/cve-2026-111497" ] || fail "Umleitung zeigt auf '$loc'"

h=$(curl -sI "$B/cve-2026-111497" | tr -d '\r')
for want in "Content-Security-Policy: default-src 'none'" "X-Content-Type-Options: nosniff" "Referrer-Policy: strict-origin-when-cross-origin" "Cache-Control: public, max-age=300"; do
  grep -qi "^$want" <<<"$h" || fail "Header fehlt: $want"
done
grep -qi '^set-cookie' <<<"$h" && fail "Set-Cookie gesetzt"
curl -sI -H 'Accept-Encoding: gzip' "$B/" | grep -qi '^content-encoding: gzip' || fail "kein gzip"
curl -sI "$B/fonts/plexsans.woff2" | grep -qi '^cache-control: public, max-age=31536000' || fail "Fonts ohne langen Cache"

for p in / /cve-2026-111497; do
  html=$(curl -s "$B$p")
  grep -qiE 'noindex|nofollow|entwurf' <<<"$html" && fail "$p enthält noindex/ENTWURF"
  grep -q '<link rel="canonical" href="https://2shell.waldemarenns.de' <<<"$html" || fail "$p ohne Canonical"
  grep -q 'Stand' <<<"$html" || fail "$p ohne Stand"
done
echo "Smoke-Test ok: $B"
