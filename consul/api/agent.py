from __future__ import annotations

import json
from typing import Any

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
        self.token = Agent.Token(agent)

    def self(self):
        """
        Returns configuration of the local agent and member information.
        """
        return self.agent.http.get(CB.json(), "/v1/agent/self")

    def services(self, filter_expr: str | None = None, token: str | None = None) -> Any:
        """
        Returns all the services that are registered with the local agent.
        These services were either provided through configuration files, or
        added dynamically using the HTTP API. It is important to note that
        the services known by the agent may be different than those
        reported by the Catalog. This is usually due to changes being made
        while there is no leader elected. The agent performs active
        anti-entropy, so in most situations everything will be in sync
        within a few seconds.
        :param filter_expr: Optional bexpr filter expression.
        :param token: token with node:read,service:read capability
        """
        params: list[tuple[str, Any]] = []
        if filter_expr:
            params.append(("filter", filter_expr))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(), "/v1/agent/services", params=params, headers=headers)

    def service_definition(self, service_id):
        """
        Returns a service definition for a single instance that is registered
        with the local agent.
        """
        return self.agent.http.get(CB.json(), f"/v1/agent/service/{service_id}")

    def checks(self, filter_expr: str | None = None, token: str | None = None) -> Any:
        """
        Returns all the checks that are registered with the local agent.
        These checks were either provided through configuration files, or
        added dynamically using the HTTP API. Similar to services,
        the checks known by the agent may be different than those
        reported by the Catalog. This is usually due to changes being made
        while there is no leader elected. The agent performs active
        anti-entropy, so in most situations everything will be in sync
        within a few seconds.
        :param filter_expr: Optional bexpr filter expression.
        :param token: token with node:read,service:read capability
        """
        params: list[tuple[str, Any]] = []
        if filter_expr:
            params.append(("filter", filter_expr))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(), "/v1/agent/checks", params=params, headers=headers)

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

    def maintenance(self, enable: bool, reason: str | None = None, token: str | None = None):
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

    def force_leave(self, node: str, prune: bool = False, token: str | None = None):
        """
        This endpoint instructs the agent to force a node into the left
        state. If a node fails unexpectedly, then it will be in a failed
        state. Once in the failed state, Consul will attempt to reconnect,
        and the services and checks belonging to that node will not be
        cleaned up. Forcing a node into the left state allows its old
        entries to be removed.

        *node* is the node to change state for.

        *prune* if set to *True* removes the node from the list of members
        entirely, instead of leaving it in the "left" state. Added in
        Consul 1.13.
        """

        params: list[tuple[str, Any]] = []
        if prune:
            params.append(("prune", "1"))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.put(CB.boolean(), f"/v1/agent/force-leave/{node}", params=params, headers=headers)

    def leave(self, token: str | None = None):
        """
        Triggers a graceful leave and shutdown of the agent. It is used to
        ensure other nodes see the agent as "left" instead of "failed".
        Nodes that leave are permanently removed from the cluster's
        membership until they rejoin. For agents running in server mode,
        this also removes the node from the Raft peer set in a graceful
        manner.

        Note that calling this will actually terminate the agent process.

        Requires a token with `agent:write` ACL capability.
        """
        headers = self.agent.prepare_headers(token)
        return self.agent.http.put(CB.boolean(), "/v1/agent/leave", headers=headers)

    def reload(self, token: str | None = None):
        """
        Instructs the agent to reload its configuration. Not all
        configuration options are reloadable, see the "Reloadable
        Configuration" section of the Consul documentation for the set of
        options that take effect via reload.

        Requires a token with `agent:write` ACL capability.
        """
        headers = self.agent.prepare_headers(token)
        return self.agent.http.put(CB.boolean(), "/v1/agent/reload", headers=headers)

    def metrics(self, format_prometheus: bool = False, token: str | None = None) -> Any:
        """
        Returns the metrics of the local agent for the most recent finished
        interval. By default, the response is returned as JSON.

        *format_prometheus* if set to *True*, returns the metrics formatted
        as ``text/plain`` in the Prometheus exposition format instead of
        JSON. Note that Prometheus output is only populated if the agent
        was started with a positive
        `telemetry.prometheus_retention_time` configured; otherwise Consul
        returns an empty 200 response body (with an `X-Consul-Reason`
        header explaining why) rather than an error.

        Requires a token with `agent:read` ACL capability.
        """
        params = []
        if format_prometheus:
            params.append(("format", "prometheus"))
        headers = self.agent.prepare_headers(token)

        if format_prometheus:
            # Prometheus output is plain text, not JSON, so CB.json() can't be used here.
            def cb(response):
                CB._status(response)  # pylint: disable=protected-access
                return response.body

            return self.agent.http.get(cb, "/v1/agent/metrics", params=params, headers=headers)

        return self.agent.http.get(CB.json(), "/v1/agent/metrics", params=params, headers=headers)

    def monitor(self, loglevel: str | None = None, logjson: bool = False, token: str | None = None) -> Any:
        """
        Streams logs from the local agent until the connection is closed.

        *loglevel* is an optional log level to filter on, e.g. "trace",
        "debug", "info", "warn", or "err". Defaults to "info" on the
        Consul side if not supplied.

        *logjson* if set to *True*, outputs each log line as JSON instead
        of Consul's default plain-text log format.

        Requires a token with `agent:read` ACL capability.

        .. warning::
            In real Consul this is a chunked/streaming endpoint that keeps
            the connection open indefinitely, only sending data as new log
            lines are produced; it does not close the connection on its
            own. This client implementation is a first pass and does
            **not** provide true streaming: it makes a single blocking GET
            request and returns whatever text body has accumulated once
            the connection ends. Neither the underlying sync nor async
            HTTP clients in this library currently expose a per-call
            socket/read timeout, so calling this method against a live,
            long-running agent can block forever unless the connection is
            closed by some other means (e.g. the agent shutting down, or a
            timeout enforced by the caller, such as running this call in a
            separate thread/task and cancelling it externally). Do not use
            this method in latency-sensitive or production code paths
            until true streaming support is added.
        """
        params = []
        if loglevel:
            params.append(("loglevel", loglevel))
        if logjson:
            params.append(("logjson", "true"))
        headers = self.agent.prepare_headers(token)

        def cb(response):
            # the response body is plain text log lines (optionally one JSON
            # object per line if logjson=True), never a single JSON document,
            # so we can't use CB.json() here.
            CB._status(response)  # pylint: disable=protected-access
            return response.body

        return self.agent.http.get(cb, "/v1/agent/monitor", params=params, headers=headers)

    class Service:
        def __init__(self, agent) -> None:
            self.agent = agent

        @staticmethod
        def _gateway_proxy_fields(
            kind: str | None,
            proxy: dict[str, Any] | None,
            socket_path: str | None,
            locality: dict[str, str] | None,
        ) -> dict[str, Any]:
            fields: dict[str, Any] = {}
            if kind:
                fields["Kind"] = kind
            if proxy:
                fields["Proxy"] = proxy
            if socket_path:
                fields["SocketPath"] = socket_path
            if locality:
                fields["Locality"] = locality
            return fields

        # pylint: disable=too-many-branches
        def register(
            self,
            name: str,
            service_id=None,
            address=None,
            port: int | None = None,
            tags=None,
            check=None,
            token: str | None = None,
            meta=None,
            weights=None,
            # *deprecated* use check parameter
            script=None,
            interval=None,
            ttl: int | None = None,
            http=None,
            timeout=None,
            enable_tag_override: bool = False,
            extra_checks=None,
            replace_existing_checks=False,
            tagged_addresses: dict | None = None,
            connect: dict[str, Any] | None = None,
            kind: str | None = None,
            proxy: dict[str, Any] | None = None,
            socket_path: str | None = None,
            locality: dict[str, str] | None = None,
        ):
            """
            Add a new service to the local agent. There is more
            documentation on services
            `here <https://developer.hashicorp.com/consul/docs/fundamentals/service>`_.

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

            *tagged_addresses* specifies alternative addresses for the service,
            e.g. for use with Connect. Formatted as { "lan": "<address>", "wan": "<address>" }.

            *connect* specifies configuration for Connect. Formatted as { "sidecar_service": {} }.

            *kind* identifies this as a proxy/gateway instance rather than a plain
            service, e.g. "connect-proxy", "mesh-gateway", "terminating-gateway" or
            "ingress-gateway".

            *proxy* specifies the connect proxy configuration when *kind* is
            "connect-proxy", e.g. {"DestinationServiceName": "web", "LocalServicePort": 8080}.

            *socket_path* specifies a Unix domain socket path the service listens on,
            as an alternative to *address*/*port*.

            *locality* specifies the region/zone this service instance is deployed to,
            e.g. {"Region": "us-west-1", "Zone": "us-west-1a"}.

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
            https://developer.hashicorp.com/consul/docs/fundamentals/service
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
            if tagged_addresses:
                payload["tagged_addresses"] = tagged_addresses
            if connect:
                payload["connect"] = connect
            payload.update(self._gateway_proxy_fields(kind, proxy, socket_path, locality))
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

        def maintenance(self, service_id: str, enable: bool, reason: str | None = None, token: str | None = None):
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
            ttl: int | None = None,
            http=None,
            timeout=None,
        ):
            """
            Register a new check with the local agent. More documentation
            on checks can be found `here
            <https://developer.hashicorp.com/consul/docs/register/health-check/vm>`_.

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
            `here <https://developer.hashicorp.com/consul/api-docs/agent/connect>`_.

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

    class Token:
        """
        Used to update the ACL tokens currently in use by the local agent.
        See `here <https://developer.hashicorp.com/consul/api-docs/agent#update-acl-tokens>`_
        for more information.

        Tokens set this way are only persisted to disk (surviving an agent
        restart) if the agent was started with
        `acl.enable_token_persistence` set to *True*.
        """

        #: Literal path segments accepted by Consul for `PUT /v1/agent/token/:type`.
        VALID_TOKEN_TYPES = frozenset({
            "default",
            "agent",
            "agent_recovery",
            "replication",
            "config_file_service_registration",
        })

        def __init__(self, agent) -> None:
            self.agent = agent

        def set(self, token_type: str, secret: str, token: str | None = None) -> bool:
            """
            Sets the ACL token currently in use by the agent for *token_type*.

            *token_type* must be one of "default", "agent", "agent_recovery",
            "replication" or "config_file_service_registration". Note that
            "agent_recovery" was named "agent_master" in Consul versions
            prior to 1.11.

            *secret* is the secret ID of the ACL token to set. Pass an
            empty string to clear the currently configured token.

            *token* is an optional ACL token to authenticate this request;
            it requires `agent:write` ACL capability.

            Returns *True* on success.
            """
            if token_type not in Agent.Token.VALID_TOKEN_TYPES:
                raise ValueError(
                    f"token_type must be one of {sorted(Agent.Token.VALID_TOKEN_TYPES)}, got {token_type!r}"
                )
            payload = {"Token": secret}
            headers = self.agent.prepare_headers(token)
            return self.agent.http.put(
                CB.boolean(), f"/v1/agent/token/{token_type}", headers=headers, data=json.dumps(payload)
            )

        def set_default(self, secret: str, token: str | None = None) -> bool:
            """
            Sets the default ACL token used for both client requests and
            to secure the agent's internal RPCs itself.
            """
            return self.set("default", secret, token=token)

        def set_agent(self, secret: str, token: str | None = None) -> bool:
            """
            Sets the ACL token used for internal agent operations, such
            as service/check registration and anti-entropy syncs. Falls
            back to the "default" token if not set.
            """
            return self.set("agent", secret, token=token)

        def set_agent_recovery(self, secret: str, token: str | None = None) -> bool:
            """
            Sets the ACL agent recovery token. This token can be used to
            access agent endpoints even when the servers are unreachable,
            e.g. for local troubleshooting. It was named "agent_master"
            in Consul versions prior to 1.11.
            """
            return self.set("agent_recovery", secret, token=token)

        def set_replication(self, secret: str, token: str | None = None) -> bool:
            """
            Sets the ACL replication token used to replicate ACLs, as
            well as Connect Certificate Authority state and prepared
            queries, to non-primary datacenters.
            """
            return self.set("replication", secret, token=token)

        def set_config_file_service_registration(self, secret: str, token: str | None = None) -> bool:
            """
            Sets the ACL token used for service registrations declared in
            the agent's local configuration files.
            """
            return self.set("config_file_service_registration", secret, token=token)
