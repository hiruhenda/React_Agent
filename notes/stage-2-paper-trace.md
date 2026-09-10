\# Stage 2 — Paper Traces and Loop Analysis



\## 1. Hand Traces for Three Representative Questions



\---







\### Trace 1: Given Spec Question

\*\*Question:\*\* "What is the population of France divided by the area of Germany in square kilometres?"



Thought: I need to find the population of France and the area of Germany in square kilometres, then divide the former by the latter. First, let's search for the population of France.

Action: search\_world\_facts

Action Input: population of France

Observation: \[{"topic": "population, france", "fact": "The population of France is approximately 68,170,000 (2024 estimate)."}]



Thought: The population of France is approximately 68,170,000. Now I need to find the area of Germany in square kilometres.

Action: search\_world\_facts

Action Input: area of Germany

Observation: \[{"topic": "area, germany", "fact": "Germany has a total area of 357,022 square kilometres."}]



Thought: France has a population of 68,170,000 and Germany has an area of 357,022 square kilometres. Now I need to divide 68170000 by 357022.

Action: calculate\_expression

Action Input: 68170000 / 357022

Observation: 190.94061430388043



Thought: I now have the calculation result.

Final Answer: The population of France (approximately 68,170,000) divided by the total area of Germany (357,022 km²) is approximately 190.94 people per square kilometre.









Trace 2: Tideline Corpus Retrieval + Arithmetic

Question: "What is the retention period in days for the Raw tier in RFC-014, and how many total hours does that represent?



Thought: I need to look up the retention period of the Raw tier in RFC-014, then convert that duration from days into hours by multiplying by 24.

Action: retrieve\_tideline\_docs

Action Input: RFC-014 Raw tier retention duration

Observation: \[Document Chunk from 02-rfc-014-retention-and-downsampling.md: "Raw tier retains full-resolution telemetry metrics for exactly 14 days before downsampling."]



Thought: The Raw tier retention period is 14 days. To find the total hours, I need to calculate 14 multiplied by 24.

Action: calculate\_expression

Action Input: 14 \* 24

Observation: 336



Thought: I now know the Raw tier retains data for 14 days, which equals 336 hours.

Final Answer: According to RFC-014, the retention period for the Raw tier is 14 days, which equals 336 hours.











Trace 3: Multi-Document Retrieval / Postmortem Investigation

Question: "What incident was caused by the downsampling buffer overflow and which RFC documented the unverified assumption behind it?



Thought: I need to search the corpus for a downsampling buffer overflow incident and determine which engineering RFC contained the unverified assumption that caused it.

Action: retrieve\_tideline\_docs

Action Input: downsampling buffer overflow incident root cause

Observation: \[Document Chunk from 04-postmortem-inc-2291.md: "Postmortem INC-2291: Ingestion buffer overflow in the downsampler pipeline due to memory exhaustion under out-of-order timestamps."]



Thought: INC-2291 describes the buffer overflow. Now I need to retrieve documentation regarding the unverified assumptions in the downsampler design to identify the RFC.

Action: retrieve\_tideline\_docs

Action Input: INC-2291 unverified assumption RFC

Observation: \[Document Chunk from 02-rfc-014-retention-and-downsampling.md: "Section 4.3: Open Questions \& Assumptions: The timestamp ordering assumption across distributed ingest nodes remains unverified under simulated network split conditions."]



Thought: The buffer overflow was documented in INC-2291, and the root cause stemmed from an unverified assumption regarding timestamp ordering explicitly noted in RFC-014.

Final Answer: The downsampling buffer overflow was documented in incident postmortem INC-2291, caused by an unverified assumption regarding distributed timestamp ordering that was originally acknowledged in RFC-014.











2\. Loop Investigation Answers



Q1: Exact Structure at Iteration 3 \& Observation Transmissions

Structure sent to the model at Iteration 3:

At Iteration 3 of Trace 1, the prompt composed by the runner consists of:



1. System Instruction: Role framing, tool registry descriptions, loop formatting rules (Thought, Action, Action Input, Observation, Final Answer).
2. Execution Context \& Cumulative Scratchpa











Question: What is the population of France divided by the area of Germany in square kilometres?



Thought: I need to find the population of France and the area of Germany in square kilometres, then divide the former by the latter. First, let's search for the population of France.

Action: search\_world\_facts

Action Input: population of France

Observation: \[{"topic": "population, france", "fact": "The population of France is approximately 68,170,000 (2024 estimate)."}]

Thought: The population of France is approximately 68,170,000. Now I need to find the area of Germany in square kilometres.

Action: search\_world\_facts

Action Input: area of Germany

Observation: \[{"topic": "area, germany", "fact": "Germany has a total area of 357,022 square kilometres."}]











Observation Transmission Count:

* The observation from Step 1 is generated after iteration 1.
* It is sent to the LLM in Iteration 2, Iteration 3, and Iteration 4 (the step emitting Final Answer:).
* Total transmissions: 3 times. (In an $N$-step loop, Step 1's observation is transmitted $N-1$ times).











Q2: Token Cost Growth

Token consumption grows quadratically: $O(N^2)$, where $N$ is the number of loop iterations.

* Each iteration resends the fixed system prompt + the original question + the cumulative history of all previous thoughts, actions, and observations.
* Token growth rate is steepest on iterations immediately following retrieval tool steps (retrieve\_tideline\_docs), because retrieving multiple Markdown chunks introduces several hundred to thousands of characters into the prompt in a single step, which is subsequently retransmitted on every subsequent turn.











Q3: Tool Name Mismatch 

(Action: calculator vs calculate\_expression)

1. Parser Phase: The parser regex extracts Action: calculator.
2. Lookup Phase: The loop checks action in TOOL\_MAP. Because the registered tool map only contains {"retrieve\_tideline\_docs": ..., "search\_world\_facts": ..., "calculate\_expression": ...}, calculator is not found.
3. Point of Failure:
* In LangChain default implementations: The loop raises an OutputParserException or constructs an observation: "calculator is not a valid tool, try one of \[calculate\_expression, retrieve\_tideline\_docs, search\_world\_facts]".
* In our decoupled custom ReAct implementation: If action not in TOOL\_MAP, the execution bypasses tool invocation and falls through to evaluation or feeds back an error observation.











Q4: Model Emits Both Action and Final Answer Simultaneously

1. Regex Priority:
* In standard text-parsing ReAct loops, parsers search for Final Answer: first, or evaluate the string sequentially.
* If Final Answer: takes precedence: The agent terminates immediately, returning the answer string while the requested action is discarded and never executed.
* If Action: takes precedence or regexes truncate the scratchpad at Action:: The loop executes the tool, discards the preliminary answer, and appends the new observation to the scratchpad for the next step. 







2\. Architectural Consequence: Emitting both indicates the model attempted to answer before verifying the tool observation, which is why system prompts strictly enforce: "Emit EITHER an Action OR a Final Answer, never both."

