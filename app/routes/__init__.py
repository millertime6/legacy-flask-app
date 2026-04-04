from app.routes.activity_routes import activity_bp
from app.routes.application_routes import application_bp
from app.routes.contact_routes import contact_bp
from app.routes.health_routes import health_bp
from app.routes.loan_routes import loan_bp
from app.routes.ui_routes import ui_bp


def register_blueprints(app):
    app.register_blueprint(health_bp)
    app.register_blueprint(ui_bp)
    app.register_blueprint(application_bp, url_prefix="/api/v1/applications")
    app.register_blueprint(activity_bp, url_prefix="/api/v1/activities")
    app.register_blueprint(loan_bp, url_prefix="/api/v1/loans")
    app.register_blueprint(contact_bp, url_prefix="/api/v1/contacts")
