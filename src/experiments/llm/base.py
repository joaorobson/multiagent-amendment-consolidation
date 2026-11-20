from abc import ABC, abstractmethod
from typing import Any


class BaseLLMClient(ABC):
    def __init__(self, sdk_client: Any) -> None:
        self.sdk_client = sdk_client

    @abstractmethod
    def call(self, prompt: str, **kwargs: Any) -> str:
        """Send a prompt to the underlying LLM SDK and return the text response."""
        ...