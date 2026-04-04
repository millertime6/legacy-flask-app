import hmac
from functools import wraps
from urllib.parse import urlparse

from flask import current_app, redirect, request, session, url_for


def is_authenticated() -> bool:
    return bool(session.get("ui_authenticated"))


def validate_credentials(username: str, password: str) -> bool:
    expected_user = current_app.config["UI_USERNAME"]
    expected_password = current_app.config["UI_PASSWORD"]
    return hmac.compare_digest(username, expected_user) and hmac.compare_digest(
        password, expected_password
    )


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for("ui.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def safe_next_path(next_path: str | None) -> str:
    if not next_path:
        return url_for("ui.servicing_dashboard")

    parsed = urlparse(next_path)
    if parsed.netloc:
        return url_for("ui.servicing_dashboard")
    if not next_path.startswith("/"):
        return url_for("ui.servicing_dashboard")
    return next_path
