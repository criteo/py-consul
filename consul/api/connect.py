from consul.callback import CB


class Connect:
    def __init__(self, agent):
        self.agent = agent
        self.ca = Connect.CA(agent)

    class CA:
        def __init__(self, agent):
            self.agent = agent

        def roots(self, pem=False, token=None):
            params = []
            params.append(("pem", int(pem)))
            token = token or self.agent.token
            if token:
                params.append(("token", token))

            return self.agent.http.get(CB.json(), "/v1/connect/ca/roots", params=params)

        def configuration(self, token=None):
            params = []
            token = token or self.agent.token
            if token:
                params.append(("token", token))

            return self.agent.http.get(CB.json(), "/v1/connect/ca/configuration", params=params)
