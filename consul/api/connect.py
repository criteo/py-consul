from __future__ import annotations

import json
import typing
from typing import Any, TypedDict

from consul.callback import CB

if typing.TYPE_CHECKING:
    import builtins


class Intention(TypedDict, total=False):
    SourceNS: str
    SourceName: str
    DestinationNS: str
    DestinationName: str
    SourcePartition: str
    DestinationPartition: str
    SourcePeer: str
    SourceType: str
    Action: str
    Permissions: list[dict[str, Any]]
    Description: str
    Meta: dict[str, str]
    Precedence: int
    CreateIndex: int
    ModifyIndex: int


class Connect:
    def __init__(self, agent) -> None:
        self.agent = agent
        self.ca = Connect.CA(agent)
        self.intentions = Connect.Intentions(agent)

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

        def update_configuration(
            self,
            provider: str,
            config: dict[str, Any],
            force_without_cross_signing: bool = False,
            token: str | None = None,
        ) -> bool:
            """
            Updates the configuration for the CA provider. Requires a token with
            operator:write capability.
            :param provider: The CA provider type to use, e.g. "consul" or "vault".
            :param config: The raw, provider-specific configuration.
            :param force_without_cross_signing: If True, force a CA change without
                cross-signing support from the old provider. Defaults to False.
            :param token: token with operator:write capability
            :return: True if the configuration was updated
            """
            json_data: dict[str, Any] = {"Provider": provider, "Config": config}
            if force_without_cross_signing:
                json_data["ForceWithoutCrossSigning"] = force_without_cross_signing
            headers = self.agent.prepare_headers(token)
            return self.agent.http.put(
                CB.boolean(), "/v1/connect/ca/configuration", headers=headers, data=json.dumps(json_data)
            )

    class Intentions:
        """
        Manages intentions using the exact-match model (Consul 1.9+). The legacy
        UUID-based CRUD model (``/v1/connect/intentions/:uuid``) is deprecated and
        intentionally not implemented here.
        """

        def __init__(self, agent) -> None:
            self.agent = agent

        def upsert(
            self,
            source: str,
            destination: str,
            token: str | None = None,
            action: str | None = None,
            source_type: str = "consul",
            description: str = "",
            meta: dict[str, str] | None = None,
            permissions: list[dict[str, Any]] | None = None,
            dc: str | None = None,
        ) -> bool:
            """
            Creates or updates an intention between *source* and *destination*.
            Requires a token with intentions:write on the destination service.
            :param source: The source service name (or "*" for wildcard).
            :param destination: The destination service name (or "*" for wildcard).
            :param token: token with intentions:write capability
            :param action: Either "allow" or "deny". Mutually exclusive with *permissions*.
            :param source_type: Currently only "consul" is supported by Consul itself.
            :param description: Free form human-readable description of the intention.
            :param meta: Optional key/value metadata to attach to the intention.
            :param permissions: Optional list of L7 permissions. Mutually exclusive with *action*.
            :param dc: Optional datacenter to target; defaults to the client's own dc.
            :return: True if the intention was created or updated
            """
            params: list[tuple[str, Any]] = [("source", source), ("destination", destination)]
            dc = dc or self.agent.dc
            if dc:
                params.append(("dc", dc))

            json_data: dict[str, Any] = {"SourceType": source_type}
            if action:
                json_data["Action"] = action
            if description:
                json_data["Description"] = description
            if meta:
                json_data["Meta"] = meta
            if permissions:
                json_data["Permissions"] = permissions

            headers = self.agent.prepare_headers(token)
            return self.agent.http.put(
                CB.boolean(), "/v1/connect/intentions/exact", params=params, headers=headers, data=json.dumps(json_data)
            )

        def read(self, source: str, destination: str, token: str | None = None, dc: str | None = None) -> Intention:
            """
            Reads the intention between *source* and *destination*.
            Requires a token with intentions:read on either the source or the destination service.
            """
            params: list[tuple[str, Any]] = [("source", source), ("destination", destination)]
            dc = dc or self.agent.dc
            if dc:
                params.append(("dc", dc))
            headers = self.agent.prepare_headers(token)
            return self.agent.http.get(CB.json(), "/v1/connect/intentions/exact", params=params, headers=headers)

        def delete(self, source: str, destination: str, token: str | None = None, dc: str | None = None) -> bool:
            """
            Deletes the intention between *source* and *destination*.
            Requires a token with intentions:write on the destination service.
            """
            params: list[tuple[str, Any]] = [("source", source), ("destination", destination)]
            dc = dc or self.agent.dc
            if dc:
                params.append(("dc", dc))
            headers = self.agent.prepare_headers(token)
            return self.agent.http.delete(CB.boolean(), "/v1/connect/intentions/exact", params=params, headers=headers)

        def list(
            self, token: str | None = None, dc: str | None = None, filter_expr: str | None = None
        ) -> builtins.list[Intention]:
            """
            Lists all intentions. Requires a token with intentions:read capability.
            :param filter_expr: Optional bexpr filter expression.
            """
            params: list[tuple[str, Any]] = []
            dc = dc or self.agent.dc
            if dc:
                params.append(("dc", dc))
            if filter_expr:
                params.append(("filter", filter_expr))
            headers = self.agent.prepare_headers(token)
            return self.agent.http.get(CB.json(), "/v1/connect/intentions", params=params, headers=headers)

        def check(
            self,
            source: str,
            destination: str,
            token: str | None = None,
            source_type: str | None = None,
            dc: str | None = None,
        ) -> bool:
            """
            Evaluates whether a connection from *source* to *destination* is allowed
            given the current intentions. Requires a token with intentions:read capability.
            :param source_type: Defaults to "consul" server-side if omitted.
            :return: True if the connection is allowed
            """
            params: list[tuple[str, Any]] = [("source", source), ("destination", destination)]
            if source_type:
                params.append(("source-type", source_type))
            dc = dc or self.agent.dc
            if dc:
                params.append(("dc", dc))
            headers = self.agent.prepare_headers(token)
            return self.agent.http.get(
                CB.json(postprocess=lambda data: data["Allowed"]),
                "/v1/connect/intentions/check",
                params=params,
                headers=headers,
            )

        def match(
            self, by: str, name: str, token: str | None = None, dc: str | None = None
        ) -> dict[str, builtins.list[Intention]]:
            """
            Returns the list of intentions matching *name*, in evaluation order.
            Requires a token with intentions:read capability.
            :param by: Either "source" or "destination".
            :param name: The service name to match against.
            """
            assert by in ("source", "destination"), "by must be either 'source' or 'destination'"
            params: list[tuple[str, Any]] = [("by", by), ("name", name)]
            dc = dc or self.agent.dc
            if dc:
                params.append(("dc", dc))
            headers = self.agent.prepare_headers(token)
            return self.agent.http.get(CB.json(), "/v1/connect/intentions/match", params=params, headers=headers)
