import asyncio
import random
import aiohttp
from typing import Optional
from datetime import datetime

from app.config import settings
from app.core.logging import logger


MODEL_PRICING = {
    "openai/gpt-4o-mini": {"in": 0.15, "out": 0.60},
    "openai/gpt-4o": {"in": 2.50, "out": 10.00},
    "anthropic/claude-3.5-haiku": {"in": 0.80, "out": 4.00},
    "anthropic/claude-sonnet-4": {"in": 3.00, "out": 15.00},
    "google/gemini-2.0-flash": {"in": 0.10, "out": 0.40},
    "google/gemini-2.5-flash": {"in": 0.15, "out": 0.60},
    "deepseek/deepseek-chat-v3": {"in": 0.14, "out": 0.28},
    "meta-llama/llama-3.1-8b-instruct": {"in": 0.02, "out": 0.04},
    "mistralai/mistral-7b-instruct": {"in": 0.03, "out": 0.05},
}

DEFAULT_MODELS = {
    "primary": "openai/gpt-4o-mini",
    "secondary": "google/gemini-2.0-flash",
    "fallback": "deepseek/deepseek-chat-v3",
}


class OpenRouterClient:
    """OpenRouter API client with budget controls and fallback."""

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_key: Optional[str] = None, budget_limit_usd: float = 100.0):
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.budget_limit = budget_limit_usd
        self.daily_spend = 0.0
        self.total_spend = 0.0
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def chat_completion(
        self,
        messages: list[dict],
        model: str = "openai/gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 100,
        fallback_models: Optional[list[str]] = None,
        **kwargs,
    ) -> Optional[str]:
        if not self.api_key:
            logger.warning("No OpenRouter API key configured")
            return None

        if self.total_spend >= self.budget_limit:
            logger.warning(
                "Budget limit reached", spent=self.total_spend, limit=self.budget_limit
            )
            return None

        models_to_try = [model] + (
            fallback_models or [DEFAULT_MODELS["secondary"], DEFAULT_MODELS["fallback"]]
        )

        for attempt_model in models_to_try:
            try:
                result = await self._make_request(
                    model=attempt_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=kwargs.get("top_p", 0.9),
                    frequency_penalty=kwargs.get("frequency_penalty", 0.3),
                    presence_penalty=kwargs.get("presence_penalty", 0.2),
                )

                if result and "choices" in result:
                    usage = result.get("usage", {})
                    cost = self._calculate_cost(attempt_model, usage)
                    self.daily_spend += cost
                    self.total_spend += cost

                    logger.info(
                        "LLM completion",
                        model=attempt_model,
                        cost=f"${cost:.4f}",
                        total=f"${self.total_spend:.2f}",
                    )
                    return result["choices"][0]["message"]["content"]

            except RateLimitError:
                logger.warning("Rate limited, trying next model", model=attempt_model)
                await asyncio.sleep(2)
                continue

            except Exception as e:
                logger.error("Model failed", model=attempt_model, error=str(e))
                continue

        return None

    async def _make_request(self, **kwargs) -> Optional[dict]:
        session = await self._get_session()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://gramscout.local",
            "X-Title": "GramScout",
            "Content-Type": "application/json",
        }

        payload = {
            "model": kwargs["model"],
            "messages": kwargs["messages"],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 100),
            "top_p": kwargs.get("top_p", 0.9),
            "frequency_penalty": kwargs.get("frequency_penalty", 0.3),
            "presence_penalty": kwargs.get("presence_penalty", 0.2),
        }

        async with session.post(
            f"{self.BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            if resp.status == 429:
                raise RateLimitError()
            if resp.status in (401, 403):
                raise AuthError()
            if resp.status >= 500:
                raise ServerError()
            return await resp.json()

    def _calculate_cost(self, model: str, usage: dict) -> float:
        pricing = MODEL_PRICING.get(model, {"in": 0, "out": 0})
        input_cost = (usage.get("prompt_tokens", 0) / 1_000_000) * pricing["in"]
        output_cost = (usage.get("completion_tokens", 0) / 1_000_000) * pricing["out"]
        return input_cost + output_cost

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()


class RateLimitError(Exception):
    pass


class AuthError(Exception):
    pass


class ServerError(Exception):
    pass


# Singleton
openrouter = OpenRouterClient()
