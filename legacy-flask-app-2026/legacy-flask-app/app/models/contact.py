from app.db.database import db
from app.models.base import TimestampMixin


class Contact(db.Model, TimestampMixin):
    __tablename__ = "contacts"

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False, index=True)
    birthdate = db.Column(db.Date, nullable=True)
    ssn_last4 = db.Column(db.String(4), nullable=True)

    loans = db.relationship("Loan", backref="contact", lazy=True)
    activities = db.relationship("Activity", backref="contact", lazy=True)
