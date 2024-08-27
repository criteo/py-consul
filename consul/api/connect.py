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

            headers = self.agent.prepare_headers(token)
            return self.agent.http.get(CB.json(), "/v1/connect/ca/roots", params=params, headers=headers)

        def configuration(self, token=None):
            params = []

            headers = self.agent.prepare_headers(token)
            return self.agent.http.get(CB.json(), "/v1/connect/ca/configuration", params=params, headers=headers)
