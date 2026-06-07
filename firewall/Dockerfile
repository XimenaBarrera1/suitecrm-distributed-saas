FROM debian:12

RUN apt update && \
    apt install -y iptables iproute2 && \
    rm -rf /var/lib/apt/lists/*

COPY firewall.sh /firewall.sh

RUN chmod +x /firewall.sh

CMD ["/firewall.sh"]