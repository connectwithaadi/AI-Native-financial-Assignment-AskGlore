# Architecture: Agentic ERP Financial Statement System

## 1. Executive Summary

This document describes an architecture for an ERP-driven financial statement generation system that combines deterministic accounting controls with LLM-assisted investigation.

The system consumes a Trial Balance, Chart of Accounts (COA), manual adjustments, prior-period balances, and foreign-exchange (FX) rates. Its objective is to produce reliable financial reporting outputs with explicit validation, traceability, and human oversight.

The current implementation focuses on a working prototype slice: **manual adjustment validation and supporting financial data-quality checks**. It also integrates Groq through LangChain to generate plain-English explanations of rejected journal entries and broader investigation findings.

Complete financial statement generation, autonomous journal correction, ERP posting, and end-to-end statement-cell lineage are proposed capabilities, not completed features of the current prototype.

## 2. Inputs and Outputs

### 2.1 Source inputs

| Input | Purpose |
|---|---|
| `trial_balance.csv` | Current-period account balances and debit-credit totals |
| `chart_of_accounts.csv` | Account definitions, hierarchy, and reporting classifications |
| `manual_adjustments.json` | Proposed manual journal entries |
| `prior_period_tb.csv` | Previous-period account balances for reconciliation |
| `fx_rates.csv` | Exchange rates for currency translation |

### 2.2 Current prototype outputs

The application generates `output/validation_report.json`, containing:

- Journal validation results and statuses.
- Trial Balance data-quality findings.
- Missing FX-rate findings.
- Prior-period account reconciliation findings.
- Audit metadata and SHA-256 input fingerprints.
- LLM investigation output.
- Journal-specific rejection explanations.

The current output is a validation and investigation report, not a completed set of financial statements.

## 3. Agent Topology

### 3.1 Recommended production topology

I recommend an **orchestrator with specialized capabilities**, using deterministic tools for accounting operations and narrowly scoped LLM assistance for ambiguous investigation tasks.

A multi-agent architecture is useful when the workflow contains distinct responsibilities, but accounting calculations and approval decisions should not depend on unconstrained LLM reasoning.

```text
                    Financial Source Files
                             |
                             v
                  Ingestion and Normalization
                             |
                             v
                     Workflow Orchestrator
                             |
          +------------------+------------------+
          |                  |                  |
          v                  v                  v
   COA Mapping         Adjustment          FX and Period
   Validation          Validation          Reconciliation
   (rules/tool)        (rules/tool)          (rules/tool)
          |                  |                  |
          +------------------+------------------+
                             |
                             v
                    Validation Gate
                             |
                 +-----------+-----------+
                 |                       |
                 v                       v
           Validated inputs         Exceptions found
                 |                       |
                 v                       v
         Statement Builder       Investigation Assistant
         (deterministic)          (LLM-assisted)
                 |                       |
                 v                       v
         Statement Checks        Human Review Queue
                 |                       |
                 +-----------+-----------+
                             |
                             v
                   Audit and Lineage Store
                             |
                             v
                      Reporting Output
```

The diagram represents a proposed production design. The current prototype implements the validation, reconciliation, audit-metadata, and LLM investigation portions; it does not yet implement the complete orchestrator, statement builder, or lineage store shown above.

### 3.2 Responsibilities

**Workflow orchestrator**

- Coordinates processing stages and maintains workflow state.
- Prevents statement generation when required validation gates fail.
- Routes exceptions to the appropriate investigation or human-review path.
- Records stage outcomes and execution metadata.

**COA mapping validation**

- Checks that referenced accounts exist in the approved COA.
- Distinguishes posting accounts from header accounts.
- Flags ambiguous or missing mappings instead of inventing account classifications.

**Adjustment validation**

- Validates journal structure and account references.
- Checks debit-credit equality.
- Rejects entries that fail implemented hard rules.
- Flags suspicious entries for review.

**FX and period reconciliation**

