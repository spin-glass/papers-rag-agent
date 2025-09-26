"""Chainlit application entry point."""

import sys
from pathlib import Path

import chainlit as cl

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from adapters.mock_agent import run_agent
from ui.components import render_citations, render_cornell, render_quiz


@cl.on_chat_start
async def on_chat_start():
    """Initialize the chat session with a greeting message."""
    await cl.Message(
        content=(
            "## Papers RAG Agent (MVP)\n\n"
            "こんにちは！論文に関する質問をしてください。\n"
            "回答と共に、Cornell Note、クイズ、引用文献を提供します。\n\n"
            "何について知りたいですか？"
        )
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """
    Handle incoming messages from users.
    
    Args:
        message: Chainlit message object containing user input
    """
    # Show thinking indicator
    async with cl.Step(name="Processing", type="run") as step:
        step.output = "エージェントが回答を生成しています..."

        # Call the mock agent
        result = run_agent(message.content)

    # Create the response content
    content_parts = [
        f"## 回答\n{result.answer}\n",
        render_cornell(result.cornell_note),
        render_quiz(result.quiz_items),
        render_citations(result.citations)
    ]

    # Combine all parts
    full_content = "\n".join(content_parts)

    # Send the response
    await cl.Message(content=full_content).send()


if __name__ == "__main__":
    import os

    # Set environment variable for running the app
    os.environ["CHAINLIT_HOST"] = "localhost"
    os.environ["CHAINLIT_PORT"] = "8000"

    # This is mainly for development/testing
    # In production, use: chainlit run src/ui/app.py
    print("To run the app, use: uv run chainlit run src/ui/app.py -w")
