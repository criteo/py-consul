from __future__ import annotations

import json
from typing import Optional

from consul.callback import CB


class Session:
    def __init__(self, agent) -> None:
        self.agent = agent

    def create(
        self,
        name: Optional[str] = None,
        node=None,
        checks=None,
        lock_delay: int = 15,
        behavior: str = "release",
        ttl: Optional[int] = None,
        dc=None,
        token: str | None = None,
    ):
        """
        Creates a new session. There is more documentation for sessions
        `here <https://consul.io/docs/internals/sessions.html>`_.

        *name* is an optional human readable name for the session.

        *node* is the node to create the session on. if not provided the
        current agent's node will be used.

        *checks* is a list of checks to associate with the session. if not
        provided it defaults to the *serfHealth* check. It is highly
        recommended that, if you override this list, you include the
        default *serfHealth*.

        *lock_delay* is an integer of seconds.

        *behavior* can be set to either 'release' or 'delete'. This
        controls the behavior when a session is invalidated. By default,
        this is 'release', causing any locks that are held to be released.
        Changing this to 'delete' causes any locks that are held to be
        deleted. 'delete' is useful for creating ephemeral key/value
        entries.

        when *ttl* is provided, the session is invalidated if it is not
        renewed before the TTL expires.  If specified, it is an integer of
        seconds.  Currently it must be between 10 and 86400 seconds.

        *token* is an optional `ACL token` to apply to this request. ACL
        required : session:write

        By default the session will be created in the current datacenter
        but an optional *dc* can be provided.

        Returns the string *session_id* for the session.
        """
        params = []
        dc = dc or self.agent.dc
        if dc:
            params.append(("dc", dc))
        data = {}
        if name:
            data["name"] = name
        if node:
            data["node"] = node
        if checks is not None:
            data["checks"] = checks
        if lock_delay != 15:
            data["lockdelay"] = f"{lock_delay}s"
        assert behavior in ("release", "delete"), "behavior must be release or delete"
        if behavior != "release":
            data["behavior"] = behavior
        if ttl:
            assert 10 <= ttl <= 86400
            data["ttl"] = f"{ttl}s"
        data_str = json.dumps(data) if data else ""

        headers = self.agent.prepare_headers(token)
        return self.agent.http.put(
            CB.json(is_id=True), "/v1/session/create", params=params, headers=headers, data=data_str
        )

    def destroy(self, session_id, dc=None, token: str | None = None):
        """
        Destroys the session *session_id*

        *token* is an optional `ACL token` to apply to this request. ACL
        required : session:write

        Returns *True* on success.
        """
        params = []
        dc = dc or self.agent.dc
        if dc:
            params.append(("dc", dc))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.put(CB.boolean(), f"/v1/session/destroy/{session_id}", headers=headers, params=params)

    def list(self, index=None, wait=None, consistency=None, dc=None, token: str | None = None):
        """
        Returns a tuple of (*index*, *sessions*) of all active sessions in
        the *dc* datacenter. *dc* defaults to the current datacenter of
        this agent.

        *index* is the current Consul index, suitable for making subsequent
        calls to wait for changes since this query was last run.

        *wait* the maximum duration to wait (e.g. '10s') to retrieve
        a given index. this parameter is only applied if *index* is also
        specified. the wait time by default is 5 minutes.

        *consistency* can be either 'default', 'consistent' or 'stale'. if
        not specified *consistency* will the consistency level this client
        was configured with.

        *token* is an optional `ACL token` to apply to this request. ACL
        required : session:read

        The response looks like this::

            (index, [
                {
                    "LockDelay": 1.5e+10,
                    "Checks": [
                        "serfHealth"
                    ],
                    "Node": "foobar",
                    "ID": "adf4238a-882b-9ddc-4a9d-5b6758e4159e",
                    "CreateIndex": 1086449
                },
              ...
           ])
        """
        params = []
        dc = dc or self.agent.dc
        if dc:
            params.append(("dc", dc))
        if index:
            params.append(("index", index))
            if wait:
                params.append(("wait", wait))
        consistency = consistency or self.agent.consistency
        if consistency in ("consistent", "stale"):
            params.append((consistency, "1"))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(index=True), "/v1/session/list", headers=headers, params=params)

    def node(self, node: str, index=None, wait=None, consistency=None, dc=None, token: str | None = None):
        """
        Returns a tuple of (*index*, *sessions*) as per *session.list*, but
        filters the sessions returned to only those active for *node*.

        *index* is the current Consul index, suitable for making subsequent
        calls to wait for changes since this query was last run.

        *wait* the maximum duration to wait (e.g. '10s') to retrieve
        a given index. this parameter is only applied if *index* is also
        specified. the wait time by default is 5 minutes.

        *consistency* can be either 'default', 'consistent' or 'stale'. if
        not specified *consistency* will the consistency level this client
        was configured with.

        *token* is an optional `ACL token` to apply to this request. ACL
        required : session:read
        """
        params = []
        dc = dc or self.agent.dc
        if dc:
            params.append(("dc", dc))
        if index:
            params.append(("index", index))
            if wait:
                params.append(("wait", wait))
        consistency = consistency or self.agent.consistency
        if consistency in ("consistent", "stale"):
            params.append((consistency, "1"))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(index=True), f"/v1/session/node/{node}", headers=headers, params=params)

    def info(self, session_id: str, index=None, wait=None, consistency=None, dc=None, token: str | None = None):
        """
        Returns a tuple of (*index*, *session*) for the session
        *session_id* in the *dc* datacenter. *dc* defaults to the current
        datacenter of this agent.

        *index* is the current Consul index, suitable for making subsequent
        calls to wait for changes since this query was last run.

        *wait* the maximum duration to wait (e.g. '10s') to retrieve
        a given index. this parameter is only applied if *index* is also
        specified. the wait time by default is 5 minutes.

        *consistency* can be either 'default', 'consistent' or 'stale'. if
        not specified *consistency* will the consistency level this client
        was configured with.

        *token* is an optional `ACL token` to apply to this request. ACL
        required : session:read
        """
        params = []
        dc = dc or self.agent.dc
        if dc:
            params.append(("dc", dc))
        if index:
            params.append(("index", index))
            if wait:
                params.append(("wait", wait))
        consistency = consistency or self.agent.consistency
        if consistency in ("consistent", "stale"):
            params.append((consistency, "1"))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(
            CB.json(index=True, one=True), f"/v1/session/info/{session_id}", headers=headers, params=params
        )

    def renew(self, session_id, dc=None, token: str | None = None):
        """
        This is used with sessions that have a TTL, and it extends the
        expiration by the TTL.

        *dc* is the optional datacenter that you wish to communicate with.
        If None is provided, defaults to the agent's datacenter.

        *token* is an optional `ACL token` to apply to this request. ACL
        required : session:write

        Returns the session.
        """
        params = []
        dc = dc or self.agent.dc
        if dc:
            params.append(("dc", dc))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.put(
            CB.json(one=True, allow_404=False), f"/v1/session/renew/{session_id}", headers=headers, params=params
        )