- Checks required period-end rates.
- Compares current-period and prior-period account presence.
- Flags unresolved differences without silently changing balances.

**Statement builder**

- Aggregates validated account balances into statement lines using approved, versioned mappings.
- Uses deterministic arithmetic.
- Produces calculation references and source lineage for each output cell.

**Investigation assistant**

- Explains validation findings in plain English.
- Suggests evidence to collect and checks to perform.
- Distinguishes observed facts from possible explanations.
- Does not approve journals, create authoritative account mappings, or alter financial balances.

### 3.3 Why this topology?

A single unrestricted LLM agent would make accounting calculations and correction decisions harder to constrain, reproduce, and audit.

An orchestrator with specialized capabilities separates deterministic accounting operations from language-based investigation. It also creates explicit validation gates and supports independent testing of each component.

The current prototype uses a simpler sequential pipeline rather than a fully autonomous multi-agent system. This keeps the implementation small and testable while establishing a path to the proposed production architecture.

## 4. Deterministic Code vs. LLM Reasoning

The system follows the principle that **accounting truth is determined by validated data and approved rules, not by an LLM's confidence**.

| Responsibility | Approach | Reason |
|---|---|---|
| Journal schema validation | Deterministic Pydantic validation | Repeatable structural checks |
| Debit-credit equality | Deterministic arithmetic | Exact financial invariant |
| Account existence and posting eligibility | Deterministic COA lookup | Must use the approved account master |
| FX-rate availability | Deterministic lookup | Rates must come from an authoritative source |
| Currency conversion | Deterministic arithmetic | Reproducible calculations using an approved rate |
| Statement aggregation | Deterministic code | Exact and reproducible financial totals |
| Statement-level reconciliation | Deterministic rules | Explicit accounting invariants |
| Explaining rejection reasons | LLM-assisted | Natural-language explanations for finance users |
| Suggesting investigation steps | LLM-assisted | Helps reviewers determine what evidence to inspect |
| Proposing candidate mappings | Optional LLM assistance with evidence and human approval | A candidate must never become an approved mapping automatically |
| Journal approval or posting | Authorized human/workflow control | Requires explicit permission and segregation of duties |

### 4.1 Where AI earns its place

Generating a balance sheet from a clean, validated Trial Balance is primarily an aggregation and mapping problem. It does not inherently require an LLM.

The LLM is most useful when the system must explain why a check failed, summarize multiple exceptions, identify missing supporting evidence, or help a finance user investigate an ambiguous situation.

For example, deterministic code can report that journal `JE-002` has debits of $28,500 and credits of $25,000. The LLM can explain that the entry is out of balance by $3,500 and recommend reviewing the journal lines and supporting documentation.

The LLM must not decide which amount is correct or invent a balancing entry.

## 5. Production Failure Modes and Controls

| Failure mode | Required control | Failure behavior |
|---|---|---|
| Hallucinated account mapping | Approved COA lookup and versioned mapping rules | Do not accept an unapproved mapping; route the exception to review |
| Debits differ from credits after adjustment | Recalculate totals after every proposed adjustment | Reject the adjustment and prevent downstream statement processing |
| Account fits no COA node | Explicit unmapped-account check | Stop affected reporting for resolution; do not force an arbitrary mapping |
| Missing FX rate | Validate currency, period, rate type, and authoritative source | Block affected currency translation until a valid rate is supplied or an authorized exception is recorded |
| Circular intercompany entries | Entity/counterparty matching and graph-based cycle analysis where appropriate | Flag suspected cycles for investigation; do not assume that a cycle alone proves an accounting error |
| Duplicate journal IDs | Duplicate detection and idempotency controls | Do not process duplicates silently |
| Malformed or missing input files | Schema validation, file checks, and explicit ingestion errors | Stop affected processing and report the failure |
| LLM hallucination or unsupported recommendation | Evidence-grounded prompts and output validation | Label recommendations as unverified; require human review |
| LLM timeout or provider outage | Bounded retries and deterministic fallback | Preserve the validation report even if AI analysis is unavailable |
| Audit lineage is incomplete | Required source references and lineage completeness checks | Mark affected outputs as not fully traceable |

