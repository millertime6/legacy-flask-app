from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.get("/")
def index():
    return (
        jsonify(
            {
                "service": "legacy-loan-servicing-api",
                "status": "ok",
                "health_endpoint": "/health",
                "api_base": "/api/v1",
            }
        ),
        200,
    )


@health_bp.get("/health")
def health():
    return jsonify({"status": "ok"}), 200
