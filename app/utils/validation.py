from datetime import datetime


class ValidationError(Exception):
    pass


def require_fields(payload: dict, fields: list[str]):
    missing = [field for field in fields if field not in payload or payload[field] in (None, "")]
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")


def validate_email(email: str):
    if "@" not in email or "." not in email.split("@")[-1]:
        raise ValidationError("Invalid email format")


def validate_status(value: str, allowed: set[str], field_name: str = "status"):
    if value not in allowed:
        raise ValidationError(
            f"Invalid {field_name}. Allowed: {', '.join(sorted(allowed))}"
        )


def parse_date(value: str):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValidationError("Date must be YYYY-MM-DD") from exc
