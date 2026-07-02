from __future__ import annotations

import json
from typing import Any, Literal, TypedDict

from consul.callback import CB

BindType = Literal["service", "node", "role", "templated-policy"]


class AclBindingRule(TypedDict, total=False):
    ID: str
    Description: str
    AuthMethod: str
    Selector: str
    BindType: str
    BindName: str
    BindVars: dict[str, Any]
    CreateIndex: int
    ModifyIndex: int


class BindingRule:
    def __init__(self, agent) -> None:
        self.agent = agent

    def list(self, auth_method: str | None = None, token: str | None = None) -> list[AclBindingRule]:
        """
        Lists all the ACL binding rules. Requires a token with acl:read capability.
        :param auth_method: Optional auth method name to filter the results by.
        :param token: token with acl:read capability
        :return: the list of binding rules
        """
        params: list[tuple[str, Any]] = []
        if auth_method:
            params.append(("authmethod", auth_method))
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(), "/v1/acl/binding-rules", params=params, headers=headers)

    def read(self, binding_rule_id: str, token: str | None = None) -> AclBindingRule:
        """
        Returns the binding rule information for *binding_rule_id*. Requires a token with acl:read capability.
        :param binding_rule_id: The ID of the binding rule to read
        :param token: token with acl:read capability
        :return: selected binding rule information
        """
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(), f"/v1/acl/binding-rule/{binding_rule_id}", headers=headers)

    def delete(self, binding_rule_id: str, token: str | None = None) -> bool:
        """
        Deletes the binding rule with *binding_rule_id*. Requires a token with acl:write capability.
        :param binding_rule_id: The ID of the binding rule to delete
        :param token: token with acl:write capability
        :return: True if the binding rule was deleted
        """
        headers = self.agent.prepare_headers(token)
        return self.agent.http.delete(CB.boolean(), f"/v1/acl/binding-rule/{binding_rule_id}", headers=headers)

    def create(
        self,
        auth_method: str,
        bind_type: BindType,
        bind_name: str,
        token: str | None = None,
        description: str = "",
        selector: str = "",
        bind_vars: dict[str, Any] | None = None,
    ) -> AclBindingRule:
        """
        Create a binding rule. Requires a token with acl:write capability.
        :param auth_method: The name of the auth method this rule applies to. Immutable once created.
        :param bind_type: One of "service", "node", "role" or "templated-policy".
        :param bind_name: Name (may use HIL templating) applied to the bound object at login.
        :param token: token with acl:write capability
        :param description: Free form human-readable description of the binding rule.
        :param selector: Expression matched against verified identity attributes at login.
        :param bind_vars: Template variables, only used when bind_type is "templated-policy".
        :return: The created binding rule information
        """
        json_data: dict[str, Any] = {"AuthMethod": auth_method, "BindType": bind_type, "BindName": bind_name}
        if description:
            json_data["Description"] = description
        if selector:
            json_data["Selector"] = selector
        if bind_vars is not None:
            json_data["BindVars"] = bind_vars

        headers = self.agent.prepare_headers(token)
        return self.agent.http.put(CB.json(), "/v1/acl/binding-rule", headers=headers, data=json.dumps(json_data))

    def update(
        self,
        binding_rule_id: str,
        auth_method: str,
        bind_type: BindType,
        bind_name: str,
        token: str | None = None,
        description: str = "",
        selector: str = "",
        bind_vars: dict[str, Any] | None = None,
    ) -> AclBindingRule:
        """
        Update the binding rule identified by *binding_rule_id*. Requires a token with acl:write capability.
        :param binding_rule_id: The ID of the binding rule to update
        :param auth_method: The (unchanged) name of the auth method this rule applies to.
        :param bind_type: One of "service", "node", "role" or "templated-policy".
        :param bind_name: Name (may use HIL templating) applied to the bound object at login.
        :param token: token with acl:write capability
        :param description: Free form human-readable description of the binding rule.
        :param selector: Expression matched against verified identity attributes at login.
        :param bind_vars: Template variables, only used when bind_type is "templated-policy".
        :return: The updated binding rule information
        """
        json_data: dict[str, Any] = {"AuthMethod": auth_method, "BindType": bind_type, "BindName": bind_name}
        if description:
            json_data["Description"] = description
        if selector:
            json_data["Selector"] = selector
        if bind_vars is not None:
            json_data["BindVars"] = bind_vars

        headers = self.agent.prepare_headers(token)
        return self.agent.http.put(
            CB.json(), f"/v1/acl/binding-rule/{binding_rule_id}", headers=headers, data=json.dumps(json_data)
        )
