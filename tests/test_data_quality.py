
import pandas as pd

from src.data_quality import check_trial_balance


def test_detects_unknown_account_and_imbalance():
    trial_balance = pd.DataFrame({
        "account_code": ["1000", "9999"],
        "debit": [1000, 0],
        "credit": [0, 200],
    })

    chart_of_accounts = pd.DataFrame({
        "account_code": ["1000"],
        "account_type": ["posting"],
        "cf_category": ["Operating"],
    })

    issues = check_trial_balance(
        trial_balance,
        chart_of_accounts,
    )

    issue_codes = {issue["code"] for issue in issues}

    assert "TB_ACCOUNT_MISSING_FROM_COA" in issue_codes
    assert "TB_OUT_OF_BALANCE" in issue_codes


def test_detects_missing_cash_flow_category():
    trial_balance = pd.DataFrame({
        "account_code": ["1000"],
        "debit": [100],
        "credit": [100],
    })

    chart_of_accounts = pd.DataFrame({
        "account_code": ["1000"],
        "account_type": ["posting"],
        "cf_category": [""],
    })

    issues = check_trial_balance(
        trial_balance,
        chart_of_accounts,
    )

    assert any(
        issue["code"] == "MISSING_CF_CATEGORY"
        and issue["source_id"] == "1000"
        for issue in issues
    )


def test_clean_trial_balance_has_no_issues():
    trial_balance = pd.DataFrame({
        "account_code": ["1000", "2000"],
        "debit": [100, 0],
        "credit": [0, 100],
    })

    chart_of_accounts = pd.DataFrame({
        "account_code": ["1000", "2000"],
        "account_type": ["posting", "posting"],
        "cf_category": ["Operating", "Financing"],
    })

    issues = check_trial_balance(
        trial_balance,
        chart_of_accounts,
    )

    assert issues == []
