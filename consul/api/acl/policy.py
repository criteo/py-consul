from consul.callback import CB


class Policy:
    def __init__(self, agent):
        self.agent = agent

    def list(self, token=None):
        """
        Lists all the active ACL policies. This is a privileged endpoint, and
        requires a management token. *token* will override this client's
        default token.
        Requires a token with acl:read capability. ACLPermissionDenied raised otherwise
        """
        params = []
        token = token or self.agent.token
        if token:
            params.append(("token", token))
        return self.agent.http.get(CB.json(), "/v1/acl/policies", params=params)

    def read(self, uuid, token=None):
        """
        Returns the policy information for *id*. Requires a token with acl:read capability.
        :param accessor_id: Specifies the UUID of the policy you lookup.
        :param token: token with acl:read capability
        :return: selected Polic information
        """
        params = []
        token = token or self.agent.token
        if token:
            params.append(("token", token))
        return self.agent.http.get(CB.json(), f"/v1/acl/policy/{uuid}", params=params)
