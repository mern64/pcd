import sys
print(f"Python path: {sys.path}", file=sys.stderr)

from flask import Flask
from .module1.routes import module1_bp
from .module2.routes import module2_bp
from .upload_data.routes import upload_data_bp
from .process_data.routes import process_data_bp

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config["SECRET_KEY"] = "change-me"  # needed for flash messages

    # Ensure instance folder exists for uploads
    import os
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Register renamed blueprints
    app.register_blueprint(upload_data_bp)
    app.register_blueprint(process_data_bp)

    return app

app = create_app()
print(f"App created successfully: {app}", file=sys.stderr)