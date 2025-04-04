from __future__ import annotations

import abc
import collections
import logging
import os
import urllib
from typing import TYPE_CHECKING, Any, Optional

from consul.api.acl import ACL
from consul.api.agent import Agent
from consul.api.catalog import Catalog
from consul.api.connect import Connect
from consul.api.coordinates import Coordinate
from consul.api.event import Event
from consul.api.health import Health
from consul.api.kv import KV
from consul.api.operator import Operator
from consul.api.query import Query
from consul.api.session import Session
from consul.api.status import Status
from consul.api.txn import Txn
from consul.exceptions import ConsulException

if TYPE_CHECKING:
    from types import TracebackType

log = logging.getLogger(__name__)


#
# Convenience to define checks


Response = collections.namedtuple("Response", ["code", "headers", "body"])


class HTTPClient(metaclass=abc.ABCMeta):
    def __init__(
        self, host: str = "127.0.0.1", port: int = 8500, scheme: str = "http", verify: bool = True, cert=None
    ) -> None:
        self.host = host
        self.port = port
        self.scheme = scheme
        self.verify = verify
        self.base_uri = f"{self.scheme}://{self.host}:{self.port}"
        self.cert = cert

    def uri(self, path: str, params: list[tuple[str, Any]] | None = None):
        uri = self.base_uri + urllib.parse.quote(path, safe="/:")
        if params:
            uri = f"{uri}?{urllib.parse.urlencode(params)}"
        return uri

    @abc.abstractmethod
    def get(self, callback, path, params=None, headers: Optional[dict[str, str]] = None):
        raise NotImplementedError

    @abc.abstractmethod
    def put(self, callback, path, params=None, data: str = "", headers: Optional[dict[str, str]] = None):
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, callback, path, params=None, headers: Optional[dict[str, str]] = None):
        raise NotImplementedError

    @abc.abstractmethod
    def post(self, callback, path, params=None, data: str = "", headers: Optional[dict[str, str]] = None):
        raise NotImplementedError

    @abc.abstractmethod
    def close(self):
        raise NotImplementedError


class Consul:
    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        token: str | None = None,
        scheme: str | None = None,
        consistency: str = "default",
        dc=None,
        verify: bool | None = None,
        cert=None,
    ) -> None:
        """
        *token* is an optional `ACL token`_. If supplied it will be used by
        default for all requests made with this client session. It's still
        possible to override this token by passing a token explicitly for a
        request.

        *consistency* sets the consistency mode to use by default for all reads
        that support the consistency option. It's still possible to override
        this by passing explicitly for a given request. *consistency* can be
        either 'default', 'consistent' or 'stale'.

        *dc* is the datacenter that this agent will communicate with.
        By default the datacenter of the host is used.

        *verify* is whether to verify the SSL certificate for HTTPS requests

        *cert* client side certificates for HTTPS requests
        """

        # TODO: Status

        if os.getenv("CONSUL_HTTP_ADDR") and not (host or port):
            try:
                host, port = os.getenv("CONSUL_HTTP_ADDR").split(":")  # type: ignore
            except ValueError as err:
                raise ConsulException(
                    f"CONSUL_HTTP_ADDR ({os.getenv('CONSUL_HTTP_ADDR')}) invalid, does not match <host>:<port>"
                ) from err
        if not host:
            host = "127.0.0.1"
        if not port:
            port = 8500

        if scheme is None:
            use_ssl = os.getenv("CONSUL_HTTP_SSL")
            scheme = ("https" if use_ssl.lower() == "true" else "http") if use_ssl else "http"

        if verify is None:
            ssl_verify = os.getenv("CONSUL_HTTP_SSL_VERIFY")
            verify = ssl_verify.lower() == "true" if ssl_verify else True

        self.http = self.http_connect(host, port, scheme, verify, cert)
        self.token = os.getenv("CONSUL_HTTP_TOKEN", token)
        self.scheme = scheme
        self.dc = dc
        assert consistency in (
            "default",
            "consistent",
            "stale",
        ), "consistency must be either default, consistent or state"
        self.consistency = consistency

        self.event = Event(self)
        self.kv = KV(self)
        self.txn = Txn(self)
        self.agent = Agent(self)
        self.catalog = Catalog(self)
        self.health = Health(self)
        self.session = Session(self)
        self.acl = ACL(self)
        self.status = Status(self)
        self.query = Query(self)
        self.coordinate = Coordinate(self)
        self.operator = Operator(self)
        self.connect = Connect(self)

    def __enter__(self):
        return self

    async def __aenter__(self):
        return self

    def __exit__(
        self, exc_type: Optional[type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[TracebackType]
    ) -> None:
        self.http.close()

    async def __aexit__(
        self, exc_type: Optional[type[BaseException]], exc: Optional[BaseException], tb: Optional[TracebackType]
    ) -> None:
        await self.http.close()

    @abc.abstractmethod
    def http_connect(self, host: str, port: int, scheme, verify: bool = True, cert=None):
        pass

    def prepare_headers(self, token: Optional[str] = None) -> dict[str, str]:
        headers = {}
        if token or self.token:
            headers["X-Consul-Token"] = token or self.token
        return headers  # type: ignore
