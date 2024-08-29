from __future__ import annotations

from consul.callback import CB


class KV:
    """
    The KV endpoint is used to expose a simple key/value store. This can be
    used to store service configurations or other meta data in a simple
    way.
    """

    def __init__(self, agent) -> None:
        self.agent = agent

    def get(
        self,
        key,
        index=None,
        recurse: bool = False,
        wait=None,
        token: str | None = None,
        consistency=None,
        keys: bool = False,
        separator=None,
        dc=None,
        connections_timeout=None,
    ):
        """
        Returns a tuple of (*index*, *value[s]*)

        *index* is the current Consul index, suitable for making subsequent
        calls to wait for changes since this query was last run.

        *wait* the maximum duration to wait (e.g. '10s') to retrieve
        a given index. this parameter is only applied if *index* is also
        specified. the wait time by default is 5 minutes.

        *token* is an optional `ACL token`_ to apply to this request.

        *keys* is a boolean which, if True, says to return a flat list of
        keys without values or other metadata. *separator* can be used
        with *keys* to list keys only up to a given separator character.

        *dc* is the optional datacenter that you wish to communicate with.
        If None is provided, defaults to the agent's datacenter.

        The *value* returned is for the specified key, or if *recurse* is
        True a list of *values* for all keys with the given prefix is
        returned.

        Each *value* looks like this::

            {
                "CreateIndex": 100,
                "ModifyIndex": 200,
                "LockIndex": 200,
                "Key": "foo",
                "Flags": 0,
                "Value": "bar",
                "Session": "adf4238a-882b-9ddc-4a9d-5b6758e4159e"
            }

        Note, if the requested key does not exists *(index, None)* is
        returned. It's then possible to long poll on the index for when the
        key is created.
        """
        assert not key.startswith("/"), "keys should not start with a forward slash"
        params = []
        if index:
            params.append(("index", index))
            if wait:
                params.append(("wait", wait))
        if recurse:
            params.append(("recurse", "1"))
        dc = dc or self.agent.dc
        if dc:
            params.append(("dc", dc))
        if keys:
            params.append(("keys", True))
        if separator:
            params.append(("separator", separator))
        consistency = consistency or self.agent.consistency
        if consistency in ("consistent", "stale"):
            params.append((consistency, "1"))

        one = False
        decode: bool | str = False

        if not keys:
            decode = "Value"
        if not recurse and not keys:
            one = True
        http_kwargs = {}
        if connections_timeout:
            http_kwargs["connections_timeout"] = connections_timeout

        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(
            CB.json(index=True, decode=decode, one=one), f"/v1/kv/{key}", params=params, headers=headers, **http_kwargs
        )

    def put(
        self,
        key,
        value,
        cas=None,
        flags=None,
        acquire=None,
        release=None,
        token: str | None = None,
        dc=None,
        connections_timeout=None,
    ):
        """
        Sets *key* to the given *value*.

        *value* can either be None (useful for marking a key as a
        directory) or any string type, including binary data (e.g. a
        msgpack'd data structure)

        The optional *cas* parameter is used to turn the PUT into a
        Check-And-Set operation. This is very useful as it allows clients
        to build more complex syncronization primitives on top. If the
        index is 0, then Consul will only put the key if it does not
        already exist. If the index is non-zero, then the key is only set
        if the index matches the ModifyIndex of that key.

        An optional *flags* can be set. This can be used to specify an
        unsigned value between 0 and 2^64-1.

        *acquire* is an optional session_id. if supplied a lock acquisition
        will be attempted.

        *release* is an optional session_id. if supplied a lock release
        will be attempted.

        *token* is an optional `ACL token`_ to apply to this request. If
        the token's policy is not allowed to write to this key an
        *ACLPermissionDenied* exception will be raised.

        *dc* is the optional datacenter that you wish to communicate with.
        If None is provided, defaults to the agent's datacenter.

        The return value is simply either True or False. If False is
        returned, then the update has not taken place.
        """
        assert not key.startswith("/"), "keys should not start with a forward slash"
        assert value is None or isinstance(value, (str, bytes)), "value should be None or a string / binary data"

        params = []
        if cas is not None:
            params.append(("cas", cas))
        if flags is not None:
            params.append(("flags", flags))
        if acquire:
            params.append(("acquire", acquire))
        if release:
            params.append(("release", release))
        dc = dc or self.agent.dc
        if dc:
            params.append(("dc", dc))
        http_kwargs = {}
        if connections_timeout:
            http_kwargs["connections_timeout"] = connections_timeout
        headers = self.agent.prepare_headers(token)
        return self.agent.http.put(
            CB.json(), f"/v1/kv/{key}", params=params, headers=headers, data=value, **http_kwargs
        )

    def delete(self, key, recurse=None, cas=None, token: str | None = None, dc=None, connections_timeout=None):
        """
        Deletes a single key or if *recurse* is True, all keys sharing a
        prefix.

        *cas* is an optional flag is used to turn the DELETE into a
        Check-And-Set operation. This is very useful as a building block
        for more complex synchronization primitives. Unlike PUT, the index
        must be greater than 0 for Consul to take any action: a 0 index
        will not delete the key. If the index is non-zero, the key is only
        deleted if the index matches the ModifyIndex of that key.

        *token* is an optional `ACL token`_ to apply to this request. If
        the token's policy is not allowed to delete to this key an
        *ACLPermissionDenied* exception will be raised.

        *dc* is the optional datacenter that you wish to communicate with.
        If None is provided, defaults to the agent's datacenter.
        """
        assert not key.startswith("/"), "keys should not start with a forward slash"

        params = []
        if recurse:
            params.append(("recurse", "1"))
        if cas is not None:
            params.append(("cas", cas))
        dc = dc or self.agent.dc
        if dc:
            params.append(("dc", dc))
        http_kwargs = {}
        if connections_timeout:
            http_kwargs["connections_timeout"] = connections_timeout
        headers = self.agent.prepare_headers(token)
        return self.agent.http.delete(CB.json(), f"/v1/kv/{key}", params=params, headers=headers, **http_kwargs)
