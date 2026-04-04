from decimal import Decimal

from app.models.loan import Loan
from app.utils.serialization import model_to_dict


def get_loan_by_external_id(external_id: str):
    loan = Loan.query.filter_by(external_id=external_id).first()
    if not loan:
        return None
    return model_to_dict(loan)


def calculate_monthly_payment(principal: Decimal, annual_rate: Decimal, term_months: int) -> Decimal:
    monthly_rate = annual_rate / Decimal("100") / Decimal("12")
    if monthly_rate == 0:
        return principal / Decimal(term_months)

    numerator = principal * monthly_rate
    denominator = Decimal("1") - (Decimal("1") + monthly_rate) ** Decimal(-term_months)
    return numerator / denominator
