import abc
import collections
import logging
import os
import urllib
from typing import Dict, Optional

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

log = logging.getLogger(__name__)


#
# Convenience to define checks


Response = collections.namedtuple("Response", ["code", "headers", "body"])


class HTTPClient(metaclass=abc.ABCMeta):
    def __init__(self, host="127.0.0.1", port=8500, scheme="http", verify=True, cert=None):
        self.host = host
        self.port = port
        self.scheme = scheme
        self.verify = verify
        self.base_uri = f"{self.scheme}://{self.host}:{self.port}"
        self.cert = cert

    def uri(self, path, params=None):
        uri = self.base_uri + urllib.parse.quote(path, safe="/:")
        if params:
            uri = f"{uri}?{urllib.parse.urlencode(params)}"
        return uri

    @abc.abstractmethod
    def get(self, callback, path, params=None, headers: Optional[Dict[str, str]] = None):
        raise NotImplementedError

    @abc.abstractmethod
    def put(self, callback, path, params=None, data="", headers: Optional[Dict[str, str]] = None):
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, callback, path, params=None, headers: Optional[Dict[str, str]] = None):
        raise NotImplementedError

    @abc.abstractmethod
    def post(self, callback, path, params=None, data="", headers: Optional[Dict[str, str]] = None):
        raise NotImplementedError

    @abc.abstractmethod
    def close(self):
        raise NotImplementedError


class Consul:
    def __init__(
        self,
        host="127.0.0.1",
        port=8500,
        token=None,
        scheme="http",
        consistency="default",
        dc=None,
        verify=True,
        cert=None,
    ):
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

        if os.getenv("CONSUL_HTTP_ADDR"):
            try:
                host, port = os.getenv("CONSUL_HTTP_ADDR").split(":")
            except ValueError as err:
                raise ConsulException(
                    f"CONSUL_HTTP_ADDR ({os.getenv('CONSUL_HTTP_ADDR')}) invalid, does not match <host>:<port>"
                ) from err
        use_ssl = os.getenv("CONSUL_HTTP_SSL")
        if use_ssl is not None:
            scheme = "https" if use_ssl == "true" else "http"
        if os.getenv("CONSUL_HTTP_SSL_VERIFY") is not None:
            verify = os.getenv("CONSUL_HTTP_SSL_VERIFY") == "true"

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

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.http.close()

    async def __aexit__(self, exc_type, exc, tb):
        await self.http.close()

    @abc.abstractmethod
    def http_connect(self, host, port, scheme, verify=True, cert=None):
        pass

    def prepare_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        headers = {}
        if token or self.token:
            headers["X-Consul-Token"] = token or self.token
        return headers
