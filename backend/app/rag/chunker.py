from langchain_text_splitters import RecursiveCharacterTextSplitter


class ChunkingCancelled(Exception):
    """Raised when the user stops an in-progress document upload."""

# Production defaults
CHUNK_SIZE = 800
CHUNK_OVERLAP = 160

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=[
        "\n\n",
        "\n",
        ". ",
        "! ",
        "? ",
        " ",
        ""
    ]
)


def chunk_text(text: str, should_cancel=None) -> list[str]:
    """
    Split text into overlapping chunks.
    """
    if should_cancel and should_cancel():
        raise ChunkingCancelled()

    chunks = _splitter.split_text(text)

    if should_cancel and should_cancel():
        raise ChunkingCancelled()
    return chunks
