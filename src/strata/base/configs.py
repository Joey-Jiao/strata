import os
from typing import Any
from pathlib import Path

from dotenv import load_dotenv
from yaml import safe_load


class ConfigService:
    def __init__(self, config_dir: str | Path = "configs", env_path: str | Path | None = ".env"):
        self._config_dir = Path(config_dir)
        self._cache: dict[tuple[str, str], dict | None] = {}
        self._folders: set[str] = set()
        self._scan_config_tree()
        if env_path:
            load_dotenv(env_path, override=True)

    def _scan_config_tree(self):
        if not self._config_dir.exists():
            return
        for item in self._config_dir.iterdir():
            if item.is_dir():
                self._folders.add(item.name)
                for yaml_file in item.glob("*.yaml"):
                    self._cache[(item.name, yaml_file.stem)] = None
            elif item.suffix == ".yaml":
                self._cache[("", item.stem)] = None

    def _load_file(self, folder: str, file: str) -> dict:
        key = (folder, file)
        if key not in self._cache:
            return {}
        if self._cache[key] is None:
            path = self._config_dir / folder / f"{file}.yaml" if folder else self._config_dir / f"{file}.yaml"
            with open(path) as f:
                self._cache[key] = safe_load(f) or {}
        return self._cache[key]

    def get(self, keys: str, default: Any = None) -> Any:
        parts = keys.split(".")
        if len(parts) == 1:
            env_key = keys.upper().replace("-", "_")
            return os.environ.get(env_key, default)
        folder, file, *yaml_path = parts
        if folder in self._folders:
            content = self._load_file(folder, file)
            return self._traverse(content, yaml_path, default)
        file = parts[0]
        yaml_path = parts[1:]
        content = self._load_file("", file)
        return self._traverse(content, yaml_path, default)

    def _traverse(self, data: dict, path: list[str], default: Any) -> Any:
        value = data
        for key in path:
            if not isinstance(value, dict):
                return default
            value = value.get(key)
            if value is None:
                return default
        return value

    def list_files(self, folder: str = "") -> list[str]:
        return [f for (fo, f) in self._cache if fo == folder]
