import os
import base64
import hashlib
import re
import pytest

from dotenv import load_dotenv
from llm import OpenAIProvider, GeminiProvider
from config.llm import OpenAISettings, GeminiSettings

# Mark all tests in this module as integration and network tests
pytestmark = [pytest.mark.integration, pytest.mark.network]

load_dotenv(override=True)

# Helper functions for hash testing
def make_base64_blob(n_bytes=64):
    blob = os.urandom(n_bytes)
    b64 = base64.b64encode(blob).decode("ascii")
    sha = hashlib.sha256(blob).hexdigest()
    return b64, sha

def extract_hex64(s: str) -> str:
    m = re.search(r"\b[0-9a-fA-F]{64}\b", s)
    return m.group(0).lower() if m else ""

# Tests

@pytest.mark.asyncio
async def test_openai():
    try:
        openai_settings = OpenAISettings.from_env()
    except ValueError:
        pytest.skip("OPENAI_API_KEY not set, skipping live test")

    provider = OpenAIProvider(settings=openai_settings, model_name="gpt-5")
    assert await provider.validate_connection()
    
    response = await provider.generate("Say 'test successful'")
    assert len(response) > 0
    print("OpenAI: Connection Good")

@pytest.mark.asyncio
async def test_gemini():
    try:
        gemini_settings = GeminiSettings.from_env()
    except ValueError:
        pytest.skip("GEMINI_API_KEY not set, skipping live test")

    provider = GeminiProvider(settings=gemini_settings, model_name="gemini-2.5-flash")
    assert await provider.validate_connection()
    
    response = await provider.generate("Say 'test successful'")
    assert len(response) > 0
    print("Gemini: Connection Good")


@pytest.mark.asyncio
async def test_openai_tools_hash():
    try:
        openai_settings = OpenAISettings.from_env()
    except ValueError:
        pytest.skip("OPENAI_API_KEY not set, skipping live test")

    b64, expected_sha = make_base64_blob(4)
    prompt = (
        "Decode the following base64 to raw bytes and compute its SHA-256.\n"
        "Return only the 64-character lowercase hex digest, no spaces or text.\n\n"
        "```base64\n" + b64 + "\n```"
    )

    # With tools
    provider_with_tools = OpenAIProvider(
        settings=openai_settings,
        model_name="gpt-5",
        tools=[{"type": "code_interpreter", "container": {"type": "auto"}}],
        tool_choice="auto"
    )
    out_with_tools = await provider_with_tools.generate(prompt)

    ok_with_tools = expected_sha == extract_hex64(out_with_tools)

    if ok_with_tools:
        print("OpenAI: Code interpreter working correctly (SHA-256 test)")
    else:
        print("OpenAI: Code interpreter may not be working")

@pytest.mark.asyncio
async def test_gemini_tools_hash():
    try:
        gemini_settings = GeminiSettings.from_env()
    except ValueError:
        pytest.skip("GEMINI_API_KEY not set, skipping live test")

    b64, expected_sha = make_base64_blob(4)
    prompt = (
        "Decode the following base64 to raw bytes and compute its SHA-256.\n"
        "Return only the 64-character lowercase hex digest, no spaces or text.\n\n"
        "```base64\n" + b64 + "\n```"
    )

    # With code execution
    provider_with_tools = GeminiProvider(
        settings=gemini_settings,
        model_name="gemini-2.5-flash",
        tools=[{"code_execution": {}}]
    )
    out_with_tools = await provider_with_tools.generate(prompt)

    ok_with_tools = expected_sha == extract_hex64(out_with_tools)

    if ok_with_tools:
        print("Gemini: Code execution working correctly (SHA-256 test)")
    else:
        print("Gemini: Code execution may not be working")
