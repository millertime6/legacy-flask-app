from datetime import datetime, timezone

from app.db.database import db


def utc_now():
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_date = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    updated_date = db.Column(
        db.DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
