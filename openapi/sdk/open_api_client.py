from httpx import Client, AsyncClient, Request, URL, Timeout
from typing import Mapping, Dict, NamedTuple, Any, Union, Tuple, Optional, Iterable, AsyncIterable
from abc import ABC, abstractmethod

from .error import OpenApiClientError, OpenApiResponseError
from .signed_by import SignedBy, SignedByHeader
from .utility import HttpMethod, SignatureOption, HttpHeaderNames, generate_signature, resolve_error
from .request_result import RequestResult, AsyncRequestResult

Json = Any
RequestContent = Union[str, bytes, Iterable[bytes], AsyncIterable[bytes]]
RequestContentTypes = Union[Json, RequestContent]


class HttpContent(NamedTuple):
    content: Optional[RequestContent]
    json: Optional[Any]

    content_type: Optional[str]

    def args(self) -> Tuple[Optional[str], RequestContentTypes]:
        if self.content is not None:
            return ("content", self.content)
        elif self.json is not None:
            return ("json", self.json)
        return (None, None)


class Builder:
    _signed_by: Optional[SignedBy]
    _timeout: Optional[int]
    _query: Dict[str, str]
    _headers: Dict[str, str]
    _content_type: Optional[str]
    _json: Optional[Any]
    _content: Optional[RequestContent]

    def __init__(self):
        self._signed_by = None
        self._timeout = None
        self._query = {}
        self._headers = {}
        self._content_type = None
        self._json = None
        self._content = None

    def signed_by(self, signed_by: SignedBy) -> "Builder":
        self._signed_by = signed_by
        return self

    def timeout(self, timeout: int) -> "Builder":
        assert timeout > 0
        self._timeout = timeout
        return self

    def add_query(self, map: Optional[Dict[str, Any]] = None, /, **kwargs: Any) -> "Builder":
        dictionary: Mapping[str, Any] = (map | kwargs) if map else kwargs
        if len(dictionary) > 0:
            for name, value in dictionary.items():
                self._query[name] = str(value)
        return self

    def add_header(self, map: Optional[Dict[str, Any]] = None, /, **kwargs: Any) -> "Builder":
        dictionary: Mapping[str, Any] = (map | kwargs) if map else kwargs
        if len(dictionary) > 0:
            for name, value in dictionary.items():
                self._headers[name] = str(value)
        return self

    def content_type(self, contentType: str) -> "Builder":
        self.contentType = contentType
        return self

    def json(self, body: Json) -> "Builder":
        self._json = body
        return self

    def content(self, body: RequestContent) -> "Builder":
        self._content = body
        return self

    def build(self) -> "RequestOption":
        entity = HttpContent(content=self._content,
                             json=self._json,
                             content_type=self._content_type)
        return RequestOption(self._signed_by, self._timeout, self._query, self._headers, entity)


class RequestOption(NamedTuple):
    signed_by: Optional[SignedBy]
    timeout: Optional[int]
    query: Mapping[str, str]
    headers: Mapping[str, str]
    entity: HttpContent

    @staticmethod
    def new_builder() -> Builder:
        return Builder()


class _Client(ABC):
    _CONTENT_TYPE_VALUE = "application/json; charset=UTF-8"
    _ACCEPT_VALUE = "application/json, application/xml, */*"

    _access_id: str
    _secret_key: str
    _base_uri: URL

    def __init__(self, base_uri: str, access_id: str, secret_key: str):
        self._base_uri = URL(base_uri)
        if not access_id:
            raise OpenApiClientError("accessId不能为null或empty")
        if not secret_key:
            raise OpenApiClientError("secret不能为null或empty")

        self._access_id = access_id
        self._secret_key = secret_key

    def _make_signature(self, req: Request, signed_by: Optional[SignedBy]):
        content_type: str = req.headers.get(HttpHeaderNames.CONTENT_TYPE)
        option = SignatureOption(
            self._access_id,
            self._secret_key,
            str(req.url),
            HttpMethod[str(req.method).upper()],
            content_type,
            req.headers
        )

        signed_by = signed_by or SignedByHeader()
        signed_info = generate_signature(signed_by, option)
        if signed_info.headers:
            req.headers.update(signed_info.headers)

        if signed_info.query:
            req.url = req.url.copy_merge_params(signed_info.query)

    @abstractmethod
    def _new_request(self, method: str, api_uri: URL, **kwargs) -> Request:
        pass

    def _create_request(self, method: HttpMethod, api_path: str, option: RequestOption) -> Request:
        kwargs: Mapping[str, Any] = {
            'headers': dict(option.headers)
        }
        if option.entity:
            name, value = option.entity.args()
            if name:
                kwargs[name] = value
            content_type = option.entity.content_type or _Client._CONTENT_TYPE_VALUE
            kwargs['headers'][HttpHeaderNames.CONTENT_TYPE] = content_type
        if option.timeout and option.timeout > 0:
            kwargs['timeout'] = Timeout(timeout=option.timeout, connect=5.0)

        api_uri = self._base_uri.join(api_path)
        if len(option.query) > 0:
            api_uri = api_uri.copy_merge_params(option.query)

        req = self._new_request(str(method), api_uri, **kwargs)
        self._make_signature(req, option.signed_by)
        return req


