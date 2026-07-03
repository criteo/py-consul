from __future__ import annotations

import json
import typing
from typing import Any, TypedDict

from consul.callback import CB
from consul.exceptions import ConsulException

if typing.TYPE_CHECKING:
    import builtins

    from consul.base import Response


class AutopilotConfiguration(TypedDict, total=False):
    CleanupDeadServers: bool
    LastContactThreshold: str
    MaxTrailingLogs: int
    MinQuorum: int
    ServerStabilizationTime: str
    RedundancyZoneTag: str
    DisableUpgradeMigration: bool
    UpgradeVersionTag: str
    CreateIndex: int
    ModifyIndex: int


class AutopilotServerHealth(TypedDict, total=False):
    ID: str
    Name: str
    Address: str
    SerfStatus: str
    Version: str
    Leader: bool
    LastContact: str
    LastTerm: int
    LastIndex: int
    Healthy: bool
    Voter: bool
    StableSince: str


class AutopilotHealth(TypedDict, total=False):
    Healthy: bool
    FailureTolerance: int
    Servers: builtins.list[AutopilotServerHealth]


class KeyringResponse(TypedDict, total=False):
    WAN: bool
    Datacenter: str
    Segment: str
    Keys: dict[str, int]
    PrimaryKeys: dict[str, int]
    NumNodes: int


class UsageDatacenter(TypedDict, total=False):
    Services: int
    ServiceInstances: int
    ConnectServiceInstances: dict[str, int]
    BillableServiceInstances: int
    Nodes: int


class UsageResponse(TypedDict, total=False):
    Usage: dict[str, UsageDatacenter]
    Index: int
    LastContact: int
    KnownLeader: bool
    ConsistencyLevel: str
    NotModified: bool
    Backend: int
    ResultsFilteredByACLs: bool


def _autopilot_health_cb(response: Response) -> AutopilotHealth:
    """
    Callback for GET /v1/operator/autopilot/health.

    Consul returns 200 when the cluster is healthy and 429 when it is not;
    429 is a normal, expected "unhealthy" response with a full JSON body, not
    an error, so it must not raise like the rest of the 4xx range does.
    """
    if response.code == 429:
        try:
            data = json.loads(response.body)
        except (json.JSONDecodeError, TypeError) as e:
            raise ConsulException(f"Failed to decode JSON: {response.body} {e}") from e
        return data
    return CB.json()(response)


