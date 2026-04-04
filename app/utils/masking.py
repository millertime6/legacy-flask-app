def mask_ssn(value: str | None) -> str | None:
    if not value:
        return value
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) < 4:
        return "***-**-****"
    return f"***-**-{digits[-4:]}"
