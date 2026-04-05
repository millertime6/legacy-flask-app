from flask import abort, request


def _parse_allowlist(raw: str) -> frozenset[str]:
    if not raw or not raw.strip():
        return frozenset()
    return frozenset(part.strip() for part in raw.split(",") if part.strip())


def _effective_client_ip(trust_xff: bool) -> str:
    if trust_xff:
        xff = request.headers.get("X-Forwarded-For")
        if xff:
            parts = [p.strip() for p in xff.split(",") if p.strip()]
            if parts:
                # AWS ALB appends the connecting client as the last entry.
                return parts[-1]
    return request.remote_addr or ""


def _path_exempt(path: str) -> bool:
    p = path.rstrip("/") or "/"
    return p == "/health"


def register_ip_allowlist(app) -> None:
    @app.before_request
    def _enforce_ip_allowlist() -> None:
        allowed = _parse_allowlist(app.config.get("IP_ALLOWLIST", ""))
        if not allowed:
            return
        if _path_exempt(request.path):
            return
        ip = _effective_client_ip(app.config.get("TRUST_PROXY_HEADERS", False))
        if ip in allowed:
            return
        abort(403)