class Operator:
    def __init__(self, agent) -> None:
        self.agent = agent

    def raft_config(self):
        """
        Returns raft configuration.
        """
        return self.agent.http.get(CB.json(), "/v1/operator/raft/configuration")

    def raft_remove_peer(
        self, address: str | None = None, peer_id: str | None = None, token: str | None = None
    ) -> bool:
        """
        Removes the Consul server with given address or ID from the Raft
        configuration. Requires a token with operator:write capability.

        Exactly one of *address* or *peer_id* should be supplied, per Consul's
        raft/peer API.
        :param address: The address (host:port) of the peer to remove.
        :param peer_id: The ID of the peer to remove.
        :param token: token with operator:write capability
        :return: True if the request succeeded
        """
        params: list[tuple[str, Any]] = []
        if address:
            params.append(("address", address))
        if peer_id:
            params.append(("id", peer_id))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.delete(CB.boolean(), "/v1/operator/raft/peer", params=params, headers=headers)

    def raft_transfer_leader(self, peer_id: str | None = None, token: str | None = None) -> bool:
        """
        Transfers Raft leadership away from the current leader to another
        peer. Requires a token with operator:write capability.
        :param peer_id: Optional node ID of the peer to transfer leadership
            to. If not specified, Consul selects a peer at random.
        :param token: token with operator:write capability
        :return: True if the request succeeded
        """
        params: list[tuple[str, Any]] = []
        if peer_id:
            params.append(("id", peer_id))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.post(CB.boolean(), "/v1/operator/raft/transfer-leader", params=params, headers=headers)

    def autopilot_configuration(self, token: str | None = None, dc: str | None = None) -> AutopilotConfiguration:
        """
        Returns the current Autopilot configuration. Requires a token with
        operator:read capability.
        :param token: token with operator:read capability
        :param dc: Optional datacenter to target; defaults to the client's own dc.
        :return: the Autopilot configuration
        """
        params: list[tuple[str, Any]] = []
        dc = dc or self.agent.dc
        if dc:
            params.append(("dc", dc))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(), "/v1/operator/autopilot/configuration", params=params, headers=headers)

    def update_autopilot_configuration(
        self,
        cleanup_dead_servers: bool | None = None,
        last_contact_threshold: str | None = None,
        max_trailing_logs: int | None = None,
        min_quorum: int | None = None,
        server_stabilization_time: str | None = None,
        redundancy_zone_tag: str | None = None,
        disable_upgrade_migration: bool | None = None,
        upgrade_version_tag: str | None = None,
        cas: int | None = None,
        token: str | None = None,
        dc: str | None = None,
    ) -> bool:
        """
        Updates the Autopilot configuration. Requires a token with
        operator:write capability.
        :param cleanup_dead_servers: Optional, whether to remove dead servers
            from the Raft peer list when a new server joins.
        :param last_contact_threshold: Optional duration, e.g. "200ms".
        :param max_trailing_logs: Optional maximum number of log entries a
            server can trail the leader by before being considered unhealthy.
        :param min_quorum: Optional minimum number of servers to maintain
            before autopilot allows a dead server to be removed.
        :param server_stabilization_time: Optional duration, e.g. "10s".
        :param redundancy_zone_tag: Optional -autopilot-redundancy-zone-tag value.
        :param disable_upgrade_migration: Optional, disables Autopilot's
            upgrade migration strategy.
        :param upgrade_version_tag: Optional tag used to override the version
            used during a migration.
        :param cas: Optional Autopilot ModifyIndex to check-and-set against;
            the write only applies if it still matches the current
            configuration's ModifyIndex. Consul always replies with HTTP 200
            here, encoding the actual success/failure of the cas as a JSON
            boolean body, hence the CB.json() callback below rather than
            CB.boolean() (which only looks at the status code).
        :param token: token with operator:write capability
        :param dc: Optional datacenter to target; defaults to the client's own dc.
        :return: True if the update was applied. When *cas* is supplied and does
            not match the current ModifyIndex, False is returned instead of
            raising an error.
        """
        json_data: dict[str, Any] = {}
        if cleanup_dead_servers is not None:
            json_data["CleanupDeadServers"] = cleanup_dead_servers
        if last_contact_threshold is not None:
            json_data["LastContactThreshold"] = last_contact_threshold
        if max_trailing_logs is not None:
            json_data["MaxTrailingLogs"] = max_trailing_logs
        if min_quorum is not None:
            json_data["MinQuorum"] = min_quorum
        if server_stabilization_time is not None:
            json_data["ServerStabilizationTime"] = server_stabilization_time
        if redundancy_zone_tag is not None:
            json_data["RedundancyZoneTag"] = redundancy_zone_tag
        if disable_upgrade_migration is not None:
            json_data["DisableUpgradeMigration"] = disable_upgrade_migration
        if upgrade_version_tag is not None:
            json_data["UpgradeVersionTag"] = upgrade_version_tag

        params: list[tuple[str, Any]] = []
        dc = dc or self.agent.dc
        if dc:
            params.append(("dc", dc))
        if cas is not None:
            params.append(("cas", cas))

        headers = self.agent.prepare_headers(token)
        return self.agent.http.put(
            CB.json(),
            "/v1/operator/autopilot/configuration",
            params=params,
            headers=headers,
            data=json.dumps(json_data),
        )

    def autopilot_health(self, token: str | None = None, dc: str | None = None) -> AutopilotHealth:
        """
        Returns the current health of the servers, as tracked by Autopilot.
        Requires a token with operator:read capability.

        Consul responds with HTTP 200 when the cluster is healthy and HTTP
        429 when it is not; both responses carry the same JSON body shape,
        distinguished by the "Healthy" field, so neither raises an exception.
        :param token: token with operator:read capability
        :param dc: Optional datacenter to target; defaults to the client's own dc.
        :return: the Autopilot health snapshot
        """
        params: list[tuple[str, Any]] = []
        dc = dc or self.agent.dc
        if dc:
            params.append(("dc", dc))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(
            _autopilot_health_cb, "/v1/operator/autopilot/health", params=params, headers=headers
        )

    def keyring_list(
        self, relay_factor: int | None = None, local_only: bool | None = None, token: str | None = None
    ) -> builtins.list[KeyringResponse]:
        """
        Lists the gossip encryption keys installed on every member of the
        WAN and LAN rings. Requires a token with keyring:read capability.
        :param relay_factor: Optional number of extra nodes to relay the
            response through, between 0 and 5.
        :param local_only: Optional, if True, restricts the response to
            queries against the local datacenter's LAN ring only.
        :param token: token with keyring:read capability
        :return: a list of key/ring status entries, one per WAN/LAN ring
        """
        params: list[tuple[str, Any]] = []
        if relay_factor is not None:
            params.append(("relay-factor", relay_factor))
        if local_only is not None:
            params.append(("local-only", "true" if local_only else "false"))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(), "/v1/operator/keyring", params=params, headers=headers)

    def keyring_install(self, key: str, relay_factor: int | None = None, token: str | None = None) -> bool:
        """
        Installs a new gossip encryption key onto every member of the WAN
        and LAN rings. Requires a token with keyring:write capability.
        :param key: The base64-encoded gossip encryption key to install.
        :param relay_factor: Optional number of extra nodes to relay the
            request through, between 0 and 5.
        :param token: token with keyring:write capability
        :return: True if the request succeeded
        """
        params: list[tuple[str, Any]] = []
        if relay_factor is not None:
            params.append(("relay-factor", relay_factor))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.post(
            CB.boolean(), "/v1/operator/keyring", params=params, headers=headers, data=json.dumps({"Key": key})
        )

    def keyring_use(self, key: str, relay_factor: int | None = None, token: str | None = None) -> bool:
        """
        Changes the primary gossip encryption key used on every member of
        the WAN and LAN rings. The key must already be installed before it
        can be used as the primary key. Requires a token with
        keyring:write capability.
        :param key: The base64-encoded gossip encryption key to use as primary.
        :param relay_factor: Optional number of extra nodes to relay the
            request through, between 0 and 5.
        :param token: token with keyring:write capability
        :return: True if the request succeeded
        """
        params: list[tuple[str, Any]] = []
        if relay_factor is not None:
            params.append(("relay-factor", relay_factor))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.put(
            CB.boolean(), "/v1/operator/keyring", params=params, headers=headers, data=json.dumps({"Key": key})
        )

    def keyring_remove(self, key: str, relay_factor: int | None = None, token: str | None = None) -> bool:
        """
        Removes a gossip encryption key from every member of the WAN and
        LAN rings. Requires a token with keyring:write capability.
        :param key: The base64-encoded gossip encryption key to remove.
        :param relay_factor: Optional number of extra nodes to relay the
            request through, between 0 and 5.
        :param token: token with keyring:write capability
        :return: True if the request succeeded
        """
        params: list[tuple[str, Any]] = []
        if relay_factor is not None:
            params.append(("relay-factor", relay_factor))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.delete(
            CB.boolean(), "/v1/operator/keyring", params=params, headers=headers, data=json.dumps({"Key": key})
        )

    def usage(self, global_: bool | None = None, stale: bool | None = None, token: str | None = None) -> UsageResponse:
        """
        Returns key metrics about the cluster, such as the number of
        services, service instances, and nodes. Requires a token with
        operator:read capability.
        :param global_: Optional, if True, returns usage information for
            all known datacenters instead of just the client's own dc.
        :param stale: Optional, if True, allows reading the data from any
            server, not just the leader.
        :param token: token with operator:read capability
        :return: cluster usage statistics
        """
        params: list[tuple[str, Any]] = []
        if global_ is not None:
            params.append(("global", "true" if global_ else "false"))
        if stale is not None:
            params.append(("stale", "true" if stale else "false"))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(), "/v1/operator/usage", params=params, headers=headers)
