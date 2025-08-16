from abc import ABC, abstractmethod

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
    
