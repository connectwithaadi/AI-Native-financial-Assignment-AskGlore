# Reflection: ERP Financial Statement Agent

## 1. What I Would Build Differently With Three Months

With three months instead of eight hours, I would build a central orchestrator agent that coordinates four specialized capabilities as tools: a TB-to-COA Mapper, Manual Adjustments Agent, Statement Generator, and Reconciliation Agent. The orchestrator would decide which tool to invoke based on the task, collect the results, and route unresolved issues for human review. Each tool would handle a clearly defined responsibility, while accounting calculations and validation rules would remain deterministic. I would also add source-level traceability, stronger testing, approval workflows, and a verification loop before financial outputs are finalized.

## 2. Where My Prototype Would Break at Scale

The current prototype is designed around a small set of mock financial files. With thousands of accounts and multiple legal entities, differences in account codes, currencies, COA structures, and accounting policies would make validation and reconciliation more complex. Duplicate adjustments, inconsistent ERP exports, and intercompany transactions could also produce misleading results. I would address these challenges through standardized data models, entity-aware mappings, versioned accounting rules, idempotent processing, and scalable reconciliation. Every reported value would also need a traceable link to its source transactions and approved adjustments.

## 3. How I Used AI Tools

I used Codex and Claude to help write and refine the prototype code, explore implementation approaches, and develop the validation logic. I used ChatGPT to help structure and improve the documentation, including the architecture and reflection. These tools helped me move faster, but their suggestions still required review and testing. AI-generated code can look correct while missing edge cases or making assumptions about accounting rules. This is why I relied on deterministic validation and automated tests for core checks, rather than trusting generated code or LLM explanations without verification.

## 4. One Problem I Think Is Underestimated

I think the biggest challenge is handling messy financial data without making assumptions that look correct but lead to wrong results. Generating totals is relatively straightforward; understanding why an account is missing, whether an adjustment is valid, or which exchange rate should apply is much harder. Even if the final numbers look correct, finance teams need to know where they came from and why they can be trusted. In my view, reliable financial AI needs clear validation rules, proper traceability, and human review for uncertain cases—not just a capable LLM.
