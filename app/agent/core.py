import re
import time
from typing import List, Tuple, Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from langchain_core.tools import BaseTool

from app.config import settings
from app.schemas.agent import AgentRequest, ThoughtStep, AgentResponse
from app.agent.prompts import REACT_SYSTEM_PROMPT
from app.services.session import session_store
from app.tools.calculator import calculate_expression
from app.tools.search import search_world_facts
from app.tools.retriever import retrieve_tideline_docs

TOOLS: List[BaseTool] = [
    retrieve_tideline_docs,
    search_world_facts,
    calculate_expression,
]

TOOL_MAP = {tool.name: tool for tool in TOOLS}


def format_tool_descriptions(tools: List[BaseTool]) -> str:
    lines = []
    for t in tools:
        lines.append(f"- {t.name}: {t.description.strip()}")
    return "\n".join(lines)


def extract_response_text(response) -> str:
    if not response or not getattr(response, "candidates", None):
        return ""
    candidate = response.candidates[0]
    if not getattr(candidate, "content", None) or not getattr(candidate.content, "parts", None):
        return ""
    text_parts = [p.text for p in candidate.content.parts if hasattr(p, "text") and p.text]
    return "".join(text_parts).strip()


class ReActAgent:
    def __init__(self, model_name: str | None = None, temperature: float = 0.0):
        self.model_name = model_name or settings.gemini_model
        genai.configure(api_key=settings.gemini_api_key)
        
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        self.tool_descriptions = format_tool_descriptions(TOOLS)
        self.tool_names = ", ".join(TOOL_MAP.keys())

        system_instruction = REACT_SYSTEM_PROMPT.format(
            tool_descriptions=self.tool_descriptions,
            tool_names=self.tool_names,
            max_iterations=settings.max_iterations_default,
        )

        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={"temperature": temperature},
            safety_settings=safety_settings,
            system_instruction=system_instruction,
        )

    def _parse_output(self, text: str) -> Tuple[str, str, str, str]:
        clean_text = re.sub(r"[\u4e00-\u9fff\W_]*call:?", "", text).strip()

        final_match = re.search(r"Final Answer:\s*(.*)", text, re.DOTALL)
        final_answer = final_match.group(1).strip() if final_match else ""

        if "Observation:" in text:
            text = text.split("Observation:")[0].strip()

        thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|\nFinal Answer:|$)", text, re.DOTALL)
        action_match = re.search(r"Action:\s*([a-zA-Z0-9_]+)", text)
        input_match = re.search(r"Action Input:\s*(.*)", text, re.DOTALL)

        thought = thought_match.group(1).strip() if thought_match else ""
        action = action_match.group(1).strip() if action_match else ""
        action_input = input_match.group(1).strip() if input_match else ""

        if not action:
            for tool_name in TOOL_MAP.keys():
                if tool_name in clean_text:
                    action = tool_name
                    input_sub = re.search(r"Action Input:\s*(.*)", clean_text, re.DOTALL)
                    if input_sub:
                        action_input = input_sub.group(1).strip()
                    break

        return thought, action, action_input, final_answer

    def run(self, request: AgentRequest, timeout_seconds: float = 60.0) -> AgentResponse:
        start_time = time.perf_counter()
        query = request.query
        session_id = request.session_id
        limit = request.max_iterations or settings.max_iterations_default
        steps: List[ThoughtStep] = []
        scratchpad = ""

        # Retrieve prior session turns if session_id is provided
        history_prefix = ""
        if session_id:
            state = session_store.get_or_create(session_id)
            history_prefix = state.format_history_for_prompt()

        for iteration in range(1, limit + 1):
            elapsed = time.perf_counter() - start_time
            if elapsed >= timeout_seconds:
                latency = round(elapsed * 1000, 2)
                fallback = (
                    f"Execution timed out after {timeout_seconds}s. "
                    f"Last observation: {steps[-1].observation if steps else 'None'}"
                )
                if session_id:
                    session_store.record_turn(session_id, query, fallback, steps)
                return AgentResponse(
                    query=query,
                    session_id=session_id,
                    answer=fallback,
                    steps=steps if request.return_trace else [],
                    iterations=iteration - 1,
                    latency_ms=latency,
                    stop_reason="timeout",
                )

            full_prompt = f"{history_prefix}Question: {query}\n{scratchpad}"
            response = self.model.generate_content(full_prompt)
            output_text = extract_response_text(response)

            thought, action, action_input, final_answer = self._parse_output(output_text)

            if action and action in TOOL_MAP:
                tool_fn = TOOL_MAP[action]
                clean_input = action_input.strip("\"' \n")
                try:
                    observation = tool_fn.run(clean_input)
                except Exception as e:
                    observation = f"Tool Execution Error: {str(e)}"

                step_record = ThoughtStep(
                    step=iteration,
                    thought=thought,
                    action=action,
                    action_input=clean_input,
                    observation=str(observation),
                )
                steps.append(step_record)

                scratchpad += (
                    f"Thought: {thought}\n"
                    f"Action: {action}\n"
                    f"Action Input: {clean_input}\n"
                    f"Observation: {observation}\n"
                )
                continue

            answer_to_return = final_answer or output_text
            if answer_to_return:
                latency = round((time.perf_counter() - start_time) * 1000, 2)
                if session_id:
                    session_store.record_turn(session_id, query, answer_to_return, steps)
                return AgentResponse(
                    query=query,
                    session_id=session_id,
                    answer=answer_to_return,
                    steps=steps if request.return_trace else [],
                    iterations=iteration,
                    latency_ms=latency,
                    stop_reason="final_answer",
                )

        latency = round((time.perf_counter() - start_time) * 1000, 2)
        fallback_answer = (
            f"Agent reached the maximum iteration limit of {limit}. "
            f"Last observation: {steps[-1].observation if steps else 'None'}"
        )
        if session_id:
            session_store.record_turn(session_id, query, fallback_answer, steps)
        return AgentResponse(
            query=query,
            session_id=session_id,
            answer=fallback_answer,
            steps=steps if request.return_trace else [],
            iterations=limit,
            latency_ms=latency,
            stop_reason="max_iterations",
        )