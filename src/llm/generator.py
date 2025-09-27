"""Text generation using OpenAI GPT models."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from openai import OpenAI
from config import get_openai_api_key, get_llm_provider


def generate_answer(prompt: str) -> str:
    """
    Generate answer using OpenAI GPT model.
    
    Args:
        prompt: Complete prompt including instructions and context
        
    Returns:
        Generated text response
        
    Raises:
        Exception: If text generation fails
    """
    provider = get_llm_provider()
    if provider != "openai":
        raise ValueError(f"Unsupported LLM provider: {provider}")
    
    api_key = get_openai_api_key()
    client = OpenAI(api_key=api_key)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Cost-efficient model
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for factual responses
            max_tokens=1500   # Reasonable limit for responses
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        # Don't suppress exceptions - let them bubble up
        raise Exception(f"Failed to generate answer: {str(e)}") from e
