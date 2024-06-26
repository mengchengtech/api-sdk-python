import hmac
import base64
import hashlib

from httpx import Auth, Request, Response
from typing import Generator, Mapping
from datetime import datetime, timezone
from email.utils import format_datetime
from urllib.parse import urlparse, urlencode, parse_qsl, urlunparse

authorization_prefix = "IWOP"

class GatewayAuthentication(Auth):
    def __init__(self, access_id: str, secret_key: str):
        assert access_id, 'access_id不能为空'
        assert secret_key, 'secret_key不能为空'
        
        self._access_id = access_id
        self._secret_key = secret_key

    def auth_flow(self, req: Request) -> Generator[Request, Response, None]:
        mapping = self.__generate_signature(req.method, str(req.url), len(req.content) > 0, req.headers)
        req.headers.update(mapping)
        yield req


    def __generate_signature(self, method: str, resource: str, has_body: bool, headers: Mapping[str, str]):
        mapping = {}
        method = method.upper()
        content_type = headers.get('content-type')
        if method == 'POST' or method == 'PUT' or method == 'PATCH':
            if has_body:
                assert content_type, f"请求方式为[{method}]时，需要设置'content-type'"

        gmtDate = headers.get('date')
        if not gmtDate:
            gmtDate = format_datetime(datetime.now(timezone.utc), True)
            mapping['date'] = gmtDate

        items = [method.upper()]
        if content_type:
            items.append(content_type)
        items.append(gmtDate)

        for name in sorted(headers.keys()):
            if name.startswith('x-iwop-'):
                items.append(f'{name}:{headers[name]}')
        # 解析 URL
        parsed_url = urlparse(resource)
        # 解析查询部分为键值对列表
        query_pairs = parse_qsl(parsed_url.query)
        # 按键对查询部分进行排序
        sorted_query_pairs = sorted(query_pairs, key=lambda pair: pair[0])
        # 将排序后的键值对列表重新编码为查询字符串
        sorted_query_string = urlencode(sorted_query_pairs)
        new_url = urlunparse(parsed_url._replace(query=sorted_query_string))
        items.append(new_url)
        policy = "\n".join(items)
        byte_key = self._secret_key.encode("UTF-8")
        digest = hmac.digest(byte_key, policy.encode("UTF-8"), hashlib.sha1)
        signature = str(base64.b64encode(digest), 'UTF-8')

        mapping['authorization'] = f'{authorization_prefix} {self._access_id}:{signature}'
        return mapping