from app.db.database import db
from app.models.base import TimestampMixin


class Branch(db.Model, TimestampMixin):
    __tablename__ = "branches"

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    branch_name = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
