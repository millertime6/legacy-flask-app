from app.db.database import db
from app.models.base import TimestampMixin


class Application(db.Model, TimestampMixin):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    application_number = db.Column(db.String(64), unique=True, nullable=False)
    application_status = db.Column(db.String(50), nullable=False, default="SUBMITTED")
    approval_date = db.Column(db.Date, nullable=True)
    loan_amount = db.Column(db.Numeric(12, 2), nullable=False)
    credit_score = db.Column(db.Integer, nullable=False)
    risk_score = db.Column(db.Numeric(5, 2), nullable=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    ssn = db.Column(db.String(11), nullable=False)
    email = db.Column(db.String(255), nullable=False, index=True)
