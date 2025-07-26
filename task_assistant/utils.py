# In task_assistant/utils.py

import re


def normalize_text(text: str) -> str:
    """
    Normalizes text by standardizing newlines and trimming whitespace.

    Args:
        text: The input string.

    Returns:
        The normalized string.
    """
    # Replace Windows-style newlines (\r\n) with standard newlines (\n)
    normalized_text = text.replace('\r\n', '\n')

    # Trim leading/trailing whitespace from the whole text
    normalized_text = normalized_text.strip()

    return normalized_text