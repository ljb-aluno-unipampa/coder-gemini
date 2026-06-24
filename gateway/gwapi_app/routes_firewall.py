from flask import Blueprint, jsonify, request
from .auth import requires_auth
from .firewall import FirewallManager

fw_bp = Blueprint('firewall', __name__)
fm = FirewallManager()

@fw_bp.route('/firewall/rules', methods=['GET', 'POST'])
@requires_auth
def manage_rules():
    if request.method == 'POST':
        # Lógica para adicionar regra
        return jsonify({"status": "rule added"}), 201
    return jsonify(fm.state['rules'])

@fw_bp.route('/firewall/apply', methods=['POST'])
@requires_auth
def apply_firewall():
    data = request.get_json(silent=True) or {}
    policy = data.get('default_policy')
    if policy in ('accept', 'drop'):
        fm.state['default_policy'] = policy
        fm.save_state()
    success = fm.apply()
    return jsonify({"success": success})