### 5.1 Intercompany caution

The current prototype flags an intercompany entry when its description contains “intercompany” and debit and credit lines use the same account.

This is only a heuristic. It is not full circularity detection and does not establish that the transaction is incorrect.

A production solution should use legal-entity identifiers, counterparty identifiers, intercompany account mappings, settlement references, and transaction relationships. A graph-based analysis may then identify suspicious cycles for review.

## 6. Validation and Self-Correction Loop

The system must validate its output before returning it to a finance user. However, financial self-correction must be controlled and must never mean silently changing accounting records.

### 6.1 Proposed workflow

```text
Ingest source data
       |
       v
Validate schemas and identifiers
       |
       v
Apply approved mappings and adjustments
       |
       v
Run accounting invariants
       |
       v
   Checks pass?
     /      \
   Yes       No
    |         |
    v         v
Continue   Classify exception
processing      |
    |           v
    |      Can it be safely
    |      resolved using an
    |      approved rule?
    |          /     \
    |        Yes      No
    |         |        |
    |         v        v
    |   Propose change  Human review
    |         |
    |         v
    |   Revalidate all
    |   affected invariants
    |         |
    |         v
    |   Retry limit reached?
    |       /       \
    |      No        Yes
    |      |          |
    |      v          v
    |   Recheck    Stop and escalate
    |      |
    +------+
       |
       v
Final validation gate
       |
       v
Traceable output or explicit failure
```

This diagram describes the proposed production loop; the current prototype does not implement an autonomous correction-and-retry loop.

### 6.2 What must be checked before returning output?

At minimum:

1. Input files conform to the expected schemas.
2. Journal entries satisfy structural and account-validation rules.
3. Every accepted adjustment balances.
4. Required account mappings exist and are approved.
5. Required FX rates are available for the relevant currency and period.
6. The adjusted Trial Balance balances.
7. Statement-level totals and accounting invariants pass.
8. All output cells have the required source references.
9. Exceptions are explicitly classified and unresolved failures are not hidden.
10. LLM explanations do not overwrite deterministic statuses or financial values.

### 6.3 Correction policy

A system may automatically retry transient operations such as a failed LLM request, subject to a bounded retry policy.

Financial corrections are different. An LLM may propose a candidate correction, but the candidate must be checked against approved rules, revalidated, and approved under the organization's control process before it affects authoritative reporting.

If a required invariant still fails, the workflow must stop the affected downstream processing and return a clear exception report. It must not invent a balancing amount, use an unapproved exchange rate, or silently force an account into a COA category.

## 7. Auditor Traceability and Source-Row Lineage

An auditor should be able to trace a reported financial statement cell back to the account balances, journal adjustments, mappings, and rates that produced it.

### 7.1 Proposed lineage model

Each statement cell should carry a lineage record containing fields such as:

| Field | Purpose |
|---|---|
| `statement_name` | Identifies the financial statement |
| `statement_line_id` | Identifies the statement line |
| `period` | Reporting period |
| `currency` | Reporting or source currency |
| `calculated_value` | Computed value for the cell |
| `calculation_rule_id` | Versioned aggregation or calculation rule |
| `source_file` | Input filename |
| `source_row_id` | Stable source-row identifier |
| `account_code` | Source account code |
| `journal_id` | Related adjustment identifier, if applicable |
| `fx_rate_reference` | Applied rate and source reference, if applicable |
| `mapping_version` | Approved mapping version |
| `run_fingerprint` | Identifier for the processing run |

These fields are a proposed production schema. The current prototype fingerprints input files and records source identifiers for findings, but it does not yet create full statement-cell lineage.

### 7.2 Example of tracing a cell

Suppose a future generated balance sheet contains a cell for “Cash and Cash Equivalents.”

An auditor should be able to:

