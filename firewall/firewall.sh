#!/bin/sh

set -e

echo "[INFO] Habilitando IP Forwarding..."

echo 1 > /proc/sys/net/ipv4/ip_forward

echo "[INFO] Limpiando reglas..."

iptables -F
iptables -X

iptables -t nat -F
iptables -t nat -X

iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

#################################################
# ADMINISTRACION
#################################################

iptables -A INPUT -p tcp --dport 22 -j ACCEPT

#################################################
# DNS
#################################################

iptables -A INPUT -p udp --dport 53 -j ACCEPT
iptables -A INPUT -p tcp --dport 53 -j ACCEPT

#################################################
# HTTP / HTTPS PUBLICO
#################################################

iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

#################################################
# BLOQUEAR SERVICIOS INTERNOS
#################################################

iptables -A INPUT -p tcp --dport 3306 -j DROP
iptables -A INPUT -p tcp --dport 6379 -j DROP
iptables -A INPUT -p tcp --dport 5672 -j DROP
iptables -A INPUT -p tcp --dport 15672 -j DROP

#################################################
# NAT HACIA REVERSE PROXY
#################################################

iptables -t nat -A PREROUTING \
    -p tcp \
    --dport 80 \
    -j DNAT \
    --to-destination 192.168.1.5:80

iptables -t nat -A PREROUTING \
    -p tcp \
    --dport 443 \
    -j DNAT \
    --to-destination 192.168.1.5:443

#################################################
# PERMITIR FORWARD HACIA PROXY
#################################################

iptables -A FORWARD \
    -p tcp \
    -d 192.168.1.5 \
    --dport 80 \
    -j ACCEPT

iptables -A FORWARD \
    -p tcp \
    -d 192.168.1.5 \
    --dport 443 \
    -j ACCEPT

#################################################
# MASQUERADE
#################################################

iptables -t nat -A POSTROUTING -j MASQUERADE

echo "[OK] Firewall configurado"