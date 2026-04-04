from flask import Blueprint, g, jsonify, request

from app.services.activity_service import get_activity_dict, upsert_activity
from app.utils.auth import require_token_auth
from app.utils.validation import ValidationError

activity_bp = Blueprint("activities", __name__)


def _response(payload: dict, code: int):
    response = jsonify(payload)
    response.headers["X-Correlation-ID"] = g.correlation_id
    return response, code


@activity_bp.post("")
@require_token_auth
def create_activity():
    payload = request.get_json(silent=True) or {}
    try:
        record = upsert_activity(payload)
        return _response({"activity": get_activity_dict(record)}, 200)
    except ValidationError as exc:
        return _response({"error": str(exc)}, 400)
