
import pandas as pd

from src.reconciliation import (
    check_fx_rates,
    check_prior_period_accounts,
)


def test_missing_period_end_fx_rate_is_flagged():
    fx_rates = pd.DataFrame({
        "currency": ["USD", "EUR"],
        "period": ["2024-Q4", "2024-Q4"],
        "rate_type": ["closing", "closing"],
    })

    issues = check_fx_rates(
        fx_rates=fx_rates,
        required_currencies={"USD", "GBP"},
        period="2024-Q4",
    )

    assert any(
        issue["code"] == "MISSING_PERIOD_END_FX_RATE"
        and issue["source_id"] == "GBP"
        for issue in issues
    )


def test_existing_period_end_rates_pass():
    fx_rates = pd.DataFrame({
        "currency": ["USD", "GBP"],
        "period": ["2024-Q4", "2024-Q4"],
        "rate_type": ["closing", "closing"],
    })

    issues = check_fx_rates(
        fx_rates=fx_rates,
        required_currencies={"USD", "GBP"},
        period="2024-Q4",
    )

    assert issues == []


def test_prior_period_only_account_is_flagged():
    current_tb = pd.DataFrame({
        "account_code": ["1000", "2000"],
    })

    prior_tb = pd.DataFrame({
        "account_code": ["1000", "2000", "6905"],
    })

    issues = check_prior_period_accounts(
        current_tb=current_tb,
        prior_tb=prior_tb,
    )

    assert any(
        issue["code"] == "PRIOR_PERIOD_ACCOUNT_MISSING"
        and issue["source_id"] == "6905"
        for issue in issues
    )
