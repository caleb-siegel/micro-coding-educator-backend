import os
import logging
from .base import BaseLLMProvider
from .gemini import GeminiProvider
from .anthropic import AnthropicProvider

logger = logging.getLogger(__name__)

def get_llm_provider() -> BaseLLMProvider:
    """Factory method that returns the active LLM provider.
    Set LLM_PROVIDER=anthropic in environment variables to switch to Claude.
    Defaults to Gemini.
    """
    provider_name = os.getenv("LLM_PROVIDER", "gemini").strip().lower()

    if provider_name == "anthropic":
        logger.info("Initializing Anthropic Claude LLM Provider")
        return AnthropicProvider()

    logger.info("Initializing Gemini LLM Provider (Default)")
    return GeminiProvider()
