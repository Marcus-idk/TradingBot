from google import genai
from google.genai import types
from typing import Optional
from ..base import LLMProvider


class GeminiProvider(LLMProvider):
    
    def __init__(self, api_key: str, model_name: str, temperature: Optional[float] = None, **kwargs):
        super().__init__(api_key, **kwargs)
        self.model_name = model_name
        self.temperature = temperature
        self.client = genai.Client(api_key=api_key)
    
    async def generate(self, prompt: str) -> str:
        config = types.GenerateContentConfig(
            temperature=self.temperature,
            candidate_count=1,
            **self.config
        )
        
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config
        )
        
        return response.text
    
    async def validate_connection(self) -> bool:
        try:
            await self.client.aio.models.list()
            return True
        except Exception:
            return False
