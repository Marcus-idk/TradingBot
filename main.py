import asyncio
import os
from dotenv import load_dotenv
from llm import OpenAIProvider, GeminiProvider

load_dotenv(override=True)

async def main():
    # Test OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        openai = OpenAIProvider(api_key=openai_key, model_name="o3", temperature=1)
        response = await openai.generate("are u able to access the web, and use native tool calling?")
        print(f"OpenAI: {response}")
    
    # Test Gemini
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        gemini = GeminiProvider(api_key=gemini_key, model_name="gemini-2.5-flash", temperature=0.7)
        response = await gemini.generate("r u able to access the web, and use native tool calling?")
        print(f"Gemini: {response}")

if __name__ == "__main__":
    asyncio.run(main())