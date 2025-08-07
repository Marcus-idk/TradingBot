"""
LLM module for TradingBot.
Provides clean API for various LLM providers.
"""

from .base import LLMProvider
from .providers.openai import OpenAIProvider
from .providers.gemini import GeminiProvider

__all__ = [
    'LLMProvider',
    'OpenAIProvider', 
    'GeminiProvider'
]

__version__ = "1.0.0"