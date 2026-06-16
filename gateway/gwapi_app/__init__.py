from .routes_base import base_bp
from .routes_firewall import fw_bp

def create_app():
    # ... (código anterior)
    app.register_blueprint(base_bp)
    app.register_blueprint(fw_bp)
    return app