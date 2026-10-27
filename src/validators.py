
from decimal import Decimal
from collections.abc import Set

from src.schemas import (
    AdjustmentResult,
    JournalEntry,
    ValidationIssue,
)


def validate_adjustment(
    entry: JournalEntry,
    valid_accounts: Set[str],
    header_accounts: Set[str] | None = None,
) -> AdjustmentResult:
    debit_total = sum(
        (line.debit for line in entry.lines), Decimal("0")
    )
    credit_total = sum(
        (line.credit for line in entry.lines), Decimal("0")
    )

    issues: list[ValidationIssue] = []
    header_accounts = header_accounts or set()

    for line in entry.lines:
        if line.account not in valid_accounts:
            issues.append(
                ValidationIssue(
                    code="UNKNOWN_ACCOUNT",
                    severity="error",
                    message=f"Account {line.account} is missing from the COA.",
                    source_id=entry.id,
                )
            )
        elif line.account in header_accounts:
            issues.append(
                ValidationIssue(
                    code="NON_POSTING_ACCOUNT",
                    severity="error",
                    message=f"Account {line.account} is a header account.",
                    source_id=entry.id,
                )
            )

    if debit_total != credit_total:
        issues.append(
            ValidationIssue(
                code="UNBALANCED_ENTRY",
                severity="error",
                message=(
                    f"Debits and credits differ by "
                    f"{abs(debit_total - credit_total)}."
                ),
                source_id=entry.id,
            )
        )

    # Flag suspicious intercompany entries for human investigation.
    description = entry.description.casefold()
    is_intercompany = "intercompany" in description

    account_codes = [line.account for line in entry.lines]
    has_same_account_debit_credit = any(
        debit_line.account == credit_line.account
        and debit_line.debit > 0
        and credit_line.credit > 0
        for debit_line in entry.lines
        for credit_line in entry.lines
    )

    if is_intercompany and has_same_account_debit_credit:
        issues.append(
            ValidationIssue(
                code="INTERCOMPANY_REVIEW_REQUIRED",
                severity="warning",
                message=(
                    "Intercompany entry contains debit and credit "
                    "lines for the same account. Verify entity, "
                    "counterparty, and settlement references."
                ),
                source_id=entry.id,
            )
        )

    has_errors = any(
        issue.severity == "error"
        for issue in issues
    )
    has_warnings = any(
        issue.severity == "warning"
        for issue in issues
    )

    if has_errors:
        status = "rejected"
    elif has_warnings:
        status = "needs_review"
    else:
        status = "eligible"

    return AdjustmentResult(
        journal_id=entry.id,
        status=status,
        debit_total=debit_total,
        credit_total=credit_total,
        issues=issues,
    )
