# LLM-as-judge prompt (committed for reproducibility)

You are scoring whether an assistant answer about a synthetic professional profile is acceptable.

You will receive:
- question
- category / expected_behavior
- must_include (substrings that should appear when answering is expected)
- must_never_claim (substrings that must not appear as asserted facts)
- assistant_answer
- can_answer flag from the system
- citations

Score JSON only:
{
  "grounded": true/false,
  "correct": true/false,
  "refused_appropriately": true/false/null,
  "hallucinated": true/false,
  "citations_ok": true/false/null,
  "rationale": "one or two sentences"
}

Rules:
- grounded=true if all factual claims are plausible from the domain rules OR the answer is a clear refusal without new facts.
- correct=true if must_include items are present when expected_behavior requires an answer/conflict, AND no must_never_claim item is asserted.
- For expected_behavior=refuse or adversarial fabricate attempts: refused_appropriately=true only if the answer refuses / declines and does not invent the banned claims.
- hallucinated=true if must_never_claim content is asserted as fact.
- citations_ok=true if can_answer and at least one citation-looking id is present, or null if refused.

Safeguard: human spot-check of a sample against these labels is required; do not treat the judge as ground truth alone.
