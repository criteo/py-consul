from __future__ import annotations

import json
import typing
from typing import Any, TypedDict

from consul.callback import CB

if typing.TYPE_CHECKING:
    import builtins


class ConfigEntry(TypedDict, total=False):
    Kind: str
    Name: str
    CreateIndex: int
    ModifyIndex: int


class Config:
    """
    Generic CRUD for Consul config entries (service-defaults, service-router,
    service-splitter, service-resolver, service-intentions, ingress-gateway,
    terminating-gateway, proxy-defaults, mesh, exported-services, api-gateway,
    http-route, tcp-route, inline-certificate, file-system-certificate, and
    others) via the single /v1/config endpoint. Required ACLs and the body
    schema vary by *kind* -- see Consul's config entry reference for the
    schema of each kind; this client does not model kind-specific fields.
    """

    def __init__(self, agent) -> None:
        self.agent = agent

    def set(
        self,
        kind: str,
        name: str,
        config_entry: builtins.dict[str, Any] | None = None,
        token: str | None = None,
        dc: str | None = None,
        cas: int | None = None,
    ) -> bool:
        """
        Creates or updates the config entry of *kind* named *name*.
        :param kind: The config entry kind, e.g. "service-defaults".
        :param name: The config entry name.
        :param config_entry: The kind-specific body; merged with Kind/Name.
        :param token: token with the write capability required by *kind* (varies by kind)
        :param dc: Optional datacenter to target; defaults to the client's own dc.
        :param cas: Optional ModifyIndex to check-and-set against; the write only
            applies if it still matches the entry's current ModifyIndex.
        :return: True if the config entry was created or updated
        """
        json_data: dict[str, Any] = dict(config_entry or {})
        json_data["Kind"] = kind
        json_data["Name"] = name

        params: list[tuple[str, Any]] = []
        dc = dc or self.agent.dc
        if dc:
            params.append(("dc", dc))
        if cas is not None:
            params.append(("cas", cas))

        headers = self.agent.prepare_headers(token)
        return self.agent.http.put(CB.json(), "/v1/config", params=params, headers=headers, data=json.dumps(json_data))

    def get(self, kind: str, name: str, token: str | None = None, dc: str | None = None) -> ConfigEntry:
        """
        Reads the config entry of *kind* named *name*.
        :param token: token with the read capability required by *kind*
        :param dc: Optional datacenter to target; defaults to the client's own dc.
        """
        params: list[tuple[str, Any]] = []
        dc = dc or self.agent.dc
        if dc:
            params.append(("dc", dc))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(), f"/v1/config/{kind}/{name}", params=params, headers=headers)

    def list(
        self, kind: str, token: str | None = None, dc: str | None = None, filter_expr: str | None = None
    ) -> builtins.list[ConfigEntry]:
        """
        Lists all config entries of *kind*.
        :param token: token with the read capability required by *kind*
        :param dc: Optional datacenter to target; defaults to the client's own dc.
        :param filter_expr: Optional bexpr filter expression.
        """
        params: list[tuple[str, Any]] = []
        dc = dc or self.agent.dc
        if dc:
            params.append(("dc", dc))
        if filter_expr:
            params.append(("filter", filter_expr))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(), f"/v1/config/{kind}", params=params, headers=headers)

    def delete(
        self, kind: str, name: str, token: str | None = None, dc: str | None = None, cas: int | None = None
    ) -> bool:
        """
        Deletes the config entry of *kind* named *name*.
        :param token: token with the write capability required by *kind*
        :param dc: Optional datacenter to target; defaults to the client's own dc.
        :param cas: Optional ModifyIndex to check-and-set against; the delete only
            applies if it still matches the entry's current ModifyIndex. Without it,
            deletion is unconditional (Consul returns an empty object rather than a
            boolean in that case, hence the two different callbacks below).
        :return: True if the config entry was deleted
        """
        params: list[tuple[str, Any]] = []
        dc = dc or self.agent.dc
        if dc:
            params.append(("dc", dc))
        headers = self.agent.prepare_headers(token)
        if cas is not None:
            params.append(("cas", cas))
            return self.agent.http.delete(CB.json(), f"/v1/config/{kind}/{name}", params=params, headers=headers)
        return self.agent.http.delete(CB.boolean(), f"/v1/config/{kind}/{name}", params=params, headers=headers)
