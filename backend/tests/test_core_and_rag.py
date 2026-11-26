import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.llm.prompt import build_prompt
from app.main import app
from app.memory.manager import MemoryManager
from app.rag.bm25_index import BM25Index
from app.rag.chunker import ChunkingCancelled, chunk_text
from app.rag.rrf import reciprocal_rank_fusion
from app.schemas.retrieval import RetrievedChunk
from app.services.document_service import clear_all_documents, delete_documents, sanitize_filename
from app.utils.text import clean_text


class TestQueryXModules(unittest.TestCase):
    def test_clean_text_normalizes_whitespace(self):
        raw = "Hello\tworld  here \r\n\r\n\r\nNext line  "
        self.assertEqual(clean_text(raw), "Hello world here\n\nNext line")

    def test_chunk_text_splits_and_respects_cancel(self):
        text = "Paragraph one. " * 100
        chunks = chunk_text(text)
        self.assertGreater(len(chunks), 1)

        with self.assertRaises(ChunkingCancelled):
            chunk_text(text, should_cancel=lambda: True)

    def test_reciprocal_rank_fusion_merges_without_mutation(self):
        c1 = RetrievedChunk(score=0.9, document_id="d1", filename="a.pdf", chunk_id=1, text="alpha")
        c2 = RetrievedChunk(score=0.8, document_id="d2", filename="b.pdf", chunk_id=1, text="beta")
        c1_dup = RetrievedChunk(score=0.5, document_id="d1", filename="a.pdf", chunk_id=1, text="alpha")

        fused = reciprocal_rank_fusion([c1, c2], [c1_dup])
        self.assertEqual(fused[0].document_id, "d1")
        self.assertEqual(c1.score, 0.9)
        self.assertNotEqual(fused[0].score, 0.9)

    def test_bm25_search_filters_and_does_not_mutate_metadata(self):
        idx = BM25Index()
        chunk_a = RetrievedChunk(score=0.0, document_id="doc1", filename="a.pdf", chunk_id=1, text="python fastapi qdrant")
        chunk_b = RetrievedChunk(score=0.0, document_id="doc2", filename="b.pdf", chunk_id=1, text="docker nginx container")

        fake_client = MagicMock()
        fake_client.scroll.return_value = (
            [
                MagicMock(payload=chunk_a.model_dump()),
                MagicMock(payload=chunk_b.model_dump()),
            ],
            None,
        )

        with patch("app.rag.bm25_index.get_qdrant_client", return_value=fake_client):
            idx.rebuild()

        results = idx.search("python fastapi", limit=5)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].document_id, "doc1")
        self.assertGreaterEqual(results[0].score, 0.0)
        # Stored metadata score must remain untouched
        self.assertEqual(idx.metadata[0].score, 0.0)

        filtered = idx.search("python fastapi", limit=5, document_ids=["doc2"])
        self.assertEqual(filtered, [])

    def test_sanitize_filename_strips_path_traversal(self):
        self.assertEqual(sanitize_filename("../../etc/passwd.pdf"), "passwd.pdf")
        self.assertEqual(sanitize_filename(None), "document.pdf")

    def test_clear_all_documents_wipes_qdrant_and_bm25(self):
        fake_client = MagicMock()
        with patch("app.services.document_service.get_qdrant_client", return_value=fake_client), \
             patch("app.services.document_service.bm25_index.clear") as mock_clear:
            result = clear_all_documents()

        self.assertEqual(result, {"cleared": True})
        fake_client.delete.assert_called_once()
        mock_clear.assert_called_once()

    def test_delete_documents_deletes_unique_ids(self):
        fake_client = MagicMock()
        with patch("app.services.document_service.get_qdrant_client", return_value=fake_client), \
             patch("app.services.document_service.bm25_index.rebuild") as mock_rebuild:
            result = delete_documents(["doc-1", "doc-1", "doc-2"])

        self.assertEqual(result, {"deleted": 2})
        fake_client.delete.assert_called_once()
        mock_rebuild.assert_called_once()

    def test_memory_and_prompt_builder(self):
        mgr = MemoryManager()
        sid = "test-session-1"
        mgr.add_user(sid, "Hi")
        mgr.add_assistant(sid, "Hello")
        history = mgr.history(sid, limit=2)
        self.assertEqual(len(history), 2)

        chunk = RetrievedChunk(score=0.9, document_id="d1", filename="doc.pdf", chunk_id=1, text="Relevant fact.")
        prompt = build_prompt("What is the fact?", history, [chunk])
        self.assertIn("Relevant fact.", prompt)
        self.assertIn("What is the fact?", prompt)

    def test_fastapi_routes_registered(self):
        paths = {route.path for route in app.routes}
        for expected in (
            "/",
            "/health",
            "/api/upload",
            "/api/upload/stream",
            "/api/upload/cancel/{upload_id}",
            "/api/chat",
            "/api/chat/stream",
            "/api/search",
            "/api/documents",
            "/api/documents/{document_id}",
            "/api/documents/clear",
        ):
            self.assertIn(expected, paths)


if __name__ == "__main__":
    unittest.main()
