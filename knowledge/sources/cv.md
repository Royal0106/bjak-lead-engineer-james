---
id: cv
source_type: cv
synthetic: true
as_of: 2026-03-01
label: SYNTHETIC — fictional professional profile for this exercise
---

# Jordan Hale — Curriculum Vitae

**Role focus:** Engineering Manager / Lead Engineer (backend, applied AI, payments)
**Location:** Kuala Lumpur, Malaysia (open to remote SE Asia)
**Contact:** jordan.hale.synthetic@example.com

## Summary

Engineering leader with 11 years building payment and fintech systems. Most recently Staff-to-Lead path at a SE Asia neobank-adjacent payments company. Strong bias to measurable reliability, grounded AI systems, and thin slices that ship with evaluation — not demos that invent facts.

## Experience

### Lead Engineer — Meridian Ledger (synthetic neobank platform)
**2023-04 – present · Kuala Lumpur**

- Technical DRI for the customer-facing transfer orchestration service handling ~40k transfers/day.
- Introduced a retrieval-grounded support assistant for agent tooling; required citation of policy documents and refused answers without evidence (hallucinated balance = P0).
- Cut p95 transfer-initiation latency from 890ms to 410ms by removing a synchronous KYC re-check from the hot path and moving it to an async gate with clear failure UX.
- Led a team of 6 engineers (4 backend, 1 mobile, 1 QA). Ran hiring loops and incident reviews.
- Owned production quality bar: error budgets, weekly eval of the support assistant, blameless postmortems.

### Staff Engineer — Northstar Payments
**2021-01 – 2023-03 · Singapore / remote**

- Designed the idempotent payout API used by 12 merchant partners.
- Built a reconciliation pipeline that reduced unresolved settlement exceptions from ~2.1% to 0.4% of daily volume.
- Mentored three mid-level engineers; two promoted to senior during this period.
- Title on this CV: **Staff Engineer**. See `conflicts.md` for a documented title mismatch with another source.

### Senior Software Engineer — Coral Bay Bank (digital)
**2018-06 – 2020-12 · Kuala Lumpur**

- Owned the account-opening workflow service; reduced drop-off between KYC submit and account ready from 18% to 9%.
- Introduced contract tests between mobile and backend; cut integration regressions ~60% over two quarters.

### Software Engineer — Harbor Systems
**2015-01 – 2018-05 · Penang**

- Built ETL jobs for merchant settlement files (CSV/ISO8583-ish proprietary formats).
- On-call rotation for batch settlement; wrote runbooks still used after departure (per successor notes — synthetic).

## Education

- B.Sc. Computer Science — Universiti Sains Malaysia, 2014

## Skills

- Languages: Python, Go, SQL, TypeScript (read/write), Java (maintenance)
- Systems: Postgres, Redis, Kafka, Kubernetes, OpenTelemetry
- Applied AI: RAG design, evaluation harnesses, prompt + retrieval grounding, Gemini/OpenAI APIs
- Leadership: incident command, hiring, roadmap trade-offs under time boxes

## Selected talks / writing (synthetic)

- "Groundedness before fluency" — internal tech talk, Meridian Ledger, 2025
- "Idempotency keys that survive retries" — blog post, 2022 (Northstar)

## What this CV does not contain

- No claim of FAANG employment
- No claim of PhD or published research papers
- No salary, equity, or compensation figures
- No spoken-language proficiency list
