from app.db.database import db
from app.models.activity import Activity
from app.models.contact import Contact
from app.utils.logging import audit_log
from app.utils.serialization import model_to_dict
from app.utils.validation import ValidationError, parse_date, require_fields, validate_status


ALLOWED_ACTIVITY_STATUS = {"OPEN", "IN_PROGRESS", "COMPLETE", "CANCELLED"}


def upsert_activity(payload: dict) -> Activity:
    require_fields(payload, ["external_id", "account_external_id", "description", "subject"])
    status = payload.get("status", "OPEN")
    validate_status(status, ALLOWED_ACTIVITY_STATUS, field_name="activity status")

    contact = Contact.query.filter_by(external_id=payload["account_external_id"]).first()
    if not contact:
        raise ValidationError("Contact account_external_id not found")

    activity = Activity.query.filter_by(external_id=payload["external_id"]).first()
    operation = "UPDATE" if activity else "CREATE"
    if not activity:
        activity = Activity(external_id=payload["external_id"], account_id=contact.id)
        db.session.add(activity)

    activity.account_id = contact.id
    activity.description = payload["description"]
    activity.subject = payload["subject"]
    activity.status = status
    if payload.get("due_date"):
        activity.due_date = parse_date(payload["due_date"])

    db.session.commit()
    audit_log(
        entity_type="Activity",
        operation=operation,
        status="SUCCESS",
        details={"external_id": activity.external_id, "account_external_id": contact.external_id},
    )
    return activity


def get_activity_dict(activity: Activity) -> dict:
    return model_to_dict(activity)
