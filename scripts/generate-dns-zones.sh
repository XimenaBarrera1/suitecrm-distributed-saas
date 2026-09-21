#!/usr/bin/env bash

set -euo pipefail

if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

if [ -z "${DNS_IP:-}" ]; then
  echo "ERROR: DNS_IP no está definido."
  exit 1
fi

if [ -z "${FIREWALL_IP:-}" ]; then
  echo "ERROR: FIREWALL_IP no está definido."
  exit 1
fi

mkdir -p dns/zones

sed \
  -e "s/__DNS_IP__/${DNS_IP}/g" \
  -e "s/__FIREWALL_IP__/${FIREWALL_IP}/g" \
  dns/zones/templates/db.clientea.com.tpl \
  > dns/zones/db.clientea.com

sed \
  -e "s/__DNS_IP__/${DNS_IP}/g" \
  -e "s/__FIREWALL_IP__/${FIREWALL_IP}/g" \
  dns/zones/templates/db.clienteb.com.tpl \
  > dns/zones/db.clienteb.com

echo "[OK] Zonas DNS generadas"