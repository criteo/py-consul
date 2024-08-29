import consul
import consul.check
import consul.std


class TestHTTPClient:
    def test_uri(self) -> None:
        http = consul.std.HTTPClient()
        assert http.uri("/v1/kv") == "http://127.0.0.1:8500/v1/kv"
        assert http.uri("/v1/kv", params=[("index", 1)]) == "http://127.0.0.1:8500/v1/kv?index=1"
