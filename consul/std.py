from __future__ import annotations

import re

import requests
from requests import Response

from consul import base

__all__ = ["Consul"]

DEFAULT_TIMEOUT = 30
# Consul holds a blocking query without *wait* for 5 minutes.
DEFAULT_WAIT = 5 * 60
DURATION_UNITS = {"ns": 1e-9, "us": 1e-6, "µs": 1e-6, "ms": 1e-3, "s": 1, "m": 60, "h": 3600}


def parse_duration(duration: str) -> float:
    """Parse a Go duration such as "5s", "100ms" or "1m30s" into seconds."""
    return sum(float(n) * DURATION_UNITS[u] for n, u in re.findall(r"([\d.]+)(ns|us|µs|ms|s|m|h)", duration))


class HTTPClient(base.HTTPClient):
    def __init__(self, *args, connections_timeout: float | None = DEFAULT_TIMEOUT, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.session = requests.session()
        self.connections_timeout = connections_timeout

    def timeout(self, params) -> float | None:
        if self.connections_timeout is None:
            return None
        params = dict(params or ())
        if "index" not in params:
            return self.connections_timeout
        # A blocking query sends nothing until its wait, plus up to wait/16
        # of jitter, has elapsed.
        wait = parse_duration(params["wait"]) if "wait" in params else DEFAULT_WAIT
        return self.connections_timeout + wait + wait / 16

    def response(self, response: Response, raw: bool = False):
        if raw:
            # e.g. the gzip archive returned by GET /v1/snapshot -- decoding it as
            # UTF-8 text would corrupt it, so the raw bytes are kept as-is.
            return base.Response(response.status_code, response.headers, response.content)
        response.encoding = "utf-8"
        return base.Response(response.status_code, response.headers, response.text)

    def get(self, callback, path, params=None, headers: dict[str, str] | None = None, raw: bool = False):
        uri = self.uri(path, params)
        return callback(
            self.response(
                self.session.get(
                    uri, headers=headers, verify=self.verify, cert=self.cert, timeout=self.timeout(params)
                ),
                raw=raw,
            )
        )

    def put(self, callback, path, params=None, data: str | bytes = "", headers: dict[str, str] | None = None):
        uri = self.uri(path, params)
        return callback(
            self.response(
                self.session.put(
                    uri,
                    headers=headers,
                    data=data,
                    verify=self.verify,
                    cert=self.cert,
                    timeout=self.timeout(params),
                )
            )
        )

    def delete(self, callback, path, params=None, data: str | bytes = "", headers: dict[str, str] | None = None):
        uri = self.uri(path, params)
        return callback(
            self.response(
                self.session.delete(
                    uri,
                    headers=headers,
                    data=data,
                    verify=self.verify,
                    cert=self.cert,
                    timeout=self.timeout(params),
                )
            )
        )

    def post(self, callback, path, params=None, data: str = "", headers: dict[str, str] | None = None):
        uri = self.uri(path, params)
        return callback(
            self.response(
                self.session.post(
                    uri,
                    headers=headers,
                    data=data,
                    verify=self.verify,
                    cert=self.cert,
                    timeout=self.timeout(params),
                )
            )
        )

    def close(self) -> None:
        pass


class Consul(base.Consul):
    def __init__(self, *args, connections_timeout: float | None = DEFAULT_TIMEOUT, **kwargs) -> None:
        """
        *connections_timeout* is how long, in seconds, to wait for the agent
        to connect or answer before requests raises a timeout, so a
        connection the agent dropped silently does not block forever. For
        a blocking query, the query's *wait* and its jitter are added to it.
        *None* disables the timeout.
        """
        self.connections_timeout = connections_timeout
        super().__init__(*args, **kwargs)

    def http_connect(self, host: str, port: int, scheme, verify: bool | str = True, cert=None):
        return HTTPClient(host, port, scheme, verify, cert, connections_timeout=self.connections_timeout)
