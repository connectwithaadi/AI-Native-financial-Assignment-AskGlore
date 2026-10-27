import pandas as pd


def check_trial_balance(
    trial_balance: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
) -> list[dict]:
    issues = []

    tb = trial_balance.copy()
    coa = chart_of_accounts.copy()

    # Normalize account codes without changing the source files.
    tb["account_code"] = tb["account_code"].astype(str).str.strip()
    coa["account_code"] = coa["account_code"].astype(str).str.strip()

    valid_accounts = set(coa["account_code"].dropna())

    # Detect Trial Balance accounts missing from the COA.
    for account in sorted(
        set(tb["account_code"].dropna()) - valid_accounts
    ):
        issues.append({
            "code": "TB_ACCOUNT_MISSING_FROM_COA",
            "severity": "error",
            "message": (
                f"Trial Balance account {account} "
                "does not exist in the Chart of Accounts."
            ),
            "source_id": account,
        })

    # Calculate debit-credit difference.
    debit_total = pd.to_numeric(
        tb["debit"], errors="coerce"
    ).sum()

    credit_total = pd.to_numeric(
        tb["credit"], errors="coerce"
    ).sum()

    difference = round(float(debit_total - credit_total), 2)

    if difference != 0:
        issues.append({
            "code": "TB_OUT_OF_BALANCE",
            "severity": "error",
            "message": (
                f"Trial Balance debits exceed credits by "
                f"{difference:.2f}."
                if difference > 0
                else
                f"Trial Balance credits exceed debits by "
                f"{abs(difference):.2f}."
            ),
            "source_id": "trial_balance.csv",
        })

    # Detect blank cash-flow classifications in the COA.
    if "cf_category" in coa.columns:
        missing_cf = coa[
            coa["cf_category"].isna()
            | coa["cf_category"].astype(str).str.strip().eq("")
        ]

        for account in missing_cf["account_code"].dropna().unique():
            issues.append({
                "code": "MISSING_CF_CATEGORY",
                "severity": "warning",
                "message": (
                    f"Account {account} has no cash-flow "
                    "classification in the Chart of Accounts."
                ),
                "source_id": account,
            })

    return issues
