from configparser import ConfigParser


class Config:
    _cfg: ConfigParser

    def __init__(self):
        self._cfg = ConfigParser()

    def load(self, config_path: str):
        self._cfg.read(config_path)

    @property
    def access_id(self) -> str:
        return self._cfg.get("credential", "accessId", fallback="{accessId}")

    @property
    def secret_key(self) -> str:
        return self._cfg.get("credential", "secretKey", fallback="{secretKey}")

    @property
    def base_url(self) -> str:
        return self._cfg.get("default", "baseUrl", fallback="{baseUrl}")

    @property
    def api_path(self) -> str:
        return self._cfg.get("default", "apiPath", fallback="{apiPath}")

    @property
    def integration_id(self) -> str:
        return self._cfg.get("default", "integrationId", fallback="{integratedId}")
