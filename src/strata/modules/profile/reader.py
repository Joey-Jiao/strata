from strata.base.configs import ConfigService


class ProfileReader:
    def __init__(self, config: ConfigService):
        self._config = config

    def about(self) -> str:
        return self._config.get("profile.about", "")

    def identity(self) -> dict:
        return self._config.get("profile.identity", {})

    def workspace(self) -> dict:
        return self._config.get("profile.workspace", {})

    def hosts(self) -> dict:
        return self._config.get("profile.hosts", {})

    def conventions(self) -> dict:
        return self._config.get("profile.conventions", {})
