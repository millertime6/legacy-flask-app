from flask import Blueprint, g, jsonify

from app.services.loan_service import get_loan_by_external_id
from app.utils.auth import require_token_auth

loan_bp = Blueprint("loans", __name__)


@loan_bp.get("/<string:external_id>")
@require_token_auth
def get_loan(external_id: str):
    loan = get_loan_by_external_id(external_id)
    if not loan:
        response = jsonify({"error": "Loan not found"})
        response.headers["X-Correlation-ID"] = g.correlation_id
        return response, 404

    response = jsonify({"loan": loan})
    response.headers["X-Correlation-ID"] = g.correlation_id
    return response, 200
