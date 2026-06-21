# gateway/gwapi_app/dhcp_service.py
import json
import csv
import os
import re
import ipaddress
import urllib.request

RESERVATIONS_FILE = "/app/dhcp_reservations.json"
LEASES_FILE = "/var/lib/kea/kea-leases4.csv"
KEA_URL = "http://127.0.0.1:8000"

class DHCPManager:
    def __init__(self):
        self.init_files()

    def init_files(self):
        if not os.path.exists(RESERVATIONS_FILE):
            with open(RESERVATIONS_FILE, 'w') as f:
                json.dump([], f)

    def _call_kea(self, command, arguments=None):
        """Executa uma chamada JSON-RPC para o Kea Control Agent."""
        payload = {"command": command, "service": ["dhcp4"]}
        if arguments:
            payload["arguments"] = arguments
        
        req = urllib.request.Request(
            KEA_URL, 
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))[0]
        except Exception as e:
            return {"result": 1, "text": f"Erro de comunicação com o Kea: {str(e)}"}

    def validate_reservation(self, mac, ip, hostname):
        if not re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', mac):
            return False, "Endereço MAC inválido."
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            return False, "Endereço IP inválido."
        if not re.match(r'^[a-zA-Z0-9-_]+$', hostname):
            return False, "Hostname inválido."
        return True, ""

    def get_leases(self):
        """Lê os leases ativos direto do memfile CSV do Kea."""
        leases = []
        if not os.path.exists(LEASES_FILE):
            return leases
        
        try:
            with open(LEASES_FILE, mode='r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Converte o timestamp do Kea para formato legível se necessário
                    leases.append({
                        "ip_address": row.get("address"),
                        "hw_address": row.get("hwaddr"),
                        "valid_lifetime": row.get("valid_lifetime"),
                        "expire": row.get("expire"),
                        "hostname": row.get("hostname", "Desconhecido")
                    })
        except Exception:
            pass
        return leases

    def get_reservations(self):
        with open(RESERVATIONS_FILE, 'r') as f:
            return json.load(f)

    def save_reservations(self, reservations):
        with open(RESERVATIONS_FILE, 'w') as f:
            json.dump(reservations, f, indent=4)

    def apply_config(self):
        """Mescla as reservas do JSON na configuração atual do Kea e aplica."""
        # 1. Busca a configuração em execução no Kea
        current_cfg_resp = self._call_kea("config-get")
        if current_cfg_resp.get("result") != 0:
            return False, "Não foi possível obter a configuração atual do Kea."

        cfg = current_cfg_resp["arguments"]["Dhcp4"]
        reservations = self.get_reservations()

        # Formatando reservas para o padrão exigido pelo Kea
        kea_reservations = [
            {"hw-address": r["mac"], "ip-address": r["ip-address"], "hostname": r["hostname"]}
            for r in reservations
        ]

        # 2. Injeta as reservas na primeira subrede localizada
        if "subnet4" in cfg and len(cfg["subnet4"]) > 0:
            cfg["subnet4"][0]["reservations"] = kea_reservations
        else:
            return False, "Nenhuma subrede configurada encontrada no Kea."

        # 3. Envia a nova configuração de volta para o Agent rodar em memória
        set_resp = self._call_kea("config-set", {"Dhcp4": cfg})
        if set_resp.get("result") == 0:
            return True, "Configuração de DHCP aplicada com sucesso."
        return False, set_resp.get("text", "Erro ao aplicar configuração.")