import os
import asyncio
from log4py import logging

from .config import Config
from ..sdk import RequestOption, OpenApiClient, AsyncOpenApiClient, OpenApiClientError, OpenApiResponseError, SignedByQuery, QuerySignatureParams

log = logging.getLogger('python.openapi.sample')


class Application:
    _config: Config
    _client: OpenApiClient

    def __init__(self):
        config_path = os.path.join(os.path.dirname(__file__), "app.ini")
        self._config = Config()
        self._config.load(config_path)
        self._client = OpenApiClient(self._config.base_url, self._config.access_id, self._config.secret_key)

    def close(self):
        self._client.close()

    def test_get_by_header(self):
        option = RequestOption.new_builder() \
            .add_query({"integratedProjectId": self._config.integration_id}) \
            .add_header({
                "X-iwop-before": "wq666",
                "x-iwop-integration-id": self._config.integration_id,
                "x-IWOP-after": "wq666"
            }) \
            .build()
        try:
            with self._client.get(self._config.api_path, option) as result:
                print(result.get_string())
        except OpenApiClientError as e:
            log.error(str(e), e)
            # TODO: 处理异常
            # noinspection CallToPrintStackTrace
        except OpenApiResponseError as e:
            log.error(str(e), e)
            # TODO: 处理api网关返回的异常
            log.error(e.error)

    def test_get_by_query(self):
        option = RequestOption.new_builder() \
            .signed_by(SignedByQuery(QuerySignatureParams(3600))) \
            .add_query({"integratedProjectId": self._config.integration_id}) \
            .add_query({
                "X-iwop-before": "wq666",
                "x-iwop-integration-id": self._config.integration_id,
                "x-IWOP-after": "wq666",
            }) \
            .build()
        try:
            with self._client.get(self._config.api_path, option) as result:
                print(result.get_string())
        except OpenApiClientError as e:
            log.error(str(e), e)
            # TODO: 处理异常
            # noinspection CallToPrintStackTrace
        except OpenApiResponseError as e:
            log.error(str(e), e)
            # TODO: 处理api网关返回的异常
            log.error(e.error)

    def test_post_by_header(self):
        option = RequestOption.new_builder() \
            .add_query({"integratedProjectId": self._config.integration_id}) \
            .add_header({"x-iwop-integration-id": self._config.integration_id}) \
            .content_type("application/xml") \
            .content("<body></body>") \
            .build()
        try:
            with self._client.post(self._config.api_path, option) as result:
                print(result.get_string())
        except OpenApiClientError as e:
            log.error(str(e), e)
            # TODO: 处理异常
            # noinspection CallToPrintStackTrace
        except OpenApiResponseError as e:
            log.error(str(e), e)
            # TODO: 处理api网关返回的异常
            log.error(e.error)


class AsyncApplication:
    _config: Config
    _client: AsyncOpenApiClient

    def __init__(self):
        config_path = os.path.join(os.path.dirname(__file__), "app.ini")
        self._config = Config()
        self._config.load(config_path)
        self._client = AsyncOpenApiClient(self._config.base_url, self._config.access_id, self._config.secret_key)

    async def aclose(self):
        await self._client.aclose()

    async def test_get_by_header(self):
        option = RequestOption.new_builder() \
            .add_query({"integratedProjectId": self._config.integration_id}) \
            .add_header({
                "X-iwop-before": "wq666",
                "x-iwop-integration-id": self._config.integration_id,
                "x-IWOP-after": "wq666"
            }) \
            .build()
        try:
            async with await self._client.get(self._config.api_path, option) as result:
                print(await result.get_string())
        except OpenApiClientError as e:
            log.error(str(e), e)
            # TODO: 处理异常
            # noinspection CallToPrintStackTrace
        except OpenApiResponseError as e:
            log.error(str(e), e)
            # TODO: 处理api网关返回的异常
            log.error(e.error)

    async def test_get_by_query(self):
        option = RequestOption.new_builder() \
            .signed_by(SignedByQuery(QuerySignatureParams(3600))) \
            .add_query({"integratedProjectId": self._config.integration_id}) \
            .add_query({
                "X-iwop-before": "wq666",
                "x-iwop-integration-id": self._config.integration_id,
                "x-IWOP-after": "wq666",
            }) \
            .build()
        try:
            async with await self._client.get(self._config.api_path, option) as result:
                print(await result.get_string())
        except OpenApiClientError as e:
            log.error(str(e), e)
            # TODO: 处理异常
            # noinspection CallToPrintStackTrace
        except OpenApiResponseError as e:
            log.error(str(e), e)
            # TODO: 处理api网关返回的异常
            log.error(e.error)

    async def test_post_by_header(self):
        option = RequestOption.new_builder() \
            .add_query({"integratedProjectId": self._config.integration_id}) \
            .add_header({"x-iwop-integration-id": self._config.integration_id}) \
            .content_type("application/xml") \
            .content("<body></body>") \
            .build()
        try:
            async with await self._client.post(self._config.api_path, option) as result:
                print(await result.get_string())
        except OpenApiClientError as e:
            log.error(str(e), e)
            # TODO: 处理异常
            # noinspection CallToPrintStackTrace
        except OpenApiResponseError as e:
            log.error(str(e), e)
            # TODO: 处理api网关返回的异常
            log.error(e.error)


async def main_async():
    app = AsyncApplication()
    try:
        await app.test_get_by_header()
        await app.test_get_by_query()
        await app.test_post_by_header()
    finally:
        await app.aclose()


def main():
    app = Application()
    try:
        app.test_get_by_header()
        app.test_get_by_query()
        app.test_post_by_header()
    finally:
        app.close()


if __name__ == '__main__':
    main()
    asyncio.run(main_async())
