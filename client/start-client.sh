#!/bin/bash
# client/start-client.sh

# 1. Remove IPs atribuídos pelo Docker para forçar o DHCP
ip addr flush dev eth0
rm -f /var/lib/dhcp/dhclient*.leases /var/lib/dhcp/dhclient.leases

# 2. Solicita IP via DHCP (executado em background)
dhclient -v eth0

# 3. Mantém o container vivo
tail -f /dev/null
