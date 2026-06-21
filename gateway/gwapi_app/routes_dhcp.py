# gateway/gwapi_app/routes_dhcp.py
from flask import Blueprint, jsonify, request
from .auth import requires_auth
from .dhcp_service import DHCPManager

dhcp_bp = Blueprint('dhcp', __name__)
dm = DHCPManager()

@dhcp_bp.route('/api/dhcp/status', methods=['GET'])
@requires_auth
def dhcp_status():
    res = dm._call_kea("status-get")
    return jsonify(res)

@dhcp_bp.route('/api/dhcp/leases', methods=['GET'])
@requires_auth
def dhcp_leases():
    return jsonify(dm.get_leases())

@dhcp_bp.route('/api/dhcp/reservations', methods=['GET', 'POST'])
@requires_auth
def manage_reservations():
    if request.method == 'POST':
        data = request.json
        mac = data.get('mac', '').strip()
        ip = data.get('ip', '').strip()
        hostname = data.get('hostname', '').strip()

        is_valid, error_msg = dm.validate_reservation(mac, ip, hostname)
        if not is_valid:
            return jsonify({"error": error_msg}), 400

        reservations = dm.get_reservations()
        
        # Evita duplicidade de IP ou MAC nas reservas
        if any(r['mac'] == mac or r['ip-address'] == ip for r in reservations):
            return jsonify({"error": "MAC ou IP já possui uma reserva ativa."}), 400

        reservations.append({"mac": mac, "ip-address": ip, "hostname": hostname})
        dm.save_reservations(reservations)
        return jsonify({"status": "Reserva salva localmente"}), 201

    return jsonify(dm.get_reservations())

@dhcp_bp.route('/api/dhcp/reservations/<string:mac>', methods=['DELETE'])
@requires_auth
def delete_reservation(mac):
    reservations = dm.get_reservations()
    filtered = [r for r in reservations if r['mac'].lower() != mac.lower()]
    
    if len(filtered) == len(reservations):
        return jsonify({"error": "Reserva não encontrada."}), 404
        
    dm.save_reservations(filtered)
    return jsonify({"status": "Reserva removida localmente"})

@dhcp_bp.route('/api/dhcp/apply', methods=['POST'])
@requires_auth
def dhcp_apply():
    success, msg = dm.apply_config()
    if success:
        return jsonify({"status": "sucesso", "message": msg}), 200
    return jsonify({"status": "erro", "message": msg}), 500

@dhcp_bp.route('/api/dhcp/kea', methods=['POST'])
@requires_auth
def kea_proxy():
    """Proxy seguro para enviar comandos brutos estruturados ao Kea."""
    data = request.json
    command = data.get("command")
    arguments = data.get("arguments", {})
    res = dm._call_kea(command, arguments)
    return jsonify(res)