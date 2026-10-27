import os
from dotenv import load_dotenv

from src.ai_investigation import generate_investigation
import json
from pathlib import Path

import pandas as pd
from pydantic import ValidationError
from src.rejection_explanations import explain_rejections
from src.schemas import JournalEntry
from src.validators import validate_adjustment
from src.audit import build_audit_metadata
from src.data_quality import check_trial_balance
from src.ingestion import (
    load_trial_balance,
    load_chart_of_accounts,
)

from src.reconciliation import (
    check_fx_rates,
    check_prior_period_accounts,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUT = ROOT / "output"
load_dotenv(ROOT / ".env")

def main():
    OUTPUT.mkdir(exist_ok=True)

    # 1. Load manual adjustments first to get reporting period
    with open(
        DATA / "manual_adjustments.json",
        encoding="utf-8",
    ) as file:
        raw = json.load(file)

    # 2. Load current Trial Balance and Chart of Accounts
    trial_balance = load_trial_balance(
        DATA / "trial_balance.csv"
    )
    chart_of_accounts = load_chart_of_accounts(
        DATA / "chart_of_accounts.csv"
    )

    # 3. Load prior-period Trial Balance and FX rates
    prior_tb = pd.read_csv(
        DATA / "prior_period_tb.csv",
        dtype={"account_code": str},
    )

    fx_rates = pd.read_csv(
        DATA / "fx_rates.csv",
        dtype={
            "currency": str,
            "period": str,
            "rate_type": str,
        },
    )

    # 4. Run Trial Balance data-quality checks
    data_quality_issues = check_trial_balance(
        trial_balance,
        chart_of_accounts,
    )

    # 5. Determine currencies requiring FX rates
    required_currencies = set(
        trial_balance["currency"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.upper()
    )
   
    fx_issues = check_fx_rates(
        fx_rates=fx_rates,
        required_currencies=required_currencies,
        period=raw["period"],
    )

    reconciliation_issues = check_prior_period_accounts(
        current_tb=trial_balance,
        prior_tb=prior_tb,
    )

    # Load source data inside main()
    trial_balance = load_trial_balance(
        DATA / "trial_balance.csv"
    )
    chart_of_accounts = load_chart_of_accounts(
        DATA / "chart_of_accounts.csv"
    )

    data_quality_issues = check_trial_balance(
        trial_balance,
        chart_of_accounts,
    )

    with open(
        DATA / "manual_adjustments.json",
        encoding="utf-8",
    ) as file:
        raw = json.load(file)

    # Normalize account identifiers
    coa = chart_of_accounts.copy()
    coa["account_code"] = coa["account_code"].str.strip()

    valid_accounts = set(coa["account_code"].dropna())

    header_accounts = set(
        coa.loc[
            coa["account_type"].str.strip().str.lower() == "header",
            "account_code",
        ].dropna()
    )

    # Audit fingerprints for all source files
    input_paths = [
        DATA / "trial_balance.csv",
        DATA / "chart_of_accounts.csv",
        DATA / "manual_adjustments.json",
        DATA / "prior_period_tb.csv",
        DATA / "fx_rates.csv",
    ]

    audit_metadata = build_audit_metadata(
        input_paths=input_paths,
        period=raw["period"],
    )

    report = {
        "period": raw.get("period"),
        "functional_currency": raw.get("functional_currency"),
        "audit": audit_metadata,
        "data_quality_issues": data_quality_issues,
        "fx_issues": fx_issues,
        "reconciliation_issues": reconciliation_issues,
        "summary": {},
        "results": [],
    }

    seen_ids = set()

    for item in raw["entries"]:
        entry_id = str(item.get("id", "MISSING_ID"))

        if entry_id in seen_ids:
            report["results"].append({
                "journal_id": entry_id,
                "status": "needs_review",
                "issues": [{
                    "code": "DUPLICATE_JOURNAL_ID",
                    "severity": "error",
                    "message": "Journal ID has appeared more than once.",
                    "source_id": entry_id,
                }],
            })
            continue

        seen_ids.add(entry_id)

        try:
            entry = JournalEntry.model_validate(item)

            result = validate_adjustment(
                entry,
                valid_accounts,
                header_accounts,
            )

            report["results"].append(
                result.model_dump(mode="json")
            )

        except ValidationError as exc:
            report["results"].append({
                "journal_id": entry_id,
                "status": "rejected",
                "issues": [{
                    "code": "SCHEMA_VALIDATION_ERROR",
                    "severity": "error",
                    "message": error["msg"],
                    "source_id": entry_id,
                } for error in exc.errors()],
            })

    statuses = [
        item["status"] for item in report["results"]
    ]

    report["summary"] = {
        "total_entries": len(report["results"]),
        "eligible": statuses.count("eligible"),
        "rejected": statuses.count("rejected"),
        "needs_review": statuses.count("needs_review"),
    }

    output_path = OUTPUT / "validation_report.json"

    # Combine findings from the deterministic validation engine.
    all_findings = []

    all_findings.extend(report["data_quality_issues"])
    all_findings.extend(report["fx_issues"])
    all_findings.extend(report["reconciliation_issues"])    

    for result in report["results"]:
        for issue in result.get("issues", []):
            all_findings.append({
                **issue,
                "journal_id": result.get("journal_id"),
            })

    # LLM explains findings; it does not modify their status.
    report["ai_investigation"] = generate_investigation(
        summary=report["summary"],
        findings=all_findings,
    )


    report["rejection_explanations"] = explain_rejections(
        results=report["results"],
        raw_entries=raw["entries"],
    )

    output_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(report["summary"], indent=2))
    print(f"Data-quality issues: {len(data_quality_issues)}")
    print(f"Report saved to: {output_path}")


if __name__ == "__main__":
    main()
