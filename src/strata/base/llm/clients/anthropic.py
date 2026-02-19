import time

from anthropic import Anthropic

from .base import BaseClient
from ..entity import ClientConfig, LLMMessage, LLMResponse
from ..adapters import AnthropicAdapter


class AnthropicClient(BaseClient):
    def __init__(self, config: ClientConfig):
        self.config = config
        self.adapter = AnthropicAdapter
        self.client = Anthropic(api_key=config.api_key, timeout=config.timeout)

    def chat(self, messages: list[LLMMessage]) -> LLMResponse:
        formatted = self.adapter.to_chat_messages(messages)

        kwargs = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens or 4096,
            "messages": formatted["messages"],
        }
        if formatted["system"]:
            kwargs["system"] = formatted["system"]

        start = time.perf_counter()
        resp = self.client.messages.create(**kwargs)
        duration = time.perf_counter() - start

        return LLMResponse(
            message=self.adapter.extract_chat_message(resp),
            usage=self.adapter.extract_usage(resp),
            duration=duration,
        )
