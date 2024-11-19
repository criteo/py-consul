from __future__ import annotations

import collections
import contextlib
import json
from typing import Any, Callable, Optional

import pytest

import consul.check

Request = collections.namedtuple("Request", ["method", "path", "params", "headers", "data"])


class HTTPClient:
    def __init__(
        self, host: Optional[str] = None, port: Optional[int] = None, scheme=None, verify: bool = True, cert=None
    ) -> None:
        self.host = host
        self.port = int(port) if port else None
        self.scheme = scheme
        self.verify = verify
        self.cert = cert

    def get(self, callback, path, params=None, headers=None):  # pylint: disable=unused-argument
        return Request("get", path, params, headers, None)

    def put(self, callback, path, params=None, headers=None, data: str = ""):  # pylint: disable=unused-argument
        return Request("put", path, params, headers, data)

    def delete(self, callback, path, params=None, headers=None):  # pylint: disable=unused-argument
        return Request("delete", path, params, headers, None)


class Consul(consul.base.Consul):
    def http_connect(self, host: str, port: int, scheme, verify: bool = True, cert=None):
        return HTTPClient(host=host, port=port, scheme=scheme, verify=verify, cert=None)


def _should_support(c: Consul) -> tuple[Callable[..., Any], ...]:
    return (
        # kv
        lambda **kw: c.kv.get("foo", **kw),
        # catalog
        c.catalog.nodes,
        c.catalog.services,
        lambda **kw: c.catalog.node("foo", **kw),
        lambda **kw: c.catalog.service("foo", **kw),
        # session
        c.session.list,
        lambda **kw: c.session.info("foo", **kw),
        lambda **kw: c.session.node("foo", **kw),
    )


def _should_support_node_meta(c: Consul) -> tuple[Callable[..., Any], ...]:
    return (
        # catalog
        c.catalog.nodes,
        c.catalog.services,
        lambda **kw: c.catalog.service("foo", **kw),
        lambda **kw: c.catalog.register("foo", "bar", **kw),
        # health
        lambda **kw: c.health.service("foo", **kw),
        lambda **kw: c.health.checks("foo", **kw),
        lambda **kw: c.health.state("unknown", **kw),
    )


def _should_support_meta(c: Consul) -> tuple[Callable[..., Any], ...]:
    return (
        # agent
        lambda **kw: c.agent.service.register("foo", **kw),
        lambda **kw: c.agent.service.register("foo", "bar", **kw),
    )


class TestBaseInit:
    """
    Tests that connection arguments are handled
    """

    @pytest.mark.parametrize(
        ("env", "host", "port", "want"),
        [
            (
                None,
                None,
                None,
                {
                    "host": "127.0.0.1",
                    "port": 8500,
                },
            ),
            (
                "127.0.0.1:443",
                None,
                None,
                {
                    "host": "127.0.0.1",
                    "port": 443,
                },
            ),
            (
                None,
                "consul.domain.tld",
                None,
                {
                    "host": "consul.domain.tld",
                    "port": 8500,
                },
            ),
            (
                "consul.domain.tld:443",
                "127.0.0.1",
                None,
                {
                    "host": "127.0.0.1",
                    "port": 8500,
                },
            ),
            (
                "consul.domain.tld:443",
                "127.0.0.1",
                8080,
                {
                    "host": "127.0.0.1",
                    "port": 8080,
                },
            ),
            (
                "bad",
                "127.0.0.1",
                8080,
                {
                    "host": "127.0.0.1",
                    "port": 8080,
                },
            ),
        ],
    )
    def test_base_init_addr(self, monkeypatch, env, host, port, want) -> None:
        if env:
            monkeypatch.setenv("CONSUL_HTTP_ADDR", env)
        else:
            with contextlib.suppress(KeyError):
                monkeypatch.delenv("CONSUL_HTTP_ADDR")

        c = Consul(host=host, port=port)
        assert c.http.host == want["host"]
        assert c.http.port == want["port"]

    @pytest.mark.parametrize(
        ("env", "scheme", "want"),
        [
            ("true", None, "https"),
            ("false", None, "http"),
            (None, "https", "https"),
            (None, "http", "http"),
            ("http", "https", "https"),
        ],
    )
    def test_base_init_scheme(self, monkeypatch, env, scheme, want) -> None:
        if env:
            monkeypatch.setenv("CONSUL_HTTP_SSL", env)
        else:
            with contextlib.suppress(KeyError):
                monkeypatch.delenv("CONSUL_HTTP_SSL")

        c = Consul(scheme=scheme)
        assert c.http.scheme == want

    @pytest.mark.parametrize(
        ("env", "verify", "want"),
        [
            ("true", None, True),
            (None, True, True),
            ("false", True, True),
        ],
    )
    def test_base_init_verify(self, monkeypatch, env, verify, want) -> None:
        if env:
            monkeypatch.setenv("CONSUL_HTTP_SSL_VERIFY", env)
        else:
            with contextlib.suppress(KeyError):
                monkeypatch.delenv("CONSUL_HTTP_SSL_VERIFY")

        c = Consul(verify=verify)
        assert c.http.verify == want


class TestIndex:
    """
    Tests read requests that should support blocking on an index
    """

    def test_index(self) -> None:
        c = Consul()
        for r in _should_support(c):
            assert r().params == []
            assert r(index="5").params == [("index", "5")]


