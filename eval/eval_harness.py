import time
from typing import List, Dict, Any
from app.agent.core import ReActAgent
from app.schemas.agent import AgentRequest

EVAL_QUESTIONS: List[Dict[str, Any]] = [
    {
        "id": "Q1_SINGLE_TOOL",
        "category": "single-tool",
        "question": "What is 14 multiplied by 24?",
        "expected_tools": ["calculate_expression"],
        "expected_substring": "336",
    },
    {
        "id": "Q2_MULTI_HOP",
        "category": "multi-hop",
        "question": "What is the population of France divided by the area of Germany in square kilometres?",
        "expected_tools": ["search_world_facts", "calculate_expression"],
        "expected_substring": "190",
    },
    {
        "id": "Q3_EXPECTED_FAIL",
        "category": "expected-fail",
        "question": "What is the average lifespan of a Martian rover on Neptune?",
        "expected_tools": ["search_world_facts"],
        "expected_substring": "unanswerable",
    },
]


def run_harness():
    print("=" * 80)
    print("STARTING STAGE 2 EVALUATION HARNESS (WITH DETAILED TRACE)")
    print("=" * 80)

    agent = ReActAgent()
    results = []

    for item in EVAL_QUESTIONS:
        q_id = item["id"]
        question = item["question"]
        expected_tools = item["expected_tools"]
        expected_substr = item["expected_substring"]

        print(f"\n" + "-" * 70)
        print(f"[RUNNING] {q_id}: {question}")
        print("-" * 70)
        req = AgentRequest(query=question, max_iterations=6, return_trace=True)

        start_time = time.perf_counter()
        response = agent.run(req)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Print the trace steps to see why it looped
        for s in response.steps:
            print(f"  Step {s.step}:")
            print(f"    Thought: {s.thought}")
            print(f"    Action: {s.action}({s.action_input})")
            print(f"    Observation: {s.observation}")

        print(f"  Final Answer / Output: {response.answer}")

        tools_called = [step.action for step in response.steps if step.action]
        answer_text = response.answer.lower()
        contains_expected = expected_substr.lower() in answer_text

        if item["category"] == "expected-fail":
            passed = response.stop_reason in ["final_answer", "max_iterations"]
        else:
            tools_match = any(t in tools_called for t in expected_tools)
            passed = contains_expected and tools_match

        results.append({
            "id": q_id,
            "passed": passed,
            "stop_reason": response.stop_reason,
            "tools_called": tools_called,
            "iterations": response.iterations,
            "latency_ms": duration_ms,
        })

    print("\n" + "=" * 80)
    print("STAGE 2 EVALUATION SUMMARY")
    print("=" * 80)
    header = f"{'ID':<16} | {'STATUS':<6} | {'STOP REASON':<14} | {'ITERS':<5} | {'LATENCY':<9} | {'TOOLS CALLED'}"
    print(header)
    print("-" * len(header))

    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        tools_str = ", ".join(r["tools_called"]) if r["tools_called"] else "none"
        print(f"{r['id']:<16} | {status:<6} | {r['stop_reason']:<14} | {r['iterations']:<5} | {r['latency_ms']:<7}ms | {tools_str}")

    print("=" * 80)


if __name__ == "__main__":
    run_harness()