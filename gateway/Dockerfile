FROM ubuntu:24.04

# Evitar prompts interativos durante a instalação
ENV DEBIAN_FRONTEND=noninteractive

# Instalação dos pacotes base
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
    && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho da API
WORKDIR /app

# Expor portas da API e Interface Web (a configurar posteriormente)
EXPOSE 5000

# O script de entrada será criado na Fase 3
CMD ["/bin/bash"]