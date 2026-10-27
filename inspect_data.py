
from pathlib import Path

from src.ingestion import (
    load_adjustments,
    load_chart_of_accounts,
    load_fx_rates,
    load_prior_period,
    load_trial_balance,
    get_posting_accounts,
)

DATA = Path("data")

tb = load_trial_balance(DATA / "trial_balance.csv")
coa = load_chart_of_accounts(DATA / "chart_of_accounts.csv")
adjustments = load_adjustments(DATA / "manual_adjustments.json")
prior_tb = load_prior_period(DATA / "prior_period_tb.csv")
fx = load_fx_rates(DATA / "fx_rates.csv")

posting_accounts = get_posting_accounts(coa)

print("Trial Balance rows:", len(tb))
print("COA rows:", len(coa))
print("Posting accounts:", len(posting_accounts))
print("Prior-period rows:", len(prior_tb))
print("FX rate rows:", len(fx))
print("Journal entries:", len(adjustments["entries"]))

print("\nTrial Balance columns:", tb.columns.tolist())
print("COA columns:", coa.columns.tolist())

tb_accounts = set(tb["account_code"].dropna())
unknown_accounts = sorted(tb_accounts - set(coa["account_code"].dropna()))

print("\nAccounts absent from COA:", unknown_accounts)

print("\nFX rates missing for period-end:")
currencies = set(tb["currency"].dropna())
end_currencies = set(
    fx.loc[fx["rate_type"] == "period_end", "currency"].dropna()
)
print(sorted(currencies - end_currencies))
