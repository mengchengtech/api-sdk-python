import json

from typing import Optional


class ApiGatewayErrorData(object):
    PROP_CODE = "Code"
    PROP_MESSAGE = "Message"
    PROP_CLIENT_IP = "ClientIP"
    PROP_STRING_TO_SIGN_BYTES = "StringToSignBytes"
    PROP_SIGNATURE_PROVIDED = "SignatureProvided"
    PROP_STRING_TO_SIGN = "StringToSign"
    PROP_ACCESS_KEY_ID = "AccessKeyId"

    _map: dict

    def __init__(self, map: dict):
        self._map = map

    @property
    def code(self) -> str:
        return self._map[ApiGatewayErrorData.PROP_CODE]

    @property
    def message(self) -> str:
        return self._map[ApiGatewayErrorData.PROP_MESSAGE]

    @property
    def client_ip(self) -> str:
        return self._map[ApiGatewayErrorData.PROP_CLIENT_IP]

    @property
    def string_to_sign_bytes(self) -> Optional[str]:
        return self._map[ApiGatewayErrorData.PROP_STRING_TO_SIGN_BYTES]

    @property
    def signature_provided(self) -> Optional[str]:
        return self._map[ApiGatewayErrorData.PROP_SIGNATURE_PROVIDED]

    @property
    def string_to_sign(self) -> Optional[str]:
        return self._map[ApiGatewayErrorData.PROP_STRING_TO_SIGN]

    @property
    def access_key_id(self) -> Optional[str]:
        return self._map[ApiGatewayErrorData.PROP_ACCESS_KEY_ID]

    def get_property(self, name: str) -> Optional[str]:
        return self._map[name]

    def __str__(self) -> str:
        return json.dumps(self._map, ensure_ascii=False)


class OpenApiClientError(RuntimeError):
    def __init__(self, message: str):
        super().__init__(message)


class OpenApiResponseError(RuntimeError):
    _error: ApiGatewayErrorData
    _status: int

    def __init__(self, message: str, status: int, error: ApiGatewayErrorData):
        super().__init__(message)
        self._error = error
        self._status = status

    @property
    def error(self) -> ApiGatewayErrorData:
        return self._error

    @property
    def status(self) -> int:
        return self._status