class OpenApiClient(_Client):
    _client: Client

    def __init__(self, base_uri: str, access_id: str, secret_key: str):
        super().__init__(base_uri, access_id, secret_key)

        self._client = Client(
            headers={
                HttpHeaderNames.ACCEPT: _Client._ACCEPT_VALUE,
                HttpHeaderNames.ACCEPT_LANGUAGE: "zh-CN"
            }
        )

    def __enter__(self: "OpenApiClient") -> "OpenApiClient":
        return self

    def __exit__(self, exc_type=None, exc_value=None, traceback=None):
        self.close()

    def close(self):
        self._client.close()

    def _new_request(self, method: str, api_uri: URL, **kwargs) -> Request:
        return self._client.build_request(method, url=api_uri, **kwargs)

    def get(self, api_path: str, option: RequestOption) -> RequestResult:
        return self.request(HttpMethod.GET, api_path, option)

    def delete(self, api_path: str, option: RequestOption) -> RequestResult:
        return self.request(HttpMethod.DELETE, api_path, option)

    def post(self, api_path: str, option: RequestOption) -> RequestResult:
        return self.request(HttpMethod.POST, api_path, option)

    def put(self, api_path: str, option: RequestOption) -> RequestResult:
        return self.request(HttpMethod.PUT, api_path, option)

    def patch(self, api_path: str, option: RequestOption) -> RequestResult:
        return self.request(HttpMethod.PATCH, api_path, option)

    def request(self, method: HttpMethod, api_path: str, option: RequestOption) -> RequestResult:
        req = self._create_request(method, api_path, option)
        response = self._client.send(req, stream=True)

        if response.is_error:
            data = response.read()
            xmlContent = str(data, encoding=response.encoding or 'utf-8')
            error = resolve_error(xmlContent)
            raise OpenApiResponseError(error.message, response.status_code, error)
        return RequestResult(response)


class AsyncOpenApiClient(_Client):
    _client: AsyncClient

    def __init__(self, base_uri: str, access_id: str, secret_key: str):
        super().__init__(base_uri, access_id, secret_key)

        self._client = AsyncClient(
            headers={
                HttpHeaderNames.ACCEPT: _Client._ACCEPT_VALUE,
                HttpHeaderNames.ACCEPT_LANGUAGE: "zh-CN"
            }
        )

    async def __aenter__(self: "AsyncOpenApiClient") -> "AsyncOpenApiClient":
        return self

    async def __aexit__(self, exc_type=None, exc_value=None, traceback=None):
        await self.aclose()

    async def aclose(self):
        await self._client.aclose()

    def _new_request(self, method: str, api_uri: URL, **kwargs) -> Request:
        return self._client.build_request(method, url=api_uri, **kwargs)

    async def get(self, api_path: str, option: RequestOption) -> AsyncRequestResult:
        return await self.request(HttpMethod.GET, api_path, option)

    async def delete(self, api_path: str, option: RequestOption) -> AsyncRequestResult:
        return await self.request(HttpMethod.DELETE, api_path, option)

    async def post(self, api_path: str, option: RequestOption) -> AsyncRequestResult:
        return await self.request(HttpMethod.POST, api_path, option)

    async def put(self, api_path: str, option: RequestOption) -> AsyncRequestResult:
        return await self.request(HttpMethod.PUT, api_path, option)

    async def patch(self, api_path: str, option: RequestOption) -> AsyncRequestResult:
        return await self.request(HttpMethod.PATCH, api_path, option)

    async def request(self, method: HttpMethod, api_path: str, option: RequestOption) -> AsyncRequestResult:
        req = self._create_request(method, api_path, option)
        response = await self._client.send(req, stream=True)

        if response.is_error:
            data = await response.aread()
            xmlContent = str(data, encoding=response.encoding or 'utf-8')
            error = resolve_error(xmlContent)
            raise OpenApiResponseError(error.message, response.status_code, error)
        return AsyncRequestResult(response)
