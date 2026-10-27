
import json
from pathlib import Path

import pandas as pd


def load_trial_balance(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(
        path,
        dtype={
            "account_code": str,
            "account_name": str,
            "currency": str,
        },
    )


def load_chart_of_accounts(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(
        path,
        dtype={
            "account_code": str,
            "account_name": str,
            "parent_code": str,
        },
    )


def load_prior_period(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(
        path,
        dtype={
            "account_code": str,
            "account_name": str,
            "currency": str,
        },
    )


def load_fx_rates(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(
        path,
        dtype={"currency": str, "rate_type": str, "period": str},
    )


def load_adjustments(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_posting_accounts(coa: pd.DataFrame) -> set[str]:
    """Return non-header accounts that can potentially receive postings."""
    posting_rows = coa[
        coa["account_type"].str.strip().str.lower() != "header"
    ]
    return set(posting_rows["account_code"].dropna().astype(str))
