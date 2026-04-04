from uuid import uuid4

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy import or_

from app.models.application import Application
from app.models.loan import Loan
from app.services.application_service import (
    book_loan_from_application,
    decide_application,
    upsert_application,
)
from app.utils.masking import mask_ssn
from app.utils.ui_auth import login_required, safe_next_path, validate_credentials
from app.utils.validation import ValidationError

ui_bp = Blueprint("ui", __name__)


@ui_bp.route("/login", methods=["GET", "POST"])
def login():
    next_path = request.args.get("next", "")
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        next_path = request.form.get("next", "")
        if validate_credentials(username, password):
            session["ui_authenticated"] = True
            session["ui_username"] = username
            flash("Signed in successfully.", "success")
            return redirect(safe_next_path(next_path))
        flash("Invalid username or password.", "error")
        return render_template("servicing/login.html", next_path=next_path), 401

    return render_template("servicing/login.html", next_path=next_path)


@ui_bp.post("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("ui.login"))


@ui_bp.get("/servicing")
@login_required
def servicing_dashboard():
    recent_applications = Application.query.order_by(Application.updated_date.desc()).limit(8).all()
    recent_loans = Loan.query.order_by(Loan.updated_date.desc()).limit(8).all()
    metrics = {
        "application_count": Application.query.count(),
        "approved_count": Application.query.filter_by(application_status="APPROVED").count(),
        "booked_count": Application.query.filter_by(application_status="BOOKED").count(),
        "loan_count": Loan.query.count(),
    }
    return render_template(
        "servicing/dashboard.html",
        metrics=metrics,
        recent_applications=recent_applications,
        recent_loans=recent_loans,
    )


@ui_bp.get("/servicing/applications")
@login_required
def list_applications():
    query_text = request.args.get("q", "").strip()
    status = request.args.get("status", "ALL").strip().upper()

    query = Application.query
    if query_text:
        query = query.filter(
            or_(
                Application.external_id.ilike(f"%{query_text}%"),
                Application.application_number.ilike(f"%{query_text}%"),
                Application.first_name.ilike(f"%{query_text}%"),
                Application.last_name.ilike(f"%{query_text}%"),
                Application.email.ilike(f"%{query_text}%"),
            )
        )
    if status != "ALL":
        query = query.filter_by(application_status=status)

    applications = query.order_by(Application.updated_date.desc()).all()
    return render_template(
        "servicing/applications.html",
        applications=applications,
        query_text=query_text,
        status=status,
    )


@ui_bp.route("/servicing/applications/new", methods=["GET", "POST"])
@login_required
def create_application():
    if request.method == "POST":
        payload = {
            "external_id": request.form.get("external_id", "").strip()
            or f"A-WEB-{uuid4().hex[:8].upper()}",
            "application_number": request.form.get("application_number", "").strip() or None,
            "loan_amount": request.form.get("loan_amount", "").strip(),
            "credit_score": request.form.get("credit_score", "").strip(),
            "risk_score": request.form.get("risk_score", "").strip() or None,
            "first_name": request.form.get("first_name", "").strip(),
            "last_name": request.form.get("last_name", "").strip(),
            "ssn": request.form.get("ssn", "").strip(),
            "email": request.form.get("email", "").strip(),
        }
        try:
            record = upsert_application(payload)
            flash(f"Application {record.external_id} saved.", "success")
            return redirect(url_for("ui.application_detail", external_id=record.external_id))
        except ValidationError as exc:
            flash(str(exc), "error")
            return render_template("servicing/application_form.html", form_values=request.form), 400

    return render_template("servicing/application_form.html", form_values={})


@ui_bp.get("/servicing/applications/<string:external_id>")
@login_required
def application_detail(external_id: str):
    application = Application.query.filter_by(external_id=external_id).first_or_404()
    booked_loan = Loan.query.filter_by(application_external_id=external_id).first()
    return render_template(
        "servicing/application_detail.html",
        application=application,
        booked_loan=booked_loan,
        masked_ssn=mask_ssn(application.ssn),
    )


@ui_bp.post("/servicing/applications/<string:external_id>/decision")
@login_required
def decision_action(external_id: str):
    decision = request.form.get("decision", "").strip().upper()
    try:
        decide_application(external_id, decision)
        flash(f"Application {external_id} moved to {decision}.", "success")
    except ValidationError as exc:
        flash(str(exc), "error")
    return redirect(url_for("ui.application_detail", external_id=external_id))


@ui_bp.post("/servicing/applications/<string:external_id>/book")
@login_required
def book_action(external_id: str):
    try:
        _, loan = book_loan_from_application(external_id)
        flash(f"Loan {loan.external_id} booked successfully.", "success")
    except ValidationError as exc:
        flash(str(exc), "error")
    except Exception:
        flash("Booking failed and was queued for retry simulation.", "error")
    return redirect(url_for("ui.application_detail", external_id=external_id))


@ui_bp.get("/servicing/loans")
@login_required
def list_loans():
    query_text = request.args.get("q", "").strip()
    status = request.args.get("status", "ALL").strip().upper()

    query = Loan.query
    if query_text:
        query = query.filter(
            or_(
                Loan.external_id.ilike(f"%{query_text}%"),
                Loan.loan_account_number.ilike(f"%{query_text}%"),
                Loan.loan_name.ilike(f"%{query_text}%"),
                Loan.application_external_id.ilike(f"%{query_text}%"),
            )
        )
    if status != "ALL":
        query = query.filter_by(status=status)

    loans = query.order_by(Loan.updated_date.desc()).all()
    return render_template(
        "servicing/loans.html",
        loans=loans,
        query_text=query_text,
        status=status,
    )


@ui_bp.get("/servicing/loans/<string:external_id>")
@login_required
def loan_detail(external_id: str):
    loan = Loan.query.filter_by(external_id=external_id).first_or_404()
    return render_template("servicing/loan_detail.html", loan=loan)
