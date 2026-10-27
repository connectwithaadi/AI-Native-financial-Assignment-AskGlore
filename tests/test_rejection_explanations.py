
from src.rejection_explanations import (
    deterministic_explanation,
    explain_rejections,
)


def test_deterministic_explanation_includes_validation_issue():
    result = {
        "journal_id": "JE-002",
        "status": "rejected",
        "issues": [{
            "code": "UNBALANCED_ENTRY",
            "severity": "error",
            "message": "Debits and credits differ by 3500.",
            "source_id": "JE-002",
        }],
    }

    explanation = deterministic_explanation(result)

    assert "JE-002" not in explanation or "rejected" in explanation
    assert "3500" in explanation
    assert "supporting documentation" in explanation


def test_rejection_explanation_works_without_api_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    results = [{
        "journal_id": "JE-002",
        "status": "rejected",
        "issues": [{
            "code": "UNBALANCED_ENTRY",
            "severity": "error",
            "message": "Debits and credits differ by 3500.",
            "source_id": "JE-002",
        }],
    }]

    raw_entries = [{
        "id": "JE-002",
        "description": "Test journal",
        "lines": [],
    }]

    explanations = explain_rejections(results, raw_entries)

    assert len(explanations) == 1
    assert explanations[0]["journal_id"] == "JE-002"
    assert explanations[0]["status"] == "fallback"
    assert "3500" in explanations[0]["explanation"]


def test_eligible_journals_are_not_explained():
    explanations = explain_rejections(
        results=[{
            "journal_id": "JE-001",
            "status": "eligible",
            "issues": [],
        }],
        raw_entries=[],
    )

    assert explanations == []
