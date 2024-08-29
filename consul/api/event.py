from __future__ import annotations

from typing import Optional

from consul.callback import CB


class Event:
    """
    The event command provides a mechanism to fire a custom user event to
    an entire datacenter. These events are opaque to Consul, but they can
    be used to build scripting infrastructure to do automated deploys,
    restart services, or perform any other orchestration action.

    Unlike most Consul data, which is replicated using consensus, event
    data is purely peer-to-peer over gossip.

    This means it is not persisted and does not have a total ordering. In
    practice, this means you cannot rely on the order of message delivery.
    An advantage however is that events can still be used even in the
    absence of server nodes or during an outage."""

    def __init__(self, agent) -> None:
        self.agent = agent

    def fire(self, name: str, body: str = "", node=None, service=None, tag=None, token: str | None = None):
        """
        Sends an event to Consul's gossip protocol.

        *name* is the Consul-opaque name of the event. This can be filtered
        on in calls to list, below

        *body* is the Consul-opaque body to be delivered with the event.
         From the Consul documentation:
            The underlying gossip also sets limits on the size of a user
            event message. It is hard to give an exact number, as it
            depends on various parameters of the event, but the payload
            should be kept very small (< 100 bytes²). Specifying too large
            of an event will return an error.

        *node*, *service*, and *tag* are regular expressions which remote
        agents will filter against to determine if they should store the
        event

        *token* is an optional `ACL token`_ to apply to this request. If
        the token's policy is not allowed to fire an event of this *name*
        an *ACLPermissionDenied* exception will be raised.
        """
        assert not name.startswith("/"), "keys should not start with a forward slash"
        params = []
        if node is not None:
            params.append(("node", node))
        if service is not None:
            params.append(("service", service))
        if tag is not None:
            params.append(("tag", tag))

        headers = self.agent.prepare_headers(token)
        return self.agent.http.put(CB.json(), f"/v1/event/fire/{name}", params=params, headers=headers, data=body)

    def list(self, name: Optional[str] = None, index=None, wait=None):
        """
        Returns a tuple of (*index*, *events*)
            Note: Since Consul's event protocol uses gossip, there is no
            ordering, and instead index maps to the newest event that
            matches the query.

        *name* is the type of events to list, if None, lists all available.

        *index* is the current event Consul index, suitable for making
        subsequent calls to wait for changes since this query was last run.
        Check https://consul.io/docs/agent/http/event.html#event_list for
        more infos about indexes on events.

        *wait* the maximum duration to wait (e.g. '10s') to retrieve
        a given index. This parameter is only applied if *index* is also
        specified. the wait time by default is 5 minutes.

        Consul agents only buffer the most recent entries. The current
        buffer size is 256, but this value could change in the future.

        Each *event* looks like this::

            {
                  {
                    "ID": "b54fe110-7af5-cafc-d1fb-afc8ba432b1c",
                    "Name": "deploy",
                    "Payload": "1609030",
                    "NodeFilter": "",
                    "ServiceFilter": "",
                    "TagFilter": "",
                    "Version": 1,
                    "LTime": 19
                  },
            }
        """
        params = []
        if name is not None:
            params.append(("name", name))
        if index:
            params.append(("index", index))
            if wait:
                params.append(("wait", wait))
        return self.agent.http.get(CB.json(index=True, decode="Payload"), "/v1/event/list", params=params)
