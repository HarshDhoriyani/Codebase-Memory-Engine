import os
from groq import Groq
from typing import AsyncGenerator
from .prompts import get_prompt


def get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set. Add it to your .env file.")
    return Groq(api_key=api_key)


def is_available() -> bool:
    return bool(os.getenv("GROQ_API_KEY"))


async def stream_explanation(
    context: str,
    intent_type: str,
    model: str = "llama-3.1-8b-instant",
    max_tokens: int = 1024,
) -> AsyncGenerator[str, None]:
    try:
        client = get_client()
        system_prompt = get_prompt(intent_type)

        stream = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            stream=True,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": context},
            ],
        )

        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content

    except ValueError as e:
        yield f"Error: {str(e)}"
    except Exception as e:
        yield f"Error: {str(e)}"


async def get_explanation(
    context: str,
    intent_type: str,
    model: str = "llama-3.1-8b-instant",
    max_tokens: int = 1024,
) -> str:
    try:
        client = get_client()
        system_prompt = get_prompt(intent_type)

        response = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            stream=False,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": context},
            ],
        )
        return response.choices[0].message.content

    except ValueError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"