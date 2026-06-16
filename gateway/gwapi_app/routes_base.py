from flask import Blueprint, jsonify

base_bp = Blueprint('base', __name__)

@base_bp.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "Gateway API"}), 200