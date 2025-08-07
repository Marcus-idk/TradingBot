from openai import AsyncOpenAI
from typing import Optional
from ..base import LLMProvider

class OpenAIProvider(LLMProvider):
    
    def __init__(self, api_key: str, model_name: str, temperature: Optional[float] = None, **kwargs):
        super().__init__(api_key, **kwargs)
        self.model_name = model_name
        self.temperature = temperature
        self.client = AsyncOpenAI(api_key=api_key)
    
    async def generate(self, prompt: str) -> str:
        messages = [{"role": "user", "content": prompt}]
        
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
            **self.config
        )
        
        return response.choices[0].message.content
    
    async def validate_connection(self) -> bool:
        try:
            await self.client.models.list()
            return True
        except Exception:
            return False
    
    async def close(self) -> None:
        await self.client.aclose()
