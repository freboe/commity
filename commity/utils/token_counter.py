"""Token counting utilities for different LLM providers."""

from functools import lru_cache
from typing import Final

import tiktoken

# Constants
SAFETY_MARGIN: Final[float] = 1.1  # 10% safety margin for token counting


def _is_cjk_char(char: str) -> bool:
    """Check if a character is CJK (Chinese, Japanese, Korean)."""
    code_point = ord(char)
    return (
        0x4E00 <= code_point <= 0x9FFF  # CJK Unified Ideographs
        or 0x3400 <= code_point <= 0x4DBF  # CJK Unified Ideographs Extension A
        or 0x20000 <= code_point <= 0x2A6DF  # CJK Unified Ideographs Extension B
        or 0x2A700 <= code_point <= 0x2B73F  # CJK Unified Ideographs Extension C
        or 0x2B740 <= code_point <= 0x2B81F  # CJK Unified Ideographs Extension D
        or 0xF900 <= code_point <= 0xFAFF  # CJK Compatibility Ideographs
        or 0x2F800 <= code_point <= 0x2FA1F  # CJK Compatibility Ideographs Supplement
        or 0x3040 <= code_point <= 0x309F  # Hiragana
        or 0x30A0 <= code_point <= 0x30FF  # Katakana
        or 0xAC00 <= code_point <= 0xD7AF  # Hangul Syllables
    )


def _estimate_tokens(text: str, provider: str = "openai") -> int:
    """Estimate token count for different providers using character-based heuristics.

    This provides a balance between accuracy and performance:
    - For Gemini: Uses improved character estimation with CJK and code detection
    - For Ollama: Uses model-based estimation
    - Fallback: Conservative estimation for unknown providers

    Args:
    ----
        text: The text to estimate tokens for
        provider: The LLM provider (openai, gemini, ollama, openrouter)

    Returns:
    -------
        Estimated token count (without safety margin)

    """
    if not text:
        return 0

    text_length = len(text)

    # Detect if text is primarily code (high density of special chars and indentation)
    code_indicators = text.count("\n    ") + text.count("\n\t") + text.count("{") + text.count("}")
    is_code_heavy = code_indicators > text_length * 0.05  # More than 5% code indicators

    # Count CJK characters
    cjk_count = sum(1 for char in text if _is_cjk_char(char))
    cjk_ratio = cjk_count / text_length if text_length > 0 else 0

    # Provider-specific estimation
    if provider == "gemini":
        # Gemini uses SentencePiece tokenizer, different rules for different text types
        if cjk_ratio > 0.3:  # Primarily CJK text
            # CJK characters: ~1.8 tokens per character
            # Other characters: ~4 characters per token
            cjk_tokens = cjk_count * 1.8
            other_chars = text_length - cjk_count
            other_tokens = other_chars / 4.0
            return int(cjk_tokens + other_tokens)
        if is_code_heavy:
            # Code: ~3 characters per token (more special symbols)
            return int(text_length / 3.0)
        # Mixed English text: ~4 characters per token
        return int(text_length / 4.0)

    if provider == "ollama":
        # Ollama uses various models, use conservative estimation
        model_name_lower = provider.lower()
        if "llama" in model_name_lower or "mistral" in model_name_lower:
            # Similar to GPT tokenization
            return int(text_length / 4.0)
        # Conservative estimate
        return int(text_length / 3.5)

    # Conservative fallback for unknown providers
    if cjk_ratio > 0.3:
        return int(text_length / 2.0)  # Conservative for CJK
    return int(text_length / 3.5)  # Conservative for other text


@lru_cache(maxsize=10)
def get_tokenizer(model_name: str):
    """Get tiktoken tokenizer for the specified model.

    Args:
    ----
        model_name: OpenAI model name

    Returns:
    -------
        tiktoken Encoding object

    """
    try:
        return tiktoken.encoding_for_model(model_name)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str, model_name: str, provider: str = "openai") -> int:
    """Count tokens in text based on the provider.

    Args:
    ----
        text: The text to count tokens for
        model_name: The model name (used for OpenAI/OpenRouter)
        provider: The LLM provider (openai, gemini, ollama, openrouter)

    Returns:
    -------
        Estimated token count with 10% safety margin

    """
    if not text:
        return 0

    # Use tiktoken for OpenAI and OpenRouter (accurate)
    if provider in ("openai", "openrouter"):
        try:
            tokenizer = get_tokenizer(model_name)
            token_count = len(tokenizer.encode(text))
        except Exception:
            # Fallback to estimation if tiktoken fails
            token_count = _estimate_tokens(text, provider)
    else:
        # Use estimation for other providers (Gemini, Ollama, etc.)
        token_count = _estimate_tokens(text, provider)

    # Apply safety margin to avoid edge cases
    return int(token_count * SAFETY_MARGIN)
