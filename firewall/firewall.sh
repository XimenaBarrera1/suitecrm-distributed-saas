#!/bin/sh

echo 1 > /proc/sys/net/ipv4/ip_forward

iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X

iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# tráfico ya establecido
iptables -A INPUT \
-m conntrack \
--ctstate ESTABLISHED,RELATED \
-j ACCEPT

iptables -A FORWARD \
-m conntrack \
--ctstate ESTABLISHED,RELATED \
-j ACCEPT

# permitir HTTP
iptables -A INPUT \
-p tcp \
--dport 80 \
-j ACCEPT

# permitir HTTPS
iptables -A INPUT \
-p tcp \
--dport 443 \
-j ACCEPT

# forwarding HTTP hacia reverse proxy
iptables -A FORWARD \
-p tcp \
-d 192.168.1.5 \
--dport 80 \
-j ACCEPT

# forwarding HTTPS hacia reverse proxy
iptables -A FORWARD \
-p tcp \
-d 192.168.1.5 \
--dport 443 \
-j ACCEPT

# DNAT HTTP
iptables -t nat -A PREROUTING \
-p tcp \
--dport 80 \
-j DNAT --to-destination 192.168.1.5:80

# DNAT HTTPS
iptables -t nat -A PREROUTING \
-p tcp \
--dport 443 \
-j DNAT --to-destination 192.168.1.5:443

# SNAT/MASQUERADE
iptables -t nat -A POSTROUTING \
-j MASQUERADE

tail -f /dev/null