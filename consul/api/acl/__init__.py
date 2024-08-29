from consul.api.acl.policy import Policy
from consul.api.acl.token import Token


class ACL:
    def __init__(self, agent) -> None:
        self.agent = agent

        self.token = self.tokens = Token(agent)
        self.policy = self.policies = Policy(agent)
