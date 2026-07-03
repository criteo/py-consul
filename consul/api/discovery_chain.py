from __future__ import annotations

import json
from typing import Any, TypedDict

from consul.callback import CB


class DiscoveryChainResponse(TypedDict, total=False):
    Chain: dict[str, Any]


class DiscoveryChain:
    def __init__(self, agent) -> None:
        self.agent = agent

    def get(
        self,
        service: str,
        compile_dc: str | None = None,
        token: str | None = None,
        override_connect_timeout: str | None = None,
        override_protocol: str | None = None,
        override_mesh_gateway_mode: str | None = None,
    ) -> DiscoveryChainResponse:
        """
        Reads the compiled discovery chain for *service*. Uses POST instead of GET
        whenever an override is supplied, matching Consul's documented behavior for
        passing override parameters in the request body.
        :param service: The service name to compile the discovery chain for.
        :param compile_dc: Optional datacenter to use as the basis of compilation.
        :param token: token with service:read capability
        :param override_connect_timeout: Optional duration override, e.g. "10s".
        :param override_protocol: Optional protocol override, e.g. "http".
        :param override_mesh_gateway_mode: Optional mesh gateway Mode override, e.g. "local".
        :return: The compiled discovery chain
        """
        params: list[tuple[str, Any]] = []
        if compile_dc:
            params.append(("compile-dc", compile_dc))
        headers = self.agent.prepare_headers(token)

        overrides: dict[str, Any] = {}
        if override_connect_timeout:
            overrides["OverrideConnectTimeout"] = override_connect_timeout
        if override_protocol:
            overrides["OverrideProtocol"] = override_protocol
        if override_mesh_gateway_mode:
            overrides["OverrideMeshGateway"] = {"Mode": override_mesh_gateway_mode}

        if overrides:
            return self.agent.http.post(
                CB.json(),
                f"/v1/discovery-chain/{service}",
                params=params,
                headers=headers,
                data=json.dumps(overrides),
            )
        return self.agent.http.get(CB.json(), f"/v1/discovery-chain/{service}", params=params, headers=headers)