class TestConsistency:
    """
    Tests read requests that should support consistency modes
    """

    def test_explict(self) -> None:
        c = Consul()
        for r in _should_support(c):
            assert r().params == []
            assert r(consistency="default").params == []
            assert r(consistency="consistent").params == [("consistent", "1")]
            assert r(consistency="stale").params == [("stale", "1")]

    def test_implicit(self) -> None:
        c = Consul(consistency="consistent")
        for r in _should_support(c):
            assert r().params == [("consistent", "1")]
            assert r(consistency="default").params == []
            assert r(consistency="consistent").params == [("consistent", "1")]
            assert r(consistency="stale").params == [("stale", "1")]


class TestNodemeta:
    """
    Tests read requests that should support node_meta
    """

    def test_node_meta(self) -> None:
        c = Consul()
        for r in _should_support_node_meta(c):
            assert r().params == []
            assert sorted(r(node_meta={"env": "prod", "net": 1}).params) == sorted([
                ("node-meta", "net:1"),
                ("node-meta", "env:prod"),
            ])


class TestMeta:
    """
    Tests read requests that should support meta
    """

    def test_meta(self) -> None:
        c = Consul()
        for r in _should_support_meta(c):
            d = json.loads(r(meta={"env": "prod", "net": 1}).data)
            assert sorted(d["meta"]) == sorted({"env": "prod", "net": 1})


class TestChecks:
    """
    Check constructor helpers return valid check configurations.
    """

    @pytest.mark.parametrize(
        ("url", "interval", "timeout", "deregister", "header", "want"),
        [
            (
                "http://example.com",
                "10s",
                None,
                None,
                None,
                {
                    "http": "http://example.com",
                    "interval": "10s",
                },
            ),
            (
                "http://example.com",
                "10s",
                "1s",
                None,
                None,
                {
                    "http": "http://example.com",
                    "interval": "10s",
                    "timeout": "1s",
                },
            ),
            (
                "http://example.com",
                "10s",
                None,
                "1m",
                None,
                {
                    "http": "http://example.com",
                    "interval": "10s",
                    "DeregisterCriticalServiceAfter": "1m",
                },
            ),
            (
                "http://example.com",
                "10s",
                "1s",
                "1m",
                None,
                {
                    "http": "http://example.com",
                    "interval": "10s",
                    "timeout": "1s",
                    "DeregisterCriticalServiceAfter": "1m",
                },
            ),
            (
                "http://example.com",
                "10s",
                "1s",
                "1m",
                {"X-Test-Header": ["TestHeaderValue"]},
                {
                    "http": "http://example.com",
                    "interval": "10s",
                    "timeout": "1s",
                    "DeregisterCriticalServiceAfter": "1m",
                    "header": {"X-Test-Header": ["TestHeaderValue"]},
                },
            ),
        ],
    )
    def test_http_check(self, url, interval, timeout, deregister, header, want) -> None:
        ch = consul.check.Check.http(url, interval, timeout=timeout, deregister=deregister, header=header)
        assert ch == want

    @pytest.mark.parametrize(
        ("host", "port", "interval", "timeout", "deregister", "want"),
        [
            (
                "localhost",
                1234,
                "10s",
                None,
                None,
                {
                    "tcp": "localhost:1234",
                    "interval": "10s",
                },
            ),
            (
                "localhost",
                1234,
                "10s",
                "1s",
                None,
                {
                    "tcp": "localhost:1234",
                    "interval": "10s",
                    "timeout": "1s",
                },
            ),
            (
                "localhost",
                1234,
                "10s",
                None,
                "1m",
                {
                    "tcp": "localhost:1234",
                    "interval": "10s",
                    "DeregisterCriticalServiceAfter": "1m",
                },
            ),
            (
                "localhost",
                1234,
                "10s",
                "1s",
                "1m",
                {
                    "tcp": "localhost:1234",
                    "interval": "10s",
                    "timeout": "1s",
                    "DeregisterCriticalServiceAfter": "1m",
                },
            ),
        ],
    )
    def test_tcp_check(self, host: str, port: int, interval, timeout, deregister, want) -> None:
        ch = consul.check.Check.tcp(host, port, interval, timeout=timeout, deregister=deregister)
        assert ch == want

    @pytest.mark.parametrize(
        ("container_id", "shell", "script", "interval", "deregister", "want"),
        [
            (
                "wandering_bose",
                "/bin/sh",
                "/bin/true",
                "10s",
                None,
                {
                    "docker_container_id": "wandering_bose",
                    "shell": "/bin/sh",
                    "script": "/bin/true",
                    "interval": "10s",
                },
            ),
            (
                "wandering_bose",
                "/bin/sh",
                "/bin/true",
                "10s",
                "1m",
                {
                    "docker_container_id": "wandering_bose",
                    "shell": "/bin/sh",
                    "script": "/bin/true",
                    "interval": "10s",
                    "DeregisterCriticalServiceAfter": "1m",
                },
            ),
        ],
    )
    def test_docker_check(self, container_id, shell, script, interval, deregister, want) -> None:
        ch = consul.check.Check.docker(container_id, shell, script, interval, deregister=deregister)
        assert ch == want

    def test_ttl_check(self) -> None:
        ch = consul.check.Check.ttl("1m")
        assert ch == {"ttl": "1m"}
