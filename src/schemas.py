
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class JournalLine(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account: str
    debit: Decimal = Field(ge=0)
    credit: Decimal = Field(ge=0)
    memo: str = ""


class JournalEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    description: str
    date: date
    source: str
    lines: list[JournalLine] = Field(min_length=2)

    @model_validator(mode="after")
    def validate_lines(self):
        for line in self.lines:
            if line.debit > 0 and line.credit > 0:
                raise ValueError(
                    f"Account {line.account}: debit and credit "
                    "cannot both be positive on one line"
                )
        return self


class ValidationIssue(BaseModel):
    code: str
    severity: Literal["error", "warning", "info"]
    message: str
    source_id: str


class AdjustmentResult(BaseModel):
    journal_id: str
    status: Literal["eligible", "rejected", "needs_review"]
    debit_total: Decimal
    credit_total: Decimal
    issues: list[ValidationIssue] = Field(default_factory=list)
