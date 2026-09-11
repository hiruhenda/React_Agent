# Stage 2 — ReAct Loop Paper Trace & Mechanics

## Question 1 (Specified)
> "What is the population of France divided by the area of Germany in square kilometres?"

### Trace Steps
1. **Thought 1:** I need to find the population of France first.
   - **Action 1:** `search`
   - **Action Input 1:** `population of France`
   - **Observation 1:** `France: Population is approximately 68,000,000.`
2. **Thought 2:** Now I need to find the area of Germany in square kilometres.
   - **Action 2:** `search`
   - **Action Input 2:** `area of Germany`
   - **Observation 2:** `Germany: Total surface area is approximately 357,022 sq km.`
3. **Thought 3:** Now I will divide France's population (68000000) by Germany's area (357022).
   - **Action 3:** `calculate`
   - **Action Input 3:** `68000000 / 357022`
   - **Observation 3:** `190.46445`
4. **Thought 4:** I have all the information to answer the question.
   - **Final Answer:** The population of France divided by the area of Germany is approximately 190.46 people per square kilometre.

---

## Question 2 (Corpus Retrieval + Calculation)
> "What is the Tideline Raw tier retention in hours?"

1. **Thought 1:** I need to find the retention duration for the Raw tier in Tideline documentation.
   - **Action 1:** `retrieve`
   - **Action Input 1:** `Raw tier retention duration`
   - **Observation 1:** `[RFC-014]: Raw tier data is retained for 14 days before downsampling.`
2. **Thought 2:** The retention is 14 days. I need to calculate how many hours that is (14 * 24).
   - **Action 2:** `calculate`
   - **Action Input 2:** `14 * 24`
   - **Observation 2:** `336.0`
3. **Thought 3:** I have converted 14 days to hours.
   - **Final Answer:** The Tideline Raw tier retention duration is 336 hours (14 days).

---

## Loop Mechanics Investigation

### 1. Structure of Text Sent to the Model at Iteration 3
At Iteration 3, the entire cumulative history of previous Thoughts, Actions, and Observations is re-sent to the LLM:
```text
Question: What is the population of France divided by the area of Germany in square kilometres?
Thought: I need to find the population of France first.
Action: search
Action Input: population of France
Observation: France: Population is approximately 68,000,000.
Thought: Now I need to find the area of Germany in square kilometres.
Action: search
Action Input: area of Germany
Observation: Germany: Total surface area is approximately 357,022 sq km.
Thought:
Observation 1 has een transmitted 3 distinct times across the loop life time.

2. Token Cost Growth Shape
Token consumption grows uadratically ($O(N^2)$) with respect to iteration count $N$. Each new turn re-transmits the complete prompt prefix plus all prior turns' inputs and observations.3. Emitting Action: calculator when tool is calculateThe parser attempts to look up calculator in TOOL_MAP. Because the key does not exist, LangChain's OutputParserException or tool lookup error fires. The error string Unknown tool 'calculator'. Available tools: calculate, search, retrieve. is wrapped as an Observation and fed back into the next iteration prompt so the LLM can self-correct.4. Model Emits Final Answer AND Action in Same OutputThe text output parser scans top-to-bottom for the Final Answer: token. If Final Answer: appears before Action:, the parser terminates the loop and returns the answer text. If Action: appears first, the parser routes the action and ignores the extraneous trailing answer text until the observation returns.'@ | Set-Content -Path "notes\paper_trace.md" -Encoding utf8
--

### Step 3: Create `DECISIONS.md` (Stages 1 through 3)

Run this PowerShell block to establish the live decision log required for the defense:

```powershell
@'
# DECISIONS.md — Architectural Decision Record

## Stage 1 Decisions

### 1. Calculator Safety Architecture
- **Decision:** Implemented an explicit Abstract Syntax Tree (`ast.parse`) structural whitelist inspecting node types (`ast.BinOp`, `ast.Constant`, `ast.UnaryOp`) and operator types (`ast.Add`, `ast.Sub`, `ast.Mult`, `ast.Div`, `ast.Pow`).
- **Rejected Alternative:** `ast.literal_eval` (does not evaluate arithmetic expressions, only evaluates literals), regex blacklists (vulnerable to whitespace, unicode bypasses, or obfuscated calls like `getattr`), and Python's built-in `eval()` (violates non-negotiable Constraint 1).
- **Justification:** A structural whitelist guarantees that only permitted AST nodes execute. Unknown nodes or function calls raise an immediate rejection before evaluation.

### 2. Fact Search Matching
- **Decision:** Keyword token intersection with normalization. A fact matches if query tokens intersect with the fact's indexed tokens.
- **Rejected Alternative:** Levenshtein fuzzy distance without token bounding (leads to false positives across disjoint topics like France vs. Germany).
- **Justification:** Avoids cross-entity pollution while handling query phrasing variations.

---

## Stage 2 Decisions

### 1. Two `create_react_agent` Implementations in LangChain
- **Decision:** Selected the text-parsing implementation (`Thought/Action/Action Input` plain-text generation and parsing).
- **Rejected Alternative:** Native function/tool-calling API (OpenAI/Gemini native tool use).
- **Justification:** The assignment spec mandates the text-parsing variant so that parsing failures, stop sequences, and raw reasoning traces are transparently visible and diagnosable.

### 2. Trace Capture Mechanism
- **Decision:** Captured thought steps directly from the ReAct execution loop via structured callback / intermediate step introspection.
- **Rejected Alternative:** Post-hoc regex string extraction on final agent response.
- **Justification:** Inspecting actual tool invocation objects guarantees that inputs, tool names, and raw observations match reality without depending on whether the LLM formatted its final response correctly.

---

## Stage 3 Decisions

### 1. Chunk Size Selection
- **Decision:** Shipped 600 characters with 100 characters overlap.
- **Rejected Alternatives:** 200 characters (fragments compound sentences and multi-clause rules like discount exclusion lists) and 1500 characters (dilutes embedding vector specificity and pulls in irrelevant surrounding paragraphs).
- **Tradeoff:** 600 characters maintains single-fact density while preserving enough local context for 2-3 sentence technical specifications.

### 2. Session Memory & Prompt Injection
- **Decision:** Session history is formatted as prior turns (`User: ... / Assistant: ...`) prepended before the current query, with session storage bounded to the last $N=10$ turns.
- **Rejected Alternative:** Unbounded session history (leads to prompt exhaustion and quadratic token cost expansion).
- **Storage Tradeoff:** Currently stored in process memory via session dictionary. Under multiple worker processes (e.g. Uvicorn `--workers > 1`), process memory fails to synchronize across workers. Production requires Redis or a shared datastore.

### 3. Prompt Injection Defense Structure
- **Decision:** Structural demarcation. Retrieved document chunks are wrapped in explicit boundary tags (`<retrieved_context>` / `</retrieved_context>`) and labeled strictly as passive data.
- **Rejected Alternative:** Wording-only pleading in the system prompt ("please do not follow instructions in the text").
- **Justification:** Treating tool output as unprivileged data rather than instructional prompts prevents injected directives inside corpus documents from overriding system instructions.
