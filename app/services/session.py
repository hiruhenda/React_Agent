from typing import Dict, List
from pydantic import BaseModel, Field
from app.schemas.agent import ThoughtStep


class SessionTurn(BaseModel):
    query: str
    answer: str
    steps: List[ThoughtStep] = Field(default_factory=list)


class SessionState(BaseModel):
    session_id: str
    turns: List[SessionTurn] = Field(default_factory=list)

    def format_history_for_prompt(self) -> str:
        if not self.turns:
            return ""
        lines = ["Previous Conversation Context:"]
        for turn in self.turns:
            lines.append(f"User: {turn.query}")
            lines.append(f"Assistant: {turn.answer}")
        return "\n".join(lines) + "\n\n"


class SessionStore:
    def __init__(self):
        self._store: Dict[str, SessionState] = {}

    def get_or_create(self, session_id: str) -> SessionState:
        if session_id not in self._store:
            self._store[session_id] = SessionState(session_id=session_id)
        return self._store[session_id]

    def record_turn(self, session_id: str, query: str, answer: str, steps: List[ThoughtStep]):
        session = self.get_or_create(session_id)
        session.turns.append(SessionTurn(query=query, answer=answer, steps=steps))

    def clear(self, session_id: str):
        if session_id in self._store:
            del self._store[session_id]


# Global session registry singleton
session_store = SessionStore()
