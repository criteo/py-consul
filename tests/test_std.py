import socket

import pytest
import requests

import consul
import consul.check
import consul.std


class TestHTTPClient:
    def test_uri(self) -> None:
        http = consul.std.HTTPClient()
        assert http.uri("/v1/kv") == "http://127.0.0.1:8500/v1/kv"
        assert http.uri("/v1/kv", params=[("index", 1)]) == "http://127.0.0.1:8500/v1/kv?index=1"

    def test_timeout(self) -> None:
        http = consul.std.HTTPClient()
        assert http.timeout([("dc", "dc1")]) == 30
        assert http.timeout([("index", 1), ("wait", "1m30s")]) == 30 + 90 + 90 / 16
        assert http.timeout([("index", 1)]) == 30 + 300 + 300 / 16
        assert consul.std.HTTPClient(connections_timeout=None).timeout([("index", 1)]) is None

    def test_connections_timeout(self) -> None:
        # A peer that accepts but never answers, like an agent that went away
        # without closing the connection, must not block forever.
        with socket.create_server(("127.0.0.1", 0)) as server:
            port = server.getsockname()[1]
            c = consul.std.Consul(port=port, connections_timeout=0.2)
            with pytest.raises(requests.exceptions.ReadTimeout):
                c.catalog.node("foo", index=1, wait="100ms")
