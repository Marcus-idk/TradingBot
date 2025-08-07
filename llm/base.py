from abc import ABC, abstractmethod
from typing import Optional

class LLMProvider(ABC):
    
    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.config = kwargs
    
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        pass
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        pass
    
    @abstractmethod
    async def close(self) -> None:
        pass