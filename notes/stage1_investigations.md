# Stage 1 — Written Investigations & Proofs

## 1. Input Validation: Whitespace Stripping vs. Empty String Check
### Behavior Demonstration
When validating `query: str`:
- **Scenario A (Check empty first, then strip):** If input is `"   "`, checking `len(val) == 0` evaluates to `False`. The whitespace bypasses the emptiness check and enters the downstream logic unless stripped later.
- **Scenario B (Strip first, then check empty):** Applying `.strip()` collapses `"   "` to `""`. Checking `len(stripped) == 0` triggers validation rejection immediately.

### Implementation Outcome
The validator runs `v.strip()` before checking minimum length (`min_length=1`). Therefore, `"   "` raises HTTP 422 Unprocessable Entity, preventing empty or invisible queries from reaching downstream ChromaDB or LLM resources.

---

## 2. Calculator Status Code: Division by Zero (HTTP 400 vs. 422 vs. 500)
- **Why HTTP 400 (Bad Request):** The payload is syntactically valid JSON and passes type schema parsing, but contains a semantic mathematical domain violation (undefined arithmetic operation).
- **Why not 422:** HTTP 422 indicates unprocessable schema or malformed syntax (e.g., hostile tokens like `__import__` or unparseable characters).
- **Why never 500:** Division by zero is a known client-side input error, not an unexpected internal server fault. Returning 500 would imply server instability.

---

## 3. Retrieve Behavior with `top_k=0`
- If a client requests `top_k=0`, semantic similarity calculation and ChromaDB query execution are unnecessary.
- The endpoint catches `top_k <= 0` at schema validation (`ge=1`), returning HTTP 422. If bypassed internally, `retrieve_documents()` immediately returns an empty `results: []` with `total_retrieved: 0` without issuing a vector search query.
