from consul.callback import CB


class Status:
    """
    The Status endpoints are used to get information about the status
     of the Consul cluster.
    """

    def __init__(self, agent) -> None:
        self.agent = agent

    def leader(self):
        """
        This endpoint is used to get the Raft leader for the datacenter
        in which the agent is running.
        """
        return self.agent.http.get(CB.json(), "/v1/status/leader")

    def peers(self):
        """
        This endpoint retrieves the Raft peers for the datacenter in which
        the the agent is running.
        """
        return self.agent.http.get(CB.json(), "/v1/status/peers")
