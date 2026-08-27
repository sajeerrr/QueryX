from langchain_text_splitters import RecursiveCharacterTextSplitter

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


def chunk_text(text: str) -> list[str]:
    """
    Split text into overlapping chunks.
    """
    return _splitter.split_text(text)