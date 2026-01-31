import punq

from .configs import ConfigService
from .llm.service import LLMService


class ApplicationContext:
    def __init__(self, container: punq.Container):
        self._container = container

    def resolve(self, cls):
        return self._container.resolve(cls)

    def register(self, *args, **kwargs):
        return self._container.register(*args, **kwargs)


def get_context(config_dir: str = "configs", env_path: str = ".env") -> ApplicationContext:
    container = punq.Container()

    config_service = ConfigService(config_dir=config_dir, env_path=env_path)
    container.register(ConfigService, instance=config_service)

    llm_service = LLMService(config=config_service)
    container.register(LLMService, instance=llm_service)

    return ApplicationContext(container)
