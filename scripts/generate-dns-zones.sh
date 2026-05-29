#!/usr/bin/env bash
set -euo pipefail

if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

if [ -z "${DNS_IP:-}" ]; then
  echo "ERROR: DNS_IP no está definido. Crea un archivo .env basado en .env.example."
  exit 1
fi

if [ -z "${ENTRYPOINT_IP:-}" ]; then
  echo "ERROR: ENTRYPOINT_IP no está definido. Crea un archivo .env basado en .env.example."
  exit 1
fi

mkdir -p dns/zones

sed \
  -e "s/__DNS_IP__/${DNS_IP}/g" \
  -e "s/__ENTRYPOINT_IP__/${ENTRYPOINT_IP}/g" \
  dns/zones/templates/db.clientea.com.tpl \
  > dns/zones/db.clientea.com

printf "\n" >> dns/zones/db.clientea.com

sed \
  -e "s/__DNS_IP__/${DNS_IP}/g" \
  -e "s/__ENTRYPOINT_IP__/${ENTRYPOINT_IP}/g" \
  dns/zones/templates/db.clienteb.com.tpl \
  > dns/zones/db.clienteb.com

printf "\n" >> dns/zones/db.clienteb.com