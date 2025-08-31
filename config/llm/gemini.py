from dataclasses import dataclass
import os
from typing import Optional, Mapping


@dataclass(frozen=True)
class GeminiSettings:
    api_key: str

    @staticmethod
    def from_env(env: Optional[Mapping[str, str]] = None) -> "GeminiSettings":
        if env is None:
            env = os.environ
        key = (env.get("GEMINI_API_KEY") or "").strip()
        if not key:
            raise ValueError("GEMINI_API_KEY environment variable not found or empty")
        return GeminiSettings(api_key=key)