from __future__ import annotations

import json
import typing
from typing import Any, TypedDict

from consul.callback import CB

if typing.TYPE_CHECKING:
    import builtins


def parse_identities(node_identities: list[str] | None) -> dict[str, list[dict[str, str]]]:
    identities: list[dict[str, str]] = []
    if node_identities:
        for identity in node_identities:
            try:
                name, datacenter = identity.split(":", 1)
            except ValueError as e:
                raise ValueError(f"Node identity must be 'node:datacenter', got {identity!r}") from e
            identities.append({"NodeName": name, "Datacenter": datacenter})
        return {"NodeIdentities": identities}
    return {}


def _policy_links(policies_id: list[str] | None, policies_name: list[str] | None) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    if policies_id:
        links.extend({"ID": policy} for policy in policies_id)
    if policies_name:
        links.extend({"Name": policy} for policy in policies_name)
    return links


def _role_links(roles_id: list[str] | None, roles_name: list[str] | None) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    if roles_id:
        links.extend({"ID": role} for role in roles_id)
    if roles_name:
        links.extend({"Name": role} for role in roles_name)
    return links


def _templated_policy_entries(
    templated_policies: list[dict[str, dict[str, str]]] | None,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if templated_policies is not None:
        for templated_policy in templated_policies:
            for name, variables in templated_policy.items():
                entries.append({"TemplateName": name, "TemplateVariables": variables})
    return entries


class AclPolicyLink(TypedDict, total=False):
    ID: str
    Name: str


class AclToken(TypedDict, total=False):
    AccessorID: str
    SecretID: str
    Description: str
    Policies: builtins.list[AclPolicyLink]
    Roles: builtins.list[AclPolicyLink]
    ServiceIdentities: builtins.list[dict[str, Any]]
    NodeIdentities: builtins.list[dict[str, Any]]
    TemplatedPolicies: builtins.list[dict[str, Any]]
    Local: bool
    AuthMethod: str
    CreateTime: str
    Hash: str
    CreateIndex: int
    ModifyIndex: int


class Token:
    def __init__(self, agent) -> None:
        self.agent = agent

    def list(
        self,
        policy: str | None = None,
        role: str | None = None,
        authmethod: str | None = None,
        servicename: str | None = None,
        token: str | None = None,
    ) -> builtins.list[AclToken]:
        """
        Lists all the active ACL tokens. This is a privileged endpoint, and
        requires a management token. *token* will override this client's
        default token.
        Requires a token with acl:read capability. ACLPermissionDenied raised otherwise
        :param policy: Optional policy ID to filter the results by.
        :param role: Optional role ID to filter the results by.
        :param authmethod: Optional auth method name to filter the results by.
        :param servicename: Optional service name to filter the results by
            (matches tokens with a ServiceIdentity for this service).
        """
        params: list[tuple[str, Any]] = []
        if policy:
            params.append(("policy", policy))
        if role:
            params.append(("role", role))
        if authmethod:
            params.append(("authmethod", authmethod))
        if servicename:
            params.append(("servicename", servicename))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(), "/v1/acl/tokens", params=params, headers=headers)

    def read(self, accessor_id: str, token: str | None = None) -> AclToken:
        """
        Returns the token information for *accessor_id*. Requires a token with acl:read capability.
        :param accessor_id: The accessor ID of the token to read
        :param token: token with acl:read capability
        :return: selected token information
        """
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(), f"/v1/acl/token/{accessor_id}", headers=headers)

    def read_self(self, token: str | None = None) -> AclToken:
        """
        Returns the token information for the token used to authenticate the request
        (via *token*, or the client's default token). Requires no specific privileges
        beyond possessing the token's own secret.
        :param token: the token to introspect; defaults to the client's configured token
        :return: the token information
        """
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(), "/v1/acl/token/self", headers=headers)

    def delete(self, accessor_id: str, token: str | None = None) -> bool:
        """
        Deletes the token with *accessor_id*. This is a privileged endpoint, and requires a token with acl:write.
        :param accessor_id: The accessor ID of the token to delete
        :param token: token with acl:write capability
        :return: True if the token was deleted
        """
        headers = self.agent.prepare_headers(token)
        return self.agent.http.delete(CB.boolean(), f"/v1/acl/token/{accessor_id}", headers=headers)

    def clone(self, accessor_id: str, token: str | None = None, description: str = "") -> AclToken:
        """
        Clones the token identified by *accessor_id*. This is a privileged endpoint, and requires a token with acl:write.
        :param accessor_id: The accessor ID of the token to clone
        :param token: token with acl:write capability
        :param description: Optional new token description
        :return: The cloned token information
        """

        json_data = {"Description": description}
        headers = self.agent.prepare_headers(token)
        return self.agent.http.put(
            CB.json(),
            f"/v1/acl/token/{accessor_id}/clone",
            headers=headers,
            data=json.dumps(json_data),
        )

    def create(
        self,
        token: str | None = None,
        accessor_id: str | None = None,
        secret_id: str | None = None,
        node_identities: builtins.list[str] | None = None,
        service_identities: builtins.list[builtins.dict[str, Any]] | None = None,
        policies_id: builtins.list[str] | None = None,
        description: str = "",
        policies_name: builtins.list[str] | None = None,
        roles_id: builtins.list[str] | None = None,
        roles_name: builtins.list[str] | None = None,
        templated_policies: builtins.list[builtins.dict[str, builtins.dict[str, str]]] | None = None,
        expiration_time: str | None = None,
        expiration_ttl: str | None = None,
        local: bool | None = None,
    ) -> AclToken:
        """
        Create a token (optionally identified by *secret_id* and *accessor_id*).
        This is a privileged endpoint, and requires a token with acl:write.
        :param token: token with acl:write capability
        :param accessor_id: The accessor ID of the token to create
        :param secret_id: The secret ID of the token to create
        :param node_identities: Optional list of node identities (format: 'nodename:datacenter'), requires consul>=1.8.1
        :param service_identities: Optional list of service identities, e.g.
            [{"ServiceName": "web", "Datacenters": ["dc1"]}] ("Datacenters" is optional)
        :param description: Optional new token description
        :param policies_id: Optional list of policies id
        :param roles_id: Optional list of roles id
        :param roles_name: Optional list of roles name
        :param templated_policies: Optional list of templated policies,
        :param expiration_time: Optional absolute expiration timestamp (RFC3339), 1 minute
            to 24 hours in the future. Mutually exclusive with expiration_ttl.
        :param expiration_ttl: Optional expiration duration (e.g. "1h") relative to the
            token's creation time, 1 minute to 24 hours. Mutually exclusive with expiration_time.
        :param local: Optional, if True the token is local to this datacenter and not
            replicated globally.
        :return: The cloned token information
        """

        json_data: dict[str, typing.Any] = {}
        if accessor_id:
            json_data["AccessorID"] = accessor_id
        if secret_id:
            json_data["SecretID"] = secret_id
        if description:
            json_data["Description"] = description
        if service_identities is not None:
            json_data["ServiceIdentities"] = service_identities
        if expiration_time:
            json_data["ExpirationTime"] = expiration_time
        if expiration_ttl:
            json_data["ExpirationTTL"] = expiration_ttl
        if local is not None:
            json_data["Local"] = local

        json_data.update(parse_identities(node_identities))

        policies = _policy_links(policies_id, policies_name)
        if policies:
            json_data["Policies"] = policies

        roles = _role_links(roles_id, roles_name)
        if roles:
            json_data["Roles"] = roles

        templated_policy_entries = _templated_policy_entries(templated_policies)
        if templated_policy_entries:
            json_data["TemplatedPolicies"] = templated_policy_entries

        headers = self.agent.prepare_headers(token)
        return self.agent.http.put(
            CB.json(),
            "/v1/acl/token",
            headers=headers,
            data=json.dumps(json_data),
        )

    def update(
        self,
        accessor_id: str,
        token: str | None = None,
        secret_id: str | None = None,
        node_identities: builtins.list[str] | None = None,
        service_identities: builtins.list[builtins.dict[str, Any]] | None = None,
        description: str = "",
        policies_id: builtins.list[str] | None = None,
        policies_name: builtins.list[str] | None = None,
        roles_id: builtins.list[str] | None = None,
        roles_name: builtins.list[str] | None = None,
        templated_policies: builtins.list[builtins.dict[str, builtins.dict[str, str]]] | None = None,
        expiration_time: str | None = None,
        expiration_ttl: str | None = None,
        local: bool | None = None,
    ) -> AclToken:
        """
        Update a token (optionally identified by *secret_id* and *accessor_id*).
        This is a privileged endpoint, and requires a token with acl:write.
        :param accessor_id: The accessor ID of the token to update
        :param token: token with acl:write capability
        :param secret_id: Optional secret ID of the token to update
        :param node_identities: Optional list of node identities (format: 'nodename:datacenter'), requires consul>=1.8.1
        :param service_identities: Optional list of service identities, e.g.
            [{"ServiceName": "web", "Datacenters": ["dc1"]}] ("Datacenters" is optional)
        :param description: Optional new token description
        :param policies_id: Optional list of policies id
        :param roles_id: Optional list of roles id
        :param roles_name: Optional list of roles name
        :param templated_policies: Optional list of templated policies
        :param expiration_time: Optional absolute expiration timestamp (RFC3339). Note
            Consul does not allow extending a token's expiration once set.
        :param expiration_ttl: Optional expiration duration (e.g. "1h") relative to the
            token's creation time. Mutually exclusive with expiration_time.
        :param local: Optional, if True the token is local to this datacenter.
        :return: The updated token information
        """

        json_data: dict[str, typing.Any] = {"AccessorID": accessor_id}

        if secret_id:
            json_data["SecretID"] = secret_id
        if description:
            json_data["Description"] = description
        if service_identities is not None:
            json_data["ServiceIdentities"] = service_identities
        if expiration_time:
            json_data["ExpirationTime"] = expiration_time
        if expiration_ttl:
            json_data["ExpirationTTL"] = expiration_ttl
        if local is not None:
            json_data["Local"] = local

        json_data.update(parse_identities(node_identities))

        policies = _policy_links(policies_id, policies_name)
        if policies:
            json_data["Policies"] = policies

        roles = _role_links(roles_id, roles_name)
        if roles:
            json_data["Roles"] = roles

        templated_policy_entries = _templated_policy_entries(templated_policies)
        if templated_policy_entries:
            json_data["TemplatedPolicies"] = templated_policy_entries

        headers = self.agent.prepare_headers(token)
        return self.agent.http.put(
            CB.json(),
            f"/v1/acl/token/{accessor_id}",
            headers=headers,
            data=json.dumps(json_data),
        )
