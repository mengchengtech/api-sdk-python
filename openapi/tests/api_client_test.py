import unittest
import os

from openapi.tests.config import Config
from openapi.sdk import RequestOption, OpenApiClient, OpenApiResponseError, SignedByQuery, QuerySignatureParams


class ApiClientTest(unittest.TestCase):
    _config: Config
    _client: OpenApiClient

    def __init__(self, methodName: str = 'runTest'):
        super().__init__(methodName)

        config_path = os.path.join(os.path.dirname(__file__), "app.ini")
        self._config = Config()
        self._config.load(config_path)
        self._client = OpenApiClient(self._config.base_url, self._config.access_id, self._config.secret_key)
        self.addCleanup(self._client.close)

    def test_get_by_header(self):
        option = RequestOption.new_builder() \
            .add_query({"integratedProjectId": self._config.integration_id}) \
            .add_header({
                "X-iwop-before": "wq666",
                "x-iwop-integration-id": self._config.integration_id,
                "x-IWOP-after": "wq666"
            }) \
            .build()
        with self._client.get(self._config.api_path, option) as result:
            jo = result.get_json_object()
            self.assertIn("updateAt", jo)
            self.assertIn("data", jo)

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
        with self._client.get(self._config.api_path, option) as result:
            jo = result.get_json_object()
            self.assertIn("updateAt", jo)
            self.assertIn("data", jo)

    def test_post_by_header(self):
        option = RequestOption.new_builder() \
            .add_query({"integratedProjectId": self._config.integration_id}) \
            .add_header({
                "x-iwop-integration-id": self._config.integration_id,
                "x-forwarded-for": "192.168.1.1"
            }) \
            .content_type("application/xml") \
            .content("<body></body>") \
            .build()
        with self.assertRaises(OpenApiResponseError) as ctx:
            self._client.post(self._config.api_path, option)

        err = ctx.exception
        self.assertEqual(err.status, 404)
        self.assertEqual(err.error.client_ip, "192.168.1.1")
        self.assertEqual(err.error.code, "SERVICE_NOT_FOUND")
        self.assertEqual(err.error.message,
                         "'POST /api-ex/-itg-/cb/project-wbs/items' 对应的服务不存在。请检查rest请求中的method, path是否与相应api文档中的完全一致")


if __name__ == "__main__":
    unittest.main()
