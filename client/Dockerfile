FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    iproute2 \
    iputils-ping \
    isc-dhcp-client \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /root

COPY start-client.sh /usr/local/bin/start-client.sh
RUN chmod +x /usr/local/bin/start-client.sh
ENTRYPOINT ["/usr/local/bin/start-client.sh"]