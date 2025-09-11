import httpx
import json

from typing import Any


class SyncResponseDataStream:
    _stream: httpx.SyncByteStream

    def __init__(self, stream: httpx.SyncByteStream):
        self._stream = stream

    def __iter__(self):
        gen = self._stream.__iter__()
        while True:
            try:
                yield gen.__next__()
            except StopAsyncIteration:
                break

    def close(self):
        self._stream.close()


class AsyncResponseDataStream:
    _stream: httpx.AsyncByteStream

    def __init__(self, stream: httpx.AsyncByteStream):
        self._stream = stream

    def __aiter__(self):
        return self._stream.__aiter__()

    async def aclose(self):
        return self._stream.aclose()


class _Result:
    _response: httpx.Response

    def __init__(self, response: httpx.Response):
        self._response = response

    @property
    def status(self) -> int:
        '''
        返回结果状态码
        '''
        return self._response.status_code

    @property
    def content_type(self) -> str:
        _type = ''
        if self._response:
            _type = self._response.headers.get('content-type')
        return _type or ''

    def _get_encoding(self) -> str:
        encoding = self._response.encoding or 'utf-8'
        return encoding


class RequestResult(_Result):
    def __enter__(self) -> "RequestResult":
        return self

    def __exit__(self, exc_type=None, exc_value=None, traceback=None):
        self._response.close()
        # self._response = None

    def get_string(self) -> str:
        '''
        以字符串方式获取返回的文本内容
        '''
        content = self._response.read()
        return str(content, encoding=self._get_encoding())

    def get_json_object(self, **kwargs) -> Any:
        '''
        获取Json方式表示的实体对象
        '''
        content = self._response.read()
        return json.loads(content, **kwargs)

    def open_stream(self) -> SyncResponseDataStream:
        '''
        获取返回结果的Stream
        '''
        s = self._response.stream
        if isinstance(s, httpx.SyncByteStream):
            return SyncResponseDataStream(s)
        raise RuntimeError('stream类型错误')


class AsyncRequestResult(_Result):
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type=None, exc_value=None, traceback=None):
        await self._response.aclose()
        # self._response = None

    async def get_string(self) -> str:
        '''
        以字符串方式获取返回的文本内容
        '''
        content = await self._response.aread()
        return str(content, encoding=self._get_encoding())

    async def get_json_object(self, **kwargs) -> Any:
        '''
        获取Json方式表示的实体对象
        '''
        content = await self._response.aread()
        return json.loads(content, **kwargs)

    async def open_stream(self) -> AsyncResponseDataStream:
        '''
        获取返回结果的Stream
        '''
        s = self._response.stream
        if isinstance(s, httpx.AsyncByteStream):
            return AsyncResponseDataStream(s)
        raise RuntimeError('stream类型错误')
