
import pandas as pd


def check_fx_rates(
    fx_rates: pd.DataFrame,
    required_currencies: set[str],
    period: str,
) -> list[dict]:
    issues = []

    fx = fx_rates.copy()
    fx["currency"] = (
        fx["currency"].astype(str).str.strip().str.upper()
    )
    fx["period"] = fx["period"].astype(str).str.strip()

    if "rate_type" in fx.columns:
        fx["rate_type"] = (
            fx["rate_type"].astype(str).str.strip().str.lower()
        )

    for currency in sorted(required_currencies):
        currency = currency.strip().upper()

        matches = fx[
            (fx["currency"] == currency)
            & (fx["period"] == period)
        ]

        if "rate_type" in fx.columns:
            matches = matches[
                matches["rate_type"].str.contains(
                    "closing|period.end|end",
                    regex=True,
                    na=False,
                )
            ]

        if matches.empty:
            issues.append({
                "code": "MISSING_PERIOD_END_FX_RATE",
                "severity": "error",
                "message": (
                    f"No period-end FX rate found for {currency} "
                    f"for period {period}."
                ),
                "source_id": currency,
            })

    return issues


def check_prior_period_accounts(
    current_tb: pd.DataFrame,
    prior_tb: pd.DataFrame,
) -> list[dict]:
    issues = []

    current = current_tb.copy()
    prior = prior_tb.copy()

    current["account_code"] = (
        current["account_code"].astype(str).str.strip()
    )
    prior["account_code"] = (
        prior["account_code"].astype(str).str.strip()
    )

    current_accounts = set(current["account_code"].dropna())
    prior_accounts = set(prior["account_code"].dropna())

    for account in sorted(prior_accounts - current_accounts):
        issues.append({
            "code": "PRIOR_PERIOD_ACCOUNT_MISSING",
            "severity": "warning",
            "message": (
                f"Account {account} appears in the prior period "
                "but not in the current Trial Balance. "
                "Check for closure, renumbering, or mapping changes."
            ),
            "source_id": account,
        })

    return issues
