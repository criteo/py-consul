import json

from consul.callback import CB


class ACL:
    def __init__(self, agent):
        self.agent = agent
        self.token = self.tokens = Token(agent)


class Token:
    def __init__(self, agent):
        self.agent = agent

    def list(self, token=None):
        """
        Lists all the active ACL tokens. This is a privileged endpoint, and
        requires a management token. *token* will override this client's
        default token.
        Requires a token with acl:read capability. ACLPermissionDenied raised otherwise
        """
        params = []
        token = token or self.agent.token
        if token:
            params.append(("token", token))
        return self.agent.http.get(CB.json(), "/v1/acl/tokens", params=params)

    def read(self, accessor_id, token=None):
        """
        Returns the token information for *accessor_id*. Requires a token with acl:read capability.
        :param accessor_id: The accessor ID of the token to read
        :param token: token with acl:read capability
        :return: selected token information
        """
        params = []
        token = token or self.agent.token
        if token:
            params.append(("token", token))
        return self.agent.http.get(CB.json(), f"/v1/acl/token/{accessor_id}", params=params)

    def delete(self, accessor_id, token=None):
        """
        Deletes the token with *accessor_id*. This is a privileged endpoint, and requires a token with acl:write.
        :param accessor_id: The accessor ID of the token to delete
        :param token: token with acl:write capability
        :return: True if the token was deleted
        """
        params = []
        token = token or self.agent.token
        if token:
            params.append(("token", token))
        return self.agent.http.delete(CB.bool(), f"/v1/acl/token/{accessor_id}", params=params)

    def clone(self, accessor_id, token=None, description=""):
        """
        Clones the token identified by *accessor_id*. This is a privileged endpoint, and requires a token with acl:write.
        :param accessor_id: The accessor ID of the token to clone
        :param token: token with acl:write capability
        :param description: Optional new token description
        :return: The cloned token information
        """
        params = []
        token = token or self.agent.token
        if token:
            params.append(("token", token))

        json_data = {"Description": description}
        return self.agent.http.put(
            CB.json(),
            f"/v1/acl/token/{accessor_id}/clone",
            params=params,
            data=json.dumps(json_data),
        )

    def create(self, token=None, accessor_id=None, secret_id=None, description=""):
        """
        Create a token (optionally identified by *secret_id* and *accessor_id*).
        This is a privileged endpoint, and requires a token with acl:write.
        :param token: token with acl:write capability
        :param accessor_id: The accessor ID of the token to create
        :param secret_id: The secret ID of the token to create
        :param description: Optional new token description
        :return: The cloned token information
        """
        params = []
        token = token or self.agent.token
        if token:
            params.append(("token", token))

        json_data = {}
        if accessor_id:
            json_data["AccessorID"] = accessor_id
        if secret_id:
            json_data["SecretID"] = secret_id
        if description:
            json_data["Description"] = description
        return self.agent.http.put(
            CB.json(),
            "/v1/acl/token",
            params=params,
            data=json.dumps(json_data),
        )

    def update(self, accessor_id, token=None, secret_id=None, description=""):
        """
        Update a token (optionally identified by *secret_id* and *accessor_id*).
        This is a privileged endpoint, and requires a token with acl:write.
        :param accessor_id: The accessor ID of the token to update
        :param token: token with acl:write capability
        :param secret_id: Optional secret ID of the token to update
        :param description: Optional new token description
        :return: The updated token information
        """
        params = []
        token = token or self.agent.token
        if token:
            params.append(("token", token))

        json_data = {"AccessorID": accessor_id}
        if secret_id:
            json_data["SecretID"] = secret_id
        if description:
            json_data["Description"] = description
        return self.agent.http.put(
            CB.json(),
            f"/v1/acl/token/{accessor_id}",
            params=params,
            data=json.dumps(json_data),
        )
