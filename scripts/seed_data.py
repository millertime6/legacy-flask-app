from datetime import date
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


def seed():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        contacts = [
            Contact(
                external_id="C-1001",
                first_name="Alicia",
                last_name="Bennet",
                email="alicia.bennet@example.com",
                birthdate=date(1986, 2, 15),
                ssn_last4="4432",
            ),
            Contact(
                external_id="C-1002",
                first_name="Marcus",
                last_name="Diaz",
                email="marcus.diaz@example.com",
                birthdate=date(1990, 11, 3),
                ssn_last4="9921",
            ),
        ]
        db.session.add_all(contacts)
        db.session.flush()

        applications = [
            Application(
                external_id="A-2001",
                application_number="APP-2001",
                application_status="APPROVED",
                loan_amount=Decimal("15000"),
                credit_score=710,
                risk_score=Decimal("14.0"),
                first_name="Alicia",
                last_name="Bennet",
                ssn="123-45-4432",
                email="alicia.bennet@example.com",
            ),
            Application(
                external_id="A-2002",
                application_number="APP-2002",
                application_status="SUBMITTED",
                loan_amount=Decimal("23000"),
                credit_score=665,
                risk_score=Decimal("18.5"),
                first_name="Marcus",
                last_name="Diaz",
                ssn="111-22-9921",
                email="marcus.diaz@example.com",
            ),
        ]
        db.session.add_all(applications)

        loans = [
            Loan(
                external_id="L-3001",
                account_id=contacts[0].id,
                loan_account_number="ACCT-5531981",
                loan_name="Alicia Bennet Personal Loan",
                loan_amount=Decimal("15000"),
                interest_rate=Decimal("6.5"),
                monthly_payment=Decimal("293.48"),
                status="ACTIVE",
                term_months=60,
                payment_method="ACH",
                application_external_id="A-2001",
            )
        ]
        db.session.add_all(loans)

        activities = [
            Activity(
                external_id="T-4001",
                account_id=contacts[0].id,
                description="Inbound call: customer asked for due date confirmation.",
                due_date=date(2026, 4, 1),
                status="OPEN",
                subject="Customer Call",
            ),
            Activity(
                external_id="T-4002",
                account_id=contacts[1].id,
                description="Outbound comment request for additional proof of income.",
                due_date=date(2026, 4, 3),
                status="IN_PROGRESS",
                subject="Document Follow-up",
            ),
        ]
        db.session.add_all(activities)

        branches = [
            Branch(external_id="B-5001", branch_name="San Francisco Downtown", is_active=True),
            Branch(external_id="B-5002", branch_name="Austin Central", is_active=True),
            Branch(external_id="B-5003", branch_name="Legacy Branch - Archive", is_active=False),
        ]
        db.session.add_all(branches)

        db.session.commit()
        print("Seed data loaded successfully.")


if __name__ == "__main__":
    seed()
