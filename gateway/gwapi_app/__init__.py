from flask import Flask
from .config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Registro de Blueprints (adicionaremos routes_base e auth aqui)
    from .routes_base import base_bp
    app.register_blueprint(base_bp)

    return app