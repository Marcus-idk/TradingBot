from dataclasses import dataclass
import os
from typing import Mapping
from config.retry import LLMRetryConfig, DEFAULT_LLM_RETRY


@dataclass(frozen=True)
class OpenAISettings:
    api_key: str
    retry_config: LLMRetryConfig = DEFAULT_LLM_RETRY

    @staticmethod
    def from_env(env: Mapping[str, str] | None = None) -> "OpenAISettings":
        if env is None:
            env = os.environ
        key = (env.get("OPENAI_API_KEY") or "").strip()
        if not key:
            raise ValueError("OPENAI_API_KEY environment variable not found or empty")
        return OpenAISettings(api_key=key)