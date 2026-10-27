# Reflection: ERP Financial Statement Agent

## Why I Chose This Prototype

I chose the Manual Adjustments Agent because invalid journal entries and unreliable source data can compromise downstream financial reporting. Rather than attempting all four statements superficially, I focused on deterministic journal validation, data-quality checks, reconciliation findings, and human-review flags.

## Deterministic Logic vs. LLM Reasoning

Accounting invariants, including debit-credit equality and account existence, belong in deterministic Python code. An LLM is more useful for explaining validation failures and suggesting investigation steps than for calculating financial values or approving entries. The current prototype is primarily a deterministic validation pipeline with LLM-assisted explanations, not a fully autonomous multi-agent system. Uncertain cases should be escalated rather than silently corrected.

## Auditability and Handling Ambiguity

The prototype fingerprints its input files using SHA-256 and records validation findings with issue codes, severity levels, and source identifiers where available. However, file fingerprints alone do not provide complete source-row-to-statement-cell lineage. A production implementation would require immutable audit events, versioned mappings and policies, approval records, and traceable links from reported values to their originating transactions.

The system flags suspicious intercompany entries heuristically; it does not perform comprehensive circularity detection. Similarly, missing FX rates require an authoritative rate source rather than an invented value. These limitations reinforce the importance of explicit validation and human oversight.

## What I Would Build Differently With Three Months

With three months, I would strengthen ingestion and accounting validation first, then build controlled financial statement generation using approved, versioned COA mappings. I would implement source-level lineage, statement reconciliation, role-based approvals, and broader edge-case testing. I would also evaluate LLM explanations against a fixed set of finance scenarios before expanding their responsibilities.

## Where the Prototype Would Break at Scale

Across thousands of accounts and multiple legal entities, simple account-code comparisons and file-level processing would be insufficient. The system would need stable identifiers, entity-aware mappings, explicit consolidation and currency rules, idempotent processing, incremental validation, and scalable reconciliation. Duplicate adjustments and inconsistent source schemas would also require stronger controls.

## How AI Tools Helped—and Where They Can Mislead

Groq and LangChain helped generate readable explanations of validation findings. However, an LLM could plausibly suggest adding an unknown account to the chart of accounts without sufficient evidence. Such a recommendation must not become an accounting decision automatically. I therefore kept core validation in deterministic code and treated generated explanations as assistance for human review.

## What I Think Is Underestimated

The hardest problem is proving where every reported number came from. A correct-looking financial statement is not sufficient if an auditor cannot trace its values to source transactions, approved mappings, adjustments, and FX rates. Traceability must be designed into the data flow from the beginning. In financial systems, controlled autonomy, reproducibility, and auditability matter more than unrestricted automation.
