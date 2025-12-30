import os
from flask import Flask, redirect, url_for

from .config import Config
from .extensions import db

# import blueprints
from .upload_data.routes import upload_data_bp
from .process_data.routes import process_data_bp
from .defects.routes import defects_bp
from .developer.routes import developer_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        # Import models so SQLAlchemy knows about them before creating tables
        from . import models
        db.create_all()

    # register blueprints
    app.register_blueprint(upload_data_bp)
    app.register_blueprint(process_data_bp)
    app.register_blueprint(defects_bp)
    app.register_blueprint(developer_bp)

    @app.route("/")
    def index():
        return redirect(url_for("defects.list_projects"))

    return app

app = create_app()