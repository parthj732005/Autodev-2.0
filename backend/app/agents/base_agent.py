import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class AgentEvent:
    agent: str
    event: str   # started | log | completed | failed | retry
    message: str
    data: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "event": self.event,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp,
        }


_AUTH_ERROR_SIGNATURES = (
    "invalid_api_key",
    "invalid api key",
    "incorrect api key",
    "authenticationerror",
    "unauthorized",
    "401",
)

_MODEL_ERROR_SIGNATURES = (
    "model_not_found",
    "does not exist",
    "not found",
    "notfounderror",
    "invalid model",
    "unknown model",
    "unsupported model",
    "has been decommissioned",
    "has been deprecated",
)


def _extract_status_code(exc: Exception) -> int | None:
    """Different SDKs expose the HTTP status differently (openai/anthropic put it
    directly on the exception; httpx.HTTPStatusError nests it under .response)."""
    code = getattr(exc, "status_code", None)
    if code is not None:
        return code
    response = getattr(exc, "response", None)
    if response is not None:
        return getattr(response, "status_code", None)
    return None


def _non_retryable_reason(exc: Exception) -> str | None:
    """Return 'auth' or 'model' if this error will never succeed on retry
    (wrong/expired key, or a wrong/deprecated model name), else None."""
    status_code = _extract_status_code(exc)
    signature = f"{type(exc).__name__} {exc}".lower()

    if status_code == 401 or any(s in signature for s in _AUTH_ERROR_SIGNATURES):
        return "auth"

    if status_code in (400, 404) and "model" in signature:
        if any(s in signature for s in _MODEL_ERROR_SIGNATURES):
            return "model"

    return None


class BaseAgent(ABC):
    name: str = "BaseAgent"
    max_retries: int = 2

    def __init__(self, provider, emit: Optional[Callable] = None):
        self.provider = provider
        self._emit = emit

    async def emit(self, event: str, message: str, data: dict = None):
        if self._emit:
            await self._emit(AgentEvent(self.name, event, message, data or {}))

    async def run(self, context: dict) -> dict:
        await self.emit("started", f"{self.name} started")
        start = time.time()

        for attempt in range(self.max_retries + 1):
            try:
                result = await self.execute(context)
                elapsed = round(time.time() - start, 1)
                await self.emit(
                    "completed",
                    f"{self.name} completed in {elapsed}s",
                    {"elapsed": elapsed},
                )
                return result
            except Exception as exc:
                reason = _non_retryable_reason(exc)
                if attempt < self.max_retries and reason is None:
                    await self.emit(
                        "retry",
                        f"{self.name} retrying ({attempt + 1}/{self.max_retries}): {exc}",
                    )
                    await asyncio.sleep(2**attempt)
                else:
                    if reason == "auth":
                        await self.emit(
                            "failed",
                            f"{self.name} failed: invalid or unauthorized API key — check Settings",
                        )
                    elif reason == "model":
                        await self.emit(
                            "failed",
                            f"{self.name} failed: the selected model does not exist or is no longer "
                            f"available — check the model name in Settings ({exc})",
                        )
                    else:
                        await self.emit("failed", f"{self.name} failed: {exc}")
                    raise

    @abstractmethod
    async def execute(self, context: dict) -> dict:
        pass
