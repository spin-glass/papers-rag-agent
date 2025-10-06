"""Graph service for streaming responses using LangGraph workflows."""

import asyncio
from typing import AsyncGenerator, Dict, Any
from retrieval.inmemory import InMemoryIndex


async def stream_message(
    question: str, index: InMemoryIndex
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Stream a response using LangGraph workflows.

    Args:
        question: User question
        index: RAG index to search

    Yields:
        Dict chunks for streaming response
    """
    try:
        # Import here to avoid circular imports
        from graphs.message_routing import process_message_with_routing

        # Show processing status
        yield {"type": "status", "text": "🔍 質問を処理中です...", "done": False}

        # Use LangGraph workflow for streaming in a thread to avoid blocking
        response = await asyncio.to_thread(
            process_message_with_routing, question, rag_index=index
        )

        # Show completion status
        yield {"type": "status", "text": "✅ 回答を生成中です...", "done": False}

        # Stream the response in chunks
        chunk_size = 50  # Characters per chunk
        for i in range(0, len(response), chunk_size):
            chunk = response[i : i + chunk_size]
            yield {
                "type": "content",
                "text": chunk,
                "done": i + chunk_size >= len(response),
            }
            await asyncio.sleep(0.01)  # Small delay for streaming effect

    except Exception as e:
        # Fallback to simple error response
        error_msg = f"エラーが発生しました: {str(e)}"
        yield {"type": "error", "text": error_msg, "done": True}
