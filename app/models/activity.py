from app.db.database import db
from app.models.base import TimestampMixin


class Activity(db.Model, TimestampMixin):
    __tablename__ = "activities"

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    account_id = db.Column(db.Integer, db.ForeignKey("contacts.id"), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(50), nullable=False, default="OPEN")
    subject = db.Column(db.String(120), nullable=False)
