"""Mock agent implementation for testing the UI."""

from models import AnswerPayload, Citation, CornellNote, QuizItem, QuizOption


def run_agent(user_query: str) -> AnswerPayload:
    """
    Mock implementation that returns fixed test data.

    Args:
        user_query: User's question (currently ignored in mock)

    Returns:
        Fixed AnswerPayload with sample data
    """
    # TODO: （RAG）選択/上位の論文PDFをダウンロード→テキスト化→分割→埋め込み→ベクトルDBへ upsert。doc_id=f"{arxiv_id}_v{version}" で重複回避。
    # Mock citations
    citations = [
        Citation(
            id="1",
            title="Attention Is All You Need",
            authors=["Vaswani", "Shazeer", "Parmar"],
            year=2017,
            url="https://arxiv.org/abs/1706.03762",
        ),
        Citation(
            id="2",
            title="BERT: Pre-training Deep Bidirectional Transformers",
            authors=["Devlin", "Chang", "Lee", "Toutanova"],
            year=2018,
            url="https://arxiv.org/abs/1810.04805",
        ),
    ]

    # Mock answer with inline citations
    answer = (
        "Transformerは自然言語処理に革命をもたらしました。"
        "アテンション機構[1]により、モデルは入力シーケンスの関連する部分に注目することができます。"
        "BERT[2]は双方向Transformerが文脈を両方向から理解する力を実証しました。"
    )

    # Mock Cornell note
    cornell_note = CornellNote(
        cue="Transformerアーキテクチャ",
        notes=(
            "- セルフアテンション機構が再帰処理を置き換え\n"
            "- マルチヘッドアテンションを持つエンコーダ・デコーダ構造\n"
            "- シーケンス情報のための位置エンコーディング\n"
            "- BERTは双方向文脈のためにエンコーダのみを使用"
        ),
        summary=(
            "Transformerはアテンション機構を使用してシーケンスを並列処理し、"
            "RNNよりも優れたパフォーマンスと高速な学習を可能にします。"
            "BERTは双方向エンコーディングでこれを拡張しました。"
        ),
    )

    # Mock quiz questions
    quiz_items = [
        QuizItem(
            question="Transformerアーキテクチャの主要な革新は何ですか？",
            options=[
                QuizOption(id="a", text="再帰的な接続"),
                QuizOption(id="b", text="セルフアテンション機構"),
                QuizOption(id="c", text="畳み込み層"),
                QuizOption(id="d", text="メモリネットワーク"),
            ],
            correct_answer="b",
        ),
        QuizItem(
            question="BERTは何の略語ですか？",
            options=[
                QuizOption(id="a", text="Basic Encoder Representation Transformer"),
                QuizOption(
                    id="b",
                    text="Bidirectional Encoder Representations from Transformers",
                ),
                QuizOption(id="c", text="Binary Embedding Recurrent Transformer"),
                QuizOption(id="d", text="Boosted Ensemble Regression Trees"),
            ],
            correct_answer="b",
        ),
    ]

    return AnswerPayload(
        answer=answer,
        cornell_note=cornell_note,
        quiz_items=quiz_items,
        citations=citations,
    )
