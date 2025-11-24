from __future__ import annotations

import json
import typing

from consul.callback import CB


class TemplatedPolicy:
    def __init__(self, agent) -> None:
        self.agent = agent

    def list(self, token: str | None = None):
        """
        Lists all the templated policies.
        :param token: token with acl:read capability
        :return: A dictionary of templated policies
        """
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(), "/v1/acl/templated-policies", headers=headers)

    def read(self, name: str, token: str | None = None):
        """
        Reads a templated policy with the given name.
        :param name: The name of the templated policy to read
        :param token: token with acl:read capability
        :return: The templated policy information
        """
        headers = self.agent.prepare_headers(token)
        return self.agent.http.get(CB.json(), f"/v1/acl/templated-policy/name/{name}", headers=headers)

    def preview(
        self,
        name: str,
        template_variables: dict[str, str] | None = None,
        token: str | None = None,
    ):
        """
        Preview the result of a templated policy.
        :param name: The name of the templated policy
        :param template_variables: The variables to use in the template
        :param token: token with acl:write capability
        :return: The preview of the policy
        """
        json_data: dict[str, typing.Any] = {}
        if template_variables:
            json_data.update(template_variables)

        headers = self.agent.prepare_headers(token)
        return self.agent.http.post(
            CB.json(),
            f"/v1/acl/templated-policy/preview/{name}",
            headers=headers,
            data=json.dumps(json_data),
        )
