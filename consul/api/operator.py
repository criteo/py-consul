from consul.callback import CB


class Operator:
    def __init__(self, agent) -> None:
        self.agent = agent

    def raft_config(self):
        """
        Returns raft configuration.
        """
        return self.agent.http.get(CB.json(), "/v1/operator/raft/configuration")
