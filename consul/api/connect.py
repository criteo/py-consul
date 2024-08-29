from __future__ import annotations

from typing import Any

from consul.callback import CB


class Connect:
    def __init__(self, agent) -> None:
        self.agent = agent
        self.ca = Connect.CA(agent)

    class CA:
        def __init__(self, agent) -> None:
            self.agent = agent

        def roots(self, pem: bool = False, token: str | None = None):
            params: list[tuple[str, Any]] = []
            params.append(("pem", int(pem)))

            headers = self.agent.prepare_headers(token)
            return self.agent.http.get(CB.json(), "/v1/connect/ca/roots", params=params, headers=headers)

        def configuration(self, token: str | None = None):
            headers = self.agent.prepare_headers(token)
            return self.agent.http.get(CB.json(), "/v1/connect/ca/configuration", headers=headers)
