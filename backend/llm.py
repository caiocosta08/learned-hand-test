import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def call_llm(
    messages: list[dict],
    model: str = "gpt-4o",
    temperature: float = 0,
) -> str:
    """Call the OpenAI API and return the response content."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content
