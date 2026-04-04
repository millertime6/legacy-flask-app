import argparse
import random
from datetime import date, timedelta
from decimal import Decimal
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.db.database import db
from app.models.activity import Activity
from app.models.application import Application
from app.models.branch import Branch
from app.models.contact import Contact
from app.models.loan import Loan


FIRST_NAMES = [
    "Alicia",
    "Marcus",
    "Jordan",
    "Taylor",
    "Nina",
    "Rae",
    "Devon",
    "Parker",
    "Morgan",
    "Casey",
    "Skyler",
    "Avery",
]

LAST_NAMES = [
    "Bennet",
    "Diaz",
    "Hayes",
    "Cole",
    "Nguyen",
    "Patel",
    "Brown",
    "Kim",
    "Carter",
    "Lopez",
    "Price",
    "Miller",
]

APPLICATION_STATUSES = ["SUBMITTED", "IN_REVIEW", "APPROVED", "DENIED", "BOOKED"]
ACTIVITY_STATUSES = ["OPEN", "IN_PROGRESS", "COMPLETE", "CANCELLED"]
ACTIVITY_SUBJECTS = [
    "Customer Call",
    "Document Follow-up",
    "Payment Arrangement",
    "Account Review",
    "Compliance Check",
]
PAYMENT_METHODS = ["ACH", "WIRE", "CHECK"]


def _build_contacts(count: int) -> list[Contact]:
    contacts = []
    for idx in range(1, count + 1):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        ssn_last4 = f"{random.randint(0, 9999):04d}"
        birth_year = random.randint(1965, 2003)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)

        contacts.append(
            Contact(
                external_id=f"C-{1000 + idx}",
                first_name=first_name,
                last_name=last_name,
                email=f"{first_name.lower()}.{last_name.lower()}.{idx}@example.com",
                birthdate=date(birth_year, birth_month, birth_day),
                ssn_last4=ssn_last4,
            )
        )
    return contacts


def _risk_score_for_credit(credit_score: int) -> Decimal:
    return (Decimal(850 - credit_score) / Decimal("10")).quantize(Decimal("0.1"))


def _build_applications(contacts: list[Contact], count: int) -> list[Application]:
    applications = []
    for idx in range(1, count + 1):
        contact = random.choice(contacts)
        status = random.choices(
            APPLICATION_STATUSES,
            weights=[30, 20, 20, 15, 15],
            k=1,
        )[0]
        credit_score = random.randint(580, 790)
        loan_amount = Decimal(str(random.randint(5000, 75000)))
        ssn_full = f"111-22-{contact.ssn_last4}"
        approval_date = date.today() - timedelta(days=random.randint(1, 90))
        if status not in {"APPROVED", "BOOKED"}:
            approval_date = None

        applications.append(
            Application(
                external_id=f"A-{2000 + idx}",
                application_number=f"APP-{2000 + idx}",
                application_status=status,
                approval_date=approval_date,
                loan_amount=loan_amount,
                credit_score=credit_score,
                risk_score=_risk_score_for_credit(credit_score),
                first_name=contact.first_name,
                last_name=contact.last_name,
                ssn=ssn_full,
                email=contact.email,
            )
        )
    return applications


def _build_loans(applications: list[Application], contacts: list[Contact], max_count: int) -> list[Loan]:
    loan_candidates = [app for app in applications if app.application_status in {"APPROVED", "BOOKED"}]
    random.shuffle(loan_candidates)
    selected = loan_candidates[:max_count]
    loans = []
    for idx, app_record in enumerate(selected, start=1):
        # Match on applicant identity to simulate account mapping.
        matching_contact = next(
            (
                contact
                for contact in contacts
                if contact.first_name == app_record.first_name
                and contact.last_name == app_record.last_name
                and contact.email == app_record.email
            ),
            random.choice(contacts),
        )
        interest_rate = Decimal(str(random.choice([5.5, 6.0, 6.5, 7.25, 8.0])))
        term_months = random.choice([36, 48, 60, 72])
        monthly_payment = (
            (Decimal(app_record.loan_amount) / Decimal(term_months))
            + (Decimal(app_record.loan_amount) * (interest_rate / Decimal("100")) / Decimal("12"))
        ).quantize(Decimal("0.01"))

        loans.append(
            Loan(
                external_id=f"L-{3000 + idx}",
                account_id=matching_contact.id,
                loan_account_number=f"ACCT-{random.randint(1000000, 9999999)}",
                loan_name=f"{app_record.last_name} Servicing Loan",
                loan_amount=Decimal(app_record.loan_amount),
                interest_rate=interest_rate,
                monthly_payment=monthly_payment,
                status="ACTIVE",
                term_months=term_months,
                payment_method=random.choice(PAYMENT_METHODS),
                application_external_id=app_record.external_id,
            )
        )
    return loans


def _build_activities(contacts: list[Contact], count: int) -> list[Activity]:
    activities = []
    for idx in range(1, count + 1):
        contact = random.choice(contacts)
        due_date = date.today() + timedelta(days=random.randint(1, 45))
        activities.append(
            Activity(
                external_id=f"T-{4000 + idx}",
                account_id=contact.id,
                description=(
                    f"{random.choice(['Inbound', 'Outbound'])} servicing interaction for "
                    f"{contact.first_name} {contact.last_name} regarding account review."
                ),
                due_date=due_date,
                status=random.choice(ACTIVITY_STATUSES),
                subject=random.choice(ACTIVITY_SUBJECTS),
            )
        )
    return activities


def _build_branches(count: int) -> list[Branch]:
    city_names = ["San Francisco", "Austin", "Denver", "Miami", "Seattle", "Chicago", "Boston", "Phoenix"]
    branches = []
    for idx in range(1, count + 1):
        city = city_names[(idx - 1) % len(city_names)]
        branches.append(
            Branch(
                external_id=f"B-{5000 + idx}",
                branch_name=f"{city} Branch {idx}",
                is_active=(idx % 6 != 0),
            )
        )
    return branches


def seed(contact_count: int, application_count: int, loan_count: int, activity_count: int, branch_count: int):
    random.seed(2026)
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        contacts = _build_contacts(contact_count)
        db.session.add_all(contacts)
        db.session.flush()

        applications = _build_applications(contacts, application_count)
        db.session.add_all(applications)
        db.session.flush()

        loans = _build_loans(applications, contacts, min(loan_count, application_count))
        db.session.add_all(loans)

        activities = _build_activities(contacts, activity_count)
        db.session.add_all(activities)

        branches = _build_branches(branch_count)
        db.session.add_all(branches)

        db.session.commit()
        print("Seed data loaded successfully.")
        print(
            "Created: "
            f"{len(contacts)} contacts, "
            f"{len(applications)} applications, "
            f"{len(loans)} loans, "
            f"{len(activities)} activities, "
            f"{len(branches)} branches."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed a realistic dataset for local or deployment testing.")
    parser.add_argument("--contacts", type=int, default=50)
    parser.add_argument("--applications", type=int, default=120)
    parser.add_argument("--loans", type=int, default=70)
    parser.add_argument("--activities", type=int, default=240)
    parser.add_argument("--branches", type=int, default=10)
    args = parser.parse_args()
    seed(args.contacts, args.applications, args.loans, args.activities, args.branches)
