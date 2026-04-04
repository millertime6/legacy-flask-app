from decimal import Decimal


def to_number(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


def model_to_dict(model):
    data = {}
    for column in model.__table__.columns:
        value = getattr(model, column.name)
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        data[column.name] = to_number(value)
    return data
