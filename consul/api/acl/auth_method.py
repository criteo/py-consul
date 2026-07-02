from __future__ import annotations

import json
from typing import Any, TypedDict

from consul.callback import CB


class AclAuthMethod(TypedDict, total=False):
    Name: str
    Type: str
    DisplayName: str
    Description: str
    Config: dict[str, Any]
    MaxTokenTTL: str
    TokenLocality: str
    TokenNameFormat: str
    CreateIndex: int
    ModifyIndex: int


class AuthMethod:
    def __init__(self, agent) -> None:
        self.agent = agent

    def list(self, token: str | None = None) -> list[AclAuthMethod]:
        """
        Lists all the ACL auth methods. Note the response omits each method's *config*;
        use :meth:`read` for the full definition. Requires a token with acl:read capability.
        :param token: token with acl:read capability
        :return: the list of auth methods (without their Config)
        """
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(), "/v1/acl/auth-methods", headers=headers)

    def read(self, name: str, token: str | None = None) -> AclAuthMethod:
        """
        Returns the auth method information for *name*. Requires a token with acl:read capability.
        :param name: The name of the auth method to read
        :param token: token with acl:read capability
        :return: selected auth method information
        """
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(), f"/v1/acl/auth-method/{name}", headers=headers)

    def delete(self, name: str, token: str | None = None) -> bool:
        """
        Deletes the auth method *name*. This also deletes any binding rules and outstanding
        tokens created from it. Requires a token with acl:write capability.
        :param name: The name of the auth method to delete
        :param token: token with acl:write capability
        :return: True if the auth method was deleted
        """
        headers = self.agent.prepare_headers(token)
        return self.agent.http.delete(CB.boolean(), f"/v1/acl/auth-method/{name}", headers=headers)

    def create(
        self,
        name: str,
        method_type: str,
        token: str | None = None,
        display_name: str = "",
        description: str = "",
        config: dict[str, Any] | None = None,
        max_token_ttl: str | None = None,
        token_locality: str | None = None,
        token_name_format: str | None = None,
    ) -> AclAuthMethod:
        """
        Create an auth method. Requires a token with acl:write capability.
        :param name: Specifies a name for the auth method. Immutable once created.
        :param method_type: The type of auth method this is, e.g. "kubernetes", "jwt", "oidc". Immutable once created.
        :param token: token with acl:write capability
        :param display_name: Optional display name for use in UIs.
        :param description: Free form human-readable description of the auth method.
        :param config: The type-specific configuration for this auth method.
        :param max_token_ttl: Optional duration (e.g. "10m") after which created tokens expire.
        :param token_locality: Optional, either "local" or "global". Defaults to "local".
        :param token_name_format: Optional HIL template controlling generated token names.
        :return: The created auth method information
        """
        json_data: dict[str, Any] = {"Name": name, "Type": method_type}
        if display_name:
            json_data["DisplayName"] = display_name
        if description:
            json_data["Description"] = description
        if config is not None:
            json_data["Config"] = config
        if max_token_ttl:
            json_data["MaxTokenTTL"] = max_token_ttl
        if token_locality:
            json_data["TokenLocality"] = token_locality
        if token_name_format:
            json_data["TokenNameFormat"] = token_name_format

        headers = self.agent.prepare_headers(token)
        return self.agent.http.put(CB.json(), "/v1/acl/auth-method", headers=headers, data=json.dumps(json_data))

    def update(
        self,
        name: str,
        method_type: str,
        token: str | None = None,
        display_name: str = "",
        description: str = "",
        config: dict[str, Any] | None = None,
        max_token_ttl: str | None = None,
        token_locality: str | None = None,
        token_name_format: str | None = None,
    ) -> AclAuthMethod:
        """
        Update the auth method *name*. *method_type* must match the type the auth method was
        created with, as it is immutable. Requires a token with acl:write capability.
        :param name: The name of the auth method to update
        :param method_type: The (unchanged) type of the auth method
        :param token: token with acl:write capability
        :param display_name: Optional display name for use in UIs.
        :param description: Free form human-readable description of the auth method.
        :param config: The type-specific configuration for this auth method.
        :param max_token_ttl: Optional duration (e.g. "10m") after which created tokens expire.
        :param token_locality: Optional, either "local" or "global".
        :param token_name_format: Optional HIL template controlling generated token names.
        :return: The updated auth method information
        """
        json_data: dict[str, Any] = {"Name": name, "Type": method_type}
        if display_name:
            json_data["DisplayName"] = display_name
        if description:
            json_data["Description"] = description
        if config is not None:
            json_data["Config"] = config
        if max_token_ttl:
            json_data["MaxTokenTTL"] = max_token_ttl
        if token_locality:
            json_data["TokenLocality"] = token_locality
        if token_name_format:
            json_data["TokenNameFormat"] = token_name_format

        headers = self.agent.prepare_headers(token)
        return self.agent.http.put(
            CB.json(), f"/v1/acl/auth-method/{name}", headers=headers, data=json.dumps(json_data)
        )
