from flask import Flask
from .config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    from .routes_base import base_bp
    from .routes_firewall import fw_bp
    from .routes_dhcp import dhcp_bp  # Importação Nova

    app.register_blueprint(base_bp)
    app.register_blueprint(fw_bp)
    app.register_blueprint(dhcp_bp)  # Registro Novo

    return app