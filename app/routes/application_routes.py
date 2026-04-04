from flask import Blueprint, g, jsonify, request

from app.services.application_service import (
    book_loan_from_application,
    decide_application,
    get_application_by_external_id,
    upsert_application,
)
from app.utils.auth import require_token_auth
from app.utils.serialization import model_to_dict
from app.utils.validation import ValidationError

application_bp = Blueprint("applications", __name__)


def _response(payload: dict, code: int):
    response = jsonify(payload)
    response.headers["X-Correlation-ID"] = g.correlation_id
    return response, code


@application_bp.post("")
@require_token_auth
def create_or_update_application():
    payload = request.get_json(silent=True) or {}
    try:
        record = upsert_application(payload)
        return _response({"application": model_to_dict(record)}, 200)
    except ValidationError as exc:
        return _response({"error": str(exc)}, 400)


@application_bp.post("/<string:external_id>/decision")
@require_token_auth
def decision_application(external_id: str):
    payload = request.get_json(silent=True) or {}
    decision = payload.get("decision", "")
    try:
        record = decide_application(external_id, decision)
        return _response({"application": model_to_dict(record)}, 200)
    except ValidationError as exc:
        return _response({"error": str(exc)}, 400)


@application_bp.post("/<string:external_id>/book-loan")
@require_token_auth
def book_loan(external_id: str):
    try:
        application, loan = book_loan_from_application(external_id)
        return _response(
            {"application": model_to_dict(application), "loan": model_to_dict(loan)},
            200,
        )
    except ValidationError as exc:
        return _response({"error": str(exc)}, 400)
    except Exception:
        return _response(
            {"error": "Loan booking failed and was queued for retry"},
            500,
        )


@application_bp.get("/<string:external_id>")
@require_token_auth
def get_application(external_id: str):
    result = get_application_by_external_id(external_id)
    if not result:
        return _response({"error": "Application not found"}, 404)
    return _response({"application": result}, 200)
