#!/bin/bash
# gateway/start-gateway.sh

# 1. Criar pastas de controle e dar permissão total para o usuário do Kea
mkdir -p /run/kea /var/run/kea /var/lib/kea
chmod -R 777 /run/kea /var/run/kea /var/lib/kea

# 2. Detectar interfaces de forma limpa
WAN_IF=$(ip route | grep default | awk '{print $5}')
LAN_IF=$(ip route show | grep "src $LAN_GW_IP" | awk '{print $3}')

if [ -z "$LAN_IF" ]; then
    LAN_IF=$(ip link show | grep -v 'lo\|eth0' | grep 'eth' | awk -F': ' '{print $2}' | cut -d'@' -f1)
fi

echo "=> Interfaces Detectadas: WAN=$WAN_IF | LAN=$LAN_IF"

# 3. Configurar NAT e Regras Iniciais do Firewall
nft flush ruleset
nft add table inet filter
nft add chain inet filter input { type filter hook input priority 0 \; }
nft add chain inet filter forward { type filter hook forward priority 0 \; }

# Permitir DHCP, API e tráfego local
nft add rule inet filter input iifname "lo" accept
nft add rule inet filter input iifname "$LAN_IF" udp dport 67-68 accept

# Regra de NAT (Masquerade)
nft add table ip nat
nft add chain ip nat postrouting { type nat hook postrouting priority 100 \; }
nft add rule ip nat postrouting oifname "$WAN_IF" masquerade

# 4. Configurar Kea DHCP
cat <<EOF > /etc/kea/kea-dhcp4.conf
{
  "Dhcp4": {
    "interfaces-config": { 
        "interfaces": ["$LAN_IF"],
        "dhcp-socket-type": "raw" 
    },
    "lease-database": {
        "type": "memfile",
        "name": "/var/lib/kea/kea-leases4.csv",
        "lfc-interval": 3600
    },
    "subnet4": [{
        "id": 1,
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

# 5. Iniciar serviços em background
kea-dhcp4 -c /etc/kea/kea-dhcp4.conf &
kea-ctrl-agent -c /etc/kea/kea-ctrl-agent.conf &

# Iniciar API Flask redirecionando logs para o stdout do Docker
cd /app
python3 gwapi.py > /proc/1/fd/1 2>&1 &

# Mantém o container vivo
tail -f /dev/null