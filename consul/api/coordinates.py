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
