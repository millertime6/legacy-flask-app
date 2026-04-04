from flask import Flask

from app.db.database import db
from app.models import Activity, Application, Branch, Contact, Loan  # noqa: F401
from app.routes import register_blueprints
from app.utils.logging import configure_logging


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object("config.settings.Config")

    configure_logging(app)
    db.init_app(app)
    register_blueprints(app)

    with app.app_context():
        db.create_all()

    return app
