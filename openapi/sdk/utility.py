import hmac
import base64
import hashlib
import xml.etree.ElementTree as ET
import httpx

from enum import Enum
from datetime import datetime, timezone
from email.utils import format_datetime
from typing import NamedTuple, Mapping, List, Tuple, Optional
from urllib.parse import urlparse, urlencode, parse_qsl, urlunparse

from .signed_by import SignatureMode, SignedBy, SignedByQuery
from .error import OpenApiClientError, ApiGatewayErrorData


__QUERY_ACCESS_ID = "AccessId"
__QUERY_EXPIRES = "Expires"
__QUERY_SIGNATURE = "Signature"
__QUERY_KEYS = ["AccessId", "Signature", "Expires"]
__CUSTOM_PREFIX = "x-iwop-"
# 生成Query签名时间有效期默认值，单位秒
__DEFAULT_EXPIRES = 30


class HttpHeaderNames:
    ACCEPT = "Accept"
    ACCEPT_LANGUAGE = "Accept-Language"
    AUTHORIZATION = "Authorization"
    CONTENT_TYPE = "Content-Type"
    DATE = "Date"


class HttpMethod(Enum):
    GET = 'GET'
    POST = 'POST'
    DELETE = 'DELETE'
    PUT = 'PUT'
    PATCH = 'PATCH'

    def __str__(self) -> str:
        return self.value


class SignedData(NamedTuple):
    signable: str
    signature: str


class SignedInfo(NamedTuple):
    mode: SignatureMode
    signed: SignedData
    headers: Optional[Mapping[str, str]]
    query: Optional[Mapping[str, str]]


class SignatureOption(NamedTuple):
    access_id: str
    secret: str
    # 获取或设置REST调用签名中的url路径信息
    request_uri: str
    # 获取或设置设置REST调用签名中的method信息
    method: HttpMethod
    # 获取或设置REST调用中的content-type头
    content_type: Optional[str]
    # headers头
    headers: httpx.Headers


def __get_custom_map(pairs: List[Tuple[str, str]]) -> Mapping[str, str]:
    iwopValues: Mapping[str, str] = {}
    for key, value in pairs:
        lower_case_name = key.lower()
        if (lower_case_name.startswith(__CUSTOM_PREFIX)):
            iwopValues[lower_case_name] = value
    return iwopValues


def __get_resource(requestUri: str) -> str:
    # 解析 URL
    parsed_url = urlparse(requestUri)
    if not parsed_url.query:
        return requestUri

    # 解析查询部分为键值对列表
    params: Mapping[str, str] = dict(parse_qsl(parsed_url.query))
    keys = [k for k in params.keys()]
    for key in keys:
        # 排除掉表用于认证的固定参数
        if key in __QUERY_KEYS:
            del params[key]
            continue

        # 排除掉特定前缀的参数，例如 'x-iwop-'
        lower_case_name: str = key.lower()
        if (lower_case_name.startswith(__CUSTOM_PREFIX)):
            del params[key]

    sorted_query_pairs = sorted(list(params.items()), key=lambda pair: pair[0])
    # 将排序后的键值对列表重新编码为查询字符串
    sorted_query_string = urlencode(sorted_query_pairs)
    new_url = urlunparse(parsed_url._replace(query=sorted_query_string))
    return new_url


def __compute_signature(mode: SignatureMode, option: SignatureOption, time: str) -> SignedData:
    signable_items: List[str] = []
    signable_items.append(option.method.value.upper())
    if option.content_type:
        signable_items.append(option.content_type)
    signable_items.append(time)
    custom_map: Mapping[str, str]
    if (mode == SignatureMode.HEADER):
        custom_map = __get_custom_map(list(option.headers.items()))
    elif (mode == SignatureMode.QUERY):
        custom_map = __get_custom_map(parse_qsl(urlparse(option.request_uri).query))
    if custom_map:
        keys = [key for key in custom_map.keys()]
        keys.sort()
        for key in keys:
            signable_items.append(key + ":" + custom_map[key])

    canonicalized_resource = __get_resource(option.request_uri)
    signable_items.append(canonicalized_resource)

    signable = "\n".join(signable_items)
    signature = __hma_sha1(signable, option.secret)
    return SignedData(signable, signature)


def __hma_sha1(signable: str, secret: str) -> str:
    byte_key = secret.encode()
    digest = hmac.digest(byte_key, signable.encode(), hashlib.sha1)
    signature = str(base64.b64encode(digest), 'UTF-8')
    return signature


def resolve_error(xml: str) -> ApiGatewayErrorData:
    root = ET.fromstring(xml)
    map = {}
    for item in root.iter():
        name = item.tag
        value = item.text
        map[name] = value

    return ApiGatewayErrorData(map)


def generate_signature(signed_by: SignedBy, option: SignatureOption) -> SignedInfo:
    if not option.access_id:
        raise OpenApiClientError("accessId不能为null或empty")
    if not option.secret:
        raise OpenApiClientError("secret不能为null或empty")
    method = option.method.value
    if (method == HttpMethod.POST or method == HttpMethod.PUT or method == HttpMethod.PATCH):
        if not option.content_type:
            raise OpenApiClientError(
                "http请求缺少'content-type'头。请求方式为[" + method + "]时，需要在RpcInvoker的headers属性上设置'content-type'")
    time: str
    query: Optional[Mapping[str, str]] = None
    headers: Optional[Mapping[str, str]] = None
    if isinstance(signed_by, SignedByQuery):
        p = signed_by.parameters
        d = p.duration if p and p.duration > 0 else __DEFAULT_EXPIRES
        expires = d + int(datetime.now().timestamp())
        time = str(expires)
        query = {
            __QUERY_ACCESS_ID: option.access_id,
            __QUERY_EXPIRES: time,
            __QUERY_SIGNATURE: "",
        }
    else:
        time = format_datetime(datetime.now(timezone.utc), True)
        headers = {
            HttpHeaderNames.DATE: time,
            HttpHeaderNames.AUTHORIZATION: ""
        }
    signed = __compute_signature(signed_by.mode, option, time)
    if query:
        query[__QUERY_SIGNATURE] = signed.signature
    elif headers:
        headers[HttpHeaderNames.AUTHORIZATION] = "IWOP " + option.access_id + ":" + signed.signature
    return SignedInfo(signed_by.mode, signed, headers, query)
