from typing import Optional

import aiohttp

from consul import Timeout, base

__all__ = ["Consul"]


class HTTPClient(base.HTTPClient):
    """Asyncio adapter for python consul using aiohttp library"""

    def __init__(self, *args, loop=None, connections_limit=None, connections_timeout=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.loop = loop
        connector_kwargs = {}
        if connections_limit:
            connector_kwargs["limit"] = connections_limit
        connector = aiohttp.TCPConnector(loop=self.loop, verify_ssl=self.verify, **connector_kwargs)
        session_kwargs = {}
        if connections_timeout:
            timeout = aiohttp.ClientTimeout(total=connections_timeout)
            session_kwargs["timeout"] = timeout
        self._session = aiohttp.ClientSession(connector=connector, **session_kwargs)  # type: ignore

    async def _request(
        self, callback, method, uri, headers: Optional[dict[str, str]], data=None, connections_timeout=None
    ):
        session_kwargs = {}
        if connections_timeout:
            timeout = aiohttp.ClientTimeout(total=connections_timeout)
            session_kwargs["timeout"] = timeout
        resp = await self._session.request(method, uri, headers=headers, data=data, **session_kwargs)  # type: ignore
        body = await resp.text(encoding="utf-8")
        if resp.status == 599:
            raise Timeout
        r = base.Response(resp.status, resp.headers, body)
        return callback(r)

    def get(self, callback, path, params=None, headers: Optional[dict[str, str]] = None, connections_timeout=None):
        uri = self.uri(path, params)
        return self._request(callback, "GET", uri, headers=headers, connections_timeout=connections_timeout)

    def put(
        self,
        callback,
        path,
        params=None,
        data: str = "",
        headers: Optional[dict[str, str]] = None,
        connections_timeout=None,
    ):
        uri = self.uri(path, params)
        return self._request(callback, "PUT", uri, headers=headers, data=data, connections_timeout=connections_timeout)

    def delete(self, callback, path, params=None, headers: Optional[dict[str, str]] = None, connections_timeout=None):
        uri = self.uri(path, params)
        return self._request(callback, "DELETE", uri, headers=headers, connections_timeout=connections_timeout)

    def post(
        self,
        callback,
        path,
        params=None,
        data: str = "",
        headers: Optional[dict[str, str]] = None,
        connections_timeout=None,
    ):
        uri = self.uri(path, params)
        return self._request(callback, "POST", uri, headers=headers, data=data, connections_timeout=connections_timeout)

    def close(self):
        return self._session.close()


class Consul(base.Consul):
    def __init__(self, *args, loop=None, connections_limit=None, connections_timeout=None, **kwargs) -> None:
        self.loop = loop
        self.connections_limit = connections_limit
        self.connections_timeout = connections_timeout
        super().__init__(*args, **kwargs)

    def http_connect(self, host: str, port: int, scheme, verify: bool = True, cert=None):
        return HTTPClient(
            host,
            port,
            scheme,
            loop=self.loop,
            connections_limit=self.connections_limit,
            connections_timeout=self.connections_timeout,
            verify=verify,
            cert=cert,
        )

    def close(self):
        """Close all opened http connections"""
        return self.http.close()
