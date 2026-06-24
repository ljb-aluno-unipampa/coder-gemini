import subprocess
import json
import os

STATE_FILE = "/app/firewall_state.json"

class FirewallManager:
    def __init__(self):
        self.state = self.load_state()

    def load_state(self):
            default_structure = {"default_policy": "accept", "rules": []} # Temporariamente accept para testes
            if os.path.exists(STATE_FILE):
                try:
                    with open(STATE_FILE, 'r') as f:
                        content = f.read().strip()
                        if not content: # Arquivo vazio
                            return default_structure
                        return json.loads(content)
                except Exception:
                    return default_structure
            return default_structure

    def save_state(self):
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=4)

    def apply(self):
            """Aplica o estado atual ao nftables garantindo exceções de infraestrutura."""
            
            # Se a política padrão for DROP, precisamos injetar as exceções vitais de sobrevivência do laboratório
            input_policy = self.state.get('default_policy', 'drop')
            wan_if = self._detect_wan_if()
            
            ruleset = [
                "flush ruleset",
                "table inet filter {",
                "  chain input {",
                f"    type filter hook input priority 0; policy {input_policy};",
                "    iifname \"lo\" accept;", # Permite tráfego local interno
                "    ct state established,related accept;", # Permite respostas a requisições do próprio GW
                "    udp dport 67-68 accept;", # NUNCA bloqueia o DHCP vindo da LAN
                "    tcp dport 5000 accept;",  # Permite acessar o painel/API pela rede
                "  }",
                "  chain forward {",
                "    type filter hook forward priority 0; policy accept;",
                "  }",
                "}",
                "table ip nat {",
                "  chain postrouting {",
                "    type nat hook postrouting priority 100;",
                f"    oifname \"{wan_if}\" masquerade;",
                "  }",
                "}"
            ]
            
            # Execução
            cmd = ["nft", "-f", "-"]
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, text=True)
            process.communicate(input="\n".join(ruleset))
            return process.returncode == 0

    def _detect_wan_if(self):
            try:
                output = subprocess.check_output(["ip", "route", "show", "default"], text=True)
                return output.split(" dev ", 1)[1].split()[0]
            except Exception:
                return "eth0"