1. Select the statement cell and reporting period.
2. Retrieve the calculation rule and contributing account mappings.
3. Identify the Trial Balance rows included in the total.
4. Inspect related journal adjustments and their validation outcomes.
5. Inspect any FX rates applied to foreign-currency balances.
6. Reproduce the aggregation from the referenced inputs and rule versions.
7. Compare the recomputed value with the reported cell.

Source references should use stable row identifiers or explicit source-file row numbers and should be preserved through transformations. A file fingerprint identifies input content, but a fingerprint alone does not prove how an individual cell was calculated.

### 7.3 Current implementation boundary

The current implementation generates input-file fingerprints, a run fingerprint, validation findings, and journal-specific rejection explanations.

Full source-row lineage, statement-cell calculation references, and auditor drill-down are future work. They must be implemented and tested before claiming complete financial statement traceability.

## 8. Audit Metadata

The current prototype calculates SHA-256 fingerprints for five input files:

- `trial_balance.csv`
- `chart_of_accounts.csv`
- `manual_adjustments.json`
- `prior_period_tb.csv`
- `fx_rates.csv`

The report also includes the reporting period, a run fingerprint, and a validation version.

These fingerprints help identify the source-file contents associated with a run. They do not, by themselves, prove that the input data is correct or establish a complete immutable audit trail.

A production system should additionally record execution timestamps, software and mapping versions, approval decisions, user identities where appropriate, and immutable processing events.

## 9. Current Prototype Implementation and Test Coverage

The current implementation includes:

- Pydantic-based journal schema validation.
- Deterministic journal balance and account checks.
- Trial Balance account, balance, and cash-flow classification checks.
- FX-rate availability checks.
- Prior-period account difference detection.
- SHA-256 input and run fingerprints.
- Groq + LangChain investigation explanations.
- Journal-specific rejection explanations with deterministic fallback.
- Automated pytest coverage.

The latest reported test run passed 13 tests. This demonstrates that the tested cases behave as expected; it does not establish production readiness or comprehensive accounting correctness.

The prototype does not yet implement complete financial statement generation, an autonomous orchestrator with specialized sub-agents, a financial correction-and-retry loop, full intercompany cycle detection, or end-to-end statement-cell lineage.

## 10. Security, Governance, and Human Oversight

- Store API credentials in environment variables or an approved secret manager.
- Do not commit `.env` files or expose API keys.
- Send only authorized data to an external LLM provider.
- Treat source descriptions and memos as untrusted data, not as instructions to the LLM.
- Keep deterministic validation results separate from generated explanations.
- Require human authorization for accounting corrections and journal posting.
- Preserve exception evidence and record approval decisions.
- Prevent unresolved validation failures from being silently presented as final, approved financial statements.

## 11. Future Implementation Plan

The recommended order of work is:

1. Implement statement generation from validated balances using approved, versioned mappings.
2. Add post-adjustment and statement-level accounting invariants.
3. Implement stable source-row lineage and statement-cell drill-down.
4. Add explicit orchestration, exception routing, and bounded retry policies.
5. Introduce approved correction proposals with human authorization.
6. Implement entity-level intercompany matching and cycle investigation.
7. Extend tests to cover malformed files, mapping ambiguity, failed retries, lineage completeness, and statement reconciliation.
8. Add production controls, monitoring, permissions, and immutable audit events.

## 12. Design Principles

The architecture follows five core principles:

1. **Deterministic accounting:** Arithmetic and accounting invariants must be reproducible.
2. **Evidence-based AI:** The LLM explains findings and assists investigation rather than inventing financial facts.
3. **Fail safely:** Unresolved accounting errors block affected downstream processing.
4. **Human accountability:** Financial corrections and approvals remain under authorized controls.
5. **End-to-end traceability:** Every reported financial value should ultimately be reproducible from identified source data and approved calculation rules.

The objective is not unrestricted autonomy. It is a controlled financial workflow in which automation improves speed and clarity without weakening accounting integrity.
