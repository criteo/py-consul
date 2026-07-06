from __future__ import annotations

import json

from consul.callback import CB


class Catalog:
    def __init__(self, agent) -> None:
        self.agent = agent

    def register(
        self,
        node,
        address,
        service=None,
        check=None,
        dc=None,
        token: str | None = None,
        node_meta=None,
        skip_node_update: bool | None = None,
        tagged_addresses=None,
    ):
        """
        A low level mechanism for directly registering or updating entries
        in the catalog. It is usually recommended to use
        agent.service.register and agent.check.register, as they are
        simpler and perform anti-entropy.

        *node* is the name of the node to register.

        *address* is the ip of the node.

        *service* is an optional service to register. if supplied this is a
        dict::

            {
                "Service": "redis",
                "ID": "redis1",
                "Tags": [
                    "master",
                    "v1"
                ],
                "Port": 8000
            }

        where

            *Service* is required and is the name of the service

            *ID* is optional, and will be set to *Service* if not provided.
            Note *ID* must be unique for the given *node*.

            *Tags* and *Port* are optional.

        *check* is an optional check to register. if supplied this is a
        dict::

            {
                "Node": "foobar",
                "CheckID": "service:redis1",
                "Name": "Redis health check",
                "Notes": "Script based health check",
                "Status": "passing",
                "ServiceID": "redis1"
            }

        *dc* is the datacenter of the node and defaults to this agents
        datacenter.

        *token* is an optional `ACL token`_ to apply to this request.

        *node_meta* is an optional meta data used for filtering, a
        dictionary formatted as {k1:v1, k2:v2}.

        *skip_node_update* is an optional boolean which, if set to True,
        skips updating the node's information in the registration.

        *tagged_addresses* is an optional dictionary of tagged addresses
        for the node, formatted as {k1:v1, k2:v2}.

        This manipulates the health check entry, but does not setup a
        script or TTL to actually update the status. The full documentation
        is `here <https://developer.hashicorp.com/consul/api-docs/catalog>`_.

        Returns *True* on success.
        """
        data = {"node": node, "address": address}
        params = []
        dc = dc or self.agent.dc
        if dc:
            data["datacenter"] = dc
        if service:
            data["service"] = service
        if check:
            data["check"] = check
        token = token or self.agent.token
        if token:
            data["WriteRequest"] = {"Token": token}
            params.append(("token", token))
        if node_meta:
            for nodemeta_name, nodemeta_value in node_meta.items():
                params.append(("node-meta", f"{nodemeta_name}:{nodemeta_value}"))
        if skip_node_update is not None:
            data["SkipNodeUpdate"] = skip_node_update
        if tagged_addresses:
            data["TaggedAddresses"] = tagged_addresses

        headers = self.agent.prepare_headers(token)
        return self.agent.http.put(
            CB.boolean(), "/v1/catalog/register", data=json.dumps(data), params=params, headers=headers
        )

    def deregister(self, node, service_id=None, check_id=None, dc=None, token: str | None = None):
        """
        A low level mechanism for directly removing entries in the catalog.
        It is usually recommended to use the agent APIs, as they are
        simpler and perform anti-entropy.

        *node* and *dc* specify which node on which datacenter to remove.
        If *service_id* and *check_id* are not provided, all associated
        services and checks are deleted. Otherwise only one of *service_id*
        and *check_id* should be provided and only that service or check
        will be removed.

        *token* is an optional `ACL token`_ to apply to this request.

        Returns *True* on success.
        """
        assert not (service_id and check_id)
        data = {"node": node}
        dc = dc or self.agent.dc
        if dc:
            data["datacenter"] = dc
        if service_id:
            data["serviceid"] = service_id
        if check_id:
            data["checkid"] = check_id
        token = token or self.agent.token
        if token:
            data["WriteRequest"] = {"Token": token}
        headers = self.agent.prepare_headers(token)
        return self.agent.http.put(CB.boolean(), "/v1/catalog/deregister", headers=headers, data=json.dumps(data))

    def datacenters(self):
        """
        Returns all the datacenters that are known by the Consul server.
        """
        return self.agent.http.get(CB.json(), "/v1/catalog/datacenters")

    def nodes(
        self,
        index=None,
        wait=None,
        consistency=None,
        dc=None,
        near=None,
        token: str | None = None,
        node_meta=None,
        filter_expr: str | None = None,
    ):
        """
        Returns a tuple of (*index*, *nodes*) of all nodes known
        about in the *dc* datacenter. *dc* defaults to the current
        datacenter of this agent.

        *index* is the current Consul index, suitable for making subsequent
        calls to wait for changes since this query was last run.

        *wait* the maximum duration to wait (e.g. '10s') to retrieve
        a given index. this parameter is only applied if *index* is also
        specified. the wait time by default is 5 minutes.

        *near* is a node name to sort the resulting list in ascending
        order based on the estimated round trip time from that node

        *consistency* can be either 'default', 'consistent' or 'stale'. if
        not specified *consistency* will the consistency level this client
        was configured with.

        *token* is an optional `ACL token`_ to apply to this request.

        *node_meta* is an optional meta data used for filtering, a
        dictionary formatted as {k1:v1, k2:v2}.

        *filter_expr* is an optional bexpr filter expression to filter the
        results.

        The response looks like this::

            (index, [
                {
                    "Node": "baz",
                    "Address": "10.1.10.11"
                },
                {
                    "Node": "foobar",
                    "Address": "10.1.10.12"
                }
            ])
        """
        params = []
        dc = dc or self.agent.dc
        if dc:
            params.append(("dc", dc))
        if index:
            params.append(("index", index))
            if wait:
                params.append(("wait", wait))
        if near:
            params.append(("near", near))

        consistency = consistency or self.agent.consistency
        if consistency in ("consistent", "stale"):
            params.append((consistency, "1"))
        if node_meta:
            for nodemeta_name, nodemeta_value in node_meta.items():
                params.append(("node-meta", f"{nodemeta_name}:{nodemeta_value}"))
        if filter_expr:
            params.append(("filter", filter_expr))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(index=True), "/v1/catalog/nodes", params=params, headers=headers)

    def services(
        self,
        index=None,
        wait=None,
        consistency=None,
        dc=None,
        token: str | None = None,
        node_meta=None,
        filter_expr: str | None = None,
    ):
        """
        Returns a tuple of (*index*, *services*) of all services known
        about in the *dc* datacenter. *dc* defaults to the current
        datacenter of this agent.

        *index* is the current Consul index, suitable for making subsequent
        calls to wait for changes since this query was last run.

        *wait* the maximum duration to wait (e.g. '10s') to retrieve
        a given index. this parameter is only applied if *index* is also
        specified. the wait time by default is 5 minutes.

        *consistency* can be either 'default', 'consistent' or 'stale'. if
        not specified *consistency* will the consistency level this client
        was configured with.

        *token* is an optional `ACL token`_ to apply to this request.

        *node_meta* is an optional meta data used for filtering, a
        dictionary formatted as {k1:v1, k2:v2}.

        *filter_expr* is an optional bexpr filter expression to filter the
        results.

        The response looks like this::

            (index, {
                "consul": [],
                "redis": [],
                "postgresql": [
                    "master",
                    "slave"
                ]
            })

        The main keys are the service names and the list provides all the
        known tags for a given service.
        """
        params = []
        dc = dc or self.agent.dc
        if dc:
            params.append(("dc", dc))
        if index:
            params.append(("index", index))
            if wait:
                params.append(("wait", wait))
        consistency = consistency or self.agent.consistency
        if consistency in ("consistent", "stale"):
            params.append((consistency, "1"))
        if node_meta:
            for nodemeta_name, nodemeta_value in node_meta.items():
                params.append(("node-meta", f"{nodemeta_name}:{nodemeta_value}"))
        if filter_expr:
            params.append(("filter", filter_expr))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(index=True), "/v1/catalog/services", params=params, headers=headers)

    def node(
        self,
        node,
        index=None,
        wait=None,
        consistency=None,
        dc=None,
        token: str | None = None,
        filter_expr: str | None = None,
    ):
        """
        Returns a tuple of (*index*, *services*) of all services provided
        by *node*.

        *index* is the current Consul index, suitable for making subsequent
        calls to wait for changes since this query was last run.

        *wait* the maximum duration to wait (e.g. '10s') to retrieve
        a given index. this parameter is only applied if *index* is also
        specified. the wait time by default is 5 minutes.

        *consistency* can be either 'default', 'consistent' or 'stale'. if
        not specified *consistency* will the consistency level this client
        was configured with.

        *dc* is the datacenter of the node and defaults to this agents
        datacenter.

        *token* is an optional `ACL token`_ to apply to this request.

        *filter_expr* is an optional bexpr filter expression to filter the
        results.

        The response looks like this::

            (index, {
                "Node": {
                    "Node": "foobar",
                    "Address": "10.1.10.12"
                },
                "Services": {
                    "consul": {
                        "ID": "consul",
                        "Service": "consul",
                        "Tags": null,
                        "Port": 8300
                    },
                    "redis": {
                        "ID": "redis",
                        "Service": "redis",
                        "Tags": [
                            "v1"
                        ],
                        "Port": 8000
                    }
                }
            })
        """
        params = []
        dc = dc or self.agent.dc
        if dc:
            params.append(("dc", dc))
        if index:
            params.append(("index", index))
            if wait:
                params.append(("wait", wait))
        consistency = consistency or self.agent.consistency
        if consistency in ("consistent", "stale"):
            params.append((consistency, "1"))
        if filter_expr:
            params.append(("filter", filter_expr))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(index=True), f"/v1/catalog/node/{node}", params=params, headers=headers)

    def _service(
        self,
        internal_uri,
        index=None,
        wait=None,
        tag=None,
        consistency=None,
        dc=None,
        near=None,
        token: str | None = None,
        node_meta=None,
        filter_expr: str | None = None,
        peer: str | None = None,
        merge_central_config: bool | None = None,
    ):
        params = []
        dc = dc or self.agent.dc
        if dc:
            params.append(("dc", dc))
        if tag:
            params.append(("tag", tag))
        if index:
            params.append(("index", index))
            if wait:
                params.append(("wait", wait))
        if near:
            params.append(("near", near))
        consistency = consistency or self.agent.consistency
        if consistency in ("consistent", "stale"):
            params.append((consistency, "1"))
        if node_meta:
            for nodemeta_name, nodemeta_value in node_meta.items():
                params.append(("node-meta", f"{nodemeta_name}:{nodemeta_value}"))
        if filter_expr:
            params.append(("filter", filter_expr))
        if peer:
            params.append(("peer", peer))
        if merge_central_config:
            params.append(("merge-central-config", "1"))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(index=True), internal_uri, params=params, headers=headers)

    def service(self, service: str, **kwargs):
        """
        Returns a tuple of (*index*, *nodes*) of the nodes providing
        *service* in the *dc* datacenter. *dc* defaults to the current
        datacenter of this agent.

        *index* is the current Consul index, suitable for making subsequent
        calls to wait for changes since this query was last run.

        *wait* the maximum duration to wait (e.g. '10s') to retrieve
        a given index. this parameter is only applied if *index* is also
        specified. the wait time by default is 5 minutes.

        If *tag* is provided, the list of nodes returned will be filtered
        by that tag.

        *near* is a node name to sort the resulting list in ascending
        order based on the estimated round trip time from that node

        *consistency* can be either 'default', 'consistent' or 'stale'. if
        not specified *consistency* will the consistency level this client
        was configured with.

        *token* is an optional `ACL token`_ to apply to this request.

        *node_meta* is an optional meta data used for filtering, a
        dictionary formatted as {k1:v1, k2:v2}.

        *filter_expr* is an optional bexpr filter expression to filter the
        results.

        *peer* is an optional name of the peer that exported the service.

        *merge_central_config* is an optional boolean which, if set to
        True, merges the service's central configuration (proxy-defaults
        and service-defaults) into the response.

        The response looks like this::

            (index, [
                {
                    "Node": "foobar",
                    "Address": "10.1.10.12",
                    "ServiceID": "redis",
                    "ServiceName": "redis",
                    "ServiceTags": null,
                    "ServicePort": 8000
                }
            ])
        """
        internal_uri = f"/v1/catalog/service/{service}"
        return self._service(internal_uri=internal_uri, **kwargs)

    def connect(self, service: str, **kwargs):
        """
        Returns a tuple of (*index*, *nodes*) of the nodes providing
        connect-capable *service* in the *dc* datacenter. *dc* defaults
        to the current datacenter of this agent.

        Request arguments and response format are the same as catalog.service
        """
        internal_uri = f"/v1/catalog/connect/{service}"
        return self._service(internal_uri=internal_uri, **kwargs)

    def gateway_services(self, gateway: str, dc=None, token: str | None = None):
        """
        Returns the services associated with an ingress or terminating
        gateway.

        *gateway* is the name of the gateway to list services for.

        *dc* is the datacenter of the gateway and defaults to this agents
        datacenter.

        *token* is an optional `ACL token`_ to apply to this request.

        The response looks like this for an ingress gateway::

            [
                {
                    "Gateway": {
                        "Name": "ingress-gateway",
                        "Namespace": "default"
                    },
                    "Service": {
                        "Name": "web",
                        "Namespace": "default"
                    },
                    "GatewayKind": "ingress-gateway",
                    "Port": 8080,
                    "Protocol": "tcp",
                    "Hosts": [],
                    "CAFile": "",
                    "CertFile": "",
                    "KeyFile": "",
                    "SNI": "",
                    "FromWildcard": false,
                    "CreateIndex": 16,
                    "ModifyIndex": 16
                }
            ]

        and like this for a terminating gateway::

            [
                {
                    "Gateway": {
                        "Name": "terminating-gateway",
                        "Namespace": "default"
                    },
                    "Service": {
                        "Name": "api",
                        "Namespace": "default"
                    },
                    "GatewayKind": "terminating-gateway",
                    "Port": 0,
                    "Protocol": "",
                    "Hosts": null,
                    "CAFile": "/etc/certs/ca.pem",
                    "CertFile": "/etc/certs/api/client.pem",
                    "KeyFile": "/etc/certs/api/client.key",
                    "SNI": "api.my-domain",
                    "FromWildcard": false,
                    "CreateIndex": 16,
                    "ModifyIndex": 16
                }
            ]
        """
        params = []
        dc = dc or self.agent.dc
        if dc:
            params.append(("dc", dc))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(), f"/v1/catalog/gateway-services/{gateway}", params=params, headers=headers)
