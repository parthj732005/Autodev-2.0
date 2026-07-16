from abc import ABC, abstractmethod

import httpx
from openai import AsyncOpenAI


class ModelProvider(ABC):
    @abstractmethod
    async def complete(self, system: str, user: str) -> str:
        pass


class OpenAIProvider(ModelProvider):
    def __init__(self, api_key: str, model: str = "gpt-5.4-mini"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def complete(self, system: str, user: str) -> str:
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
            max_tokens=8192,
        )
        return resp.choices[0].message.content.strip()


class AnthropicProvider(ModelProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-5"):
        from anthropic import AsyncAnthropic
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def complete(self, system: str, user: str) -> str:
        resp = await self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return resp.content[0].text.strip()


class GroqProvider(ModelProvider):
    """Groq cloud — free tier, OpenAI-compatible, very fast."""

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        self.model = model

    async def complete(self, system: str, user: str) -> str:
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
            max_tokens=8000,
        )
        return resp.choices[0].message.content.strip()


class HuggingFaceProvider(ModelProvider):
    """HuggingFace Inference Router — OpenAI-compatible endpoint."""

    def __init__(self, api_key: str, model: str = "Qwen/Qwen3-Coder-30B-A3B-Instruct"):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://router.huggingface.co/v1",
        )
        self.model = model

    async def complete(self, system: str, user: str) -> str:
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
            max_tokens=4096,
        )
        return resp.choices[0].message.content.strip()


class OllamaProvider(ModelProvider):
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def complete(self, system: str, user: str) -> str:
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "stream": False,
                    "options": {"temperature": 0.2},
                },
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"].strip()


def get_provider(settings: dict) -> ModelProvider:
    provider = settings.get("provider", "openai")

    if provider == "openai":
        key = settings.get("openai_api_key", "")
        if not key:
            raise ValueError("OpenAI API key is not configured. Go to Settings.")
        return OpenAIProvider(api_key=key, model=settings.get("openai_model", "gpt-4o-mini"))

    if provider == "anthropic":
        key = settings.get("anthropic_api_key", "")
        if not key:
            raise ValueError("Anthropic API key is not configured. Go to Settings.")
        return AnthropicProvider(api_key=key, model=settings.get("anthropic_model", "claude-sonnet-4-6"))

    if provider == "groq":
        key = settings.get("groq_api_key", "")
        if not key:
            raise ValueError("Groq API key is not configured. Go to Settings.")
        return GroqProvider(api_key=key, model=settings.get("groq_model", "llama-3.3-70b-versatile"))

    if provider == "huggingface":
        key = settings.get("huggingface_api_key", "")
        if not key:
            raise ValueError("HuggingFace API key is not configured. Go to Settings.")
        return HuggingFaceProvider(api_key=key, model=settings.get("huggingface_model", "Qwen/Qwen2.5-Coder-7B-Instruct"))

    if provider == "ollama":
        return OllamaProvider(
            base_url=settings.get("ollama_base_url", "http://localhost:11434"),
            model=settings.get("ollama_model", "qwen2.5-coder:7b"),
        )

    raise ValueError(f"Unknown provider: {provider}")
