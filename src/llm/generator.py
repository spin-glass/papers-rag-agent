"""Text generation using OpenAI GPT models with LangSmith tracing."""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langsmith import traceable
from config import get_openai_api_key, get_llm_provider


@traceable
def generate_answer(prompt: str, question: str = None) -> str:
    """
    Generate answer using OpenAI GPT model with LangSmith tracing.

    Args:
        prompt: Complete prompt including instructions and context
        question: Optional original question for language detection

    Returns:
        Generated text response

    Raises:
        Exception: If text generation fails
    """
    provider = get_llm_provider()
    if provider != "openai":
        raise ValueError(f"Unsupported LLM provider: {provider}")

    api_key = get_openai_api_key()

    # Initialize ChatOpenAI with LangSmith tracing support
    llm = ChatOpenAI(
        model="gpt-4o-mini",  # Cost-efficient model
        temperature=0.1,  # Low temperature for factual responses
        max_tokens=1500,  # Reasonable limit for responses
        openai_api_key=api_key,
    )

    # Add language instruction if question is provided
    final_prompt = prompt
    if question:
        from utils.language_utils import get_response_language_instruction

        language_instruction = get_response_language_instruction(question)
        final_prompt = final_prompt + language_instruction

    try:
        # Use LangChain's ChatOpenAI for automatic LangSmith tracing
        message = HumanMessage(content=final_prompt)
        response = llm.invoke([message])

        return response.content.strip()

    except Exception as e:
        # Don't suppress exceptions - let them bubble up
        raise Exception(f"Failed to generate answer: {str(e)}") from e
