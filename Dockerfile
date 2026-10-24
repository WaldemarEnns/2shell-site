# syntax=docker/dockerfile:1
# 2shell.waldemarenns.de: statische Seite aus den Daten von WaldemarEnns/2shell-data.
# Stufe 1 holt data/2shell.json (main) und baut dist/, Stufe 2 liefert dist/ über nginx aus (Port 80).

FROM python:3.13.13-slim@sha256:aa938a849bcb82dce8f49480f056ab82bf5c1c3ebc294f0430f37b6820e7f286 AS build
WORKDIR /site
# Datenquelle, per Build-Arg änderbar (z. B. --build-arg DATA_URL=https://…/2shell.json).
ARG DATA_URL=https://raw.githubusercontent.com/WaldemarEnns/2shell-data/main/data/2shell.json
COPY build.py style.css ./
COPY fonts/ fonts/
COPY data/overlay.json data/overlay.json
COPY scripts/ scripts/
COPY tests/ tests/
# ADD lädt die Datei bei jedem Build neu (Cache nur, wenn sich der Inhalt nicht geändert hat)
# und bricht den Build bei HTTP-Fehlern ab. check_data.py stoppt bei leeren oder kaputten Daten.
ADD --chmod=644 ${DATA_URL} data/2shell.json
RUN python3 -m unittest discover -s tests \
 && python3 scripts/check_data.py \
 && python3 build.py --prod \
 && python3 scripts/check_dist.py

FROM nginx:1.30.6-alpine@sha256:47928bf67eb62a1863cb08d9ecb52d3e704304ba614eaee17884204677702951
RUN rm -f /etc/nginx/conf.d/*.conf /usr/share/nginx/html/*
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY nginx/security-headers.conf /etc/nginx/snippets/security-headers.conf
COPY --from=build /site/dist/ /usr/share/nginx/html/
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
