"""Corrective RAG pipeline with HyDE."""


from models import AnswerResult
from pipelines.baseline import baseline_answer
from llm.hyde import hyde_rewrite
from config import get_support_threshold


def answer_with_correction(
    question: str, theta: float = None, index=None
) -> AnswerResult:
    """
    Generate answer using corrective RAG with HyDE fallback.

    Args:
        question: User question
        theta: Support threshold (uses environment default if None)
        index: Index to use for retrieval

    Returns:
        AnswerResult with answer or no-answer response
    """
    if theta is None:
        theta = get_support_threshold()

    # 1. Try baseline RAG first
    answer = baseline_answer(question, index)

    # 2. Check if support is sufficient
    if answer.support >= theta:
        return answer

    # 3. Try HyDE rewrite + baseline RAG
    try:
        hyde_query = hyde_rewrite(question)
        print(f"HyDE rewrite: {hyde_query[:100]}...")

        hyde_answer = baseline_answer(hyde_query, index)

        # 4. Check HyDE result support
        if hyde_answer.support >= theta:
            # Add HyDE attempt to the result
            hyde_attempt = {
                "type": "hyde",
                "query": hyde_query,
                "top_ids": hyde_answer.attempts[0]["top_ids"]
                if hyde_answer.attempts
                else [],
                "support": hyde_answer.support,
            }
            hyde_answer.attempts.append(hyde_attempt)
            return hyde_answer

    except Exception as e:
        print(f"Warning: HyDE failed: {e}")

    # 5. Return no-answer response
    all_attempts = answer.attempts.copy()
    if "hyde_answer" in locals():
        all_attempts.extend(hyde_answer.attempts)

    return no_answer(question, attempts=all_attempts)


def no_answer(question: str, attempts: list = None) -> AnswerResult:
    """
    Generate no-answer response with missing information hints.

    Args:
        question: Original question
        attempts: Previous attempts for context

    Returns:
        AnswerResult with no-answer template
    """
    if attempts is None:
        attempts = []

    # Analyze question to suggest missing information
    missing_elements = analyze_missing_elements(question)

    # Build no-answer response
    no_answer_text = (
        "この質問に答えるには、以下の情報が不足している可能性があります：\n\n"
    )

    for i, element in enumerate(missing_elements, 1):
        no_answer_text += f"{i}. {element}\n"

    no_answer_text += "\nより具体的な期間、手法名、データセット名などを含めて質問を再試行してください。"

    return AnswerResult(
        text=no_answer_text, citations=[], support=0.0, attempts=attempts
    )


def analyze_missing_elements(question: str) -> list:
    """
    Heuristic analysis to suggest missing information elements.

    Args:
        question: User question

    Returns:
        List of suggested missing information elements
    """
    missing_elements = []
    question_lower = question.lower()

    # Check for time period indicators
    time_indicators = [
        "year",
        "years",
        "年",
        "最近",
        "recent",
        "latest",
        "新しい",
        "古い",
        "2023",
        "2024",
        "2025",
        "since",
        "before",
        "after",
    ]
    has_time = any(indicator in question_lower for indicator in time_indicators)

    # Check for method/algorithm indicators
    method_indicators = [
        "algorithm",
        "method",
        "アルゴリズム",
        "手法",
        "model",
        "モデル",
        "approach",
        "technique",
        "framework",
        "architecture",
        "transformer",
        "bert",
        "gpt",
        "neural",
        "deep learning",
        "machine learning",
    ]
    has_method = any(indicator in question_lower for indicator in method_indicators)

    # Check for dataset indicators
    dataset_indicators = [
        "dataset",
        "data",
        "データセット",
        "データ",
        "benchmark",
        "corpus",
        "imagenet",
        "coco",
        "glue",
        "squad",
        "evaluation",
    ]
    has_dataset = any(indicator in question_lower for indicator in dataset_indicators)

    # Check for domain indicators
    domain_indicators = [
        "computer vision",
        "nlp",
        "natural language",
        "画像",
        "テキスト",
        "speech",
        "音声",
        "robotics",
        "ロボット",
        "medical",
        "医療",
    ]
    has_domain = any(indicator in question_lower for indicator in domain_indicators)

    # Suggest missing elements based on heuristics
    if not has_time:
        missing_elements.append("具体的な時期や年代（例：2023年以降、最近の研究など）")

    if not has_method:
        missing_elements.append(
            "特定の手法やアルゴリズム名（例：Transformer、BERT、CNNなど）"
        )

    if not has_dataset:
        missing_elements.append(
            "対象となるデータセットやベンチマーク（例：ImageNet、GLUE、CoCoなど）"
        )

    if not has_domain:
        missing_elements.append(
            "研究領域の詳細（例：コンピュータビジョン、自然言語処理、音声認識など）"
        )

    # Ensure we have at least some suggestions
    if not missing_elements:
        missing_elements = [
            "より具体的な研究分野や応用領域",
            "特定の技術的要件や制約条件",
            "比較対象となる既存手法",
        ]

    return missing_elements[:3]  # Limit to 3 suggestions
