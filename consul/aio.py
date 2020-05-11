import asyncio

import aiohttp
from consul import base


__all__ = ['Consul']


class HTTPClient(base.HTTPClient):
    """Asyncio adapter for python consul using aiohttp library"""

    def __init__(self, *args, loop=None, **kwargs):
        super(HTTPClient, self).__init__(*args, **kwargs)
        self._loop = loop or asyncio.get_event_loop()
        connector = aiohttp.TCPConnector(loop=self._loop,
                                         verify_ssl=self.verify)
        self._session = aiohttp.ClientSession(connector=connector)

    async def _request(self, callback, method, uri, data=None):
        resp = await self._session.request(method, uri, data=data)
        body = await resp.text(encoding='utf-8')
        if resp.status == 599:
            raise base.Timeout
        r = base.Response(resp.status, resp.headers, body)
        return callback(r)

    def get(self, callback, path, params=None):
        uri = self.uri(path, params)
        return self._request(callback, 'GET', uri)

    def put(self, callback, path, params=None, data=''):
        uri = self.uri(path, params)
        return self._request(callback, 'PUT', uri, data=data)

    def delete(self, callback, path, params=None):
        uri = self.uri(path, params)
        return self._request(callback, 'DELETE', uri)

    def post(self, callback, path, params=None, data=''):
        uri = self.uri(path, params)
        return self._request(callback, 'POST', uri, data=data)

    def close(self):
        self._session.close()


class Consul(base.Consul):

    def __init__(self, *args, loop=None, **kwargs):
        self._loop = loop or asyncio.get_event_loop()
        super().__init__(*args, **kwargs)

    def connect(self, host, port, scheme, verify=True, cert=None):
        return HTTPClient(host, port, scheme, loop=self._loop,
                          verify=verify, cert=None)

    def close(self):
        """Close all opened http connections"""
        self.http.close()
