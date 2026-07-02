from __future__ import annotations

import json
import typing
from typing import Any, TypedDict

from consul.callback import CB

if typing.TYPE_CHECKING:
    import builtins


class AclPolicyLink(TypedDict, total=False):
    ID: str
    Name: str


class AclServiceIdentity(TypedDict, total=False):
    ServiceName: str
    Datacenters: builtins.list[str]


class AclNodeIdentity(TypedDict, total=False):
    NodeName: str
    Datacenter: str


class AclTemplatedPolicy(TypedDict, total=False):
    TemplateName: str
    TemplateVariables: dict[str, Any]


class AclRole(TypedDict, total=False):
    ID: str
    Name: str
    Description: str
    Policies: builtins.list[AclPolicyLink]
    ServiceIdentities: builtins.list[AclServiceIdentity]
    NodeIdentities: builtins.list[AclNodeIdentity]
    TemplatedPolicies: builtins.list[AclTemplatedPolicy]
    Hash: str
    CreateIndex: int
    ModifyIndex: int


def _role_body(
    name: str,
    description: str,
    policies_id: builtins.list[str] | None,
    policies_name: builtins.list[str] | None,
    service_identities: builtins.list[AclServiceIdentity] | None,
    node_identities: builtins.list[AclNodeIdentity] | None,
    templated_policies: builtins.list[builtins.dict[str, builtins.dict[str, str]]] | None,
) -> dict[str, Any]:
    json_data: dict[str, Any] = {"Name": name}
    if description:
        json_data["Description"] = description

    policies: list[dict[str, str]] = []
    if policies_id:
        policies.extend({"ID": policy} for policy in policies_id)
    if policies_name:
        policies.extend({"Name": policy} for policy in policies_name)
    if policies:
        json_data["Policies"] = policies

    if service_identities:
        json_data["ServiceIdentities"] = service_identities
    if node_identities:
        json_data["NodeIdentities"] = node_identities

    if templated_policies is not None:
        json_data["TemplatedPolicies"] = []
        for templated_policy in templated_policies:
            for template_name, variables in templated_policy.items():
                json_data["TemplatedPolicies"].append({"TemplateName": template_name, "TemplateVariables": variables})

    return json_data


class Role:
    def __init__(self, agent) -> None:
        self.agent = agent

    def list(self, policy: str | None = None, token: str | None = None) -> builtins.list[AclRole]:
        """
        Lists all the ACL roles. Requires a token with acl:read capability.
        :param policy: Optional policy ID to filter the results by.
        :param token: token with acl:read capability
        :return: the list of roles
        """
        params: list[tuple[str, Any]] = []
        if policy:
            params.append(("policy", policy))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(), "/v1/acl/roles", params=params, headers=headers)

    def read(self, role_id: str, token: str | None = None) -> AclRole:
        """
        Returns the role information for *role_id*. Requires a token with acl:read capability.
        :param role_id: The ID of the role to read
        :param token: token with acl:read capability
        :return: selected role information
        """
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(), f"/v1/acl/role/{role_id}", headers=headers)

    def read_by_name(self, name: str, token: str | None = None) -> AclRole:
        """
        Returns the role information for the role named *name*. Requires a token with acl:read capability.
        :param name: The name of the role to read
        :param token: token with acl:read capability
        :return: selected role information
        """
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(), f"/v1/acl/role/name/{name}", headers=headers)

    def delete(self, role_id: str, token: str | None = None) -> bool:
        """
        Deletes the role with *role_id*. Requires a token with acl:write capability.
        :param role_id: The ID of the role to delete
        :param token: token with acl:write capability
        :return: True if the role was deleted
        """
        headers = self.agent.prepare_headers(token)
        return self.agent.http.delete(CB.boolean(), f"/v1/acl/role/{role_id}", headers=headers)

    def create(
        self,
        name: str,
        token: str | None = None,
        description: str = "",
        policies_id: builtins.list[str] | None = None,
        policies_name: builtins.list[str] | None = None,
        service_identities: builtins.list[AclServiceIdentity] | None = None,
        node_identities: builtins.list[AclNodeIdentity] | None = None,
        templated_policies: builtins.list[builtins.dict[str, builtins.dict[str, str]]] | None = None,
    ) -> AclRole:
        """
        Create a role. Requires a token with acl:write capability.
        :param name: Specifies a name for the ACL role.
        :param token: token with acl:write capability
        :param description: Free form human-readable description of the role.
        :param policies_id: Optional list of policy IDs to link.
        :param policies_name: Optional list of policy names to link.
        :param service_identities: Optional list of service identities, e.g. [{"ServiceName": "web"}]
        :param node_identities: Optional list of node identities, e.g. [{"NodeName": "node1", "Datacenter": "dc1"}]
        :param templated_policies: Optional list of templated policies
        :return: The created role information
        """
        json_data = _role_body(
            name, description, policies_id, policies_name, service_identities, node_identities, templated_policies
        )
        headers = self.agent.prepare_headers(token)
        return self.agent.http.put(CB.json(), "/v1/acl/role", headers=headers, data=json.dumps(json_data))

    def update(
        self,
        role_id: str,
        name: str,
        token: str | None = None,
        description: str = "",
        policies_id: builtins.list[str] | None = None,
        policies_name: builtins.list[str] | None = None,
        service_identities: builtins.list[AclServiceIdentity] | None = None,
        node_identities: builtins.list[AclNodeIdentity] | None = None,
        templated_policies: builtins.list[builtins.dict[str, builtins.dict[str, str]]] | None = None,
    ) -> AclRole:
        """
        Update the role identified by *role_id*. Requires a token with acl:write capability.
        :param role_id: The ID of the role to update
        :param name: Specifies a name for the ACL role.
        :param token: token with acl:write capability
        :param description: Free form human-readable description of the role.
        :param policies_id: Optional list of policy IDs to link.
        :param policies_name: Optional list of policy names to link.
        :param service_identities: Optional list of service identities.
        :param node_identities: Optional list of node identities.
        :param templated_policies: Optional list of templated policies
        :return: The updated role information
        """
        json_data = _role_body(
            name, description, policies_id, policies_name, service_identities, node_identities, templated_policies
        )
        json_data["ID"] = role_id
        headers = self.agent.prepare_headers(token)
        return self.agent.http.put(CB.json(), f"/v1/acl/role/{role_id}", headers=headers, data=json.dumps(json_data))
