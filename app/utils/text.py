import re


def clean_text(text: str) -> str:
    """
    Clean and normalize extracted PDF text while preserving structure.
    """

    # Normalize Windows line endings
    text = text.replace("\r\n", "\n")

    # Replace tabs with spaces
    text = text.replace("\t", " ")

    # Collapse multiple spaces
    text = re.sub(r"[ ]{2,}", " ", text)

    # Remove spaces before newlines
    text = re.sub(r" +\n", "\n", text)

    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()