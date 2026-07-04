from flask import Flask

from config import Config

from .models import db
from .routes import register_routes
from .utils import initialize_database, load_local_env


load_local_env()


def create_app(config=None):
    flask_app = Flask(__name__, instance_relative_config=True)
    flask_app.config.from_object(Config)
    if config:
        flask_app.config.update(config)

    db.init_app(flask_app)
    register_routes(flask_app)

    if not flask_app.config.get("TESTING"):
        with flask_app.app_context():
            initialize_database()

    return flask_app
