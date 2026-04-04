from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.db.database import db
from app.models.application import Application
from app.models.contact import Contact
from app.models.loan import Loan
from app.services.loan_service import calculate_monthly_payment
from app.utils.logging import audit_log
from app.utils.masking import mask_ssn
from app.utils.retry_queue import retry_queue
from app.utils.serialization import model_to_dict
from app.utils.validation import ValidationError, parse_date, require_fields, validate_email


ALLOWED_APPLICATION_STATUSES = {"SUBMITTED", "IN_REVIEW", "APPROVED", "DENIED", "BOOKED"}
DECISION_STATES = {"APPROVED", "DENIED"}
TRANSITIONS = {
    "SUBMITTED": {"IN_REVIEW", "APPROVED", "DENIED"},
    "IN_REVIEW": {"APPROVED", "DENIED"},
    "APPROVED": {"BOOKED"},
    "DENIED": set(),
    "BOOKED": set(),
}


def _next_application_number() -> str:
    latest = Application.query.order_by(Application.id.desc()).first()
    next_id = 100001 if not latest else 100000 + latest.id + 1
    return f"APP-{next_id}"


def upsert_application(payload: dict) -> Application:
    require_fields(
        payload,
        ["external_id", "loan_amount", "credit_score", "first_name", "last_name", "ssn", "email"],
    )
    validate_email(payload["email"])

    app_record = Application.query.filter_by(external_id=payload["external_id"]).first()
    operation = "UPDATE" if app_record else "CREATE"

    if not app_record:
        app_record = Application(
            external_id=payload["external_id"],
            application_number=payload.get("application_number") or _next_application_number(),
            application_status="SUBMITTED",
        )
        db.session.add(app_record)

    requested_status = payload.get("application_status", app_record.application_status)
    if requested_status not in ALLOWED_APPLICATION_STATUSES:
        raise ValidationError("Invalid application_status value")

    app_record.loan_amount = Decimal(str(payload["loan_amount"]))
    app_record.credit_score = int(payload["credit_score"])
    risk_input = payload.get("risk_score")
    if risk_input in (None, ""):
        app_record.risk_score = _derive_risk_score(app_record.credit_score)
    else:
        app_record.risk_score = Decimal(str(risk_input))
    app_record.first_name = payload["first_name"]
    app_record.last_name = payload["last_name"]
    app_record.ssn = payload["ssn"]
    app_record.email = payload["email"]

    if payload.get("approval_date"):
        app_record.approval_date = parse_date(payload["approval_date"])

    if operation == "UPDATE" and requested_status != app_record.application_status:
        _assert_transition(app_record.application_status, requested_status)
        app_record.application_status = requested_status

    db.session.commit()
    audit_log(
        entity_type="Application",
        operation=operation,
        status="SUCCESS",
        details={"external_id": app_record.external_id, "ssn": mask_ssn(app_record.ssn)},
    )
    return app_record


def decide_application(external_id: str, decision: str) -> Application:
    decision = decision.upper()
    if decision not in DECISION_STATES:
        raise ValidationError("Decision must be APPROVED or DENIED")

    app_record = Application.query.filter_by(external_id=external_id).first()
    if not app_record:
        raise ValidationError("Application not found")

    _assert_transition(app_record.application_status, decision)
    app_record.application_status = decision
    if decision == "APPROVED":
        app_record.approval_date = date.today()

    db.session.commit()
    audit_log(
        entity_type="Application",
        operation=f"DECISION_{decision}",
        status="SUCCESS",
        details={"external_id": app_record.external_id},
    )
    return app_record


def book_loan_from_application(external_id: str) -> tuple[Application, Loan]:
    app_record = Application.query.filter_by(external_id=external_id).first()
    if not app_record:
        raise ValidationError("Application not found")
    if app_record.application_status != "APPROVED":
        raise ValidationError("Only APPROVED applications can be booked")

    existing_loan = Loan.query.filter_by(application_external_id=external_id).first()
    if existing_loan:
        return app_record, existing_loan

    try:
        contact = _upsert_contact_for_application(app_record)
        principal = Decimal(app_record.loan_amount)
        annual_rate = Decimal("6.50")
        term_months = 60
        monthly_payment = calculate_monthly_payment(principal, annual_rate, term_months)

        loan = Loan(
            external_id=f"LN-{external_id}",
            account_id=contact.id,
            loan_account_number=f"ACCT-{uuid4().hex[:10].upper()}",
            loan_name=f"{app_record.last_name} Personal Loan",
            loan_amount=principal,
            interest_rate=annual_rate,
            monthly_payment=monthly_payment.quantize(Decimal("0.01")),
            status="ACTIVE",
            term_months=term_months,
            payment_method="ACH",
            application_external_id=external_id,
        )
        db.session.add(loan)
        app_record.application_status = "BOOKED"
        db.session.commit()
        audit_log(
            entity_type="Loan",
            operation="BOOK_FROM_APPLICATION",
            status="SUCCESS",
            details={"application_external_id": external_id, "loan_external_id": loan.external_id},
        )
        return app_record, loan
    except Exception:
        db.session.rollback()
        retry_queue.enqueue(
            entity="Loan",
            operation="BOOK_FROM_APPLICATION",
            payload={"application_external_id": external_id},
        )
        audit_log(
            entity_type="Loan",
            operation="BOOK_FROM_APPLICATION",
            status="RETRY_QUEUED",
            details={"application_external_id": external_id, "queue_size": retry_queue.size()},
        )
        raise


def get_application_by_external_id(external_id: str) -> dict | None:
    app_record = Application.query.filter_by(external_id=external_id).first()
    if not app_record:
        return None
    result = model_to_dict(app_record)
    result["ssn"] = mask_ssn(app_record.ssn)
    return result


def _assert_transition(current: str, target: str):
    if target not in TRANSITIONS.get(current, set()):
        raise ValidationError(f"Invalid status transition: {current} -> {target}")


def _derive_risk_score(credit_score: int) -> Decimal:
    # Lower risk score is better in this simplified model.
    return Decimal(max(0, 850 - credit_score)) / Decimal("10")


def _upsert_contact_for_application(app_record: Application) -> Contact:
    external_contact_id = f"C-{app_record.external_id}"
    contact = Contact.query.filter_by(external_id=external_contact_id).first()
    ssn_digits = "".join(ch for ch in app_record.ssn if ch.isdigit())
    if not contact:
        contact = Contact(external_id=external_contact_id)
        db.session.add(contact)

    contact.first_name = app_record.first_name
    contact.last_name = app_record.last_name
    contact.email = app_record.email
    contact.ssn_last4 = ssn_digits[-4:] if ssn_digits else None
    db.session.flush()
    return contact
