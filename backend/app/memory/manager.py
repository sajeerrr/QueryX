from app.memory.store import memory_store


class MemoryManager:

    def add_user(self, session_id, message):

        memory_store.add(
            session_id,
            "user",
            message,
        )

    def add_assistant(self, session_id, message):

        memory_store.add(
            session_id,
            "assistant",
            message,
        )

    def history(
        self,
        session_id,
        limit=6,
    ):

        return memory_store.get(session_id)[-limit:]


memory_manager = MemoryManager()