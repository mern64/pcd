import os
from flask import Flask

# import blueprints
from .upload_data.routes import upload_data_bp
from .process_data.routes import process_data_bp


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

    # register blueprints
    app.register_blueprint(upload_data_bp)
    app.register_blueprint(process_data_bp)


    return app

app = create_app()
