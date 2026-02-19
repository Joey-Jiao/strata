from ..configs import ConfigService
from .entity import ClientConfig
from .clients.anthropic import AnthropicClient
from .clients.deepseek import DeepSeekClient
from .clients.openai import OpenAIClient

_CLIENT_REGISTRY = {
    "openai": OpenAIClient,
    "deepseek": DeepSeekClient,
    "anthropic": AnthropicClient,
}


class LLMService:
    def __init__(self, config: ConfigService):
        self._config = {}
        provider_config = config.get("base.llm", {})

        if not provider_config:
            return

        for provider_name, _ in provider_config.items():
            self._config[provider_name] = {}
            model_config = config.get(f"base.llm.{provider_name}", {})

            if not model_config:
                continue

            for model_name, _ in model_config.items():
                api_key = config.get(f"{provider_name}_api_key", default=None)
                endpoint = config.get(f"base.llm.{provider_name}.{model_name}.endpoint", default=None)
                timeout = config.get(f"base.llm.{provider_name}.{model_name}.timeout", default=30)

                max_tokens = config.get(f"base.llm.{provider_name}.{model_name}.max_tokens", default=None)

                client_config = ClientConfig(
                    api_key=api_key,
                    endpoint=endpoint,
                    timeout=timeout,
                    max_tokens=max_tokens,
                    model=model_name,
                    provider=provider_name,
                )
                self._config[provider_name][model_name] = client_config

    def ls_providers(self):
        return list(self._config.keys())

    def ls_models(self, provider: str):
        return list(self._config.get(provider, {}).keys())

    def get_client_config(self, provider: str, model: str) -> ClientConfig:
        return self._config.get(provider, {}).get(model)

    def get_client(self, provider: str, model: str):
        client_config = self.get_client_config(provider, model)
        if not client_config:
            return None
        client_cls = _CLIENT_REGISTRY.get(provider)
        if not client_cls:
            raise ValueError(f"Unknown LLM provider: {provider}")
        return client_cls(client_config)
