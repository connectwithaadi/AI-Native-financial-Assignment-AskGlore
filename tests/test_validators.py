
from datetime import date
from decimal import Decimal

from src.schemas import JournalEntry
from src.validators import validate_adjustment


def make_entry(debit, credit, account="6100"):
    return JournalEntry(
        id="JE-TEST",
        description="Test journal",
        date=date(2024, 12, 31),
        source="Unit test",
        lines=[
            {
                "account": account,
                "debit": Decimal(str(debit)),
                "credit": Decimal("0"),
            },
            {
                "account": "2120",
                "debit": Decimal("0"),
                "credit": Decimal(str(credit)),
            },
        ],
    )


def test_balanced_entry_is_eligible():
    entry = make_entry(1000, 1000)

    result = validate_adjustment(
        entry,
        {"6100", "2120"},
    )

    assert result.status == "eligible"
    assert result.debit_total == result.credit_total


def test_unbalanced_entry_is_rejected():
    entry = make_entry(1000, 900)

    result = validate_adjustment(
        entry,
        {"6100", "2120"},
    )

    assert result.status == "rejected"
    assert any(
        issue.code == "UNBALANCED_ENTRY"
        for issue in result.issues
    )


def test_unknown_account_is_rejected():
    entry = make_entry(1000, 1000, account="9999")

    result = validate_adjustment(
        entry,
        {"6100", "2120"},
    )

    assert result.status == "rejected"
    assert any(
        issue.code == "UNKNOWN_ACCOUNT"
        for issue in result.issues
    )



def test_intercompany_entry_requires_review():
    entry = JournalEntry(
        id="JE-008",
        description="Intercompany settlement — UK sub",
        date=date(2024, 12, 30),
        source="IC reconciliation",
        lines=[
            {
                "account": "2170",
                "debit": Decimal("320000"),
                "credit": Decimal("0"),
            },
            {
                "account": "2170",
                "debit": Decimal("0"),
                "credit": Decimal("320000"),
            },
        ],
    )

    result = validate_adjustment(entry, {"2170"})

    assert result.status == "needs_review"
    assert any(
        issue.code == "INTERCOMPANY_REVIEW_REQUIRED"
        for issue in result.issues
    )
