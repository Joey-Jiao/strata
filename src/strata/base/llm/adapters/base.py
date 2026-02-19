from abc import ABC, abstractmethod

from ..entity import LLMMessage, LLMUsage


class BaseAdapter(ABC):
    @classmethod
    @abstractmethod
    def to_chat_messages(cls, messages: list[LLMMessage]):
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def extract_chat_message(cls, resp) -> LLMMessage:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def extract_usage(cls, resp) -> LLMUsage:
        raise NotImplementedError()
