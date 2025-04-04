from typing import Optional

import requests
from requests import Response

from consul import base

__all__ = ["Consul"]


class HTTPClient(base.HTTPClient):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.session = requests.session()

    def response(self, response: Response):
        response.encoding = "utf-8"
        return base.Response(response.status_code, response.headers, response.text)

    def get(self, callback, path, params=None, headers: Optional[dict[str, str]] = None):
        uri = self.uri(path, params)
        return callback(self.response(self.session.get(uri, headers=headers, verify=self.verify, cert=self.cert)))

    def put(self, callback, path, params=None, data: str = "", headers: Optional[dict[str, str]] = None):
        uri = self.uri(path, params)
        return callback(
            self.response(self.session.put(uri, headers=headers, data=data, verify=self.verify, cert=self.cert))
        )

    def delete(self, callback, path, params=None, headers: Optional[dict[str, str]] = None):
        uri = self.uri(path, params)
        return callback(self.response(self.session.delete(uri, headers=headers, verify=self.verify, cert=self.cert)))

    def post(self, callback, path, params=None, data: str = "", headers: Optional[dict[str, str]] = None):
        uri = self.uri(path, params)
        return callback(
            self.response(self.session.post(uri, headers=headers, data=data, verify=self.verify, cert=self.cert))
        )

    def close(self) -> None:
        pass


class Consul(base.Consul):
    def http_connect(self, host: str, port: int, scheme, verify: bool = True, cert=None):
        return HTTPClient(host, port, scheme, verify, cert)
