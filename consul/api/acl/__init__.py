from consul.api.acl.token import Token


class ACL:
    def __init__(self, agent):
        self.agent = agent
        self.token = self.tokens = Token(agent)
