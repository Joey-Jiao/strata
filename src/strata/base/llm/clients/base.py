from abc import ABC, abstractmethod

from ..entity import LLMMessage, LLMResponse


class BaseClient(ABC):
    @abstractmethod
    def chat(self, messages: list[LLMMessage]) -> LLMResponse:
        pass
