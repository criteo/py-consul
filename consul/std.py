from __future__ import annotations

import requests
from requests import Response

from consul import base

__all__ = ["Consul"]


class HTTPClient(base.HTTPClient):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.session = requests.session()

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
            self.response(self.session.get(uri, headers=headers, verify=self.verify, cert=self.cert), raw=raw)
        )

    def put(self, callback, path, params=None, data: str | bytes = "", headers: dict[str, str] | None = None):
        uri = self.uri(path, params)
        return callback(
            self.response(self.session.put(uri, headers=headers, data=data, verify=self.verify, cert=self.cert))
        )

    def delete(self, callback, path, params=None, data: str | bytes = "", headers: dict[str, str] | None = None):
        uri = self.uri(path, params)
        return callback(
            self.response(self.session.delete(uri, headers=headers, data=data, verify=self.verify, cert=self.cert))
        )

    def post(self, callback, path, params=None, data: str = "", headers: dict[str, str] | None = None):
        uri = self.uri(path, params)
        return callback(
            self.response(self.session.post(uri, headers=headers, data=data, verify=self.verify, cert=self.cert))
        )

    def close(self) -> None:
        pass


class Consul(base.Consul):
    def http_connect(self, host: str, port: int, scheme, verify: bool | str = True, cert=None):
        return HTTPClient(host, port, scheme, verify, cert)
