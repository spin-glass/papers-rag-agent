"""HyDE (Hypothetical Document Embeddings) implementation."""


from llm.generator import generate_answer


def hyde_rewrite(question: str) -> str:
    """
    Rewrite question as hypothetical document summary for better retrieval.

    HyDE approach: Generate a hypothetical answer/summary that would contain
    the information needed to answer the question, then use this as search query.

    Args:
        question: Original user question

    Returns:
        Hypothetical document summary for enhanced search

    Raises:
        Exception: If HyDE generation fails
    """
    prompt = f"""Generate a hypothetical academic paper summary (150-250 words) that would contain the information needed to answer this question: "{question}"

Write as if you're summarizing a research paper that directly addresses this question. Include:
- Technical terms and methodology keywords relevant to the question
- Specific concepts, algorithms, or approaches that would be discussed
- Academic language typical of research abstracts

Focus on creating searchable content rather than answering the question directly.

Question: {question}

Hypothetical paper summary:"""

    try:
        hypothetical_summary = generate_answer(prompt, question)
        return hypothetical_summary.strip()

    except Exception as e:
        # Don't suppress exceptions - let them bubble up
        raise Exception(f"Failed to generate HyDE query: {str(e)}") from e
