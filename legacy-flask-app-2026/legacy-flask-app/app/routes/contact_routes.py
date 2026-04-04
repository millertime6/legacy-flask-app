from flask import Blueprint, g, jsonify

from app.services.contact_service import get_contact_by_external_id
from app.utils.auth import require_token_auth

contact_bp = Blueprint("contacts", __name__)


@contact_bp.get("/<string:external_id>")
@require_token_auth
def get_contact(external_id: str):
    contact = get_contact_by_external_id(external_id)
    if not contact:
        response = jsonify({"error": "Contact not found"})
        response.headers["X-Correlation-ID"] = g.correlation_id
        return response, 404

    response = jsonify({"contact": contact})
    response.headers["X-Correlation-ID"] = g.correlation_id
    return response, 200
