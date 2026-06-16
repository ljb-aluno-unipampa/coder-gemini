FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    kea-dhcp4-server \
    kea-ctrl-agent \
    nftables \
    iproute2 \
    iputils-ping \
    curl \
    jq \
    python3 \
    python3-pip \
    python3-flask \
    python3-dotenv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

EXPOSE 5000

COPY start-gateway.sh /usr/local/bin/start-gateway.sh
RUN chmod +x /usr/local/bin/start-gateway.sh
ENTRYPOINT ["/usr/local/bin/start-gateway.sh"]