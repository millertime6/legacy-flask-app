from functools import wraps

from flask import current_app, jsonify, request


def require_token_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        expected = f"Bearer {current_app.config['API_TOKEN']}"
        if auth_header != expected:
            return jsonify({"error": "Unauthorized"}), 401
        return func(*args, **kwargs)

    return wrapper
