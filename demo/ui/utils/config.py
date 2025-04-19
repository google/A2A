import tomllib
from pathlib import Path
from typing import List

from utils import constants


def get_project_root() -> Path:
    """Get the project root directory"""
    return Path(__file__).resolve().parent.parent

PROJECT_ROOT = get_project_root()

class Config:

    def __init__(self):
        self._config_path = Config._get_config_path()
        self._address: List[str] = self._load_initial_config()

    @staticmethod
    def _get_config_path() -> Path:
        config_path = PROJECT_ROOT / "config" / "config.toml"
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        return config_path

    def _load_initial_config(self):
        try:
            with self._config_path.open("rb") as f:
                raw_config = tomllib.load(f)
            base_remote_agent_addresses = raw_config.get(constants.REMOTE_AGENT_ADDRESSES_KEY, {})
            return list(base_remote_agent_addresses.values())
        except Exception as e:
            raise ValueError(f"Failed to load configuration: {e}")

    @property
    def remote_agent_addresses(self) -> list[str]:
        return self._address

config = Config()

if __name__ == '__main__':
    print(config.remote_agent_addresses)