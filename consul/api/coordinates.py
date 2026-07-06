from __future__ import annotations

import json

from consul.callback import CB


class Coordinate:
    def __init__(self, agent) -> None:
        self.agent = agent

    def datacenters(self):
        """
        Returns the WAN network coordinates for all Consul servers,
        organized by DCs.
        """
        return self.agent.http.get(CB.json(), "/v1/coordinate/datacenters")

    def nodes(self, dc=None, index=None, wait=None, consistency=None):
        """
        *dc* is the datacenter that this agent will communicate with. By
        default the datacenter of the host is used.

        *index* is the current Consul index, suitable for making subsequent
        calls to wait for changes since this query was last run.

        *wait* the maximum duration to wait (e.g. '10s') to retrieve
        a given index. this parameter is only applied if *index* is also
        specified. the wait time by default is 5 minutes.

        *consistency* can be either 'default', 'consistent' or 'stale'. if
        not specified *consistency* will the consistency level this client
        was configured with.
        """
        params = []
        if dc:
            params.append(("dc", dc))
        if index:
            params.append(("index", index))
            if wait:
                params.append(("wait", wait))
        consistency = consistency or self.agent.consistency
        if consistency in ("consistent", "stale"):
            params.append((consistency, "1"))
        return self.agent.http.get(CB.json(index=True), "/v1/coordinate/nodes", params=params)

    def node(self, node: str, dc=None, index=None, wait=None, consistency=None):
        """
        Returns the LAN network coordinates for the node *node*.

        *dc* is the datacenter that this agent will communicate with. By
        default the datacenter of the host is used.

        *index* is the current Consul index, suitable for making subsequent
        calls to wait for changes since this query was last run.

        *wait* the maximum duration to wait (e.g. '10s') to retrieve
        a given index. this parameter is only applied if *index* is also
        specified. the wait time by default is 5 minutes.

        *consistency* can be either 'default', 'consistent' or 'stale'. if
        not specified *consistency* will the consistency level this client
        was configured with.
        """
        params = []
        if dc:
            params.append(("dc", dc))
        if index:
            params.append(("index", index))
            if wait:
                params.append(("wait", wait))
        consistency = consistency or self.agent.consistency
        if consistency in ("consistent", "stale"):
            params.append((consistency, "1"))
        return self.agent.http.get(CB.json(index=True), f"/v1/coordinate/node/{node}", params=params)

    def update(self, node: str, coord: dict, segment: str | None = None, dc=None, token: str | None = None):
        """
        Updates the LAN network coordinates for the node *node*.

        *coord* is the network coordinate, a dict with the keys 'Adjustment',
        'Error', 'Height' and 'Vec', as returned by *coordinate.node* or
        *coordinate.nodes*.

        *segment* is the network segment the node belongs to. Enterprise
        only.

        *dc* is the datacenter that this agent will communicate with. By
        default the datacenter of the host is used.

        *token* is an optional `ACL token` to apply to this request. ACL
        required : node:write

        Returns *True* on success.
        """
        params = []
        if dc:
            params.append(("dc", dc))
        data = {"Node": node, "Segment": segment or "", "Coord": coord}
        data_str = json.dumps(data)
        headers = self.agent.prepare_headers(token)
        return self.agent.http.put(CB.boolean(), "/v1/coordinate/update", params=params, headers=headers, data=data_str)
