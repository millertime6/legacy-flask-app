from app.db.database import db
from app.models.base import TimestampMixin


class Loan(db.Model, TimestampMixin):
    __tablename__ = "loans"

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    account_id = db.Column(db.Integer, db.ForeignKey("contacts.id"), nullable=False, index=True)
    loan_account_number = db.Column(db.String(64), unique=True, nullable=False)
    loan_name = db.Column(db.String(255), nullable=False)
    loan_amount = db.Column(db.Numeric(12, 2), nullable=False)
    interest_rate = db.Column(db.Numeric(5, 2), nullable=False)
    monthly_payment = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="ACTIVE")
    term_months = db.Column(db.Integer, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)

    application_external_id = db.Column(db.String(64), nullable=True, index=True)
