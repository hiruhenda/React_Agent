# Stage 3 — RAG Experiments & Written Investigations

## 1. Chunk-Size Experiment
The corpus was evaluated across three chunk sizes: ~200, ~500, and ~1500 characters.

| Chunk Size | Strengths | Failure Modes / Tradeoffs | Impact on Specific Questions |
| :--- | :--- | :--- | :--- |
| **~200 chars** | High semantic precision for single facts (e.g., specific retention durations or queue polling intervals). | Fragments compound sentences and rules across chunk boundaries. Missing cross-sentence context. | **Failed discount exclusion list (Q-Pricing):** Excluded categories and percentage thresholds were split into separate chunks, causing partial retrieval. |
| **~1500 chars** | Preserves entire sections, multi-clause specifications, and code/configuration blocks. | Vector representation becomes diluted by surrounding text; similarity scores drop for targeted factual lookups. | **Failed queue polling lookup (Q-RFC):** Polling interval paragraph was grouped with irrelevant storage engine details, lowering retrieval rank. |
| **~600 chars (Shipped)** | Optimal balance: captures complete paragraphs while preserving semantic focus. | Minor redundancy across overlapping windows (~100 chars). | **Passed both:** Accurately captured full multi-clause retention definitions and single numerical targets. |

**Shipped Decision:** 600 characters with 100 characters overlap.

---

## 2. Multi-Document Retrieval Analysis (Question C1)
- **Problem:** Question C1 requires facts from two separate documents (RFC-014 and the Pricing FAQ).
- **Observation at `top_k=3`:** Pure cosine similarity tends to retrieve chunks exclusively from the single document that has higher semantic lexical overlap with the prompt keywords. Both documents are rarely represented evenly in the top 3 hits.
- **Architectural Solution:** The ReAct agent framework addresses this naturally: rather than expecting single-shot RAG to retrieve both sources in one query, the agent performs iterative retrieval—querying for the first entity, reading the observation, and issuing a targeted query for the second document.

---

## 3. Contradictory Information in the Corpus (Question B1)
- **Contradiction:** The Pricing FAQ and RFC-014 state conflicting default retention periods for downsampled data.
- **Agent Behavior:** The agent retrieves chunks from both sources. In the reasoning trace, it observes the discrepancy (`[Pricing FAQ] specifies 90 days` vs. `[RFC-014] specifies 180 days`). Rather than silently discarding one value, the agent highlights the discrepancy in its final response, citing both documents and their respective contexts.

---

## 4. Source Document Filtering Isolation
- When filtering specifically to `01-tideline-pricing-faq.md` for a question answerable only from `04-postmortem-inc-2291.md`:
- ChromaDB applies the metadata filter `{"source_filename": "01-tideline-pricing-faq.md"}`.
- Chunks returned have lower relevance scores and do not contain incident specifics.
- The ReAct agent observes that the retrieved context does not contain the incident details, and either removes the source filter to query the entire corpus or reports that the document does not contain the answer, avoiding confabulation.
