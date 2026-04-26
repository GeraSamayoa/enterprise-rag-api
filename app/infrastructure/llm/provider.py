import httpx

from app.core.config import settings


class LLMProviderError(Exception):
    pass


def _get_llm_config(provider: str) -> dict:
    if provider == "groq":
        return {
            "api_key": settings.llm_primary_api_key,
            "base_url": settings.llm_primary_base_url,
            "model": settings.llm_primary_model,
        }

    if provider == "openrouter":
        return {
            "api_key": settings.llm_secondary_api_key,
            "base_url": settings.llm_secondary_base_url,
            "model": settings.llm_secondary_model,
        }

    raise ValueError(f"Unsupported LLM provider: {provider}")


def generate_chat_completion(
    messages: list[dict],
    provider: str = "groq",
    model: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 700,
) -> str:
    config = _get_llm_config(provider)

    api_key = config["api_key"]
    base_url = config["base_url"]
    selected_model = model or config["model"]

    if not api_key or not base_url or not selected_model:
        raise LLMProviderError("LLM provider configuration is incomplete")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    if provider == "openrouter":
        if settings.openrouter_referer:
            headers["HTTP-Referer"] = settings.openrouter_referer

        if settings.openrouter_app_name:
            headers["X-Title"] = settings.openrouter_app_name
    payload = {
        "model": selected_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    url = f"{base_url.rstrip('/')}/chat/completions"

    with httpx.Client(timeout=60) as client:
        response = client.post(url, headers=headers, json=payload)

    if response.status_code >= 400:
        raise LLMProviderError(response.text)

    data = response.json()
    return data["choices"][0]["message"]["content"]