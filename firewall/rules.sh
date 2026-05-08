#!/usr/bin/env bash
set -e

echo "[INFO] Configurando firewall base con UFW..."

sudo ufw --force reset

sudo ufw default deny incoming
sudo ufw default allow outgoing

# Administracion por SSH
sudo ufw allow 22/tcp comment "SSH administracion"

# Servicios publicos de entrada
sudo ufw allow 80/tcp comment "HTTP entrada publica"
sudo ufw allow 443/tcp comment "HTTPS entrada publica"

# DNS para resolucion de dominios del proyecto
sudo ufw allow 53/tcp comment "DNS TCP"
sudo ufw allow 53/udp comment "DNS UDP"

# Bloqueos explicitos de servicios internos
sudo ufw deny 3306/tcp comment "Bloquear MariaDB externo"
sudo ufw deny 5672/tcp comment "Bloquear RabbitMQ AMQP externo"
sudo ufw deny 15672/tcp comment "Bloquear RabbitMQ Management externo"
sudo ufw deny 6379/tcp comment "Bloquear Redis externo"

sudo ufw --force enable

echo "[INFO] Estado actual del firewall:"
sudo ufw status numbered
