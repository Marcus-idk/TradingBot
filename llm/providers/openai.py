from openai import AsyncOpenAI
from typing import Optional, Union, List, Dict
from ..base import LLMProvider
from config.llm import OpenAISettings


class OpenAIProvider(LLMProvider):
    
    def __init__(
        self,
        settings: OpenAISettings,
        model_name: str,
        temperature: Optional[float] = None,
        reasoning: Optional[Dict] = None,
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[Union[str, Dict]] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.settings = settings
        self.model_name = model_name
        self.temperature = temperature
        self.reasoning = reasoning
        self.tools = tools
        self.tool_choice = tool_choice
        self.client = AsyncOpenAI(api_key=settings.api_key)

    async def generate(self, prompt: str) -> str:
        args = {"model": self.model_name, "input": prompt, **self.config}

        if self.temperature is not None:
            args["temperature"] = self.temperature

        if self.reasoning is not None:
            args["reasoning"] = self.reasoning

        if self.tools:
            args["tools"] = self.tools

        if self.tool_choice:
            args["tool_choice"] = self.tool_choice

        resp = await self.client.responses.create(**args)
        return resp.output_text

    async def validate_connection(self) -> bool:
        try:
            await self.client.models.list()
            return True
        except Exception:
            return False
