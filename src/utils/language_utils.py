import re


def is_japanese_text(text: str) -> bool:
    """
    Check if text contains Japanese characters.

    Args:
        text: Input text to check

    Returns:
        True if text contains Japanese characters (hiragana, katakana, kanji)
    """
    # Japanese character ranges:
    # Hiragana: U+3040-U+309F
    # Katakana: U+30A0-U+30FF
    # Kanji: U+4E00-U+9FAF
    japanese_pattern = r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]"
    return bool(re.search(japanese_pattern, text))


def get_response_language_instruction(question: str) -> str:
    """
    Get language instruction based on question language.

    Args:
        question: User question

    Returns:
        Language instruction to add to prompt
    """
    if is_japanese_text(question):
        return "\n\nIMPORTANT: Please respond in Japanese (日本語で回答してください)."
    else:
        return ""
