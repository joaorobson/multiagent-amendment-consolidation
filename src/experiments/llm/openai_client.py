
from openai import OpenAI
from typing import Any, Optional, Type, TypeVar
from pydantic import BaseModel

from .base import BaseLLMClient

T = TypeVar("T", bound=BaseModel)


class OpenAIClient(BaseLLMClient):
    """
    Cliente OpenAI com Structured Outputs (Pydantic),
    configuração de geração e telemetria.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.0,
        seed: int = 42,
    ):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.temperature = temperature
        self.seed = seed

        self.call_count = 0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0

    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: Optional[Type[T]] = None,
    ) -> Any:

        self.call_count += 1

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        kwargs = {
            "model": self.model,
            "messages": messages,
            "seed": self.seed,
        }

        if response_format is not None:
            kwargs["response_format"] = response_format

        if self.temperature:
            kwargs["temperature"] = self.temperature

        res = self.client.chat.completions.parse(**kwargs)

        self._registrar_tokens(res)

        message = res.choices[0].message

        if message.refusal:
            raise ValueError(f"Model refusal: {message.refusal}")

        if response_format is not None:
            return message.parsed

        return message.content

    def _registrar_tokens(self, completion: Any) -> None:
        if completion.usage:
            self.total_prompt_tokens += completion.usage.prompt_tokens or 0
            self.total_completion_tokens += completion.usage.completion_tokens or 0

    def get_metrics(self) -> dict[str, int]:
        return {
            "calls": self.call_count,
            "prompt_tokens": self.total_prompt_tokens,
            "completion_tokens": self.total_completion_tokens,
            "total_tokens": (
                self.total_prompt_tokens + self.total_completion_tokens
            ),
        }
