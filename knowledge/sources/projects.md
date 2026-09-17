---
id: projects
source_type: project_docs
synthetic: true
as_of: 2026-02-15
label: SYNTHETIC — project deep-dives
---

# Project deep-dives

## Project: Transfer orchestration rebuild (Meridian Ledger)

**Problem:** Transfer initiation mixed policy checks, partner calls, and ledger writes on one request path. Timeouts cascaded into duplicate submissions.

**Approach:** Split into (1) validate + reserve, (2) async execute with idempotency key, (3) reconcile. Exposed a single `Idempotency-Key` header to clients.

**Outcome:** Duplicate transfer rate fell from 0.08% to 0.01%. p95 initiation latency 890ms → 410ms.

**Trade-off rejected:** Full rewrite of the ledger. Too risky inside a quarter; instead wrapped the existing ledger behind a clearer reservation API.

**Sources of truth for claims:** internal RFC-2024-17 (not committed; summarised here), production metrics dashboard (synthetic numbers).

## Project: Grounded agent-support assistant (Meridian Ledger)

**Problem:** Support agents paraphrased policy incorrectly; escalations rose.

**Approach:** RAG over policy markdown + product FAQs. Answers must cite chunk IDs. If retrieval score < threshold, reply "I don't have that in policy — escalate."

**Outcome:** Agent handle-time for policy questions down ~18% in a 4-week pilot; zero known fabricated fee-schedule answers in sampled audits (n=120).

**Evaluation:** Weekly set of 40 questions; groundedness and refusal correctness tracked. Failures reviewed in eng+ops sync.

## Project: Settlement exception reducer (Northstar Payments)

**Problem:** Manual ops handled ~2.1% of daily settlements as exceptions.

**Approach:** Deterministic matching rules first; ML classifier only for residual "unknown reason code" bucket, never for money movement decisions.

**Outcome:** Unresolved exceptions 2.1% → 0.4%. ML suggestions were advisory; ops confirmed before action.

**Deliberate non-AI decision:** Money movement matching stayed rule-based. Model output was not allowed to approve a payout.
