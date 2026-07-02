from __future__ import annotations

import json
from typing import Any, TypedDict

from consul.api.acl.auth_method import AuthMethod
from consul.api.acl.binding_rule import BindingRule
from consul.api.acl.policy import Policy
from consul.api.acl.role import Role
from consul.api.acl.templated_policy import TemplatedPolicy
from consul.api.acl.token import AclToken, Token
from consul.callback import CB


class AclLoginResult(TypedDict, total=False):
    AccessorID: str
    SecretID: str
    Description: str
    Roles: list[dict[str, str]]
    ServiceIdentities: list[dict[str, Any]]
    Local: bool
    AuthMethod: str
    CreateTime: str
    Hash: str
    CreateIndex: int
    ModifyIndex: int


class ACL:
    def __init__(self, agent) -> None:
        self.agent = agent

        self.token = self.tokens = Token(agent)
        self.policy = self.policies = Policy(agent)
        self.templated_policy = self.templated_policies = TemplatedPolicy(agent)
        self.role = self.roles = Role(agent)
        self.auth_method = self.auth_methods = AuthMethod(agent)
        self.binding_rule = self.binding_rules = BindingRule(agent)

    def bootstrap(self, bootstrap_secret: str | None = None) -> AclToken:
        """
        Performs a one-time bootstrap of the ACL system, creating the initial management token.
        Only succeeds once per cluster; fails with ACLPermissionDenied if already bootstrapped.
        Requires no token.
        :param bootstrap_secret: Optional pre-generated SecretID for the bootstrap token
            (supported on newer Consul versions; omit to let Consul generate one).
        :return: The bootstrap (initial management) token information
        """
        json_data: dict[str, Any] = {}
        if bootstrap_secret:
            json_data["BootstrapSecret"] = bootstrap_secret
        return self.agent.http.put(CB.json(), "/v1/acl/bootstrap", data=json.dumps(json_data))

    def login(
        self,
        auth_method: str,
        bearer_token: str,
        meta: dict[str, str] | None = None,
    ) -> AclLoginResult:
        """
        Exchanges an auth method bearer token for a newly-created Consul ACL token.
        Requires no token; the bearer token itself is validated against *auth_method*.
        :param auth_method: The name of the auth method to authenticate against.
        :param bearer_token: The bearer token to present to the auth method (e.g. a Kubernetes
            service account token or a signed JWT).
        :param meta: Optional key/value metadata to link to the created token.
        :return: The newly-created token information
        """
        json_data: dict[str, Any] = {"AuthMethod": auth_method, "BearerToken": bearer_token}
        if meta:
            json_data["Meta"] = meta
        return self.agent.http.post(CB.json(), "/v1/acl/login", data=json.dumps(json_data))

    def logout(self, token: str) -> bool:
        """
        Destroys a token created via :meth:`login`. Requires no privileges beyond possessing
        *token* itself.
        :param token: The secret ID of the token to destroy (not the client's default token).
        :return: True if the token was destroyed
        """
        headers = self.agent.prepare_headers(token)
        return self.agent.http.post(CB.boolean(), "/v1/acl/logout", headers=headers)
