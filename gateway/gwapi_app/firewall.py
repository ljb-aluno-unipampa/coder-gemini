import subprocess
import json
import os

STATE_FILE = "/app/firewall_state.json"

class FirewallManager:
    def __init__(self):
        self.state = self.load_state()

    def load_state(self):
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        return {"default_policy": "drop", "rules": []}

    def save_state(self):
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=4)

    def apply(self):
        """Aplica o estado atual ao nftables."""
        ruleset = [
            "flush ruleset",
            "table inet filter {",
            f"  chain input {{ type filter hook input priority 0; policy {self.state['default_policy']}; }}",
            "  chain forward { type filter hook forward priority 0; policy accept; }",
            "}"
        ]
        
        # Adicionar regras customizadas aqui...
        
        # Execução segura
        cmd = ["nft", "-f", "-"]
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, text=True)
        process.communicate(input="\n".join(ruleset))
        return process.returncode == 0