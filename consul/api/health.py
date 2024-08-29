from __future__ import annotations

from consul.callback import CB


class Health:
    # TODO: All of the health endpoints support all consistency modes
    def __init__(self, agent) -> None:
        self.agent = agent

    def _service(
        self,
        internal_uri,
        index=None,
        wait=None,
        passing=None,
        tag=None,
        dc=None,
        near=None,
        token: str | None = None,
        node_meta=None,
    ):
        params = []
        if index:
            params.append(("index", index))
            if wait:
                params.append(("wait", wait))
        if passing:
            params.append(("passing", "1"))
        if tag is not None:
            if not isinstance(tag, list):
                tag = [tag]
            for tag_item in tag:
                params.append(("tag", tag_item))
        dc = dc or self.agent.dc
        if dc:
            params.append(("dc", dc))
        if near:
            params.append(("near", near))
        if node_meta:
            for nodemeta_name, nodemeta_value in node_meta.items():
                params.append(("node-meta", f"{nodemeta_name}:{nodemeta_value}"))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(index=True), internal_uri, params=params, headers=headers)

    def service(self, service: str, **kwargs):
        """
        Returns a tuple of (*index*, *nodes*)

        *index* is the current Consul index, suitable for making subsequent
        calls to wait for changes since this query was last run.

        *wait* the maximum duration to wait (e.g. '10s') to retrieve
        a given index. this parameter is only applied if *index* is also
        specified. the wait time by default is 5 minutes.

        *nodes* are the nodes providing the given service.

        Calling with *passing* set to True will filter results to only
        those nodes whose checks are currently passing.

        Calling with *tag* will filter the results by tag, multiple tags
        using list possible.

        *dc* is the datacenter of the node and defaults to this agents
        datacenter.

        *near* is a node name to sort the resulting list in ascending
        order based on the estimated round trip time from that node

        *token* is an optional `ACL token`_ to apply to this request.

        *node_meta* is an optional meta data used for filtering, a
        dictionary formatted as {k1:v1, k2:v2}.
        """
        internal_uri = f"/v1/health/service/{service}"
        return self._service(internal_uri=internal_uri, **kwargs)

    def connect(self, service, **kwargs):
        """
        Returns a tuple of (*index*, *nodes*) of the nodes providing
        connect-capable *service* in the *dc* datacenter. *dc* defaults
        to the current datacenter of this agent.

        Request arguments and response format are the same as health.service
        """
        internal_uri = f"/v1/health/connect/{service}"
        return self._service(internal_uri=internal_uri, **kwargs)

    def checks(self, service, index=None, wait=None, dc=None, near=None, token: str | None = None, node_meta=None):
        """
        Returns a tuple of (*index*, *checks*) with *checks* being the
        checks associated with the service.

        *service* is the name of the service being checked.

        *index* is the current Consul index, suitable for making subsequent
        calls to wait for changes since this query was last run.

        *wait* the maximum duration to wait (e.g. '10s') to retrieve
        a given index. this parameter is only applied if *index* is also
        specified. the wait time by default is 5 minutes.

        *dc* is the datacenter of the node and defaults to this agents
        datacenter.

        *near* is a node name to sort the resulting list in ascending
        order based on the estimated round trip time from that node

        *token* is an optional `ACL token`_ to apply to this request.

        *node_meta* is an optional meta data used for filtering, a
        dictionary formatted as {k1:v1, k2:v2}.
        """
        params = []
        if index:
            params.append(("index", index))
            if wait:
                params.append(("wait", wait))
        dc = dc or self.agent.dc
        if dc:
            params.append(("dc", dc))
        if near:
            params.append(("near", near))
        if node_meta:
            for nodemeta_name, nodemeta_value in node_meta.items():
                params.append(("node-meta", f"{nodemeta_name}:{nodemeta_value}"))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(index=True), f"/v1/health/checks/{service}", params=params, headers=headers)

    def state(self, name: str, index=None, wait=None, dc=None, near=None, token: str | None = None, node_meta=None):
        """
        Returns a tuple of (*index*, *nodes*)

        *name* is a supported state. From the Consul docs:

            The supported states are any, unknown, passing, warning, or
            critical. The any state is a wildcard that can be used to
            return all checks.

        *index* is the current Consul index, suitable for making subsequent
        calls to wait for changes since this query was last run.

        *wait* the maximum duration to wait (e.g. '10s') to retrieve
        a given index. this parameter is only applied if *index* is also
        specified. the wait time by default is 5 minutes.

        *dc* is the datacenter of the node and defaults to this agents
        datacenter.

        *near* is a node name to sort the resulting list in ascending
        order based on the estimated round trip time from that node

        *token* is an optional `ACL token`_ to apply to this request.

        *node_meta* is an optional meta data used for filtering, a
        dictionary formatted as {k1:v1, k2:v2}.

        *nodes* are the nodes providing the given service.
        """
        assert name in ["any", "unknown", "passing", "warning", "critical"]
        params = []
        if index:
            params.append(("index", index))
            if wait:
                params.append(("wait", wait))
        dc = dc or self.agent.dc
        if dc:
            params.append(("dc", dc))
        if near:
            params.append(("near", near))
        if node_meta:
            for nodemeta_name, nodemeta_value in node_meta.items():
                params.append(("node-meta", f"{nodemeta_name}:{nodemeta_value}"))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(index=True), f"/v1/health/state/{name}", params=params, headers=headers)

    def node(self, node, index=None, wait=None, dc=None, token: str | None = None):
        """
        Returns a tuple of (*index*, *checks*)

        *index* is the current Consul index, suitable for making subsequent
        calls to wait for changes since this query was last run.

        *wait* the maximum duration to wait (e.g. '10s') to retrieve
        a given index. this parameter is only applied if *index* is also
        specified. the wait time by default is 5 minutes.

        *dc* is the datacenter of the node and defaults to this agents
        datacenter.

        *token* is an optional `ACL token`_ to apply to this request.

        *nodes* are the nodes providing the given service.
        """
        params = []
        if index:
            params.append(("index", index))
            if wait:
                params.append(("wait", wait))
        dc = dc or self.agent.dc
        if dc:
            params.append(("dc", dc))

        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(index=True), f"/v1/health/node/{node}", params=params, headers=headers)
