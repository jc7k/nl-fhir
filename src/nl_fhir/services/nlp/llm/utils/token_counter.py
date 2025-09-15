"""
Token counting utilities for LLM processing
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TokenCounter:
    """Utility class for counting tokens in text"""

    def __init__(self):
        self.encoding = None
        self._initialize_tokenizer()

    def _initialize_tokenizer(self):
        """Initialize tokenizer for token counting"""
        try:
            import tiktoken
            self.encoding = tiktoken.encoding_for_model("gpt-4")
            logger.info("Token counter initialized with tiktoken")
        except ImportError:
            logger.warning("tiktoken not available - using approximate token counting")
            self.encoding = None

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            # Rough approximation: 1 token ≈ 4 characters
            return len(text) // 4

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str = "gpt-4o-mini") -> float:
        """Estimate cost based on token usage"""
        # Pricing as of 2024 (prices per 1K tokens)
        pricing = {
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002}
        }

        if model not in pricing:
            model = "gpt-4o-mini"  # Default fallback

        input_cost = (input_tokens / 1000) * pricing[model]["input"]
        output_cost = (output_tokens / 1000) * pricing[model]["output"]

        return input_cost + output_cost

    def check_token_limit(self, text: str, max_tokens: int = 8000) -> bool:
        """Check if text exceeds token limit"""
        token_count = self.count_tokens(text)
        return token_count <= max_tokens

    def truncate_to_limit(self, text: str, max_tokens: int = 8000) -> str:
        """Truncate text to stay within token limit"""
        if self.check_token_limit(text, max_tokens):
            return text

        if self.encoding:
            tokens = self.encoding.encode(text)
            truncated_tokens = tokens[:max_tokens]
            return self.encoding.decode(truncated_tokens)
        else:
            # Rough truncation
            max_chars = max_tokens * 4
            return text[:max_chars]