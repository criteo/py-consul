from __future__ import annotations

from typing import Any

from consul.callback import CB


class Snapshot:
    """
    Saves/restores a full point-in-time snapshot of the Consul server state.
    Both endpoints require a management-level ACL token -- not a granular ACL
    rule -- and are primarily intended for disaster recovery.
    """

    def __init__(self, agent) -> None:
        self.agent = agent

    def save(self, token: str | None = None, dc: str | None = None, stale: bool = False) -> bytes:
        """
        Saves a snapshot of the current Consul server state as a gzip archive.
        :param token: a management-level token
        :param dc: Optional datacenter to target; defaults to the client's own dc.
        :param stale: If True, allows any server (not just the leader) to service the request.
        :return: the raw gzip archive bytes
        """
        params: list[tuple[str, Any]] = []
        dc = dc or self.agent.dc
        if dc:
            params.append(("dc", dc))
        if stale:
            params.append(("stale", "true"))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.binary(), "/v1/snapshot", params=params, headers=headers, raw=True)

    def restore(self, snapshot: bytes, token: str | None = None, dc: str | None = None) -> bool:
        """
        Restores a previously-saved snapshot. This is a disaster-recovery operation;
        the target cluster must run the same Consul version as the source cluster.
        :param snapshot: raw gzip archive bytes, as returned by :meth:`save`
        :param token: a management-level token
        :param dc: Optional datacenter to target; defaults to the client's own dc.
        :return: True if the restore succeeded
        """
        params: list[tuple[str, Any]] = []
        dc = dc or self.agent.dc
        if dc:
            params.append(("dc", dc))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.put(CB.boolean(), "/v1/snapshot", params=params, headers=headers, data=snapshot)
