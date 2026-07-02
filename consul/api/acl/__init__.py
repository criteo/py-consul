from consul.api.acl.auth_method import AuthMethod
from consul.api.acl.binding_rule import BindingRule
from consul.api.acl.policy import Policy
from consul.api.acl.role import Role
from consul.api.acl.templated_policy import TemplatedPolicy
from consul.api.acl.token import Token


class ACL:
    def __init__(self, agent) -> None:
        self.agent = agent

        self.token = self.tokens = Token(agent)
        self.policy = self.policies = Policy(agent)
        self.templated_policy = self.templated_policies = TemplatedPolicy(agent)
        self.role = self.roles = Role(agent)
        self.auth_method = self.auth_methods = AuthMethod(agent)
        self.binding_rule = self.binding_rules = BindingRule(agent)
