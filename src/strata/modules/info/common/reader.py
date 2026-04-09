from strata.base.configs import ConfigService


class InfoReader:
    def __init__(self, config: ConfigService):
        self._config = config

    def about(self) -> str:
        return self._config.get("info.context.about", "")

    def identity(self) -> dict:
        return self._config.get("info.context.identity", {})

    def workspace(self) -> dict:
        return self._config.get("info.context.workspace", {})

    def hosts(self) -> dict:
        return self._config.get("info.context.hosts", {})

    def conventions(self) -> dict:
        return self._config.get("info.conventions", {})

    def reading(self) -> dict:
        return self._config.get("info.reading", {})
