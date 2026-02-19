from .base import BaseAdapter
from ..entity import LLMMessage, LLMUsage


class AnthropicAdapter(BaseAdapter):
    @classmethod
    def to_chat_messages(cls, messages: list[LLMMessage]):
        system = None
        chat_messages = []
        for msg in messages:
            if msg.role == "system":
                system = msg.content
            else:
                role = msg.role if msg.role in ("user", "assistant") else "user"
                chat_messages.append({"role": role, "content": msg.content})
        return {"system": system, "messages": chat_messages}

    @classmethod
    def extract_chat_message(cls, resp) -> LLMMessage:
        content = resp.content[0].text
        return LLMMessage.assistant(text=content)

    @classmethod
    def extract_usage(cls, resp) -> LLMUsage:
        usage = resp.usage
        cached = getattr(usage, "cache_read_input_tokens", 0) or 0
        return LLMUsage(
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cached_tokens=cached,
        )
