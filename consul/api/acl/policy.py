from __future__ import annotations

import json
from typing import Optional

from consul.callback import CB


class Policy:
    def __init__(self, agent) -> None:
        self.agent = agent

    def list(self, token: str | None = None):
        """
        Lists all the active ACL policies. This is a privileged endpoint, and
        requires a management token. *token* will override this client's
        default token.
        Requires a token with acl:read capability. ACLPermissionDenied raised otherwise
        """

        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(), "/v1/acl/policies", headers=headers)

    def read(self, uuid, token: str | None = None):
        """
        Returns the policy information for *id*. Requires a token with acl:read capability.
        :param uuid: Specifies the UUID of the policy you look up.
        :param token: token with acl:read capability
        :return: selected Polic information
        """
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(), f"/v1/acl/policy/{uuid}", headers=headers)

    def create(self, name: str, token: str | None = None, description: Optional[str] = None, rules=None):
        """
        Create a policy
        This is a privileged endpoint, and requires a token with acl:write.
        :param name: Specifies a name for the ACL policy.
        :param token: token with acl:write capability
        :param description: Free form human-readable description of the policy.
        :param rules: Specifies rules for the ACL policy.
        :return: The cloned token information
        """
        json_data = {"name": name}
        if rules:
            json_data["rules"] = json.dumps(rules)
        if description:
            json_data["Description"] = description
        headers = self.agent.prepare_headers(token)
        return self.agent.http.put(
            CB.json(),
            "/v1/acl/policy",
            headers=headers,
            data=json.dumps(json_data),
        )
