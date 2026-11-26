from collections import defaultdict
from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


class MemoryStore:
    """In-memory per-session conversation history."""

    def __init__(self):
        self.sessions: dict[str, list[Message]] = defaultdict(list)

    def add(self, session_id: str, role: str, content: str) -> None:
        self.sessions[session_id].append(Message(role=role, content=content))

    def get(self, session_id: str) -> list[Message]:
        return self.sessions.get(session_id, [])

    def clear(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)


class MemoryManager:
    """High-level helper for appending and reading recent conversation turns."""

    def __init__(self, store: MemoryStore | None = None):
        self._store = store or memory_store

    def add_user(self, session_id: str, message: str) -> None:
        self._store.add(session_id, "user", message)

    def add_assistant(self, session_id: str, message: str) -> None:
        self._store.add(session_id, "assistant", message)

    def history(self, session_id: str, limit: int = 6) -> list[Message]:
        return self._store.get(session_id)[-limit:]


memory_store = MemoryStore()
memory_manager = MemoryManager(memory_store)
