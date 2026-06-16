#!/bin/bash
# gateway/start-gateway.sh

# 1. Detectar interfaces
# Eth0 (WAN) e Eth1 (LAN) assumindo a ordem do compose
WAN_IF=$(ip route | grep default | awk '{print $5}')
LAN_IF=$(ip link show | grep -v 'lo\|eth0' | grep 'eth' | awk -F': ' '{print $2}')

# 2. Habilitar Forwarding
sysctl -w net.ipv4.ip_forward=1

# 3. Configurar NAT (Masquerade) com nftables
# Remove qualquer estado anterior
nft flush ruleset
# Adiciona tabela e chains básicos
nft add table inet filter
nft add chain inet filter forward { type filter hook forward priority 0 \; }
nft add chain inet filter input { type filter hook input priority 0 \; }

# Regra de NAT (Masquerade para sair pela WAN)
nft add table ip nat
nft add chain ip nat postrouting { type nat hook postrouting priority 100 \; }
nft add rule ip nat postrouting oifname "$WAN_IF" masquerade

# 4. Configurar Kea DHCP
# Gera o arquivo básico de config a partir das envs
cat <<EOF > /etc/kea/kea-dhcp4.conf
{
  "Dhcp4": {
    "interfaces-config": { "interfaces": ["$LAN_IF"] },
    "subnet4": [{
        "subnet": "192.168.222.0/24",
        "pools": [ { "pool": "$DHCP_START - $DHCP_END" } ],
        "option-data": [
            { "name": "routers", "data": "$LAN_GW_IP" },
            { "name": "domain-name-servers", "data": "$DHCP_DNS" }
        ]
    }],
    "control-socket": { "socket-type": "unix", "socket-name": "/tmp/kea-dhcp4.sock" }
  }
}
EOF

# 5. Iniciar serviços
kea-dhcp4 -c /etc/kea/kea-dhcp4.conf &
kea-ctrl-agent -c /etc/kea/kea-ctrl-agent.conf &

# Mantém rodando
tail -f /dev/null