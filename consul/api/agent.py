from __future__ import annotations

import json
from typing import Any, Optional

from consul import Check
from consul.callback import CB


class Agent:
    """
    The Agent endpoints are used to interact with a local Consul agent.
    Usually, services and checks are registered with an agent, which then
    takes on the burden of registering with the Catalog and performing
    anti-entropy to recover from outages.
    """

    def __init__(self, agent) -> None:
        self.agent = agent
        self.service = Agent.Service(agent)
        self.check = Agent.Check(agent)
        self.connect = Agent.Connect(agent)

    def self(self):
        """
        Returns configuration of the local agent and member information.
        """
        return self.agent.http.get(CB.json(), "/v1/agent/self")

    def services(self) -> Any:
        """
        Returns all the services that are registered with the local agent.
        These services were either provided through configuration files, or
        added dynamically using the HTTP API. It is important to note that
        the services known by the agent may be different than those
        reported by the Catalog. This is usually due to changes being made
        while there is no leader elected. The agent performs active
        anti-entropy, so in most situations everything will be in sync
        within a few seconds.
        """
        return self.agent.http.get(CB.json(), "/v1/agent/services")

    def service_definition(self, service_id):
        """
        Returns a service definition for a single instance that is registered
        with the local agent.
        """
        return self.agent.http.get(CB.json(), f"/v1/agent/service/{service_id}")

    def checks(self) -> Any:
        """
        Returns all the checks that are registered with the local agent.
        These checks were either provided through configuration files, or
        added dynamically using the HTTP API. Similar to services,
        the checks known by the agent may be different than those
        reported by the Catalog. This is usually due to changes being made
        while there is no leader elected. The agent performs active
        anti-entropy, so in most situations everything will be in sync
        within a few seconds.
        """
        return self.agent.http.get(CB.json(), "/v1/agent/checks")

    def members(self, wan: bool = False):
        """
        Returns all the members that this agent currently sees. This may
        vary by agent, use the nodes api of Catalog to retrieve a cluster
        wide consistent view of members.

        For agents running in server mode, setting *wan* to *True* returns
        the list of WAN members instead of the LAN members which is
        default.
        """
        params = []
        if wan:
            params.append(("wan", 1))
        return self.agent.http.get(CB.json(), "/v1/agent/members", params=params)

    def maintenance(self, enable: bool, reason: Optional[str] = None, token: str | None = None):
        """
        The node maintenance endpoint can place the agent into
        "maintenance mode".

        *enable* is either 'true' or 'false'. 'true' enables maintenance
        mode, 'false' disables maintenance mode.

        *reason* is an optional string. This is simply to aid human
        operators.
        """

        params: list[tuple[str, Any]] = []

        params.append(("enable", enable))
        if reason:
            params.append(("reason", reason))

        headers = self.agent.prepare_headers(token)
        return self.agent.http.put(CB.boolean(), "/v1/agent/maintenance", params=params, headers=headers)

    def join(self, address: str, wan: bool = False, token: str | None = None):
        """
        This endpoint instructs the agent to attempt to connect to a
        given address.

        *address* is the ip to connect to.

        *wan* is either 'true' or 'false'. For agents running in server
        mode, 'true' causes the agent to attempt to join using the WAN
        pool. Default is 'false'.
        """

        params = []

        if wan:
            params.append(("wan", 1))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.put(CB.boolean(), f"/v1/agent/join/{address}", params=params, headers=headers)

    def force_leave(self, node: str, token: str | None = None):
        """
        This endpoint instructs the agent to force a node into the left
        state. If a node fails unexpectedly, then it will be in a failed
        state. Once in the failed state, Consul will attempt to reconnect,
        and the services and checks belonging to that node will not be
        cleaned up. Forcing a node into the left state allows its old
        entries to be removed.

        *node* is the node to change state for.
        """

        headers = self.agent.prepare_headers(token)
        return self.agent.http.put(CB.boolean(), f"/v1/agent/force-leave/{node}", headers=headers)

    class Service:
        def __init__(self, agent) -> None:
            self.agent = agent

        def register(
            self,
            name: str,
            service_id=None,
            address=None,
            port: Optional[int] = None,
            tags=None,
            check=None,
            token: str | None = None,
            meta=None,
            weights=None,
            # *deprecated* use check parameter
            script=None,
            interval=None,
            ttl: Optional[int] = None,
            http=None,
            timeout=None,
            enable_tag_override: bool = False,
            extra_checks=None,
            replace_existing_checks=False,
        ):
            """
            Add a new service to the local agent. There is more
            documentation on services
            `here <http://www.consul.io/docs/agent/services.html>`_.

            *name* is the name of the service.

            If the optional *service_id* is not provided it is set to
            *name*. You cannot have duplicate *service_id* entries per
            agent, so it may be necessary to provide one.

            *address* will default to the address of the agent if not
            provided.

            An optional health *check* can be created for this service is
            one of `Check.script`_, `Check.http`_, `Check.tcp`_,
            `Check.ttl`_ or `Check.docker`_.

            *token* is an optional `ACL token`_ to apply to this request.
            Note this call will return successful even if the token doesn't
            have permissions to register this service.

            *meta* specifies arbitrary KV metadata linked to the service
            formatted as {k1:v1, k2:v2}.

            *weights* specifies weights for the service; default to
            {"Passing": 1, "Warning": 1}.

            *script*, *interval*, *ttl*, *http*, and *timeout* arguments
            are deprecated. use *check* instead.

            *replace_existing_checks* Missing health checks from the request will
            be deleted from the agent.
            Using this parameter allows to idempotently register a service and its
            checks without having to manually deregister checks.

            *enable_tag_override* is an optional bool that enable you
            to modify a service tags from servers(consul agent role server)
            Default is set to False.
            This option is only for >=v0.6.0 version on both agent and
            servers.
            for more information
            https://www.consul.io/docs/agent/services.html
            """

            if extra_checks is None:
                extra_checks = []
            payload: dict[str, Any] = {}

            payload["name"] = name
            if enable_tag_override:
                payload["enabletagoverride"] = enable_tag_override
            if service_id:
                payload["id"] = service_id
            if address:
                payload["address"] = address
            if port:
                payload["port"] = port
            if tags:
                payload["tags"] = tags
            if meta:
                payload["meta"] = meta
            if check:
                payload["checks"] = [check] + extra_checks
            if weights:
                payload["weights"] = weights
            else:
                payload.update(
                    Check._compat(  # pylint: disable=protected-access
                        script=script, interval=interval, ttl=ttl, http=http, timeout=timeout
                    )
                )
            params = []
            if replace_existing_checks:
                params.append(("replace-existing-checks", "true"))
            headers = self.agent.prepare_headers(token)
            return self.agent.http.put(
                CB.boolean(), "/v1/agent/service/register", params=params, headers=headers, data=json.dumps(payload)
            )

        def deregister(self, service_id: str, token: str | None = None):
            """
            Used to remove a service from the local agent. The agent will
            take care of deregistering the service with the Catalog. If
            there is an associated check, that is also deregistered.
            """
            headers = self.agent.prepare_headers(token)

            return self.agent.http.put(CB.boolean(), f"/v1/agent/service/deregister/{service_id}", headers=headers)

        def maintenance(self, service_id: str, enable: bool, reason: Optional[str] = None, token: str | None = None):
            """
            The service maintenance endpoint allows placing a given service
            into "maintenance mode".

            *service_id* is the id of the service that is to be targeted
            for maintenance.

            *enable* is either 'true' or 'false'. 'true' enables
            maintenance mode, 'false' disables maintenance mode.

            *reason* is an optional string. This is simply to aid human
            operators.
            """

            params: list[tuple[str, Any]] = []

            params.append(("enable", enable))
            if reason:
                params.append(("reason", reason))

            headers = self.agent.prepare_headers(token)

            return self.agent.http.put(
                CB.boolean(), f"/v1/agent/service/maintenance/{service_id}", params=params, headers=headers
            )

    class Check:
        def __init__(self, agent) -> None:
            self.agent = agent

        def register(
            self,
            name: str,
            check=None,
            check_id=None,
            notes=None,
            service_id=None,
            token: str | None = None,
            # *deprecated* use check parameter
            script=None,
            interval=None,
            ttl: Optional[int] = None,
            http=None,
            timeout=None,
        ):
            """
            Register a new check with the local agent. More documentation
            on checks can be found `here
            <http://www.consul.io/docs/agent/checks.html>`_.

            *name* is the name of the check.

            *check* is one of `Check.script`_, `Check.http`_, `Check.tcp`_
            `Check.ttl`_ or `Check.docker`_ and is required.

            If the optional *check_id* is not provided it is set to *name*.
            *check_id* must be unique for this agent.

            *notes* is not used by Consul, and is meant to be human
            readable.

            Optionally, a *service_id* can be specified to associate a
            registered check with an existing service.

            *token* is an optional `ACL token`_ to apply to this request.
            Note this call will return successful even if the token doesn't
            have permissions to register this check.

            *script*, *interval*, *ttl*, *http*, and *timeout* arguments
            are deprecated. use *check* instead.

            Returns *True* on success.
            """
            payload = {"name": name}

            assert check or script or ttl or http, "check is required"

            if check:
                payload.update(check)

            else:
                payload.update(
                    Check._compat(script=script, interval=interval, ttl=ttl, http=http, timeout=timeout)["check"]
                )

            if check_id:
                payload["id"] = check_id
            if notes:
                payload["notes"] = notes
            if service_id:
                payload["serviceid"] = service_id

            headers = self.agent.prepare_headers(token)
            return self.agent.http.put(
                CB.boolean(), "/v1/agent/check/register", headers=headers, data=json.dumps(payload)
            )

        def deregister(self, check_id: str, token: str | None = None):
            """
            Remove a check from the local agent.
            """
            headers = self.agent.prepare_headers(token)

            return self.agent.http.put(CB.boolean(), f"/v1/agent/check/deregister/{check_id}", headers=headers)

        def ttl_pass(self, check_id: str, notes=None, token: str | None = None):
            """
            Mark a ttl based check as passing. Optional notes can be
            attached to describe the status of the check.
            """
            params = []
            if notes:
                params.append(("note", notes))
            headers = self.agent.prepare_headers(token)

            return self.agent.http.put(CB.boolean(), f"/v1/agent/check/pass/{check_id}", params=params, headers=headers)

        def ttl_fail(self, check_id: str, notes=None, token: str | None = None):
            """
            Mark a ttl based check as failing. Optional notes can be
            attached to describe why check is failing. The status of the
            check will be set to critical and the ttl clock will be reset.
            """
            params = []
            if notes:
                params.append(("note", notes))
            headers = self.agent.prepare_headers(token)

            return self.agent.http.put(CB.boolean(), f"/v1/agent/check/fail/{check_id}", params=params, headers=headers)

        def ttl_warn(self, check_id: str, notes=None, token: str | None = None):
            """
            Mark a ttl based check with warning. Optional notes can be
            attached to describe the warning. The status of the
            check will be set to warn and the ttl clock will be reset.
            """
            params = []
            if notes:
                params.append(("note", notes))
            headers = self.agent.prepare_headers(token)

            return self.agent.http.put(CB.boolean(), f"/v1/agent/check/warn/{check_id}", params=params, headers=headers)

    class Connect:
        def __init__(self, agent) -> None:
            self.agent = agent
            self.ca = Agent.Connect.CA(agent)

        def authorize(self, target, client_cert_uri, client_cert_serial, token: str | None = None):
            """
            Tests whether a connection attempt is authorized between
            two services.
            More information is available
            `here <https://www.consul.io/api-docs/agent/connect>`_.

            *target* is the name of the service that is being requested.

            *client_cert_uri* The unique identifier for the requesting
            client.

            *client_cert_serial* The colon-hex-encoded serial number for
            the requesting client cert.
            """

            payload = {"Target": target, "ClientCertURI": client_cert_uri, "ClientCertSerial": client_cert_serial}

            headers = self.agent.prepare_headers(token)

            return self.agent.http.put(
                CB.json(), "/v1/agent/connect/authorize", headers=headers, data=json.dumps(payload)
            )

        class CA:
            def __init__(self, agent) -> None:
                self.agent = agent

            def roots(self):
                return self.agent.http.get(CB.json(), "/v1/agent/connect/ca/roots")

            def leaf(self, service, token: str | None = None):
                headers = self.agent.prepare_headers(token)

                return self.agent.http.get(CB.json(), f"/v1/agent/connect/ca/leaf/{service}", headers=headers)
