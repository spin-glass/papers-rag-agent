"""Chunked message sending for Chainlit."""

import chainlit as cl
from src.config import get_max_output_chars


async def send_long_message(content) -> None:
    """
    Send long content by splitting into chunks if necessary.

    Args:
        content: Content to send (str or cl.Message)
    """
    max_chars = get_max_output_chars()

    # Extract text content
    if isinstance(content, cl.Message):
        text = content.content
    else:
        text = str(content)

    # If content is short enough, send as-is
    if len(text) <= max_chars:
        if isinstance(content, cl.Message):
            await content.send()
        else:
            await cl.Message(content=text).send()
        return

    # Split into chunks
    chunks = split_text_smartly(text, max_chars)

    # Send chunks sequentially
    for i, chunk in enumerate(chunks):
        if i == 0:
            # First chunk - no prefix
            await cl.Message(content=chunk).send()
        else:
            # Subsequent chunks - add continuation indicator
            await cl.Message(content=f"（続き {i + 1}）\n\n{chunk}").send()


def split_text_smartly(text: str, max_chars: int) -> list:
    """
    Split text into chunks trying to preserve structure.

    Args:
        text: Text to split
        max_chars: Maximum characters per chunk

    Returns:
        List of text chunks
    """
    if len(text) <= max_chars:
        return [text]

    chunks = []
    remaining = text

    while remaining:
        if len(remaining) <= max_chars:
            chunks.append(remaining)
            break

        # Find good split point within max_chars
        chunk_end = max_chars

        # Try to split at paragraph boundary (double newline)
        last_para = remaining[:chunk_end].rfind("\n\n")
        if last_para > max_chars * 0.7:  # At least 70% of max_chars
            chunk_end = last_para + 2

        # Try to split at sentence boundary
        elif remaining[:chunk_end].rfind("。") > max_chars * 0.7:
            chunk_end = remaining[:chunk_end].rfind("。") + 1

        # Try to split at line boundary
        elif remaining[:chunk_end].rfind("\n") > max_chars * 0.7:
            chunk_end = remaining[:chunk_end].rfind("\n") + 1

        # Extract chunk
        chunk = remaining[:chunk_end].strip()
        chunks.append(chunk)

        # Update remaining text
        remaining = remaining[chunk_end:].strip()

    return chunks
