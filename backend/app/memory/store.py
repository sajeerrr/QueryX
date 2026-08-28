from collections import defaultdict

from app.memory.models import Message


class MemoryStore:

    def __init__(self):
        self.sessions = defaultdict(list)

    def add(self, session_id: str, role: str, content: str):

        self.sessions[session_id].append(
            Message(
                role=role,
                content=content,
            )
        )

    def get(self, session_id: str):

        return self.sessions.get(session_id, [])

    def clear(self, session_id: str):

        self.sessions.pop(session_id, None)


memory_store = MemoryStore()